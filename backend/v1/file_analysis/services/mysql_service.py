import os
import uuid
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
import pymysql
from pymysql.cursors import DictCursor
from pymysql.connections import Connection

from config import config
from models.document import DocumentMetadata, DocumentChunk
from utils.logger import logger


def convert_datetime(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj


class MySQLService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.connection_pool = self._create_pool()
        self._init_tables()
    
    def _create_pool(self):
        return pymysql.connect(
            host=config.mysql.HOST,
            port=config.mysql.PORT,
            user=config.mysql.USER,
            password=config.mysql.PASSWORD,
            database=config.mysql.DATABASE,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
    
    def _get_connection(self) -> Connection:
        return pymysql.connect(
            host=config.mysql.HOST,
            port=config.mysql.PORT,
            user=config.mysql.USER,
            password=config.mysql.PASSWORD,
            database=config.mysql.DATABASE,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
    
    def _init_tables(self):
        """
        初始化数据库表（如果表不存在则创建）
        """
        create_documents_table = """
        CREATE TABLE IF NOT EXISTS documents (
            doc_id VARCHAR(64) PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            file_type VARCHAR(32),
            file_size BIGINT,
            minio_url TEXT,
            minio_bucket VARCHAR(128),
            minio_object VARCHAR(512),
            total_pages INT DEFAULT 0,
            total_chunks INT DEFAULT 0,
            text_length INT DEFAULT 0,
            title VARCHAR(512),
            has_images BOOLEAN DEFAULT FALSE,
            has_tables BOOLEAN DEFAULT FALSE,
            has_formulas BOOLEAN DEFAULT FALSE,
            processing_time FLOAT,
            status ENUM('processing', 'completed', 'failed') DEFAULT 'processing',
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            extra_metadata JSON,
            INDEX idx_status (status),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        create_chunks_table = """
        CREATE TABLE IF NOT EXISTS document_chunks (
            chunk_id VARCHAR(128) PRIMARY KEY,
            doc_id VARCHAR(64) NOT NULL,
            content TEXT,
            chunk_index INT,
            page_number INT,
            start_pos INT,
            end_pos INT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
            INDEX idx_doc_id (doc_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        create_kb_doc_relations_table = """
        CREATE TABLE IF NOT EXISTS kb_document_relations (
            relation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            kb_id VARCHAR(64) NOT NULL,
            doc_id VARCHAR(64) NOT NULL,
            status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
            progress INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_kb_doc (kb_id, doc_id),
            INDEX idx_kb (kb_id),
            INDEX idx_doc (doc_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(create_documents_table)
                cursor.execute(create_chunks_table)
                cursor.execute(create_kb_doc_relations_table)
                conn.commit()
            logger.info("MySQL tables initialized")
        except Exception as e:
            logger.error(f"Init tables failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def _migrate_tables(self):
        pass
    
    def create_document(self, metadata: DocumentMetadata) -> str:
        """
        创建文档记录
        
        Args:
            metadata: 文档元数据对象
            
        Returns:
            doc_id: 文档ID
        """
        doc_id = metadata.doc_id or str(uuid.uuid4())
        
        sql = """
        INSERT INTO documents 
        (doc_id, filename, file_type, file_size, minio_url, minio_bucket, minio_object,
         total_pages, total_chunks, text_length, status, extra_metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # 修复：将 extra_metadata 转换为 JSON 字符串
        extra_metadata = metadata.extra_metadata
        if isinstance(extra_metadata, dict):
            extra_metadata = json.dumps(extra_metadata)
        elif extra_metadata is None:
            extra_metadata = json.dumps({})
        # 如果已经是字符串，直接使用
        
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    doc_id,
                    metadata.filename,
                    metadata.file_type,
                    metadata.file_size,
                    metadata.minio_url,
                    metadata.minio_bucket,
                    metadata.minio_object,
                    metadata.total_pages,
                    metadata.total_chunks,
                    metadata.text_length,
                    metadata.status,
                    extra_metadata
                ))
                conn.commit()
            
            logger.info(f"Created document: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Create document failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def update_document_status(self, doc_id: str, status: str, **kwargs):
        """
        更新文档状态
        
        Args:
            doc_id: 文档ID
            status: 新的状态
            **kwargs: 其他要更新的字段
        """
        return self.update_document(doc_id, status=status, **kwargs)
    
    def update_document(self, doc_id: str, **kwargs):
        """
        更新文档
        
        Args:
            doc_id: 文档ID
            **kwargs: 要更新的字段
        """
        fields = []
        values = []
        
        for key, value in kwargs.items():
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            fields.append(f"{key} = %s")
            values.append(value)
        
        if not fields:
            return False
        
        fields.append("updated_at = %s")
        values.append(datetime.now())
        values.append(doc_id)
        
        sql = f"UPDATE documents SET {', '.join(fields)} WHERE doc_id = %s"
        
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, values)
                conn.commit()
            
            logger.info(f"Updated document {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Update document failed: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档记录
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档数据字典或 None
        """
        sql = "SELECT * FROM documents WHERE doc_id = %s"
        
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (doc_id,))
                result = cursor.fetchone()
                if result:
                    return {k: convert_datetime(v) for k, v in result.items()}
                return result
        except Exception as e:
            logger.error(f"Get document failed: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def delete_document(self, doc_id: str):
        """
        删除文档记录（彻底删除，谨慎使用）
        
        Args:
            doc_id: 文档ID
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT minio_object, minio_url FROM documents WHERE doc_id = %s", (doc_id,))
                result = cursor.fetchone()
                if result:
                    file_path = result.get('minio_object') or result.get('minio_url')
                    if file_path and not os.path.isabs(file_path):
                        file_path = os.path.join('uploads', file_path)
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.info(f"Deleted physical file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete physical file: {e}")
                
                cursor.execute("DELETE FROM documents WHERE doc_id = %s", (doc_id,))
                conn.commit()
            
            logger.info(f"Deleted document: {doc_id}")
            
        except Exception as e:
            logger.error(f"Delete document failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def list_documents(
        self,
        user_id: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """
        列出文档
        
        Args:
            user_id: 用户ID（可选）
            knowledge_base_id: 知识库ID（可选）- 通过关联表查询
            status: 文档状态（可选）
            page: 页码（从 1 开始）
            size: 每页数量
            
        Returns:
            包含文档列表和分页信息的字典
        """
        if knowledge_base_id:
            return self.list_kb_documents(knowledge_base_id, status, page, size)
        
        where_clauses = []
        values = []
        
        if user_id:
            where_clauses.append("user_id = %s")
            values.append(user_id)
        
        if status:
            where_clauses.append("status = %s")
            values.append(status)
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        count_sql = f"SELECT COUNT(*) as total FROM documents {where_sql}"
        query_sql = f"SELECT * FROM documents {where_sql} ORDER BY created_at DESC LIMIT %s OFFSET %s"
        
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(count_sql, values)
                total = cursor.fetchone()['total']
                
                offset = (page - 1) * size
                cursor.execute(query_sql, values + [size, offset])
                documents = cursor.fetchall()
            
            converted_documents = []
            for doc in documents:
                converted_doc = {k: convert_datetime(v) for k, v in doc.items()}
                converted_documents.append(converted_doc)
            
            return {
                'total': total,
                'page': page,
                'size': size,
                'documents': converted_documents
            }
            
        except Exception as e:
            logger.error(f"List documents failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def list_kb_documents(self, kb_id: str, status: Optional[str] = None,
                         page: int = 1, size: int = 10) -> Dict[str, Any]:
        where_clauses = ["r.kb_id = %s"]
        values = [kb_id]
        
        if status:
            where_clauses.append("r.status = %s")
            values.append(status)
        
        where_sql = "WHERE " + " AND ".join(where_clauses)
        
        count_sql = f"""
            SELECT COUNT(*) as total 
            FROM kb_document_relations r 
            JOIN documents d ON r.doc_id = d.doc_id 
            {where_sql}
        """
        query_sql = f"""
            SELECT d.*, r.status as kb_status, r.progress as kb_progress, r.created_at as kb_created_at, r.updated_at as kb_updated_at
            FROM kb_document_relations r 
            JOIN documents d ON r.doc_id = d.doc_id 
            {where_sql}
            ORDER BY r.created_at DESC 
            LIMIT %s OFFSET %s
        """
        
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(count_sql, values)
                total = cursor.fetchone()['total']
                
                offset = (page - 1) * size
                cursor.execute(query_sql, values + [size, offset])
                documents = cursor.fetchall()
            
            converted_documents = []
            for doc in documents:
                converted_doc = {k: convert_datetime(v) for k, v in doc.items()}
                converted_documents.append(converted_doc)
            
            return {
                'total': total,
                'page': page,
                'size': size,
                'documents': converted_documents
            }
            
        except Exception as e:
            logger.error(f"List KB documents failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def associate_document_to_kb(self, kb_id: str, doc_id: str) -> bool:
        sql = """
            INSERT INTO kb_document_relations (kb_id, doc_id, status) 
            VALUES (%s, %s, 'pending')
            ON DUPLICATE KEY UPDATE status = 'pending'
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (kb_id, doc_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Associate document to KB failed: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def remove_document_from_kb(self, kb_id: str, doc_id: str) -> bool:
        sql = "DELETE FROM kb_document_relations WHERE kb_id = %s AND doc_id = %s"
        delete_chunks_sql = "DELETE FROM document_chunks WHERE kb_id = %s AND doc_id = %s"
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(delete_chunks_sql, (kb_id, doc_id))
                cursor.execute(sql, (kb_id, doc_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Remove document from KB failed: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def delete_kb_all_relations(self, kb_id: str) -> bool:
        sql = "DELETE FROM kb_document_relations WHERE kb_id = %s"
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (kb_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Delete KB all relations failed: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def update_kb_document_status(self, kb_id: str, doc_id: str, status: str, progress: int = None) -> bool:
        if progress is not None:
            sql = "UPDATE kb_document_relations SET status = %s, progress = %s WHERE kb_id = %s AND doc_id = %s"
            params = (status, progress, kb_id, doc_id)
        else:
            sql = "UPDATE kb_document_relations SET status = %s WHERE kb_id = %s AND doc_id = %s"
            params = (status, kb_id, doc_id)
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Update KB document status failed: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def list_unlinked_documents(self, page: int = 1, size: int = 10) -> Dict[str, Any]:
        sql = """
            SELECT d.* FROM documents d 
            WHERE d.doc_id NOT IN (
                SELECT doc_id FROM kb_document_relations
            )
            ORDER BY d.created_at DESC 
            LIMIT %s OFFSET %s
        """
        count_sql = """
            SELECT COUNT(*) as total FROM documents d 
            WHERE d.doc_id NOT IN (
                SELECT doc_id FROM kb_document_relations
            )
        """
        
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(count_sql)
                total = cursor.fetchone()['total']
                
                offset = (page - 1) * size
                cursor.execute(sql, [size, offset])
                documents = cursor.fetchall()
            
            converted_documents = []
            for doc in documents:
                converted_doc = {k: convert_datetime(v) for k, v in doc.items()}
                converted_documents.append(converted_doc)
            
            return {
                'total': total,
                'page': page,
                'size': size,
                'documents': converted_documents
            }
            
        except Exception as e:
            logger.error(f"List unlinked documents failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_chunks(self, doc_id: str, kb_id: str, chunks: List[Dict[str, Any]]):
        """
        保存文档分块
        
        Args:
            doc_id: 文档ID
            kb_id: 知识库ID
            chunks: 分块列表，每个分块是一个字典
        """
        if not chunks:
            return
        
        sql = """
        INSERT INTO document_chunks 
        (chunk_id, doc_id, kb_id, content, chunk_index, page_idx, bbox, chunk_type, img_id, char_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{kb_id}_{doc_id}_chunk_{i}"
                    content = chunk.get('content', chunk.get('text', ''))
                    bbox = chunk.get('bbox')
                    bbox_str = ','.join(map(str, bbox)) if bbox else None
                    
                    cursor.execute(sql, (
                        chunk_id,
                        doc_id,
                        kb_id,
                        content,
                        i,
                        chunk.get('page_idx', 0),
                        bbox_str,
                        chunk.get('type', 'text'),
                        chunk.get('img_id', ''),
                        len(content)
                    ))
                conn.commit()
            
            logger.info(f"Saved {len(chunks)} chunks for doc: {doc_id}, kb: {kb_id}")
            
        except Exception as e:
            logger.error(f"Save chunks failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_images(self, doc_id: str, kb_id: str, images: List[Dict[str, Any]]):
        """
        保存文档图片元数据
        
        Args:
            doc_id: 文档ID
            kb_id: 知识库ID
            images: 图片列表，每个图片是一个字典
        """
        if not images:
            return
        
        sql = """
        INSERT INTO document_images 
        (img_id, doc_id, kb_id, img_url, img_path_local, page_idx, bbox)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                for img in images:
                    bbox = img.get('bbox')
                    bbox_str = ','.join(map(str, bbox)) if bbox else None
                    
                    cursor.execute(sql, (
                        img.get('img_id', ''),
                        doc_id,
                        kb_id,
                        img.get('img_url', ''),
                        img.get('img_path_local', ''),
                        img.get('page_idx', 0),
                        bbox_str
                    ))
                conn.commit()
            
            logger.info(f"Saved {len(images)} images for doc: {doc_id}, kb: {kb_id}")
            
        except Exception as e:
            logger.error(f"Save images failed: {e}")
            raise
        finally:
            if conn:
                conn.close()