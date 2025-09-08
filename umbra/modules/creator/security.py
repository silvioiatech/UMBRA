"""
Security System - Comprehensive security framework for Creator v1 (CRT4)
Provides authentication, authorization, data protection, and security monitoring
"""

import logging
import time
import hashlib
import secrets
import jwt
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import re
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ...core.config import UmbraConfig
from .analytics import CreatorAnalytics
from .errors import CreatorError, SecurityError

logger = logging.getLogger(__name__)

class Permission(Enum):
    """System permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    AUDIT = "audit"

class Role(Enum):
    """User roles"""
    GUEST = "guest"
    USER = "user"
    PREMIUM = "premium"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class SecurityEvent(Enum):
    """Security event types"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    CONFIG_CHANGE = "config_change"
    API_KEY_USED = "api_key_used"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

@dataclass
class User:
    """User account information"""
    user_id: str
    username: str
    email: str
    role: Role
    permissions: Set[Permission]
    created_at: float
    last_login: Optional[float] = None
    failed_login_attempts: int = 0
    account_locked_until: Optional[float] = None
    api_keys: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIKey:
    """API key information"""
    key_id: str
    key_hash: str
    user_id: str
    name: str
    permissions: Set[Permission]
    created_at: float
    expires_at: Optional[float] = None
    last_used: Optional[float] = None
    usage_count: int = 0
    rate_limit: Optional[int] = None
    enabled: bool = True

@dataclass
class Session:
    """User session information"""
    session_id: str
    user_id: str
    created_at: float
    expires_at: float
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    permissions: Set[Permission] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityAuditLog:
    """Security audit log entry"""
    event_id: str
    event_type: SecurityEvent
    user_id: Optional[str]
    ip_address: Optional[str]
    timestamp: float
    details: Dict[str, Any]
    risk_level: str = "low"  # low, medium, high, critical

class SecurityManager:
    """Comprehensive security management system"""
    
    def __init__(self, config: UmbraConfig, analytics: Optional[CreatorAnalytics] = None):
        self.config = config
        self.analytics = analytics
        
        # Security configuration
        self.enabled = config.get("CREATOR_SECURITY_ENABLED", True)
        self.jwt_secret = config.get("CREATOR_JWT_SECRET", self._generate_secret())
        self.jwt_algorithm = config.get("CREATOR_JWT_ALGORITHM", "HS256")
        self.session_timeout = config.get("CREATOR_SESSION_TIMEOUT_HOURS", 24)
        self.max_login_attempts = config.get("CREATOR_MAX_LOGIN_ATTEMPTS", 5)
        self.lockout_duration = config.get("CREATOR_LOCKOUT_DURATION_MINUTES", 30)
        
        # Encryption
        self.encryption_key = self._derive_encryption_key(
            config.get("CREATOR_ENCRYPTION_PASSWORD", "default_password")
        )
        self.cipher = Fernet(self.encryption_key)
        
        # Storage
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.sessions: Dict[str, Session] = {}
        self.audit_log: List[SecurityAuditLog] = []
        
        # Security monitoring
        self.suspicious_ips: Set[str] = set()
        self.blocked_users: Set[str] = set()
        self.security_rules: List[Callable] = []
        
        # Rate limiting per IP
        self.ip_request_counts: Dict[str, List[float]] = {}
        self.ip_rate_limit = config.get("CREATOR_IP_RATE_LIMIT_PER_MINUTE", 100)
        
        # Initialize default users and permissions
        self._initialize_default_security()
        
        # Start security monitoring
        if self.enabled:
            self.security_monitor_task = asyncio.create_task(self._security_monitoring_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Security manager initialized")
    
    def _generate_secret(self) -> str:
        """Generate a random secret"""
        return secrets.token_urlsafe(32)
    
    def _derive_encryption_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        salt = b'creator_v1_salt'  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _initialize_default_security(self):
        """Initialize default security settings"""
        # Create default admin user
        admin_user = User(
            user_id="admin",
            username="admin",
            email="admin@creator.local",
            role=Role.ADMIN,
            permissions={Permission.READ, Permission.WRITE, Permission.DELETE, 
                        Permission.EXECUTE, Permission.ADMIN, Permission.AUDIT},
            created_at=time.time()
        )
        self.users[admin_user.user_id] = admin_user
        
        # Initialize security rules
        self._setup_security_rules()
    
    def _setup_security_rules(self):
        """Setup default security rules"""
        self.security_rules = [
            self._rule_detect_brute_force,
            self._rule_detect_suspicious_patterns,
            self._rule_detect_privilege_escalation,
            self._rule_detect_data_exfiltration
        ]
    
    async def authenticate_user(self, username: str, password: str,
                              ip_address: Optional[str] = None) -> Optional[str]:
        """Authenticate user and return session token"""
        if not self.enabled:
            return "disabled_mode_token"
        
        try:
            # Rate limiting check
            if ip_address and not self._check_ip_rate_limit(ip_address):
                await self._log_security_event(
                    SecurityEvent.RATE_LIMIT_EXCEEDED,
                    None, ip_address,
                    {"username": username}
                )
                raise SecurityError("Rate limit exceeded")
            
            # Find user
            user = self._find_user_by_username(username)
            if not user:
                await self._log_security_event(
                    SecurityEvent.LOGIN_FAILURE,
                    None, ip_address,
                    {"username": username, "reason": "user_not_found"}
                )
                raise SecurityError("Invalid credentials")
            
            # Check if account is locked
            if self._is_account_locked(user):
                await self._log_security_event(
                    SecurityEvent.LOGIN_FAILURE,
                    user.user_id, ip_address,
                    {"reason": "account_locked"}
                )
                raise SecurityError("Account is locked")
            
            # Verify password (simplified - in production, use proper hashing)
            if not self._verify_password(password, user):
                user.failed_login_attempts += 1
                
                # Lock account if too many failures
                if user.failed_login_attempts >= self.max_login_attempts:
                    user.account_locked_until = time.time() + (self.lockout_duration * 60)
                
                await self._log_security_event(
                    SecurityEvent.LOGIN_FAILURE,
                    user.user_id, ip_address,
                    {"reason": "invalid_password", "attempts": user.failed_login_attempts}
                )
                raise SecurityError("Invalid credentials")
            
            # Successful login
            user.failed_login_attempts = 0
            user.last_login = time.time()
            user.account_locked_until = None
            
            # Create session
            session_token = self._create_session(user, ip_address)
            
            await self._log_security_event(
                SecurityEvent.LOGIN_SUCCESS,
                user.user_id, ip_address,
                {"username": username}
            )
            
            return session_token
            
        except SecurityError:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise SecurityError("Authentication failed")
    
    def _find_user_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def _is_account_locked(self, user: User) -> bool:
        """Check if account is locked"""
        if user.account_locked_until is None:
            return False
        return time.time() < user.account_locked_until
    
    def _verify_password(self, password: str, user: User) -> bool:
        """Verify password (simplified implementation)"""
        # In production, use proper password hashing
        stored_hash = user.metadata.get("password_hash", "admin_hash")
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == stored_hash or password == "admin"  # Default for demo
    
    def _create_session(self, user: User, ip_address: Optional[str] = None) -> str:
        """Create user session"""
        session_id = secrets.token_urlsafe(32)
        expires_at = time.time() + (self.session_timeout * 3600)
        
        session = Session(
            session_id=session_id,
            user_id=user.user_id,
            created_at=time.time(),
            expires_at=expires_at,
            ip_address=ip_address,
            permissions=user.permissions.copy()
        )
        
        self.sessions[session_id] = session
        
        # Create JWT token
        payload = {
            "session_id": session_id,
            "user_id": user.user_id,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "exp": expires_at,
            "iat": time.time()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    def validate_session(self, token: str) -> Optional[Session]:
        """Validate session token"""
        if not self.enabled:
            return Session(
                session_id="disabled",
                user_id="disabled",
                created_at=time.time(),
                expires_at=time.time() + 3600,
                permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE}
            )
        
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            session_id = payload.get("session_id")
            
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            
            # Check if session is expired
            if time.time() > session.expires_at:
                del self.sessions[session_id]
                return None
            
            return session
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    def check_permission(self, session: Session, required_permission: Permission,
                        resource: Optional[str] = None) -> bool:
        """Check if user has required permission"""
        if not self.enabled:
            return True
        
        # Check if user has the specific permission
        if required_permission in session.permissions:
            return True
        
        # Check if user has admin permission (overrides all)
        if Permission.ADMIN in session.permissions:
            return True
        
        # Resource-specific permission checks
        if resource and self._check_resource_permission(session, required_permission, resource):
            return True
        
        return False
    
    def _check_resource_permission(self, session: Session, permission: Permission,
                                 resource: str) -> bool:
        """Check resource-specific permissions"""
        # Example: user can read their own data
        if permission == Permission.READ and resource.startswith(f"user:{session.user_id}"):
            return True
        
        return False
    
    def require_permission(self, required_permission: Permission, resource: Optional[str] = None):
        """Decorator for permission checking"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract session from kwargs or context
                session = kwargs.get('session') or kwargs.get('user_session')
                if not session:
                    raise SecurityError("No valid session")
                
                if not self.check_permission(session, required_permission, resource):
                    await self._log_security_event(
                        SecurityEvent.PERMISSION_DENIED,
                        session.user_id, session.ip_address,
                        {
                            "required_permission": required_permission.value,
                            "resource": resource,
                            "function": func.__name__
                        }
                    )
                    raise SecurityError(f"Permission denied: {required_permission.value}")
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def create_api_key(self, user_id: str, name: str, 
                      permissions: Set[Permission],
                      expires_in_days: Optional[int] = None) -> str:
        """Create API key for user"""
        if user_id not in self.users:
            raise SecurityError("User not found")
        
        # Generate API key
        key_id = secrets.token_urlsafe(16)
        api_key = f"ck_{key_id}_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = time.time() + (expires_in_days * 24 * 3600)
        
        # Create API key record
        api_key_record = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            permissions=permissions,
            created_at=time.time(),
            expires_at=expires_at
        )
        
        self.api_keys[key_id] = api_key_record
        self.users[user_id].api_keys.append(key_id)
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Validate API key"""
        if not api_key.startswith("ck_"):
            return None
        
        try:
            parts = api_key.split("_")
            if len(parts) != 3:
                return None
            
            key_id = parts[1]
            if key_id not in self.api_keys:
                return None
            
            api_key_record = self.api_keys[key_id]
            
            # Check if API key is enabled
            if not api_key_record.enabled:
                return None
            
            # Check expiration
            if api_key_record.expires_at and time.time() > api_key_record.expires_at:
                return None
            
            # Verify key hash
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            if key_hash != api_key_record.key_hash:
                return None
            
            # Update usage
            api_key_record.last_used = time.time()
            api_key_record.usage_count += 1
            
            return api_key_record
            
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise SecurityError("Encryption failed")
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise SecurityError("Decryption failed")
    
    def sanitize_input(self, input_data: Any) -> Any:
        """Sanitize user input to prevent injection attacks"""
        if isinstance(input_data, str):
            # Remove potentially dangerous characters
            sanitized = re.sub(r'[<>"\';\\]', '', input_data)
            # Limit length
            sanitized = sanitized[:10000]
            return sanitized
        elif isinstance(input_data, dict):
            return {key: self.sanitize_input(value) for key, value in input_data.items()}
        elif isinstance(input_data, list):
            return [self.sanitize_input(item) for item in input_data]
        else:
            return input_data
    
    def _check_ip_rate_limit(self, ip_address: str) -> bool:
        """Check IP-based rate limiting"""
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Clean old requests
        if ip_address in self.ip_request_counts:
            self.ip_request_counts[ip_address] = [
                timestamp for timestamp in self.ip_request_counts[ip_address]
                if timestamp > window_start
            ]
        else:
            self.ip_request_counts[ip_address] = []
        
        # Check limit
        if len(self.ip_request_counts[ip_address]) >= self.ip_rate_limit:
            return False
        
        # Record request
        self.ip_request_counts[ip_address].append(current_time)
        return True
    
    async def _log_security_event(self, event_type: SecurityEvent,
                                user_id: Optional[str], ip_address: Optional[str],
                                details: Dict[str, Any]) -> None:
        """Log security event"""
        event = SecurityAuditLog(
            event_id=secrets.token_urlsafe(16),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            timestamp=time.time(),
            details=details,
            risk_level=self._assess_risk_level(event_type, details)
        )
        
        self.audit_log.append(event)
        
        # Limit audit log size
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
        
        # Check security rules
        await self._evaluate_security_rules(event)
        
        # Log to analytics if available
        if self.analytics:
            self.analytics.track_event(
                event_type="security_event",
                action=event_type.value,
                metadata={
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "risk_level": event.risk_level,
                    **details
                }
            )
    
    def _assess_risk_level(self, event_type: SecurityEvent, details: Dict[str, Any]) -> str:
        """Assess risk level of security event"""
        high_risk_events = {
            SecurityEvent.PERMISSION_DENIED,
            SecurityEvent.SUSPICIOUS_ACTIVITY
        }
        
        medium_risk_events = {
            SecurityEvent.LOGIN_FAILURE,
            SecurityEvent.RATE_LIMIT_EXCEEDED
        }
        
        if event_type in high_risk_events:
            return "high"
        elif event_type in medium_risk_events:
            return "medium"
        else:
            return "low"
    
    async def _evaluate_security_rules(self, event: SecurityAuditLog) -> None:
        """Evaluate security rules against event"""
        for rule in self.security_rules:
            try:
                await rule(event)
            except Exception as e:
                logger.error(f"Security rule evaluation failed: {e}")
    
    async def _rule_detect_brute_force(self, event: SecurityAuditLog) -> None:
        """Detect brute force attacks"""
        if event.event_type != SecurityEvent.LOGIN_FAILURE:
            return
        
        # Check for multiple failures from same IP
        recent_failures = [
            e for e in self.audit_log[-100:]  # Check last 100 events
            if (e.event_type == SecurityEvent.LOGIN_FAILURE and
                e.ip_address == event.ip_address and
                time.time() - e.timestamp < 300)  # Last 5 minutes
        ]
        
        if len(recent_failures) >= 5:
            self.suspicious_ips.add(event.ip_address)
            await self._log_security_event(
                SecurityEvent.SUSPICIOUS_ACTIVITY,
                event.user_id, event.ip_address,
                {"type": "brute_force_detected", "failure_count": len(recent_failures)}
            )
    
    async def _rule_detect_suspicious_patterns(self, event: SecurityAuditLog) -> None:
        """Detect suspicious activity patterns"""
        if not event.user_id:
            return
        
        # Check for rapid permission escalation attempts
        recent_denials = [
            e for e in self.audit_log[-50:]
            if (e.event_type == SecurityEvent.PERMISSION_DENIED and
                e.user_id == event.user_id and
                time.time() - e.timestamp < 60)  # Last minute
        ]
        
        if len(recent_denials) >= 3:
            await self._log_security_event(
                SecurityEvent.SUSPICIOUS_ACTIVITY,
                event.user_id, event.ip_address,
                {"type": "permission_escalation_attempt", "denial_count": len(recent_denials)}
            )
    
    async def _rule_detect_privilege_escalation(self, event: SecurityAuditLog) -> None:
        """Detect privilege escalation attempts"""
        if event.event_type != SecurityEvent.PERMISSION_DENIED:
            return
        
        required_perm = event.details.get("required_permission")
        if required_perm in ["admin", "audit"]:
            await self._log_security_event(
                SecurityEvent.SUSPICIOUS_ACTIVITY,
                event.user_id, event.ip_address,
                {"type": "privilege_escalation_attempt", "permission": required_perm}
            )
    
    async def _rule_detect_data_exfiltration(self, event: SecurityAuditLog) -> None:
        """Detect potential data exfiltration"""
        if event.event_type != SecurityEvent.DATA_ACCESS:
            return
        
        # Check for large data access patterns
        data_size = event.details.get("data_size", 0)
        if data_size > 1000000:  # 1MB
            await self._log_security_event(
                SecurityEvent.SUSPICIOUS_ACTIVITY,
                event.user_id, event.ip_address,
                {"type": "large_data_access", "size": data_size}
            )
    
    async def _security_monitoring_loop(self):
        """Background security monitoring"""
        while self.enabled:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check for suspicious patterns
                await self._analyze_recent_activity()
                
                # Clean up old sessions
                self._cleanup_expired_sessions()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Security monitoring error: {e}")
    
    async def _analyze_recent_activity(self):
        """Analyze recent security activity"""
        current_time = time.time()
        recent_window = 300  # 5 minutes
        
        recent_events = [
            event for event in self.audit_log
            if current_time - event.timestamp < recent_window
        ]
        
        # Check for unusual activity spikes
        if len(recent_events) > 100:
            high_risk_events = [
                event for event in recent_events
                if event.risk_level in ["high", "critical"]
            ]
            
            if len(high_risk_events) > 10:
                logger.warning(f"High security activity detected: {len(high_risk_events)} high-risk events")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time > session.expires_at
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while self.enabled:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean up old audit logs
                cutoff_time = time.time() - (7 * 24 * 3600)  # 7 days
                self.audit_log = [
                    event for event in self.audit_log
                    if event.timestamp > cutoff_time
                ]
                
                # Clean up old IP request counts
                window_start = time.time() - 3600  # 1 hour
                for ip in list(self.ip_request_counts.keys()):
                    self.ip_request_counts[ip] = [
                        timestamp for timestamp in self.ip_request_counts[ip]
                        if timestamp > window_start
                    ]
                    
                    if not self.ip_request_counts[ip]:
                        del self.ip_request_counts[ip]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Security cleanup error: {e}")
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security system summary"""
        return {
            "enabled": self.enabled,
            "total_users": len(self.users),
            "active_sessions": len(self.sessions),
            "api_keys": len(self.api_keys),
            "audit_events": len(self.audit_log),
            "suspicious_ips": len(self.suspicious_ips),
            "blocked_users": len(self.blocked_users),
            "recent_login_failures": len([
                e for e in self.audit_log[-100:]
                if e.event_type == SecurityEvent.LOGIN_FAILURE
            ]),
            "recent_permission_denials": len([
                e for e in self.audit_log[-100:]
                if e.event_type == SecurityEvent.PERMISSION_DENIED
            ])
        }
    
    def export_audit_log(self, start_time: Optional[float] = None,
                        end_time: Optional[float] = None,
                        event_types: Optional[List[SecurityEvent]] = None) -> List[Dict[str, Any]]:
        """Export audit log with filtering"""
        filtered_events = self.audit_log
        
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]
        
        if event_types:
            filtered_events = [e for e in filtered_events if e.event_type in event_types]
        
        return [asdict(event) for event in filtered_events]
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key"""
        if key_id in self.api_keys:
            self.api_keys[key_id].enabled = False
            return True
        return False
    
    def logout_user(self, session_id: str) -> bool:
        """Logout user by session ID"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def block_user(self, user_id: str, reason: str = "") -> bool:
        """Block user account"""
        if user_id in self.users:
            self.blocked_users.add(user_id)
            
            # Terminate all sessions
            sessions_to_remove = [
                sid for sid, session in self.sessions.items()
                if session.user_id == user_id
            ]
            
            for session_id in sessions_to_remove:
                del self.sessions[session_id]
            
            return True
        return False
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'security_monitor_task') and self.security_monitor_task and not self.security_monitor_task.done():
            self.security_monitor_task.cancel()
        if hasattr(self, 'cleanup_task') and self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()

# Security decorators
def require_auth(security_manager: SecurityManager):
    """Decorator requiring authentication"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            token = kwargs.get('auth_token') or kwargs.get('token')
            if not token:
                raise SecurityError("Authentication required")
            
            session = security_manager.validate_session(token)
            if not session:
                raise SecurityError("Invalid or expired session")
            
            kwargs['session'] = session
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(security_manager: SecurityManager, permission: Permission):
    """Decorator requiring specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            session = kwargs.get('session')
            if not session:
                raise SecurityError("No valid session")
            
            if not security_manager.check_permission(session, permission):
                raise SecurityError(f"Permission required: {permission.value}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Exception classes
class SecurityError(CreatorError):
    """Security-specific error"""
    pass

class AuthenticationError(SecurityError):
    """Authentication error"""
    pass

class AuthorizationError(SecurityError):
    """Authorization error"""
    pass
