"""
对话持久化服务 — ConversationService

负责对话会话和消息的 MySQL 存储，替代前端 localStorage 方案。

表结构（自动建表）：
  chat_conversations  — 会话表（一个 conversation_id 对应一段对话）
  chat_messages       — 消息表（每条 user/assistant 消息单独一行）

使用方式：
  svc = ConversationService()
  conv_id = svc.create(user_id="xxx", kb_id="yyy", title="新对话")
  svc.append_message(conv_id, role="user", content="你好")
  msgs = svc.get_messages(conv_id)
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

import pymysql
from pymysql.cursors import DictCursor

from config import config
from utils.logger import logger


# ---------------------------------------------------------------------------
# 建表 SQL（首次启动自动执行）
# ---------------------------------------------------------------------------

_CREATE_CONVERSATIONS_SQL = """
CREATE TABLE IF NOT EXISTS chat_conversations (
    id          VARCHAR(64)  PRIMARY KEY COMMENT '会话唯一ID',
    user_id     VARCHAR(64)  NOT NULL    COMMENT '所属用户ID（admin用固定值admin）',
    kb_id       VARCHAR(64)  NOT NULL    COMMENT '关联知识库ID',
    title       VARCHAR(200) NOT NULL DEFAULT '新对话' COMMENT '会话标题',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id   (user_id),
    INDEX idx_kb_id     (kb_id),
    INDEX idx_update    (update_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话会话表';
"""

_CREATE_MESSAGES_SQL = """
CREATE TABLE IF NOT EXISTS chat_messages (
    id              BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '消息自增ID',
    conversation_id VARCHAR(64)  NOT NULL    COMMENT '所属会话ID',
    role            VARCHAR(16)  NOT NULL    COMMENT 'user / assistant',
    content         MEDIUMTEXT   NOT NULL    COMMENT '消息正文',
    thinking        MEDIUMTEXT   NULL        COMMENT '思考链内容（Qwen3 reasoning）',
    reference       JSON         NULL        COMMENT '引用来源 citations 列表',
    create_time     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_conv_id   (conversation_id),
    INDEX idx_create    (create_time),
    FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话消息表';
"""


class ConversationService:
    """对话持久化服务（单例）"""

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
        self._ensure_tables()

    # ------------------------------------------------------------------
    # 内部：数据库连接
    # ------------------------------------------------------------------

    def _get_conn(self):
        return pymysql.connect(
            host=config.mysql.HOST,
            port=config.mysql.PORT,
            user=config.mysql.USER,
            password=config.mysql.PASSWORD,
            database=config.mysql.DATABASE,
            charset="utf8mb4",
            cursorclass=DictCursor,
        )

    def _ensure_tables(self):
        """首次启动时自动建表，已存在则跳过"""
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_CREATE_CONVERSATIONS_SQL)
                    cur.execute(_CREATE_MESSAGES_SQL)
                conn.commit()
            logger.info("[ConversationService] 对话表初始化完成")
        except Exception as e:
            logger.error(f"[ConversationService] 建表失败: {e}")

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def create(
        self,
        user_id: str,
        kb_id: str,
        title: str = "新对话",
    ) -> str:
        """
        创建新会话，返回 conversation_id。
        user_id 对管理员传 'admin'，对普通用户传实际 user_id。
        """
        conv_id = str(uuid.uuid4())
        sql = """
        INSERT INTO chat_conversations (id, user_id, kb_id, title)
        VALUES (%s, %s, %s, %s)
        """
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (conv_id, user_id, kb_id, title))
                conn.commit()
            logger.info(f"[ConversationService] 创建会话 conv_id={conv_id} user={user_id}")
            return conv_id
        except Exception as e:
            logger.error(f"[ConversationService] 创建会话失败: {e}")
            raise

    def get(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取会话元信息"""
        sql = "SELECT * FROM chat_conversations WHERE id = %s"
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (conversation_id,))
                    row = cur.fetchone()
            if row:
                row["create_time"] = str(row["create_time"])
                row["update_time"] = str(row["update_time"])
            return row
        except Exception as e:
            logger.error(f"[ConversationService] 获取会话失败: {e}")
            return None

    def list_by_user(
        self,
        user_id: str,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """按用户列出会话列表（按最近更新倒序）"""
        count_sql = "SELECT COUNT(*) AS total FROM chat_conversations WHERE user_id = %s"
        query_sql = """
        SELECT id, user_id, kb_id, title, create_time, update_time
        FROM chat_conversations
        WHERE user_id = %s
        ORDER BY update_time DESC
        LIMIT %s OFFSET %s
        """
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(count_sql, (user_id,))
                    total = cur.fetchone()["total"]
                    offset = (page - 1) * size
                    cur.execute(query_sql, (user_id, size, offset))
                    rows = cur.fetchall()
            for r in rows:
                r["create_time"] = str(r["create_time"])
                r["update_time"] = str(r["update_time"])
            return {"total": total, "page": page, "size": size, "conversations": rows}
        except Exception as e:
            logger.error(f"[ConversationService] 列出会话失败: {e}")
            return {"total": 0, "page": page, "size": size, "conversations": []}

    def delete(self, conversation_id: str) -> bool:
        """删除会话（级联删除消息）"""
        sql = "DELETE FROM chat_conversations WHERE id = %s"
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (conversation_id,))
                conn.commit()
            logger.info(f"[ConversationService] 删除会话 {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"[ConversationService] 删除会话失败: {e}")
            return False

    def update_title(self, conversation_id: str, title: str) -> bool:
        """更新会话标题"""
        sql = "UPDATE chat_conversations SET title = %s WHERE id = %s"
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (title, conversation_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[ConversationService] 更新标题失败: {e}")
            return False

    def append_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        thinking: str = None,
        reference: List[Dict] = None,
    ) -> int:
        """
        追加一条消息到会话，返回消息 id。
        同时更新会话的 update_time。
        """
        sql = """
        INSERT INTO chat_messages (conversation_id, role, content, thinking, reference)
        VALUES (%s, %s, %s, %s, %s)
        """
        touch_sql = "UPDATE chat_conversations SET update_time = NOW() WHERE id = %s"
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (
                        conversation_id,
                        role,
                        content,
                        thinking,
                        json.dumps(reference, ensure_ascii=False) if reference else None,
                    ))
                    msg_id = cur.lastrowid
                    cur.execute(touch_sql, (conversation_id,))
                conn.commit()
            return msg_id
        except Exception as e:
            logger.error(f"[ConversationService] 追加消息失败: {e}")
            raise

    def get_messages(
        self,
        conversation_id: str,
    ) -> List[Dict[str, Any]]:
        """
        获取会话的完整消息列表（按时间升序）。
        返回格式与 OpenAI messages 兼容：[{"role": ..., "content": ...}, ...]
        """
        sql = """
        SELECT id, role, content, thinking, reference, create_time
        FROM chat_messages
        WHERE conversation_id = %s
        ORDER BY id ASC
        """
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (conversation_id,))
                    rows = cur.fetchall()
            result = []
            for r in rows:
                item = {
                    "id": r["id"],
                    "role": r["role"],
                    "content": r["content"],
                    "thinking": r["thinking"],
                    "reference": json.loads(r["reference"]) if r["reference"] else [],
                    "create_time": str(r["create_time"]),
                }
                result.append(item)
            return result
        except Exception as e:
            logger.error(f"[ConversationService] 获取消息失败: {e}")
            return []

    def get_messages_for_llm(
        self,
        conversation_id: str,
    ) -> List[Dict[str, str]]:
        """
        获取适合直接传给 LLM 的历史消息列表。
        只返回 role + content，过滤掉 thinking/reference 等字段。
        """
        rows = self.get_messages(conversation_id)
        return [{"role": r["role"], "content": r["content"]} for r in rows]
