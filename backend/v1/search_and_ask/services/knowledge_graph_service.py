"""
知识图谱服务 — Neo4j + 本地图存储

支持两种后端：
  1. Neo4j (生产级) - 需要部署 Neo4j 服务
  2. NetworkX (轻量级) - 完全内存/本地文件，无需额外依赖
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict

from config import config
from utils.logger import logger


@dataclass
class Entity:
    """知识图谱实体"""
    id: str
    name: str
    entity_type: str
    properties: Dict[str, Any] = None
    doc_ids: List[str] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.doc_ids is None:
            self.doc_ids = []


@dataclass
class Relation:
    """知识图谱关系"""
    id: str
    source_id: str
    target_id: str
    relation_type: str
    confidence: float = 0.8
    properties: Dict[str, Any] = None
    doc_ids: List[str] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.doc_ids is None:
            self.doc_ids = []


class Neo4jKG:
    """Neo4j 知识图谱实现"""
    
    def __init__(self):
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                config.kg.NEO4J_URI,
                auth=(config.kg.NEO4J_USER, config.kg.NEO4J_PASSWORD)
            )
            self.db = config.kg.NEO4J_DATABASE
            logger.info(f"[Neo4jKG] 已连接到 {config.kg.NEO4J_URI}")
        except Exception as e:
            logger.error(f"[Neo4jKG] 连接失败: {e}")
            raise
    
    def create_entity(self, entity: Entity) -> bool:
        """创建或更新实体"""
        try:
            with self.driver.session(database=self.db) as session:
                session.write_transaction(
                    self._tx_create_entity, entity
                )
            return True
        except Exception as e:
            logger.error(f"[Neo4jKG] 创建实体失败: {e}")
            return False
    
    @staticmethod
    def _tx_create_entity(tx, entity: Entity):
        cypher = """
        MERGE (e:Entity {id: $id})
        SET e.name = $name,
            e.type = $type,
            e.properties = $props,
            e.docs = $docs
        """
        tx.run(cypher, {
            "id": entity.id,
            "name": entity.name,
            "type": entity.entity_type,
            "props": json.dumps(entity.properties),
            "docs": entity.doc_ids
        })
    
    def create_relation(self, relation: Relation) -> bool:
        """创建或更新关系"""
        try:
            with self.driver.session(database=self.db) as session:
                session.write_transaction(
                    self._tx_create_relation, relation
                )
            return True
        except Exception as e:
            logger.error(f"[Neo4jKG] 创建关系失败: {e}")
            return False
    
    @staticmethod
    def _tx_create_relation(tx, relation: Relation):
        cypher = f"""
        MATCH (src:Entity {{id: $src_id}})
        MATCH (tgt:Entity {{id: $tgt_id}})
        MERGE (src)-[r:{relation.relation_type}]->(tgt)
        SET r.confidence = $conf,
            r.properties = $props,
            r.docs = $docs
        """
        tx.run(cypher, {
            "src_id": relation.source_id,
            "tgt_id": relation.target_id,
            "conf": relation.confidence,
            "props": json.dumps(relation.properties),
            "docs": relation.doc_ids
        })
    
    def search_entity(self, name: str, limit: int = 10) -> List[Entity]:
        """搜索实体"""
        try:
            with self.driver.session(database=self.db) as session:
                result = session.read_transaction(
                    self._tx_search_entity, name, limit
                )
            return result
        except Exception as e:
            logger.error(f"[Neo4jKG] 搜索实体失败: {e}")
            return []
    
    @staticmethod
    def _tx_search_entity(tx, name: str, limit: int) -> List[Entity]:
        cypher = """
        MATCH (e:Entity)
        WHERE e.name CONTAINS $name
        RETURN e.id, e.name, e.type, e.properties, e.docs
        LIMIT $limit
        """
        result = tx.run(cypher, {"name": name, "limit": limit})
        entities = []
        for record in result:
            entities.append(Entity(
                id=record["e.id"],
                name=record["e.name"],
                entity_type=record["e.type"],
                properties=json.loads(record["e.properties"] or "{}"),
                doc_ids=record["e.docs"] or []
            ))
        return entities
    
    def multi_hop_search(
        self,
        entity_name: str,
        hops: int = 2,
        limit: int = 50
    ) -> Dict[str, Any]:
        """多跳路径搜索"""
        try:
            with self.driver.session(database=self.db) as session:
                result = session.read_transaction(
                    self._tx_multi_hop_search, entity_name, hops, limit
                )
            return result
        except Exception as e:
            logger.error(f"[Neo4jKG] 多跳搜索失败: {e}")
            return {"entities": [], "relations": []}
    
    @staticmethod
    def _tx_multi_hop_search(
        tx, entity_name: str, hops: int, limit: int
    ) -> Dict[str, Any]:
        cypher = f"""
        MATCH (start:Entity {{name: $name}})
        MATCH path = (start)-[*1..{hops}]-(end:Entity)
        WITH DISTINCT end
        LIMIT $limit
        RETURN end.id, end.name, end.type
        """
        result = tx.run(cypher, {"name": entity_name, "limit": limit})
        
        entities = []
        for record in result:
            entities.append({
                "id": record["end.id"],
                "name": record["end.name"],
                "type": record["end.type"]
            })
        
        return {"entities": entities, "relations": []}
    
    def delete_kb_data(self, kb_id: str) -> bool:
        """删除知识库相关的图数据"""
        try:
            with self.driver.session(database=self.db) as session:
                session.write_transaction(self._tx_delete_kb_data, kb_id)
            return True
        except Exception as e:
            logger.error(f"[Neo4jKG] 删除知识库数据失败: {e}")
            return False
    
    @staticmethod
    def _tx_delete_kb_data(tx, kb_id: str):
        cypher = """
        MATCH (e:Entity {kb_id: $kb_id})
        DETACH DELETE e
        """
        tx.run(cypher, {"kb_id": kb_id})


class NetworkXKG:
    """基于 NetworkX 的本地图存储"""
    
    def __init__(self):
        try:
            import networkx as nx
            self.nx = nx
            self.graph = nx.DiGraph()
            self.persist_dir = config.kg.GRAPH_PERSIST_DIR
            os.makedirs(self.persist_dir, exist_ok=True)
            
            self._load_graph()
            logger.info(f"[NetworkXKG] 图存储已初始化，节点数={self.graph.number_of_nodes()}")
        except ImportError:
            logger.error("[NetworkXKG] 需要安装 networkx")
            raise
    
    def _load_graph(self):
        """从文件加载图"""
        graph_file = os.path.join(self.persist_dir, "graph.json")
        if os.path.exists(graph_file):
            try:
                with open(graph_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.graph = self.nx.node_link_graph(data, directed=True)
                logger.info(f"[NetworkXKG] 已加载图: {graph_file}")
            except Exception as e:
                logger.warning(f"[NetworkXKG] 加载失败: {e}，使用空图")
    
    def _save_graph(self):
        """将图保存到文件"""
        graph_file = os.path.join(self.persist_dir, "graph.json")
        try:
            data = self.nx.node_link_data(self.graph)
            with open(graph_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[NetworkXKG] 保存失败: {e}")
    
    def create_entity(self, entity: Entity) -> bool:
        """创建实体节点"""
        try:
            self.graph.add_node(
                entity.id,
                name=entity.name,
                type=entity.entity_type,
                properties=entity.properties,
                doc_ids=entity.doc_ids
            )
            self._save_graph()
            return True
        except Exception as e:
            logger.error(f"[NetworkXKG] 创建实体失败: {e}")
            return False
    
    def create_relation(self, relation: Relation) -> bool:
        """创建关系边"""
        try:
            if relation.source_id not in self.graph:
                self.create_entity(Entity(
                    id=relation.source_id,
                    name=relation.source_id,
                    entity_type="Unknown"
                ))
            if relation.target_id not in self.graph:
                self.create_entity(Entity(
                    id=relation.target_id,
                    name=relation.target_id,
                    entity_type="Unknown"
                ))
            
            self.graph.add_edge(
                relation.source_id,
                relation.target_id,
                relation_type=relation.relation_type,
                confidence=relation.confidence,
                properties=relation.properties,
                doc_ids=relation.doc_ids
            )
            self._save_graph()
            return True
        except Exception as e:
            logger.error(f"[NetworkXKG] 创建关系失败: {e}")
            return False
    
    def search_entity(self, name: str, limit: int = 10) -> List[Entity]:
        """搜索实体"""
        try:
            results = []
            for node_id in self.graph.nodes():
                node = self.graph.nodes[node_id]
                if name.lower() in node.get('name', '').lower():
                    results.append(Entity(
                        id=node_id,
                        name=node.get('name', ''),
                        entity_type=node.get('type', 'Unknown'),
                        properties=node.get('properties', {}),
                        doc_ids=node.get('doc_ids', [])
                    ))
                if len(results) >= limit:
                    break
            return results
        except Exception as e:
            logger.error(f"[NetworkXKG] 搜索失败: {e}")
            return []
    
    def multi_hop_search(
        self,
        entity_name: str,
        hops: int = 2,
        limit: int = 50
    ) -> Dict[str, Any]:
        """多跳搜索"""
        try:
            start_nodes = [
                n for n in self.graph.nodes()
                if self.graph.nodes[n].get('name', '') == entity_name
            ]
            
            if not start_nodes:
                return {"entities": [], "relations": []}
            
            start_node = start_nodes[0]
            entities_set = {start_node}
            relations = []
            
            current_level = {start_node}
            for hop in range(hops):
                next_level = set()
                for node in current_level:
                    for neighbor in self.graph.successors(node):
                        if neighbor not in entities_set:
                            next_level.add(neighbor)
                            edge_data = self.graph.get_edge_data(node, neighbor)
                            relations.append({
                                "source": node,
                                "target": neighbor,
                                "relation_type": edge_data.get('relation_type', ''),
                                "confidence": edge_data.get('confidence', 0.8)
                            })
                    for neighbor in self.graph.predecessors(node):
                        if neighbor not in entities_set:
                            next_level.add(neighbor)
                            edge_data = self.graph.get_edge_data(neighbor, node)
                            relations.append({
                                "source": neighbor,
                                "target": node,
                                "relation_type": edge_data.get('relation_type', ''),
                                "confidence": edge_data.get('confidence', 0.8)
                            })
                
                entities_set.update(next_level)
                current_level = next_level
                
                if len(entities_set) >= limit:
                    break
            
            entities = [
                {
                    "id": eid,
                    "name": self.graph.nodes[eid].get('name', ''),
                    "type": self.graph.nodes[eid].get('type', 'Unknown')
                }
                for eid in list(entities_set)[:limit]
            ]
            
            return {"entities": entities, "relations": relations[:limit]}
        except Exception as e:
            logger.error(f"[NetworkXKG] 多跳搜索失败: {e}")
            return {"entities": [], "relations": []}
    
    def delete_kb_data(self, kb_id: str) -> bool:
        """删除知识库相关数据"""
        try:
            nodes_to_remove = []
            for node_id in self.graph.nodes():
                if kb_id in self.graph.nodes[node_id].get('doc_ids', []):
                    nodes_to_remove.append(node_id)
            
            for node_id in nodes_to_remove:
                self.graph.remove_node(node_id)
            
            self._save_graph()
            return True
        except Exception as e:
            logger.error(f"[NetworkXKG] 删除失败: {e}")
            return False


class KnowledgeGraphService:
    """知识图谱服务（选择合适的后端）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_backend()
        return cls._instance
    
    def _init_backend(self):
        """初始化后端"""
        if not config.kg.ENABLED:
            logger.warning("[KnowledgeGraphService] 知识图谱已禁用")
            self.backend = None
            return
        
        try:
            if config.kg.BACKEND == "neo4j":
                self.backend = Neo4jKG()
                logger.info("[KnowledgeGraphService] 使用 Neo4j 后端")
            else:
                self.backend = NetworkXKG()
                logger.info("[KnowledgeGraphService] 使用 NetworkX 后端")
        except Exception as e:
            logger.error(f"[KnowledgeGraphService] 初始化失败: {e}，知识图谱功能禁用")
            self.backend = None
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self.backend is not None
    
    def create_entity(self, entity: Entity) -> bool:
        if not self.backend:
            return False
        return self.backend.create_entity(entity)
    
    def create_relation(self, relation: Relation) -> bool:
        if not self.backend:
            return False
        return self.backend.create_relation(relation)
    
    def search_entity(self, name: str, limit: int = 10) -> List[Entity]:
        if not self.backend:
            return []
        return self.backend.search_entity(name, limit)
    
    def multi_hop_search(
        self,
        entity_name: str,
        hops: int = 2,
        limit: int = 50
    ) -> Dict[str, Any]:
        if not self.backend:
            return {"entities": [], "relations": []}
        return self.backend.multi_hop_search(entity_name, hops, limit)
    
    def delete_kb_data(self, kb_id: str) -> bool:
        if not self.backend:
            return False
        return self.backend.delete_kb_data(kb_id)
