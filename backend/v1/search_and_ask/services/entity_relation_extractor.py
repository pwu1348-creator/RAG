"""
实体与关系提取模块 — 使用 LLM 自动从文本中抽取

流程：
  1. 将文本分割成合理长度（避免 LLM token 超限）
  2. 调用 LLM 提示词进行实体识别和关系抽取
  3. 解析 LLM 输出，构建 Entity 和 Relation 对象
  4. 存储到知识图谱
"""

import json
import asyncio
import hashlib
from typing import List, Dict, Any, Tuple
from datetime import datetime

from config import config
from services.knowledge_graph_service import (
    KnowledgeGraphService, Entity, Relation
)
from utils.logger import logger


EXTRACTION_PROMPT = """
你是一个专业的知识图谱提取专家。请从以下文本中提取实体和关系信息。

【文本内容】
{text}

【任务】
1. 识别文本中的关键实体，包括：
   - Person（人物）：人名、组织负责人等
   - Organization（组织）：公司、机构、部门等
   - Location（地点）：城市、国家、地区等
   - Product（产品）：具体产品名称
   - Concept（概念）：抽象概念、理论、技术名词等
   - Event（事件）：重要事件、时间点
   - Attribute（属性）：特征、性质

2. 识别实体之间的关系类型，包括：
   - 属于（belongs_to）：X属于Y
   - 包含（contains）：X包含Y
   - 关联（associated_with）：X与Y关联
   - 生产/制造（produces）：X生产Y
   - 发生地点（located_in）：X位于Y
   - 时间关系（occurred_at）：X发生于Y

【输出格式】
请以严格的 JSON 格式输出，格式如下：
{{
  "entities": [
    {{
      "text": "实体文本",
      "type": "Person|Organization|Location|Product|Concept|Event|Attribute",
      "confidence": 0.95
    }}
  ],
  "relations": [
    {{
      "source": "源实体文本",
      "target": "目标实体文本",
      "relation_type": "关系类型",
      "confidence": 0.90
    }}
  ]
}}

【约束条件】
- 只返回 JSON，不要包含其他内容
- confidence 值应该在 0.5-1.0 之间
- 关系的源和目标必须是已识别的实体
- 最多识别 {max_entities} 个实体和 {max_relations} 个关系
"""


class EntityRelationExtractor:
    """实体和关系提取器"""
    
    def __init__(self):
        self.kg_service = KnowledgeGraphService()
    
    async def extract_from_document(
        self,
        doc_id: str,
        kb_id: str,
        content: str,
        chunk_size: int = 2000,
    ) -> Tuple[List[Entity], List[Relation]]:
        """
        从文档提取实体和关系
        
        Args:
            doc_id: 文档ID
            kb_id: 知识库ID
            content: 文档内容
            chunk_size: 分块大小（字符数）
        
        Returns:
            (entities, relations) 元组
        """
        if not self.kg_service.is_enabled():
            logger.warning("[EntityRelationExtractor] 知识图谱已禁用")
            return [], []
        
        try:
            chunks = self._split_text(content, chunk_size)
            all_entities = []
            all_relations = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"[EntityRelationExtractor] 处理块 {i+1}/{len(chunks)}")
                entities, relations = await self._extract_chunk(
                    chunk, doc_id, kb_id
                )
                all_entities.extend(entities)
                all_relations.extend(relations)
            
            unique_entities = self._deduplicate_entities(all_entities)
            unique_relations = self._deduplicate_relations(all_relations)
            
            for entity in unique_entities:
                self.kg_service.create_entity(entity)
            
            for relation in unique_relations:
                self.kg_service.create_relation(relation)
            
            logger.info(
                f"[EntityRelationExtractor] 完成提取：实体={len(unique_entities)}, "
                f"关系={len(unique_relations)}"
            )
            
            return unique_entities, unique_relations
        
        except Exception as e:
            logger.error(f"[EntityRelationExtractor] 提取失败: {e}", exc_info=True)
            return [], []
    
    async def _extract_chunk(
        self,
        text: str,
        doc_id: str,
        kb_id: str,
    ) -> Tuple[List[Entity], List[Relation]]:
        """提取单个文本块"""
        try:
            prompt = EXTRACTION_PROMPT.format(
                text=text,
                max_entities=config.kg.MAX_ENTITIES_PER_DOC,
                max_relations=config.kg.MAX_RELATIONS_PER_DOC,
            )
            
            result_text = await self._call_llm(prompt)
            
            entities, relations = self._parse_extraction(
                result_text, doc_id, kb_id, text
            )
            
            return entities, relations
        
        except Exception as e:
            logger.error(f"[EntityRelationExtractor] 块提取失败: {e}")
            return [], []
    
    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM 进行提取（httpx 直接请求，与 qa.py 保持一致）"""
        import httpx
        import json as _json

        url = f"{config.llm.BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.llm.API_KEY}",
        }
        body: dict = {
            "model": config.llm.MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的知识图谱提取专家。请提取实体和关系，并严格按照 JSON 格式输出。",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "temperature": 0.3,
            "max_tokens": 2048,
            "top_p": config.llm.TOP_P,
            "n": 1,
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"] or ""
        except Exception as e:
            logger.error(f"[EntityRelationExtractor] LLM 调用失败: {e}")
            return "{\"entities\": [], \"relations\": []}"
    
    def _parse_extraction(
        self,
        result_text: str,
        doc_id: str,
        kb_id: str,
        chunk_text: str
    ) -> Tuple[List[Entity], List[Relation]]:
        """解析 LLM 输出"""
        entities = []
        relations = []
        
        try:
            json_text = result_text
            if "```json" in result_text:
                json_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                json_text = result_text.split("```")[1].split("```")[0]
            
            data = json.loads(json_text)
            
            entity_names = set()
            
            for item in data.get("entities", []):
                if item.get("confidence", 0) < config.kg.MIN_CONFIDENCE:
                    continue
                
                entity_text = item.get("text", "").strip()
                if not entity_text:
                    continue
                
                entity_id = self._make_entity_id(entity_text, item.get("type", ""))
                entity_names.add(entity_text)
                
                entity = Entity(
                    id=entity_id,
                    name=entity_text,
                    entity_type=item.get("type", "Concept"),
                    properties={
                        "source": "extracted",
                        "extraction_time": datetime.now().isoformat(),
                    },
                    doc_ids=[doc_id]
                )
                entities.append(entity)
            
            for item in data.get("relations", []):
                if item.get("confidence", 0) < config.kg.MIN_CONFIDENCE:
                    continue
                
                source = item.get("source", "").strip()
                target = item.get("target", "").strip()
                
                if not source or not target:
                    continue
                
                if source not in entity_names or target not in entity_names:
                    continue
                
                source_id = self._make_entity_id(source, "")
                target_id = self._make_entity_id(target, "")
                relation_id = self._make_relation_id(source_id, target_id, item.get("relation_type"))
                
                relation = Relation(
                    id=relation_id,
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=item.get("relation_type", "related_to"),
                    confidence=min(item.get("confidence", 0.8), 1.0),
                    properties={
                        "source": "extracted",
                        "extraction_time": datetime.now().isoformat(),
                    },
                    doc_ids=[doc_id]
                )
                relations.append(relation)
        
        except json.JSONDecodeError:
            logger.warning("[EntityRelationExtractor] 无法解析 LLM 输出为 JSON")
        except Exception as e:
            logger.error(f"[EntityRelationExtractor] 解析失败: {e}")
        
        return entities, relations
    
    @staticmethod
    def _split_text(text: str, chunk_size: int = 2000) -> List[str]:
        """将文本分块"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        sentences = text.replace("。", "。\n").replace("！", "！\n").replace("？", "？\n").split("\n")
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    @staticmethod
    def _make_entity_id(name: str, entity_type: str) -> str:
        """生成实体 ID"""
        key = f"{name}_{entity_type}".lower()
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    @staticmethod
    def _make_relation_id(source_id: str, target_id: str, relation_type: str) -> str:
        """生成关系 ID"""
        key = f"{source_id}_{target_id}_{relation_type}".lower()
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """去重实体（按 ID）"""
        seen = {}
        for entity in entities:
            if entity.id not in seen:
                seen[entity.id] = entity
            else:
                seen[entity.id].doc_ids = list(set(
                    seen[entity.id].doc_ids + entity.doc_ids
                ))
        return list(seen.values())
    
    def _deduplicate_relations(self, relations: List[Relation]) -> List[Relation]:
        """去重关系（按 source + target + type）"""
        seen = {}
        for relation in relations:
            key = (relation.source_id, relation.target_id, relation.relation_type)
            if key not in seen:
                seen[key] = relation
            else:
                seen[key].doc_ids = list(set(
                    seen[key].doc_ids + relation.doc_ids
                ))
                seen[key].confidence = max(
                    seen[key].confidence,
                    relation.confidence
                )
        return list(seen.values())
