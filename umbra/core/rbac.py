"""
RBAC (Role-Based Access Control) for Umbra modules
Defines permissions matrix and enforcement helpers.
"""
import json
import os
from typing import Dict, List, Optional, Any
from enum import Enum

from .logger import get_context_logger

logger = get_context_logger(__name__)


class Role(Enum):
    """User roles in Umbra system."""
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


class RBACManager:
    """
    Role-Based Access Control manager.
    
    Controls access to module actions based on user roles.
    """
    
    def __init__(self):
        """Initialize RBAC with default permissions."""
        self._permissions_matrix = self._load_default_permissions()
        self._custom_permissions_file = os.getenv('RBAC_PERMISSIONS_FILE')
        
        if self._custom_permissions_file and os.path.exists(self._custom_permissions_file):
            self._load_custom_permissions()
    
    def _load_default_permissions(self) -> Dict[str, Dict[str, List[str]]]:
        """Load default RBAC permissions matrix."""
        return {
            # General Chat - everyone can use
            "general_chat": {
                "ask": [Role.USER.value, Role.ADMIN.value],
                "calculate": [Role.USER.value, Role.ADMIN.value],
                "time": [Role.USER.value, Role.ADMIN.value],
                "convert": [Role.USER.value, Role.ADMIN.value]
            },
            
            # Swiss Accountant - users and admins
            "swiss_accountant": {
                "ingest_document": [Role.USER.value, Role.ADMIN.value],
                "infer_document": [Role.USER.value, Role.ADMIN.value],
                "import_statement": [Role.USER.value, Role.ADMIN.value],
                "parse_qr_bill": [Role.USER.value, Role.ADMIN.value],
                "add_expense": [Role.USER.value, Role.ADMIN.value],
                "list_expenses": [Role.USER.value, Role.ADMIN.value],
                "reconcile": [Role.USER.value, Role.ADMIN.value],
                "monthly_report": [Role.USER.value, Role.ADMIN.value],
                "set_tax_profile": [Role.USER.value, Role.ADMIN.value],
                "yearly_tax_report": [Role.USER.value, Role.ADMIN.value],
                "tva_ledger": [Role.USER.value, Role.ADMIN.value],
                "export_tax_csv": [Role.USER.value, Role.ADMIN.value],
                "export_excel": [Role.USER.value, Role.ADMIN.value],
                "evidence_pack": [Role.USER.value, Role.ADMIN.value],
                "add_rule": [Role.ADMIN.value],  # Admin only
                "list_rules": [Role.USER.value, Role.ADMIN.value],
                "delete_rule": [Role.ADMIN.value],  # Admin only
                "update_rates": [Role.ADMIN.value],  # Admin only
                "ai_set_policy": [Role.USER.value, Role.ADMIN.value],
                "delete_document": [Role.ADMIN.value],  # Admin only
                "delete_expense": [Role.ADMIN.value],  # Admin only
                "rename_category": [Role.ADMIN.value],  # Admin only
                "upsert_alias": [Role.ADMIN.value]  # Admin only
            },
            
            # Business Module - users and admins
            "business": {
                "create_instance": [Role.USER.value, Role.ADMIN.value],
                "list_instances": [Role.USER.value, Role.ADMIN.value],
                "delete_instance": [Role.USER.value, Role.ADMIN.value],
                "get_instance": [Role.USER.value, Role.ADMIN.value],
                "instance_logs": [Role.USER.value, Role.ADMIN.value]
            },
            
            # Concierge - admin only for safety
            "concierge": {
                "check_system": [Role.ADMIN.value],
                "exec": [Role.ADMIN.value],
                "file_read": [Role.ADMIN.value],
                "file_write": [Role.ADMIN.value],
                "file_delete": [Role.ADMIN.value],
                "file_export": [Role.ADMIN.value],
                "file_import": [Role.ADMIN.value],
                "docker_list": [Role.ADMIN.value],
                "docker_logs": [Role.ADMIN.value],
                "docker_restart": [Role.ADMIN.value],
                "docker_stats": [Role.ADMIN.value],
                "patch_preview": [Role.ADMIN.value],
                "patch_apply": [Role.ADMIN.value],
                "patch_rollback": [Role.ADMIN.value],
                "instances_create": [Role.ADMIN.value],
                "instances_list": [Role.ADMIN.value],
                "instances_delete": [Role.ADMIN.value],
                "update_watch_start": [Role.ADMIN.value],
                "update_watch_stop": [Role.ADMIN.value],
                "update_watch_status": [Role.ADMIN.value]
            },
            
            # Creator - users and admins
            "creator": {
                "text": [Role.USER.value, Role.ADMIN.value],
                "image": [Role.USER.value, Role.ADMIN.value],
                "video": [Role.USER.value, Role.ADMIN.value],
                "audio": [Role.USER.value, Role.ADMIN.value],
                "music": [Role.USER.value, Role.ADMIN.value],
                "transcribe": [Role.USER.value, Role.ADMIN.value],
                "bundle": [Role.USER.value, Role.ADMIN.value],
                "export": [Role.USER.value, Role.ADMIN.value],
                "clear_cache": [Role.ADMIN.value]  # Admin only
            },
            
            # Production - users and admins
            "production": {
                "plan": [Role.USER.value, Role.ADMIN.value],
                "build": [Role.USER.value, Role.ADMIN.value],
                "validate": [Role.USER.value, Role.ADMIN.value],
                "draft": [Role.USER.value, Role.ADMIN.value],
                "activate": [Role.USER.value, Role.ADMIN.value],
                "test": [Role.USER.value, Role.ADMIN.value],
                "run": [Role.USER.value, Role.ADMIN.value],
                "list_workflows": [Role.USER.value, Role.ADMIN.value],
                "delete_workflow": [Role.ADMIN.value]  # Admin only
            }
        }
    
    def _load_custom_permissions(self):
        """Load custom permissions from file."""
        try:
            with open(self._custom_permissions_file, 'r') as f:
                custom_permissions = json.load(f)
                
            # Merge with defaults (custom overrides defaults)
            for module, actions in custom_permissions.items():
                if module in self._permissions_matrix:
                    self._permissions_matrix[module].update(actions)
                else:
                    self._permissions_matrix[module] = actions
                    
            logger.info(f"Loaded custom RBAC permissions from {self._custom_permissions_file}")
            
        except Exception as e:
            logger.error(f"Failed to load custom RBAC permissions: {e}")
    
    def is_action_allowed(self, user_role: str, module: str, action: str) -> bool:
        """
        Check if a user role is allowed to perform an action on a module.
        
        Args:
            user_role: User's role (user, admin, system)
            module: Module name
            action: Action name
            
        Returns:
            True if allowed, False otherwise
        """
        if not user_role or not module or not action:
            return False
            
        # System role can do anything
        if user_role == Role.SYSTEM.value:
            return True
            
        # Check permissions matrix
        module_permissions = self._permissions_matrix.get(module, {})
        allowed_roles = module_permissions.get(action, [])
        
        return user_role in allowed_roles
    
    def get_allowed_actions(self, user_role: str, module: str) -> List[str]:
        """
        Get list of actions a user role can perform on a module.
        
        Args:
            user_role: User's role
            module: Module name
            
        Returns:
            List of allowed actions
        """
        if not user_role or not module:
            return []
            
        # System role can do anything
        if user_role == Role.SYSTEM.value:
            return list(self._permissions_matrix.get(module, {}).keys())
            
        module_permissions = self._permissions_matrix.get(module, {})
        allowed_actions = []
        
        for action, roles in module_permissions.items():
            if user_role in roles:
                allowed_actions.append(action)
                
        return allowed_actions
    
    def get_user_role(self, user_id: str, admin_ids: List[str]) -> str:
        """
        Determine user role based on admin list.
        
        Args:
            user_id: User ID
            admin_ids: List of admin user IDs
            
        Returns:
            Role string (user or admin)
        """
        if user_id in admin_ids:
            return Role.ADMIN.value
        return Role.USER.value
    
    def enforce_permission(self, user_id: str, admin_ids: List[str], module: str, action: str) -> bool:
        """
        Enforce permission check with detailed logging.
        
        Args:
            user_id: User ID
            admin_ids: List of admin user IDs
            module: Module name
            action: Action name
            
        Returns:
            True if allowed, raises exception if denied
            
        Raises:
            PermissionError: If access is denied
        """
        user_role = self.get_user_role(user_id, admin_ids)
        allowed = self.is_action_allowed(user_role, module, action)
        
        if not allowed:
            error_msg = f"Access denied: user {user_id} (role: {user_role}) cannot perform '{action}' on module '{module}'"
            logger.warning(error_msg, extra={
                'user_id': user_id,
                'user_role': user_role,
                'module': module,
                'action': action,
                'security_event': 'access_denied'
            })
            raise PermissionError(error_msg)
            
        logger.debug(f"Access granted: user {user_id} (role: {user_role}) can perform '{action}' on module '{module}'", extra={
            'user_id': user_id,
            'user_role': user_role,
            'module': module,
            'action': action,
            'security_event': 'access_granted'
        })
        
        return True
    
    def get_permissions_summary(self) -> Dict[str, Any]:
        """Get summary of all permissions for debugging."""
        summary = {}
        
        for module, actions in self._permissions_matrix.items():
            summary[module] = {
                'total_actions': len(actions),
                'admin_only_actions': [action for action, roles in actions.items() if roles == [Role.ADMIN.value]],
                'user_actions': [action for action, roles in actions.items() if Role.USER.value in roles],
                'all_actions': list(actions.keys())
            }
            
        return summary


# Global RBAC manager instance
rbac_manager = RBACManager()
