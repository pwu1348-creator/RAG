import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from config import JWTConfig
from database.db_manager import DatabaseManager
from utils.logger import logger


class AuthService:
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
        self.jwt_config = JWTConfig()

    def create_jwt_token(self, payload: Dict[str, Any]) -> str:
        expire_at = datetime.now() + timedelta(hours=self.jwt_config.ACCESS_TOKEN_EXPIRE_HOURS)
        payload.update({
            'exp': expire_at,
            'iat': datetime.now()
        })
        token = jwt.encode(
            payload,
            self.jwt_config.SECRET_KEY,
            algorithm=self.jwt_config.ALGORITHM
        )
        return token

    def decode_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(
                token,
                self.jwt_config.SECRET_KEY,
                algorithms=[self.jwt_config.ALGORITHM],
                options={"verify_iat": False}
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.info("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.info(f"JWT token invalid: {e}")
            return None

    def admin_login(self, username: str, password: str,
                   login_ip: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        管理员登录
        password 参数已经是前端 SHA-256 加密后的值
        """
        admin = self.db.get_admin_by_username(username)

        if not admin:
            self.db.create_login_log('admin', '', login_ip, user_agent, 'failed', 'User not found')
            return {'success': False, 'message': 'Invalid username or password'}

        if admin['status'] != 'active':
            self.db.create_login_log('admin', admin['admin_id'], login_ip, user_agent, 'failed', 'Account locked')
            return {'success': False, 'message': 'Account is locked or inactive'}

        # 使用 bcrypt 验证密码
        if not self.db.verify_password(password, admin['password_hash']):
            self.db.create_login_log('admin', admin['admin_id'], login_ip, user_agent, 'failed', 'Wrong password')
            return {'success': False, 'message': 'Invalid username or password'}

        token_payload = {
            'type': 'admin',
            'id': admin['admin_id'],
            'admin_id': admin['admin_id'],
            'username': admin['username'],
            'role': admin.get('role', 'admin')
        }
        
        token = self.create_jwt_token(token_payload)
        
        self.db.create_login_log('admin', admin['admin_id'], login_ip, user_agent, 'success', 'Login successful')
        logger.info(f"Admin login success: {admin['username']}, token created")

        return {
            'success': True,
            'message': 'Login successful',
            'token': token,
            'admin': {
                'admin_id': admin['admin_id'],
                'username': admin['username'],
                'role': admin.get('role', 'admin'),
                'real_name': admin.get('real_name'),
                'email': admin.get('email')
            }
        }

    def user_login(self, username: str, password: str,
                  login_ip: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        用户登录
        password 参数已经是前端 SHA-256 加密后的值
        """
        user = self.db.get_user_by_username(username)
        
        if not user:
            self.db.create_login_log('user', '', login_ip, user_agent, 'failed', 'User not found')
            return {'success': False, 'message': 'Invalid username or password'}
        
        if user.get('status') != 'active':
            self.db.create_login_log('user', user.get('user_id'), login_ip, user_agent, 'failed', 'Account locked')
            return {'success': False, 'message': 'Account is locked or inactive'}
        
        # 使用 bcrypt 验证密码
        if not self.db.verify_password(password, user.get('password_hash', '')):
            self.db.create_login_log('user', user.get('user_id'), login_ip, user_agent, 'failed', 'Wrong password')
            return {'success': False, 'message': 'Invalid username or password'}
        
        token_payload = {
            'type': 'user',
            'user_id': user.get('user_id'),
            'username': user.get('username'),
            'role': user.get('role', 'user')
        }
        
        token = self.create_jwt_token(token_payload)
        
        self.db.create_login_log('user', user.get('user_id'), login_ip, user_agent, 'success', 'Login successful')
        
        return {
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'user_id': user.get('user_id'),
                'username': user.get('username'),
                'role': user.get('role', 'user'),
                'real_name': user.get('real_name'),
                'email': user.get('email'),
                'avatar_url': user.get('avatar_url')
            }
        }

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        if not token:
            logger.info("verify_token: token is None or empty")
            return None
        
        logger.info("verify_token: decoding JWT token")
        
        payload = self.decode_jwt_token(token)
        if not payload:
            logger.info("verify_token: invalid or expired token")
            return None
            
        logger.info(f"verify_token: token_data: {payload}")
        return payload

    def logout(self, token: str) -> bool:
        return True

    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        return self.verify_token(token)


auth_service = AuthService()
