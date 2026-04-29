"""
服务模块：文档重索引

将知识库中的文档按父子分块策略重新索引：
1. 读取现有文档 chunks（按 doc_id 聚合原文）
2. 使用 ParentChildChunker 切分为父块 + 子块
3. 父块 → MySQL document_chunks (chunk_type='parent')
4. 子块 → MySQL document_chunks (chunk_type='child') + ChromaDB（带 embedding + parent_chunk_id 元数据）
5. 清理旧的非父子 chunks
"""

import uuid
from typing import List, Dict, Any, Optional
from collections import defaultdict

from config import config
from core.chunker import ParentChildChunker
from services.chromadb_service import ChromaDBService
from services.embedding_service import EmbeddingService
from utils.logger import logger


class IndexService:
    """文档重索引服务"""

    def __init__(self):
        self.chunker = ParentChildChunker()
        self.chromadb = ChromaDBService()
        self.embedding = EmbeddingService()
        self._mysql = None

    # ------------------------------------------------------------------
    # MySQL 连接
    # ------------------------------------------------------------------

    def _get_mysql_conn(self):
        if self._mysql is None or not getattr(self._mysql, "open", False):
            import pymysql
            from pymysql.cursors import DictCursor
            self._mysql = pymysql.connect(
                host=config.mysql.HOST,
                port=config.mysql.PORT,
                user=config.mysql.USER,
                password=config.mysql.PASSWORD,
                database=config.mysql.DATABASE,
                charset="utf8mb4",
                cursorclass=DictCursor,
            )
        return self._mysql

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def reindex_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """重索整个知识库的所有文档"""
        doc_ids = self._get_kb_doc_ids(kb_id)
        total_parents = 0
        total_children = 0
        processed = 0

        for doc_id in doc_ids:
            try:
                p, c = self.reindex_document(doc_id, kb_id)
                total_parents += p
                total_children += c
                processed += 1
            except Exception as e:
                logger.error(f"[IndexService] 文档重索引失败 doc={doc_id}: {e}")

        logger.info(
            f"[IndexService] KB={kb_id} 重索引完成: "
            f"docs={processed} parents={total_parents} children={total_children}"
        )
        return {
            "success": True,
            "kb_id": kb_id,
            "docs_processed": processed,
            "parents": total_parents,
            "children": total_children,
        }

    def reindex_document(self, doc_id: str, kb_id: str) -> tuple:
        """重索单个文档；返回 (parent_count, child_count)"""
        text = self._get_document_text(doc_id)
        if not text:
            logger.warning(f"[IndexService] 文档无内容，跳过: {doc_id}")
            return 0, 0

        title = self._get_document_title(doc_id) or ""

        parents, children = self.chunker.chunk(
            text=text, doc_id=doc_id, kb_id=kb_id, title=title
        )
        if not parents or not children:
            logger.warning(f"[IndexService] 分块结果为空: {doc_id}")
            return 0, 0

        self._delete_old_chunks(doc_id, kb_id)
        self._save_parents_to_mysql(parents, doc_id, kb_id)
        self._save_children(children, doc_id, kb_id)

        return len(parents), len(children)

    # ------------------------------------------------------------------
    # 数据读取
    # ------------------------------------------------------------------

    def _get_kb_doc_ids(self, kb_id: str) -> List[str]:
        conn = self._get_mysql_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT doc_id FROM document_chunks WHERE kb_id = %s", (kb_id,)
            )
            return [r["doc_id"] for r in cur.fetchall()]

    def _get_document_text(self, doc_id: str) -> str:
        conn = self._get_mysql_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT content FROM document_chunks WHERE doc_id = %s ORDER BY chunk_index",
                (doc_id,),
            )
            rows = cur.fetchall()
        return "\n\n".join(r["content"] for r in rows if r.get("content"))

    def _get_document_title(self, doc_id: str) -> str:
        conn = self._get_mysql_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT title FROM documents WHERE doc_id = %s", (doc_id,))
            row = cur.fetchone()
        return (row or {}).get("title", "")

    # ------------------------------------------------------------------
    # 数据清理
    # ------------------------------------------------------------------

    def _delete_old_chunks(self, doc_id: str, kb_id: str):
        """删除文档旧 chunks（MySQL + ChromaDB）"""
        conn = self._get_mysql_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM document_chunks WHERE doc_id = %s AND kb_id = %s",
                    (doc_id, kb_id),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"[IndexService] MySQL 删除旧 chunks 失败: {e}")

        try:
            self.chromadb.collection.delete(
                where={"$and": [{"doc_id": doc_id}, {"kb_id": kb_id}]}
            )
        except Exception as e:
            logger.error(f"[IndexService] ChromaDB 删除旧 chunks 失败: {e}")

    # ------------------------------------------------------------------
    # 数据写入
    # ------------------------------------------------------------------

    def _save_parents_to_mysql(
        self, parents: List[Dict[str, Any]], doc_id: str, kb_id: str
    ):
        """父块仅写 MySQL"""
        conn = self._get_mysql_conn()
        sql = (
            "INSERT INTO document_chunks "
            "(chunk_id, doc_id, kb_id, content, chunk_index, page_idx, chunk_type, char_count) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        )
        try:
            with conn.cursor() as cur:
                for p in parents:
                    cur.execute(
                        sql,
                        (
                            p["chunk_id"], doc_id, kb_id, p["content"],
                            p["chunk_index"], p.get("page_idx", 0),
                            "parent", p.get("char_count", len(p["content"])),
                        ),
                    )
                conn.commit()
            logger.info(f"[IndexService] 写入 {len(parents)} 个父块到 MySQL")
        except Exception as e:
            logger.error(f"[IndexService] 父块写入失败: {e}")
            raise

    def _save_children(
        self, children: List[Dict[str, Any]], doc_id: str, kb_id: str
    ):
        """子块写入 MySQL + ChromaDB（含 embedding）"""
        # MySQL
        conn = self._get_mysql_conn()
        sql = (
            "INSERT INTO document_chunks "
            "(chunk_id, doc_id, kb_id, content, chunk_index, page_idx, chunk_type, char_count) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        )
        try:
            with conn.cursor() as cur:
                for c in children:
                    cur.execute(
                        sql,
                        (
                            c["chunk_id"], doc_id, kb_id, c["content"],
                            c["chunk_index"], c.get("page_idx", 0),
                            "child", c.get("char_count", len(c["content"])),
                        ),
                    )
                conn.commit()
            logger.info(f"[IndexService] 写入 {len(children)} 个子块到 MySQL")
        except Exception as e:
            logger.error(f"[IndexService] 子块 MySQL 写入失败: {e}")
            raise

        # ChromaDB
        try:
            texts = [c["content"] for c in children]
            embeddings = self.embedding.encode(texts) if texts else []

            self.chromadb.collection.add(
                ids=[c["chunk_id"] for c in children],
                documents=texts,
                metadatas=[
                    {
                        "doc_id": doc_id,
                        "kb_id": kb_id,
                        "chunk_index": c["chunk_index"],
                        "page_idx": c.get("page_idx", 0),
                        "chunk_type": "child",
                        "parent_chunk_id": c.get("parent_chunk_id", ""),
                    }
                    for c in children
                ],
                embeddings=embeddings if embeddings else None,
            )
            logger.info(f"[IndexService] 写入 {len(children)} 个子块到 ChromaDB")
        except Exception as e:
            logger.error(f"[IndexService] 子块 ChromaDB 写入失败: {e}")
            raise
