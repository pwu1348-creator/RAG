import os
import re
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from config import config
from services.embedding_service import EmbeddingService
from retriever import SearchService
from utils.logger import logger


class QuestionAnswering:
    """问答生成器"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.embedding = EmbeddingService()
        
        self.system_prompt = """你是一个专业的文档问答助手。请根据提供的检索结果回答用户问题。

要求：
1. 仅使用提供的检索结果中的信息
2. 回答要准确、简洁、专业
3. 如果检索结果无法回答问题，请明确说明
4. 引用相关段落的出处（doc_id和chunk_index）
5. 使用中文回答"""

    def _build_context(self, results: List[Dict[str, Any]], max_chars: int = 8000) -> str:
        """构建上下文"""
        context_parts = []
        total_chars = 0
        
        for i, doc in enumerate(results, 1):
            content = doc.get('content', doc.get('text', ''))
            
            if not content:
                continue
            
            if total_chars + len(content) > max_chars:
                content = content[:max_chars - total_chars]
            
            doc_id = doc.get('doc_id', 'unknown')
            chunk_idx = doc.get('chunk_index', 0)
            page_idx = doc.get('page_idx', doc.get('page_number', 0))
            
            context_parts.append(f"[段落 {i}] (doc_id: {doc_id}, chunk: {chunk_idx}, page: {page_idx})\n{content}")
            
            total_chars += len(content)
            
            if total_chars >= max_chars:
                break
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str, is_write_mode: bool = False) -> str:
        """构建Prompt"""
        if is_write_mode:
            system_prompt = """你是一个专业的文档撰写助手。请根据提供的检索结果帮助用户撰写文档内容。

要求：
1. 仅使用提供的检索结果中的信息
2. 内容要专业、准确、有逻辑性
3. 引用相关段落的出处（doc_id和chunk_index）
4. 使用中文回答
5. 可以适当扩展和组织内容"""
        else:
            system_prompt = self.system_prompt
        
        prompt = f"""{system_prompt}

检索结果：
{context}

用户问题：
{query}

请回答："""
        
        return prompt
    
    async def chat(
        self,
        query: str,
        knowledge_base_id: str,
        chat_history: List[Dict[str, str]] = None,
        top_k: int = 10,
        min_score: float = 0.3,
        is_write_mode: bool = False,
        max_context_chars: int = 8000
    ) -> Dict[str, Any]:
        """
        问答接口（非流式）
        
        Args:
            query: 用户问题
            knowledge_base_id: 知识库ID
            chat_history: 对话历史
            top_k: 检索结果数
            min_score: 最小相似度阈值
            is_write_mode: 是否为撰写模式
            max_context_chars: 最大上下文字符数
            
        Returns:
            包含回答和引用的字典
        """
        try:
            results = self.search_service.search(
                query=query,
                knowledge_base_id=knowledge_base_id,
                top_k=top_k,
                min_score=min_score
            )
            
            context = self._build_context(results, max_context_chars)
            prompt = self._build_prompt(query, context, is_write_mode)
            
            response = await self._call_llm(prompt)
            
            citations = self._extract_citations(results)
            
            return {
                'answer': response,
                'citations': citations,
                'search_results': results[:5],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[QuestionAnswering] 问答失败: {e}")
            return {
                'answer': f"抱歉，处理您的请求时出现错误: {str(e)}",
                'citations': [],
                'search_results': [],
                'timestamp': datetime.now().isoformat()
            }
    
    async def chat_stream(
        self,
        query: str,
        knowledge_base_id: str,
        chat_history: List[Dict[str, str]] = None,
        top_k: int = 10,
        min_score: float = 0.3,
        is_write_mode: bool = False,
        max_context_chars: int = 8000
    ) -> AsyncGenerator[str, None]:
        """
        问答接口（流式）
        
        Args:
            query: 用户问题
            knowledge_base_id: 知识库ID
            chat_history: 对话历史
            top_k: 检索结果数
            min_score: 最小相似度阈值
            is_write_mode: 是否为撰写模式
            max_context_chars: 最大上下文字符数
            
        Yields:
            流式响应的文本片段
        """
        try:
            results = self.search_service.search(
                query=query,
                knowledge_base_id=knowledge_base_id,
                top_k=top_k,
                min_score=min_score
            )
            
            context = self._build_context(results, max_context_chars)
            prompt = self._build_prompt(query, context, is_write_mode)
            
            full_response = ""
            
            async for chunk in self._call_llm_stream(prompt):
                full_response += chunk
                yield chunk
            
            citations = self._extract_citations(results)
            
            yield json.dumps({
                'citations': citations,
                'search_results': results[:5],
                'timestamp': datetime.now().isoformat()
            }, ensure_ascii=False) + '\n'
            
        except Exception as e:
            logger.error(f"[QuestionAnswering] 流式问答失败: {e}")
            yield json.dumps({
                'answer': f"抱歉，处理您的请求时出现错误: {str(e)}",
                'citations': [],
                'timestamp': datetime.now().isoformat()
            }, ensure_ascii=False) + '\n'
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM生成回答（占位符）"""
        from openai import OpenAI
        
        client = OpenAI(
            base_url=config.embedding.BASE_URL,
            api_key=config.embedding.API_KEY
        )
        
        try:
            response = client.chat.completions.create(
                model=config.embedding.MODEL.replace('-Embedding', '-Chat'),
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2048
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"[QuestionAnswering] LLM调用失败: {e}")
            return "抱歉，生成回答时出现错误。"
    
    async def _call_llm_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """调用LLM生成回答（流式，占位符）"""
        from openai import OpenAI
        
        client = OpenAI(
            base_url=config.embedding.BASE_URL,
            api_key=config.embedding.API_KEY
        )
        
        try:
            response = client.chat.completions.create(
                model=config.embedding.MODEL.replace('-Embedding', '-Chat'),
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2048,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"[QuestionAnswering] LLM流式调用失败: {e}")
    
    def _extract_citations(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取引用"""
        citations = []
        seen = set()
        
        for doc in results:
            doc_id = doc.get('doc_id', '')
            chunk_idx = doc.get('chunk_index', 0)
            
            if (doc_id, chunk_idx) in seen:
                continue
            
            seen.add((doc_id, chunk_idx))
            
            citations.append({
                'doc_id': doc_id,
                'chunk_index': chunk_idx,
                'content': doc.get('content', '')[:200] + '...',
                'similarity': doc.get('similarity', doc.get('bm25_score', 0))
            })
        
        return citations[:5]
