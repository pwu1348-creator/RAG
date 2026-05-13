from typing import Optional, Dict, Any, List
from datetime import datetime

from database.db_manager import DatabaseManager
from utils.logger import logger


class AdminService:
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
        self.db = DatabaseManager()

    def create_admin(self, username: str, password: str,
                     email: str = None, phone: str = None, real_name: str = None,
                     role: str = 'admin') -> Dict[str, Any]:
        existing = self.db.get_admin_by_username(username)
        if existing:
            return {'success': False, 'message': 'Username already exists'}

        admin_id = self.db.create_admin(username, password, email, phone, real_name, role)

        if admin_id:
            logger.info(f"Admin created: {username}")
            return {'success': True, 'admin_id': admin_id}

        return {'success': False, 'message': 'Failed to create admin'}

    def create_user(self, username: str, password: str,
                    email: str = None, department: str = None) -> Dict[str, Any]:
        existing = self.db.get_user_by_username(username)
        if existing:
            return {'success': False, 'message': 'Username already exists'}

        user_id = self.db.create_user(username, password, email, department)

        if user_id:
            logger.info(f"User created: {username}")
            return {'success': True, 'user_id': user_id}

        return {'success': False, 'message': 'Failed to create user'}

    def update_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        user = self.db.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}

        success = self.db.update_user(user_id, **kwargs)

        if success:
            logger.info(f"User updated: {user_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to update user'}

    def reset_user_password(self, user_id: str, new_password: str) -> Dict[str, Any]:
        user = self.db.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}

        success = self.db.update_user_password(user_id, new_password)

        if success:
            logger.info(f"User password reset: {user_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to reset password'}

    def lock_user(self, user_id: str) -> Dict[str, Any]:
        return self.update_user(user_id, status='locked')

    def unlock_user(self, user_id: str) -> Dict[str, Any]:
        return self.update_user(user_id, status='active')

    def delete_user(self, user_id: str) -> Dict[str, Any]:
        user = self.db.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}

        success = self.db.delete_user(user_id)

        if success:
            logger.info(f"User deleted: {user_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to delete user'}

    def list_users(self, status: str = None, keyword: str = None,
                   page: int = 1, size: int = 10) -> Dict[str, Any]:
        return self.db.list_users(status, keyword, page, size)

    def list_admins(self, status: str = None, page: int = 1, size: int = 10) -> Dict[str, Any]:
        return self.db.list_admins(status, page, size)

    def get_user_detail(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.db.get_user_by_id(user_id)

    def get_admin_detail(self, admin_id: str) -> Optional[Dict[str, Any]]:
        return self.db.get_admin_by_id(admin_id)

    def update_admin(self, target_admin_id: str, **kwargs) -> Dict[str, Any]:
        admin = self.db.get_admin_by_id(target_admin_id)
        if not admin:
            return {'success': False, 'message': 'Admin not found'}

        success = self.db.update_admin(target_admin_id, **kwargs)

        if success:
            logger.info(f"Admin updated: {target_admin_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to update admin'}

    def delete_admin(self, target_admin_id: str) -> Dict[str, Any]:
        admin = self.db.get_admin_by_id(target_admin_id)
        if not admin:
            return {'success': False, 'message': 'Admin not found'}

        success = self.db.delete_admin(target_admin_id)

        if success:
            logger.info(f"Admin deleted: {target_admin_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to delete admin'}

    def get_statistics(self) -> Dict[str, Any]:
        try:
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) as total FROM users")
                    total_users = cursor.fetchone()['total']

                    cursor.execute("SELECT COUNT(*) as total FROM users WHERE status = 'active'")
                    active_users = cursor.fetchone()['total']

                    cursor.execute("SELECT COUNT(*) as total FROM admins")
                    total_admins = cursor.fetchone()['total']

                    cursor.execute("SELECT COUNT(*) as total FROM documents")
                    total_documents = cursor.fetchone()['total']

                    cursor.execute("SELECT COUNT(*) as total FROM documents WHERE status = 'completed'")
                    completed_documents = cursor.fetchone()['total']

                    cursor.execute("""
                        SELECT DATE(created_at) as date, COUNT(*) as count
                        FROM login_logs
                        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                        GROUP BY DATE(created_at)
                        ORDER BY date
                    """)
                    login_stats = cursor.fetchall()

            return {
                'success': True,
                'data': {
                    'users': {
                        'total': total_users,
                        'active': active_users,
                        'locked': total_users - active_users
                    },
                    'admins': {
                        'total': total_admins
                    },
                    'documents': {
                        'total': total_documents,
                        'completed': completed_documents,
                        'processing': total_documents - completed_documents
                    },
                    'login_stats': login_stats
                }
            }
        except Exception as e:
            logger.error(f"Get statistics failed: {e}")
            return {'success': False, 'message': str(e)}

    def get_stored_statistics(self) -> Dict[str, Any]:
        try:
            stats = self.db.get_all_statistics()
            
            if not stats:
                self.sync_statistics()
                stats = self.db.get_all_statistics()
            
            return {
                'total_users': stats.get('total_users', 0),
                'active_users': stats.get('active_users', 0),
                'total_documents': stats.get('total_documents', 0),
                'completed_documents': stats.get('completed_documents', 0),
                'total_chunks': stats.get('total_chunks', 0),
                'total_storage': stats.get('total_storage', '0 B'),
                'total_knowledge_bases': stats.get('total_knowledge_bases', 0)
            }
        except Exception as e:
            logger.error(f"Get stored statistics failed: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'total_documents': 0,
                'completed_documents': 0,
                'total_chunks': 0,
                'total_storage': '0 B',
                'total_knowledge_bases': 0
            }

    def sync_statistics(self) -> Dict[str, Any]:
        try:
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) as total FROM users")
                    total_users = cursor.fetchone()['total']

                    cursor.execute("SELECT COUNT(*) as total FROM users WHERE status = 'active'")
                    active_users = cursor.fetchone()['total']

                    cursor.execute("SELECT COUNT(*) as total FROM documents")
                    total_documents = cursor.fetchone()['total']

                    cursor.execute("SELECT COUNT(*) as total FROM documents WHERE status = 'completed'")
                    completed_documents = cursor.fetchone()['total']

                    cursor.execute("SELECT COUNT(*) as total FROM document_chunks")
                    total_chunks = cursor.fetchone()['total']

                    cursor.execute("SELECT COALESCE(SUM(file_size), 0) as total FROM documents")
                    total_storage = cursor.fetchone()['total']

                    cursor.execute("SELECT COUNT(*) as total FROM knowledge_bases")
                    total_knowledge_bases = cursor.fetchone()['total']

            stats = {
                'total_users': total_users,
                'active_users': active_users,
                'total_documents': total_documents,
                'completed_documents': completed_documents,
                'total_chunks': total_chunks,
                'total_storage': total_storage,
                'total_knowledge_bases': total_knowledge_bases
            }

            self.db.batch_update_statistics(stats)

            logger.info(f"Statistics synced: {stats}")
            return {'success': True, 'data': stats}
        except Exception as e:
            logger.error(f"Sync statistics failed: {e}")
            return {'success': False, 'message': str(e)}


    def create_knowledge_base(self, admin_id: str, name: str, description: str = None,
                              embedding_model: str = None, vector_dimension: int = 1024,
                              owner_id: str = None, owner_type: str = None) -> Dict[str, Any]:
        from config import config

        kb_id = self.db.generate_id()
        index_id = f"kb_{kb_id}_{int(datetime.now().timestamp())}"

        if not owner_type:
            owner_type = 'user' if owner_id else 'admin'
        actual_owner_id = owner_id if owner_id else admin_id

        success = self.db.create_knowledge_base(
            kb_id=kb_id,
            index_id=index_id,
            name=name,
            owner_type=owner_type,
            owner_id=actual_owner_id,
            description=description,
            embedding_model=embedding_model or config.embedding.MODEL,
            vector_dimension=vector_dimension
        )

        if success:
            self.db.create_operation_log(
                'admin', admin_id, 'create_knowledge_base', kb_id,
                {'name': name, 'index_id': index_id}
            )
            logger.info(f"Knowledge base created: {name} by admin {admin_id}")
            return {'success': True, 'kb_id': kb_id, 'index_id': index_id}

        return {'success': False, 'message': 'Failed to create knowledge base'}

    def list_knowledge_bases(self, status: str = None, keyword: str = None,
                             page: int = 1, size: int = 10) -> Dict[str, Any]:
        return self.db.list_knowledge_bases(status=status, keyword=keyword, page=page, size=size)

    def get_knowledge_base_detail(self, kb_id: str) -> Optional[Dict[str, Any]]:
        return self.db.get_knowledge_base_by_id(kb_id)

    def update_knowledge_base(self, admin_id: str, kb_id: str, **kwargs) -> Dict[str, Any]:
        kb = self.db.get_knowledge_base_by_id(kb_id)
        if not kb:
            return {'success': False, 'message': 'Knowledge base not found'}

        allowed_fields = ['name', 'description', 'status', 'owner_type', 'owner_id']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields or (k in ('owner_type', 'owner_id') and v is None)}

        if not update_data:
            return {'success': False, 'message': 'No valid fields to update'}

        success = self.db.update_knowledge_base(kb_id, **update_data)

        if success:
            self.db.create_operation_log(
                'admin', admin_id, 'update_knowledge_base', kb_id, update_data
            )
            logger.info(f"Knowledge base updated: {kb_id} by admin {admin_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to update knowledge base'}

    def delete_knowledge_base(self, admin_id: str, kb_id: str) -> Dict[str, Any]:
        kb = self.db.get_knowledge_base_by_id(kb_id)
        if not kb:
            return {'success': False, 'message': 'Knowledge base not found'}

        success = self.db.delete_knowledge_base(kb_id)

        if success:
            self.db.create_operation_log(
                'admin', admin_id, 'delete_knowledge_base', kb_id, {'name': kb['name']}
            )
            logger.info(f"Knowledge base deleted: {kb_id} by admin {admin_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to delete knowledge base'}


    def add_user_to_kb(self, admin_id: str, user_id: str, kb_id: str, role: str = 'viewer') -> Dict[str, Any]:
        user = self.db.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}

        kb = self.db.get_knowledge_base_by_id(kb_id)
        if not kb:
            return {'success': False, 'message': 'Knowledge base not found'}

        success = self.db.add_user_to_kb(user_id, kb_id, role)

        if success:
            self.db.create_operation_log(
                'admin', admin_id, 'add_user_to_kb', kb_id,
                {'user_id': user_id, 'role': role}
            )
            logger.info(f"User {user_id} added to kb {kb_id} with role {role} by admin {admin_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to add user to knowledge base'}

    def remove_user_from_kb(self, admin_id: str, user_id: str, kb_id: str) -> Dict[str, Any]:
        success = self.db.remove_user_from_kb(user_id, kb_id)

        if success:
            self.db.create_operation_log(
                'admin', admin_id, 'remove_user_from_kb', kb_id, {'user_id': user_id}
            )
            logger.info(f"User {user_id} removed from kb {kb_id} by admin {admin_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to remove user from knowledge base'}

    def update_user_kb_role(self, admin_id: str, user_id: str, kb_id: str, role: str) -> Dict[str, Any]:
        if role not in ['owner', 'editor', 'viewer']:
            return {'success': False, 'message': 'Invalid role'}

        success = self.db.update_user_kb_role(user_id, kb_id, role)

        if success:
            self.db.create_operation_log(
                'admin', admin_id, 'update_user_kb_role', kb_id,
                {'user_id': user_id, 'role': role}
            )
            logger.info(f"User {user_id} role updated to {role} in kb {kb_id} by admin {admin_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to update user role'}

    def list_kb_users(self, kb_id: str, page: int = 1, size: int = 10) -> Dict[str, Any]:
        return self.db.list_kb_users(kb_id, page, size)

    def list_user_kbs(self, user_id: str, page: int = 1, size: int = 10) -> Dict[str, Any]:
        return self.db.list_user_kbs(user_id, page, size)


admin_service = AdminService()
