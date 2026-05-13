import json
from typing import Optional, Dict, Any, List

from database.db_manager import DatabaseManager
from utils.logger import logger


class SettingsService:
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
        self._init_defaults()

    def _init_defaults(self):
        try:
            self.db.init_default_settings()
        except Exception as e:
            logger.error(f"Init default settings failed: {e}")

    def _parse_value(self, value: str, value_type: str) -> Any:
        if value_type == 'integer':
            return int(value)
        elif value_type == 'float':
            return float(value)
        elif value_type == 'boolean':
            return value.lower() == 'true'
        elif value_type == 'json':
            return json.loads(value)
        return value

    def get_setting(self, category: str, key: str) -> Optional[Any]:
        setting = self.db.get_setting(category, key)
        if setting:
            return self._parse_value(setting['setting_value'], setting['value_type'])
        return None

    def get_setting_detail(self, category: str, key: str) -> Optional[Dict[str, Any]]:
        return self.db.get_setting(category, key)

    def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        settings = self.db.get_settings_by_category(category)
        result = {}
        for setting in settings:
            key = setting['setting_key']
            result[key] = {
                'value': self._parse_value(setting['setting_value'], setting['value_type']),
                'type': setting['value_type'],
                'description': setting['description'],
                'editable': setting['is_editable']
            }
        return result

    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        all_settings = self.db.get_all_settings()
        result = {}
        for category, settings in all_settings.items():
            result[category] = {}
            for setting in settings:
                key = setting['setting_key']
                result[category][key] = {
                    'value': self._parse_value(setting['setting_value'], setting['value_type']),
                    'type': setting['value_type'],
                    'description': setting['description'],
                    'editable': setting['is_editable']
                }
        return result

    def set_setting(self, category: str, key: str, value: Any,
                    value_type: str = None, description: str = None) -> Dict[str, Any]:
        existing = self.db.get_setting(category, key)

        if existing and not existing['is_editable']:
            return {'success': False, 'message': 'Setting is not editable'}

        if value_type is None:
            value_type = existing['value_type'] if existing else 'string'

        if isinstance(value, (list, dict)):
            value = json.dumps(value)
            value_type = 'json'
        elif isinstance(value, bool):
            value = str(value).lower()
            value_type = 'boolean'
        elif isinstance(value, int):
            value = str(value)
            value_type = 'integer'
        elif isinstance(value, float):
            value = str(value)
            value_type = 'float'
        else:
            value = str(value)

        success = self.db.set_setting(category, key, value, value_type, description)

        if success:
            return {'success': True}
        return {'success': False, 'message': 'Failed to update setting'}

    def update_settings_batch(self, settings: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in settings:
            category = item.get('category')
            key = item.get('key')
            value = item.get('value')

            if not all([category, key]):
                results.append({'category': category, 'key': key, 'success': False, 'error': 'Missing required fields'})
                continue

            result = self.set_setting(category, key, value)
            results.append({
                'category': category,
                'key': key,
                'success': result['success'],
                'error': result.get('message')
            })

        success_count = sum(1 for r in results if r['success'])
        return {
            'success': success_count == len(results),
            'total': len(results),
            'success_count': success_count,
            'results': results
        }


    def create_api_config(self, admin_id: str, name: str, api_type: str, provider: str,
                          base_url: str, api_key: str = None, model_name: str = None,
                          max_tokens: int = 2048, timeout: int = 30,
                          is_default: bool = False, config: Dict = None) -> Dict[str, Any]:
        api_id = self.db.generate_id()

        success = self.db.create_api_config(
            api_id=api_id, name=name, api_type=api_type, provider=provider,
            base_url=base_url, api_key=api_key, model_name=model_name,
            max_tokens=max_tokens, timeout=timeout,
            is_default=is_default, config_json=config
        )

        if success:
            self.db.create_operation_log(
                'admin', admin_id, 'create_api_config', api_id,
                {'name': name, 'type': api_type, 'provider': provider}
            )
            logger.info(f"API config created: {name} by admin {admin_id}")
            return {'success': True, 'api_id': api_id}

        return {'success': False, 'message': 'Failed to create API config'}

    def list_api_configs(self, api_type: str = None, is_active: bool = None) -> List[Dict[str, Any]]:
        configs = self.db.list_api_configs(api_type, is_active)
        for config in configs:
            config.pop('api_key', None)
        return configs

    def get_api_config(self, api_id: str, include_key: bool = False) -> Optional[Dict[str, Any]]:
        config = self.db.get_api_config(api_id)
        if config and not include_key:
            config.pop('api_key', None)
        return config

    def get_default_api_config(self, api_type: str) -> Optional[Dict[str, Any]]:
        return self.db.get_default_api_config(api_type)

    def update_api_config(self, admin_id: str, api_id: str, **kwargs) -> Dict[str, Any]:
        config = self.db.get_api_config(api_id)
        if not config:
            return {'success': False, 'message': 'API config not found'}

        success = self.db.update_api_config(api_id, **kwargs)

        if success:
            self.db.create_operation_log(
                'admin', admin_id, 'update_api_config', api_id, kwargs
            )
            logger.info(f"API config updated: {api_id} by admin {admin_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to update API config'}

    def delete_api_config(self, admin_id: str, api_id: str) -> Dict[str, Any]:
        config = self.db.get_api_config(api_id)
        if not config:
            return {'success': False, 'message': 'API config not found'}

        success = self.db.delete_api_config(api_id)

        if success:
            self.db.create_operation_log(
                'admin', admin_id, 'delete_api_config', api_id, {'name': config['name']}
            )
            logger.info(f"API config deleted: {api_id} by admin {admin_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to delete API config'}

    def set_default_api_config(self, admin_id: str, api_id: str) -> Dict[str, Any]:
        return self.update_api_config(admin_id, api_id, is_default=True)


    def get_retrieval_settings(self, kb_id: str = None) -> Optional[Dict[str, Any]]:
        settings = self.db.get_retrieval_setting(kb_id)
        if settings:
            return {
                'search_type': settings['search_type'],
                'top_k': settings['top_k'],
                'similarity_threshold': settings['similarity_threshold'],
                'rerank_enabled': settings['rerank_enabled'],
                'rerank_model': settings['rerank_model'],
                'keyword_weight': settings['keyword_weight'],
                'semantic_weight': settings['semantic_weight']
            }
        return None

    def set_retrieval_settings(self, admin_id: str, kb_id: str = None, **kwargs) -> Dict[str, Any]:
        allowed_fields = ['search_type', 'top_k', 'similarity_threshold', 'rerank_enabled',
                         'rerank_model', 'keyword_weight', 'semantic_weight']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_data:
            return {'success': False, 'message': 'No valid fields to update'}

        if 'search_type' in update_data and update_data['search_type'] not in ['semantic', 'keyword', 'hybrid']:
            return {'success': False, 'message': 'Invalid search type'}

        success = self.db.set_retrieval_setting(kb_id, **update_data)

        if success:
            target = kb_id if kb_id else 'global'
            self.db.create_operation_log(
                'admin', admin_id, 'update_retrieval_settings', target, update_data
            )
            logger.info(f"Retrieval settings updated for {target} by admin {admin_id}")
            return {'success': True}

        return {'success': False, 'message': 'Failed to update retrieval settings'}

    def get_system_info(self) -> Dict[str, Any]:
        all_settings = self.get_all_settings()

        result = {
            'general': all_settings.get('general', {}),
            'model': all_settings.get('model', {}),
            'retrieval': all_settings.get('retrieval', {}),
        }
        return result


settings_service = SettingsService()
