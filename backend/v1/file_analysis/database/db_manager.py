import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
import pymysql
from pymysql.cursors import DictCursor
import bcrypt

from config import config
from utils.logger import logger


class DatabaseManager:
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
        self._init_tables()

    def _get_connection(self, use_db=True):
        conn_params = {
            'host': config.mysql.HOST,
            'port': config.mysql.PORT,
            'user': config.mysql.USER,
            'password': config.mysql.PASSWORD,
            'charset': 'utf8mb4',
            'cursorclass': DictCursor
        }
        if use_db:
            conn_params['database'] = config.mysql.DATABASE
        return pymysql.connect(**conn_params)

    def _create_database_if_not_exists(self):
        try:
            with self._get_connection(use_db=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.mysql.DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    conn.commit()
            logger.info(f"Database {config.mysql.DATABASE} created or already exists")
            return True
        except Exception as e:
            logger.error(f"Create database failed: {e}")
            return False

    def _init_tables(self):
        # 先创建数据库
        if not self._create_database_if_not_exists():
            return

        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if not os.path.exists(schema_path):
            logger.warning(f"Schema file not found: {schema_path}")
            return

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()

            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    for statement in schema.split(';'):
                        stmt = statement.strip()
                        if stmt:
                            cursor.execute(stmt)
                    conn.commit()

            logger.info("Database tables initialized")
            
            # 创建默认管理员账号
            self._init_default_admin()
        except Exception as e:
            logger.error(f"Init tables failed: {e}")

    def _init_default_admin(self):
        username = config.admin.DEFAULT_USERNAME
        password = config.admin.DEFAULT_PASSWORD
        email = config.admin.DEFAULT_EMAIL
        role = config.admin.DEFAULT_ROLE
        
        # 检查是否已存在管理员
        existing = self.get_admin_by_username(username)
        if existing:
            logger.info(f"Default admin already exists: {username}")
            return
        
        try:
            # 模拟前端行为：先 SHA-256 哈希密码，再存储
            # 因为前端登录时会先 SHA-256 加密再发送
            password_sha256 = hashlib.sha256(password.encode()).hexdigest()
            admin_id = self.create_admin(
                username=username,
                password=password_sha256,
                email=email,
                real_name='System Administrator',
                role=role
            )
            if admin_id:
                logger.info(f"Default admin created: {username}")
            else:
                logger.warning(f"Failed to create default admin: {username}")
        except Exception as e:
            logger.error(f"Init default admin failed: {e}")

    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用 bcrypt 对密码进行加盐哈希
        前端已经做了 SHA-256，这里再用 bcrypt 加盐存储
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        验证密码是否匹配 bcrypt 哈希
        """
        try:
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except (ValueError, TypeError):
            # 兼容旧的 SHA-256 哈希格式（迁移期）
            legacy_hash = hashlib.sha256(password.encode()).hexdigest()
            return legacy_hash == password_hash

    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

    # ==================== Admin Operations ====================

    def create_admin(self, username: str, password: str, email: str = None,
                     phone: str = None, real_name: str = None,
                     role: str = 'admin') -> Optional[str]:
        admin_id = self.generate_id()
        password_hash = self.hash_password(password)

        sql = """
        INSERT INTO admins (admin_id, username, password_hash, email, phone, real_name, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (admin_id, username, password_hash, email, phone, real_name, role))
                    conn.commit()
            logger.info(f"Created admin: {username}")
            return admin_id
        except pymysql.IntegrityError:
            logger.warning(f"Admin already exists: {username}")
            return None
        except Exception as e:
            logger.error(f"Create admin failed: {e}")
            raise

    def get_admin_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM admins WHERE username = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (username,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Get admin failed: {e}")
            return None

    def get_admin_by_id(self, admin_id: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM admins WHERE admin_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (admin_id,))
                    admin = cursor.fetchone()
                    if admin:
                        admin = {
                            **admin,
                            'last_login_at': str(admin['last_login_at']) if admin.get('last_login_at') else None,
                            'created_at': str(admin['created_at']) if admin.get('created_at') else None,
                            'updated_at': str(admin['updated_at']) if admin.get('updated_at') else None
                        }
                    return admin
        except Exception as e:
            logger.error(f"Get admin failed: {e}")
            return None

    def update_admin_last_login(self, admin_id: str):
        sql = "UPDATE admins SET last_login_at = NOW() WHERE admin_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (admin_id,))
                    conn.commit()
        except Exception as e:
            logger.error(f"Update admin login time failed: {e}")

    def list_admins(self, status: str = None, page: int = 1, size: int = 10) -> Dict[str, Any]:
        where_clause = "WHERE 1=1"
        params = []

        if status:
            where_clause += " AND status = %s"
            params.append(status)

        count_sql = f"SELECT COUNT(*) as total FROM admins {where_clause}"
        query_sql = f"""
        SELECT admin_id, username, email, phone, real_name, role, status, last_login_at, created_at
        FROM admins {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_sql, params)
                    total = cursor.fetchone()['total']

                    offset = (page - 1) * size
                    cursor.execute(query_sql, params + [size, offset])
                    admins = cursor.fetchall()

            return {'total': total, 'page': page, 'size': size, 'admins': admins}
        except Exception as e:
            logger.error(f"List admins failed: {e}")
            raise

    def update_admin(self, admin_id: str, **kwargs) -> bool:
        allowed_fields = ['email', 'phone', 'real_name', 'role', 'status']
        updates = []
        values = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                values.append(value)

        if not updates:
            return False

        sql = f"UPDATE admins SET {', '.join(updates)} WHERE admin_id = %s"
        values.append(admin_id)

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Update admin failed: {e}")
            return False

    def delete_admin(self, admin_id: str) -> bool:
        sql = "DELETE FROM admins WHERE admin_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (admin_id,))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Delete admin failed: {e}")
            return False

    # ==================== User Operations ====================

    def create_user(self, username: str, password: str, email: str = None,
                    department: str = None) -> Optional[str]:
        user_id = self.generate_id()
        password_hash = self.hash_password(password)

        sql = """
        INSERT INTO users (user_id, username, password_hash, email, department, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (user_id, username, password_hash, email, department))
                    conn.commit()
            logger.info(f"Created user: {username}")
            return user_id
        except pymysql.IntegrityError:
            logger.warning(f"User already exists: {username}")
            return None
        except Exception as e:
            logger.error(f"Create user failed: {e}")
            raise

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM users WHERE username = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (username,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Get user failed: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM users WHERE user_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (user_id,))
                    user = cursor.fetchone()
                    if user:
                        user = {
                            **user,
                            'created_at': str(user['created_at']) if user.get('created_at') else None,
                            'updated_at': str(user['updated_at']) if user.get('updated_at') else None
                        }
                    return user
        except Exception as e:
            logger.error(f"Get user failed: {e}")
            return None

    def update_user_last_login(self, user_id: str):
        sql = "UPDATE users SET last_login_at = NOW() WHERE user_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (user_id,))
                    conn.commit()
        except Exception as e:
            logger.error(f"Update user login time failed: {e}")

    def list_users(self, status: str = None, keyword: str = None,
                   page: int = 1, size: int = 10) -> Dict[str, Any]:
        where_clause = "WHERE 1=1"
        params = []

        if status:
            where_clause += " AND status = %s"
            params.append(status)

        if keyword:
            where_clause += " AND (username LIKE %s OR email LIKE %s)"
            like_pattern = f"%{keyword}%"
            params.extend([like_pattern, like_pattern])

        count_sql = f"SELECT COUNT(*) as total FROM users {where_clause}"
        query_sql = f"""
        SELECT user_id, username, email, department, status, avatar_url, created_at
        FROM users {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_sql, params)
                    total = cursor.fetchone()['total']

                    offset = (page - 1) * size
                    cursor.execute(query_sql, params + [size, offset])
                    users = cursor.fetchall()
                    
                    users = [
                        {**user, 'created_at': str(user['created_at']) if user.get('created_at') else None}
                        for user in users
                    ]

            return {'total': total, 'page': page, 'size': size, 'users': users}
        except Exception as e:
            logger.error(f"List users failed: {e}")
            raise

    def update_user(self, user_id: str, **kwargs) -> bool:
        allowed_fields = ['username', 'email', 'department', 'status', 'avatar_url']
        updates = []
        values = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                values.append(value)

        if not updates:
            return False

        sql = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
        values.append(user_id)

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Update user failed: {e}")
            return False

    def update_user_password(self, user_id: str, new_password: str) -> bool:
        password_hash = self.hash_password(new_password)
        sql = "UPDATE users SET password_hash = %s WHERE user_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (password_hash, user_id))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Update user password failed: {e}")
            return False

    def delete_user(self, user_id: str) -> bool:
        sql = "DELETE FROM users WHERE user_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (user_id,))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Delete user failed: {e}")
            return False

    # ==================== Admin-User Relations ====================

    def record_admin_action(self, admin_id: str, user_id: str,
                           action_type: str, action_detail: Dict = None):
        sql = """
        INSERT INTO admin_user_relations (admin_id, user_id, action_type, action_detail)
        VALUES (%s, %s, %s, %s)
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    import json
                    cursor.execute(sql, (admin_id, user_id, action_type,
                                        json.dumps(action_detail) if action_detail else None))
                    conn.commit()
        except Exception as e:
            logger.error(f"Record admin action failed: {e}")

    # ==================== Login Logs ====================

    def create_login_log(self, account_type: str, account_id: str,
                        login_ip: str, user_agent: str,
                        status: str, fail_reason: str = None):
        sql = """
        INSERT INTO login_logs (account_type, account_id, login_ip, login_user_agent, login_status, fail_reason)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (account_type, account_id, login_ip, user_agent, status, fail_reason))
                    conn.commit()
        except Exception as e:
            logger.error(f"Create login log failed: {e}")

    def list_login_logs(self, account_type: str = None, account_id: str = None,
                       page: int = 1, size: int = 10) -> Dict[str, Any]:
        where_clause = "WHERE 1=1"
        params = []

        if account_type:
            where_clause += " AND account_type = %s"
            params.append(account_type)

        if account_id:
            where_clause += " AND account_id = %s"
            params.append(account_id)

        count_sql = f"SELECT COUNT(*) as total FROM login_logs {where_clause}"
        query_sql = f"""
        SELECT * FROM login_logs {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_sql, params)
                    total = cursor.fetchone()['total']

                    offset = (page - 1) * size
                    cursor.execute(query_sql, params + [size, offset])
                    logs = cursor.fetchall()

            return {'total': total, 'page': page, 'size': size, 'logs': logs}
        except Exception as e:
            logger.error(f"List login logs failed: {e}")
            raise

    # ==================== Operation Logs ====================

    def create_operation_log(self, operator_type: str, operator_id: str,
                            operation_type: str, operation_target: str = None,
                            operation_detail: Dict = None, operation_ip: str = None):
        sql = """
        INSERT INTO operation_logs (operator_type, operator_id, operation_type, operation_target, operation_detail, operation_ip)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    import json
                    cursor.execute(sql, (operator_type, operator_id, operation_type,
                                        operation_target,
                                        json.dumps(operation_detail) if operation_detail else None,
                                        operation_ip))
                    conn.commit()
        except Exception as e:
            logger.error(f"Create operation log failed: {e}")

    # ==================== Knowledge Base Operations ====================

    def create_knowledge_base(self, kb_id: str, index_id: str, name: str,
                              owner_type: str, owner_id: str,
                              description: str = None,
                              embedding_model: str = None,
                              vector_dimension: int = 1024) -> bool:
        sql = """
        INSERT INTO knowledge_bases (kb_id, index_id, name, description, owner_type, owner_id, embedding_model, vector_dimension)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (kb_id, index_id, name, description, owner_type, owner_id, embedding_model, vector_dimension))
                    conn.commit()
            logger.info(f"Created knowledge base: {name}")
            return True
        except pymysql.IntegrityError:
            logger.warning(f"Knowledge base already exists: {name}")
            return False
        except Exception as e:
            logger.error(f"Create knowledge base failed: {e}")
            raise

    def get_knowledge_base_by_id(self, kb_id: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM knowledge_bases WHERE kb_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (kb_id,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Get knowledge base failed: {e}")
            return None

    def get_knowledge_base_by_index_id(self, index_id: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM knowledge_bases WHERE index_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (index_id,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Get knowledge base by index_id failed: {e}")
            return None

    def list_knowledge_bases(self, owner_type: str = None, owner_id: str = None,
                             status: str = None, keyword: str = None,
                             page: int = 1, size: int = 10) -> Dict[str, Any]:
        where_clause = "WHERE 1=1"
        params = []

        if owner_type and owner_id:
            where_clause += " AND owner_type = %s AND owner_id = %s"
            params.extend([owner_type, owner_id])

        if status:
            where_clause += " AND status = %s"
            params.append(status)

        if keyword:
            where_clause += " AND (name LIKE %s OR description LIKE %s)"
            like_pattern = f"%{keyword}%"
            params.extend([like_pattern, like_pattern])

        count_sql = f"SELECT COUNT(*) as total FROM knowledge_bases {where_clause}"
        query_sql = f"""
        SELECT kb_id, index_id, name, description, owner_type, owner_id, status,
               doc_count, total_chunks, embedding_model, vector_dimension, created_at, updated_at
        FROM knowledge_bases {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_sql, params)
                    total = cursor.fetchone()['total']

                    offset = (page - 1) * size
                    cursor.execute(query_sql, params + [size, offset])
                    kbs = cursor.fetchall()

            return {'total': total, 'page': page, 'size': size, 'knowledge_bases': kbs}
        except Exception as e:
            logger.error(f"List knowledge bases failed: {e}")
            raise

    def update_knowledge_base(self, kb_id: str, **kwargs) -> bool:
        allowed_fields = ['name', 'description', 'status', 'doc_count', 'total_chunks']
        updates = []
        values = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                values.append(value)

        if not updates:
            return False

        sql = f"UPDATE knowledge_bases SET {', '.join(updates)} WHERE kb_id = %s"
        values.append(kb_id)

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Update knowledge base failed: {e}")
            return False

    def delete_knowledge_base(self, kb_id: str) -> bool:
        sql = "DELETE FROM knowledge_bases WHERE kb_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (kb_id,))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Delete knowledge base failed: {e}")
            return False

    def increment_kb_doc_count(self, kb_id: str, increment: int = 1) -> bool:
        sql = "UPDATE knowledge_bases SET doc_count = doc_count + %s WHERE kb_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (increment, kb_id))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Increment kb doc count failed: {e}")
            return False

    # ==================== User-KB Relations ====================

    def add_user_to_kb(self, user_id: str, kb_id: str, role: str = 'viewer') -> bool:
        sql = """
        INSERT INTO user_kb_relations (user_id, kb_id, role)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE role = %s
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (user_id, kb_id, role, role))
                    conn.commit()
            logger.info(f"Added user {user_id} to kb {kb_id} with role {role}")
            return True
        except Exception as e:
            logger.error(f"Add user to kb failed: {e}")
            return False

    def remove_user_from_kb(self, user_id: str, kb_id: str) -> bool:
        sql = "DELETE FROM user_kb_relations WHERE user_id = %s AND kb_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (user_id, kb_id))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Remove user from kb failed: {e}")
            return False

    def update_user_kb_role(self, user_id: str, kb_id: str, role: str) -> bool:
        sql = "UPDATE user_kb_relations SET role = %s WHERE user_id = %s AND kb_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (role, user_id, kb_id))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Update user kb role failed: {e}")
            return False

    def list_kb_users(self, kb_id: str, page: int = 1, size: int = 10) -> Dict[str, Any]:
        count_sql = "SELECT COUNT(*) as total FROM user_kb_relations WHERE kb_id = %s"
        query_sql = """
        SELECT u.user_id, u.username, u.email, u.department, ukr.role, ukr.created_at
        FROM user_kb_relations ukr
        JOIN users u ON ukr.user_id = u.user_id
        WHERE ukr.kb_id = %s
        ORDER BY ukr.created_at DESC
        LIMIT %s OFFSET %s
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_sql, (kb_id,))
                    total = cursor.fetchone()['total']

                    offset = (page - 1) * size
                    cursor.execute(query_sql, (kb_id, size, offset))
                    users = cursor.fetchall()

            return {'total': total, 'page': page, 'size': size, 'users': users}
        except Exception as e:
            logger.error(f"List kb users failed: {e}")
            raise

    def list_user_kbs(self, user_id: str, page: int = 1, size: int = 10) -> Dict[str, Any]:
        count_sql = "SELECT COUNT(*) as total FROM user_kb_relations WHERE user_id = %s"
        query_sql = """
        SELECT kb.kb_id, kb.index_id, kb.name, kb.description, kb.doc_count, kb.total_chunks,
               kb.status, kb.created_at, ukr.role
        FROM user_kb_relations ukr
        JOIN knowledge_bases kb ON ukr.kb_id = kb.kb_id
        WHERE ukr.user_id = %s
        ORDER BY kb.created_at DESC
        LIMIT %s OFFSET %s
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(count_sql, (user_id,))
                    total = cursor.fetchone()['total']

                    offset = (page - 1) * size
                    cursor.execute(query_sql, (user_id, size, offset))
                    kbs = cursor.fetchall()

            return {'total': total, 'page': page, 'size': size, 'knowledge_bases': kbs}
        except Exception as e:
            logger.error(f"List user kbs failed: {e}")
            raise

    def get_user_kb_role(self, user_id: str, kb_id: str) -> Optional[str]:
        sql = "SELECT role FROM user_kb_relations WHERE user_id = %s AND kb_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (user_id, kb_id))
                    result = cursor.fetchone()
                    return result['role'] if result else None
        except Exception as e:
            logger.error(f"Get user kb role failed: {e}")
            return None

    # ==================== System Settings ====================

    def get_setting(self, category: str, key: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM system_settings WHERE category = %s AND setting_key = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (category, key))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Get setting failed: {e}")
            return None

    def get_settings_by_category(self, category: str) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM system_settings WHERE category = %s AND is_visible = TRUE"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (category,))
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Get settings by category failed: {e}")
            return []

    def get_all_settings(self) -> Dict[str, List[Dict[str, Any]]]:
        sql = "SELECT * FROM system_settings WHERE is_visible = TRUE ORDER BY category, setting_key"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    settings = cursor.fetchall()

            result = {}
            for setting in settings:
                category = setting['category']
                if category not in result:
                    result[category] = []
                result[category].append(setting)

            return result
        except Exception as e:
            logger.error(f"Get all settings failed: {e}")
            return {}

    def set_setting(self, category: str, key: str, value: str,
                    value_type: str = 'string', description: str = None,
                    is_editable: bool = True) -> bool:
        sql = """
        INSERT INTO system_settings (category, setting_key, setting_value, value_type, description, is_editable)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        setting_value = VALUES(setting_value),
        value_type = VALUES(value_type),
        description = VALUES(description)
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (category, key, value, value_type, description, is_editable))
                    conn.commit()
            return True
        except Exception as e:
            logger.error(f"Set setting failed: {e}")
            return False

    def delete_setting(self, category: str, key: str) -> bool:
        sql = "DELETE FROM system_settings WHERE category = %s AND setting_key = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (category, key))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Delete setting failed: {e}")
            return False

    def init_default_settings(self):
        defaults = [
            ('general', 'system_name', 'RAG知识库系统', 'string', '系统名称', True),
            ('general', 'system_logo', '', 'string', '系统Logo URL', True),
            ('general', 'theme', 'light', 'string', '主题风格(light/dark)', True),
            ('general', 'language', 'zh-CN', 'string', '系统语言', True),
            ('general', 'footer_text', '© 2024 RAG System', 'string', '页脚文本', True),
            ('security', 'password_min_length', '8', 'integer', '密码最小长度', True),
            ('security', 'password_require_uppercase', 'true', 'boolean', '密码需要大写字母', True),
            ('security', 'password_require_number', 'true', 'boolean', '密码需要数字', True),
            ('security', 'login_max_attempts', '5', 'integer', '最大登录尝试次数', True),
            ('security', 'session_timeout', '24', 'integer', '会话超时时间(小时)', True),
            ('security', 'token_expire_hours', '24', 'integer', 'Token过期时间(小时)', True),
            ('parser', 'max_file_size', '50', 'integer', '最大文件大小(MB)', True),
            ('parser', 'allowed_extensions', '[".pdf", ".docx", ".txt", ".md"]', 'json', '允许的文件类型', True),
            ('parser', 'chunk_size', '1000', 'integer', '文档分块大小', True),
            ('parser', 'chunk_overlap', '200', 'integer', '分块重叠大小', True),
        ]

        for category, key, value, value_type, desc, editable in defaults:
            self.set_setting(category, key, value, value_type, desc, editable)

        logger.info("Default settings initialized")

    # ==================== API Configs ====================

    def create_api_config(self, api_id: str, name: str, api_type: str, provider: str,
                          base_url: str, api_key: str = None, model_name: str = None,
                          max_tokens: int = 2048, timeout: int = 30,
                          is_default: bool = False, config_json: Dict = None) -> bool:
        if is_default:
            self._clear_default_api_config(api_type)

        sql = """
        INSERT INTO api_configs (api_id, name, api_type, provider, base_url, api_key, model_name,
                                 max_tokens, timeout, is_default, config_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    import json
                    cursor.execute(sql, (api_id, name, api_type, provider, base_url, api_key,
                                        model_name, max_tokens, timeout, is_default,
                                        json.dumps(config_json) if config_json else None))
                    conn.commit()
            logger.info(f"Created API config: {name}")
            return True
        except Exception as e:
            logger.error(f"Create API config failed: {e}")
            return False

    def _clear_default_api_config(self, api_type: str):
        sql = "UPDATE api_configs SET is_default = FALSE WHERE api_type = %s"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (api_type,))
                    conn.commit()
        except Exception as e:
            logger.error(f"Clear default API config failed: {e}")

    def get_api_config(self, api_id: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM api_configs WHERE api_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (api_id,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Get API config failed: {e}")
            return None

    def get_default_api_config(self, api_type: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM api_configs WHERE api_type = %s AND is_default = TRUE AND is_active = TRUE"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (api_type,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Get default API config failed: {e}")
            return None

    def list_api_configs(self, api_type: str = None, is_active: bool = None) -> List[Dict[str, Any]]:
        where_clause = "WHERE 1=1"
        params = []

        if api_type:
            where_clause += " AND api_type = %s"
            params.append(api_type)

        if is_active is not None:
            where_clause += " AND is_active = %s"
            params.append(is_active)

        sql = f"SELECT * FROM api_configs {where_clause} ORDER BY is_default DESC, created_at DESC"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"List API configs failed: {e}")
            return []

    def update_api_config(self, api_id: str, **kwargs) -> bool:
        if 'is_default' in kwargs and kwargs['is_default']:
            config = self.get_api_config(api_id)
            if config:
                self._clear_default_api_config(config['api_type'])

        allowed_fields = ['name', 'base_url', 'api_key', 'model_name', 'max_tokens',
                         'timeout', 'is_default', 'is_active', 'config_json']
        updates = []
        values = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                values.append(value)

        if not updates:
            return False

        sql = f"UPDATE api_configs SET {', '.join(updates)} WHERE api_id = %s"
        values.append(api_id)

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Update API config failed: {e}")
            return False

    def delete_api_config(self, api_id: str) -> bool:
        sql = "DELETE FROM api_configs WHERE api_id = %s"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (api_id,))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Delete API config failed: {e}")
            return False

    # ==================== Retrieval Settings ====================

    def get_retrieval_setting(self, kb_id: str = None) -> Optional[Dict[str, Any]]:
        if kb_id:
            sql = "SELECT * FROM retrieval_settings WHERE kb_id = %s"
            params = (kb_id,)
        else:
            sql = "SELECT * FROM retrieval_settings WHERE kb_id IS NULL LIMIT 1"
            params = ()

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Get retrieval setting failed: {e}")
            return None

    def set_retrieval_setting(self, kb_id: str = None, **kwargs) -> bool:
        existing = self.get_retrieval_setting(kb_id)

        allowed_fields = ['search_type', 'top_k', 'similarity_threshold', 'rerank_enabled',
                         'rerank_model', 'keyword_weight', 'semantic_weight']

        if existing:
            updates = []
            values = []
            for key, value in kwargs.items():
                if key in allowed_fields:
                    updates.append(f"{key} = %s")
                    values.append(value)

            if not updates:
                return False

            sql = f"UPDATE retrieval_settings SET {', '.join(updates)} WHERE setting_id = %s"
            values.append(existing['setting_id'])
        else:
            fields = ['kb_id'] + [k for k in kwargs.keys() if k in allowed_fields]
            placeholders = ['%s'] * len(fields)
            values = [kb_id] + [kwargs[k] for k in kwargs.keys() if k in allowed_fields]

            sql = f"INSERT INTO retrieval_settings ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
                    conn.commit()
            return True
        except Exception as e:
            logger.error(f"Set retrieval setting failed: {e}")
            return False

    def get_all_statistics(self) -> Dict[str, Any]:
        sql = "SELECT stat_type, stat_value, stat_extra, updated_at FROM system_statistics"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    results = cursor.fetchall()
            
            stats = {}
            for row in results:
                stat_type = row['stat_type']
                stat_value = row['stat_value']
                stat_extra = row['stat_extra']
                
                if stat_type == 'total_storage':
                    stats[stat_type] = self._format_bytes(stat_value)
                else:
                    stats[stat_type] = stat_value
                
                if stat_extra:
                    stats[f'{stat_type}_extra'] = stat_extra
            
            return stats
        except Exception as e:
            logger.error(f"Get all statistics failed: {e}")
            return {}

    def get_statistics(self, stat_type: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT stat_type, stat_value, stat_extra, updated_at FROM system_statistics WHERE stat_type = %s"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (stat_type,))
                    result = cursor.fetchone()
            
            if result:
                if result['stat_type'] == 'total_storage':
                    result['stat_value'] = self._format_bytes(result['stat_value'])
                return result
            return None
        except Exception as e:
            logger.error(f"Get statistics failed: {e}")
            return None

    def update_statistics(self, stat_type: str, stat_value: int, stat_extra: str = None) -> bool:
        sql = """
            INSERT INTO system_statistics (stat_type, stat_value, stat_extra)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE stat_value = %s, stat_extra = %s
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (stat_type, stat_value, stat_extra, stat_value, stat_extra))
                    conn.commit()
            return True
        except Exception as e:
            logger.error(f"Update statistics failed: {e}")
            return False

    def batch_update_statistics(self, stats: Dict[str, Any]) -> bool:
        if not stats:
            return True
        
        placeholders = []
        values = []
        for stat_type, stat_value in stats.items():
            placeholders.append('(%s, %s, %s)')
            values.extend([stat_type, stat_value, None])
        
        sql = f"""
            INSERT INTO system_statistics (stat_type, stat_value, stat_extra)
            VALUES {', '.join(placeholders)}
            ON DUPLICATE KEY UPDATE stat_value = VALUES(stat_value)
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
                    conn.commit()
            return True
        except Exception as e:
            logger.error(f"Batch update statistics failed: {e}")
            return False

    def _format_bytes(self, bytes_value: int) -> str:
        if bytes_value == 0:
            return "0 B"
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        value = float(bytes_value)
        while value >= 1024 and unit_index < len(units) - 1:
            value /= 1024
            unit_index += 1
        return f"{value:.2f} {units[unit_index]}"
