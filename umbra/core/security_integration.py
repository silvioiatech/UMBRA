"""
UMBRA Security Integration
=========================

Integrates RBAC, logging, metrics, and audit systems into UMBRA core components.
Provides middleware for bot dispatcher and module registry with comprehensive
security controls and observability.

Version: 1.0.0
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from functools import wraps

from ..core.config import UmbraConfig
from ..core.rbac import (
    initialize_rbac, get_rbac_guard, check_permission, 
    UserContext, Role, RBACRule
)
from ..core.logging_mw import (
    initialize_logging, get_logging_middleware, track_function,
    track_request, end_request_tracking, log_with_context
)
from ..core.metrics import (
    initialize_metrics, get_metrics_registry, track_metrics,
    start_metrics_collection, increment_counter, set_gauge, observe_histogram
)
from ..core.audit import (
    initialize_audit, get_audit_logger, audit_log, audit_permission_check,
    AuditEventType, AuditSeverity
)

logger = logging.getLogger(__name__)

class SecurityIntegration:
    """
    Central security integration for UMBRA platform
    
    Coordinates RBAC, logging, metrics, and audit systems to provide
    comprehensive security and observability across all modules.
    """
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        self.enabled = config.get('SECURITY_INTEGRATION_ENABLED', True)
        
        # Component references
        self.rbac_matrix = None
        self.rbac_guard = None
        self.logging_middleware = None
        self.metrics_registry = None
        self.audit_logger = None
        
        # Integration state
        self.initialized = False
    
    async def initialize(self):
        """Initialize all security components"""
        if not self.enabled:
            logger.info("Security integration disabled")
            return
        
        try:
            logger.info("Initializing UMBRA security integration...")
            
            # Initialize RBAC system
            self.rbac_matrix = initialize_rbac(self.config)
            self.rbac_guard = get_rbac_guard()
            
            # Initialize logging middleware
            self.logging_middleware = initialize_logging(self.config)
            
            # Initialize metrics system
            self.metrics_registry = initialize_metrics(self.config)
            await start_metrics_collection()
            
            # Initialize audit system
            self.audit_logger = await initialize_audit(self.config)
            
            self.initialized = True
            logger.info("Security integration initialized successfully")
            
            # Log system start event
            await self._log_system_event("system_start", "Security integration started")
            
        except Exception as e:
            logger.error(f"Failed to initialize security integration: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown all security components"""
        if not self.initialized:
            return
        
        try:
            # Log system shutdown
            await self._log_system_event("system_stop", "Security integration stopping")
            
            # Shutdown components
            if self.audit_logger:
                from ..core.audit import shutdown_audit
                await shutdown_audit()
            
            if self.metrics_registry:
                from ..core.metrics import stop_metrics_collection
                await stop_metrics_collection()
            
            logger.info("Security integration shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during security integration shutdown: {e}")
    
    async def _log_system_event(self, event_type: str, message: str):
        """Log system-level events"""
        if self.audit_logger:
            await audit_log(
                event_type=AuditEventType.SYSTEM_START if event_type == "system_start" else AuditEventType.SYSTEM_STOP,
                severity=AuditSeverity.INFO,
                source="security_integration",
                outcome="success",
                details={"message": message, "timestamp": datetime.utcnow().isoformat()}
            )

class BotDispatcherSecurity:
    """Security middleware for bot dispatcher"""
    
    def __init__(self, security_integration: SecurityIntegration):
        self.security = security_integration
    
    def secure_dispatch(self, module: str, action: str):
        """Decorator to secure bot dispatch operations"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract user context from arguments
                user_context = self._extract_user_context(*args, **kwargs)
                request_id = track_request(module, action, user_context.user_id, 
                                         user_context.session_id)
                
                start_time = asyncio.get_event_loop().time()
                
                try:
                    # RBAC check
                    if not check_permission(user_context, module, action):
                        await audit_permission_check(module, action, user_context.user_id, 
                                                    "denied", {"reason": "insufficient_permissions"})
                        increment_counter("umbra_permission_checks_total", 
                                        module=module, action=action, result="denied")
                        raise PermissionError(f"Access denied: {module}.{action}")
                    
                    # Log permission granted
                    await audit_permission_check(module, action, user_context.user_id, 
                                                "granted")
                    increment_counter("umbra_permission_checks_total", 
                                    module=module, action=action, result="granted")
                    
                    # Execute function
                    log_with_context("info", f"Executing {module}.{action}", 
                                   module=module, action=action, user_id=user_context.user_id)
                    
                    result = await func(*args, **kwargs)
                    
                    # Track success metrics
                    duration = (asyncio.get_event_loop().time() - start_time) * 1000
                    increment_counter("umbra_requests_total", 
                                    module=module, action=action, status="success")
                    observe_histogram("umbra_request_duration_seconds", 
                                    duration / 1000, module=module, action=action)
                    
                    return result
                    
                except PermissionError:
                    # Track permission denied
                    duration = (asyncio.get_event_loop().time() - start_time) * 1000
                    increment_counter("umbra_requests_total", 
                                    module=module, action=action, status="permission_denied")
                    observe_histogram("umbra_request_duration_seconds", 
                                    duration / 1000, module=module, action=action)
                    raise
                    
                except Exception as e:
                    # Track error
                    duration = (asyncio.get_event_loop().time() - start_time) * 1000
                    increment_counter("umbra_requests_total", 
                                    module=module, action=action, status="error")
                    increment_counter("umbra_errors_total", 
                                    module=module, action=action, error_type=type(e).__name__)
                    observe_histogram("umbra_request_duration_seconds", 
                                    duration / 1000, module=module, action=action)
                    
                    log_with_context("error", f"Error in {module}.{action}: {e}", 
                                   module=module, action=action, 
                                   error_type=type(e).__name__, error_message=str(e))
                    raise
                    
                finally:
                    end_request_tracking(request_id)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Similar logic for sync functions
                user_context = self._extract_user_context(*args, **kwargs)
                
                # RBAC check
                if not check_permission(user_context, module, action):
                    increment_counter("umbra_permission_checks_total", 
                                    module=module, action=action, result="denied")
                    raise PermissionError(f"Access denied: {module}.{action}")
                
                increment_counter("umbra_permission_checks_total", 
                                module=module, action=action, result="granted")
                
                # Execute function
                try:
                    result = func(*args, **kwargs)
                    increment_counter("umbra_requests_total", 
                                    module=module, action=action, status="success")
                    return result
                except Exception as e:
                    increment_counter("umbra_requests_total", 
                                    module=module, action=action, status="error")
                    increment_counter("umbra_errors_total", 
                                    module=module, action=action, error_type=type(e).__name__)
                    raise
            
            # Return appropriate wrapper
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def _extract_user_context(self, *args, **kwargs) -> UserContext:
        """Extract user context from function arguments"""
        # Try to find user context in common parameter patterns
        for key in ['user_context', 'user', 'context']:
            if key in kwargs and isinstance(kwargs[key], UserContext):
                return kwargs[key]
        
        # Try to construct from individual parameters
        user_id = kwargs.get('user_id') or kwargs.get('userId', 'anonymous')
        roles = kwargs.get('roles', [Role.USER])
        
        if isinstance(roles, str):
            roles = [Role(roles)]
        elif isinstance(roles, list) and roles and isinstance(roles[0], str):
            roles = [Role(r) for r in roles]
        
        return UserContext(
            user_id=user_id,
            roles=roles,
            session_id=kwargs.get('session_id'),
            ip_address=kwargs.get('ip_address'),
            metadata=kwargs.get('metadata', {})
        )

class ModuleRegistrySecurity:
    """Security middleware for module registry"""
    
    def __init__(self, security_integration: SecurityIntegration):
        self.security = security_integration
    
    async def validate_module_access(self, user_context: UserContext, module_name: str, 
                                   operation: str) -> bool:
        """Validate user access to module operations"""
        try:
            # Check basic module access
            has_access = check_permission(user_context, module_name, operation)
            
            # Log access attempt
            await audit_log(
                event_type=AuditEventType.PERMISSION_GRANTED if has_access else AuditEventType.PERMISSION_DENIED,
                severity=AuditSeverity.INFO if has_access else AuditSeverity.WARNING,
                source="module_registry",
                outcome="granted" if has_access else "denied",
                details={
                    "module": module_name,
                    "operation": operation,
                    "user_roles": [r.value for r in user_context.roles]
                },
                user_id=user_context.user_id,
                session_id=user_context.session_id,
                module=module_name,
                action=operation
            )
            
            # Update metrics
            increment_counter("umbra_module_access_attempts_total", 
                            module=module_name, operation=operation, 
                            result="granted" if has_access else "denied")
            
            return has_access
            
        except Exception as e:
            logger.error(f"Error validating module access: {e}")
            return False
    
    async def log_module_operation(self, user_context: UserContext, module_name: str,
                                 operation: str, outcome: str, details: Dict[str, Any] = None):
        """Log module operation for audit trail"""
        await audit_log(
            event_type=AuditEventType.CUSTOM,
            severity=AuditSeverity.INFO,
            source="module_registry",
            outcome=outcome,
            details={
                "module": module_name,
                "operation": operation,
                **(details or {})
            },
            user_id=user_context.user_id,
            session_id=user_context.session_id,
            module=module_name,
            action=operation
        )

# Global security integration instance
_security_integration: Optional[SecurityIntegration] = None
_bot_dispatcher_security: Optional[BotDispatcherSecurity] = None
_module_registry_security: Optional[ModuleRegistrySecurity] = None

async def initialize_security_integration(config: UmbraConfig) -> SecurityIntegration:
    """Initialize global security integration"""
    global _security_integration, _bot_dispatcher_security, _module_registry_security
    
    _security_integration = SecurityIntegration(config)
    await _security_integration.initialize()
    
    _bot_dispatcher_security = BotDispatcherSecurity(_security_integration)
    _module_registry_security = ModuleRegistrySecurity(_security_integration)
    
    logger.info("Security integration initialized")
    return _security_integration

async def shutdown_security_integration():
    """Shutdown global security integration"""
    global _security_integration
    
    if _security_integration:
        await _security_integration.shutdown()

def get_security_integration() -> Optional[SecurityIntegration]:
    """Get global security integration instance"""
    return _security_integration

def get_bot_dispatcher_security() -> Optional[BotDispatcherSecurity]:
    """Get bot dispatcher security instance"""
    return _bot_dispatcher_security

def get_module_registry_security() -> Optional[ModuleRegistrySecurity]:
    """Get module registry security instance"""
    return _module_registry_security

# Convenience decorators
def secure_bot_dispatch(module: str, action: str):
    """Decorator to secure bot dispatch operations"""
    if _bot_dispatcher_security:
        return _bot_dispatcher_security.secure_dispatch(module, action)
    else:
        # No-op decorator if security not initialized
        def decorator(func):
            return func
        return decorator

def secure_module_operation(module: str, action: str):
    """Decorator to secure module operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if _module_registry_security:
                # Extract user context
                user_context = None
                for key in ['user_context', 'user', 'context']:
                    if key in kwargs and isinstance(kwargs[key], UserContext):
                        user_context = kwargs[key]
                        break
                
                if user_context:
                    # Validate access
                    has_access = await _module_registry_security.validate_module_access(
                        user_context, module, action
                    )
                    
                    if not has_access:
                        raise PermissionError(f"Access denied: {module}.{action}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Export key classes and functions
__all__ = [
    'SecurityIntegration', 'BotDispatcherSecurity', 'ModuleRegistrySecurity',
    'initialize_security_integration', 'shutdown_security_integration',
    'get_security_integration', 'get_bot_dispatcher_security', 'get_module_registry_security',
    'secure_bot_dispatch', 'secure_module_operation'
]
