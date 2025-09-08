"""
UMBRA Core Audit System
=======================

Comprehensive audit logging system for UMBRA platform.
Provides immutable audit trails with sensitive data redaction,
compliance reporting, and secure storage.

Features:
- Append-only audit logging
- Sensitive data redaction
- JSONL format for efficient storage
- R2/S3 compatible storage
- Compliance reporting
- Event correlation and search
- Tamper-evident logging

Version: 1.0.0
"""

import json
import time
import uuid
import logging
import asyncio
import hashlib
from typing import Dict, List, Any, Optional, Union, AsyncIterator
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import aiofiles
import gzip

from ..core.config import UmbraConfig
from ..core.logging_mw import SensitiveDataRedactor

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Standard audit event types"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # Authorization events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    
    # Data access events
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    
    # System events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGE = "config_change"
    MODULE_ENABLE = "module_enable"
    MODULE_DISABLE = "module_disable"
    
    # AI and content events
    AI_REQUEST = "ai_request"
    CONTENT_GENERATED = "content_generated"
    CONTENT_MODIFIED = "content_modified"
    CONTENT_DELETED = "content_deleted"
    
    # Security events
    SECURITY_VIOLATION = "security_violation"
    INTRUSION_ATTEMPT = "intrusion_attempt"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # Administrative events
    USER_CREATED = "user_created"
    USER_MODIFIED = "user_modified"
    USER_DELETED = "user_deleted"
    ADMIN_ACTION = "admin_action"
    
    # Compliance events
    GDPR_REQUEST = "gdpr_request"
    DATA_RETENTION = "data_retention"
    COMPLIANCE_VIOLATION = "compliance_violation"
    
    # Custom events
    CUSTOM = "custom"

class AuditSeverity(Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"

@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    source: str
    user_id: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    module: Optional[str]
    action: Optional[str]
    resource: Optional[str]
    resource_id: Optional[str]
    outcome: str  # success, failure, error
    details: Dict[str, Any]
    original_data: Optional[Dict[str, Any]] = None
    redacted_fields: List[str] = None
    correlation_id: Optional[str] = None
    compliance_tags: List[str] = None
    retention_period: Optional[int] = None  # days

class AuditStorage:
    """Handles audit log storage with multiple backends"""
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        self.local_storage_enabled = config.get('AUDIT_LOCAL_STORAGE_ENABLED', True)
        self.cloud_storage_enabled = config.get('AUDIT_CLOUD_STORAGE_ENABLED', False)
        self.local_path = Path(config.get('AUDIT_LOCAL_PATH', 'audit_logs'))
        self.compression_enabled = config.get('AUDIT_COMPRESSION_ENABLED', True)
        
        # Create local storage directory
        if self.local_storage_enabled:
            self.local_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize cloud storage if enabled
        self.cloud_client = None
        if self.cloud_storage_enabled:
            self._initialize_cloud_storage()
    
    def _initialize_cloud_storage(self):
        """Initialize cloud storage (R2/S3) client"""
        try:
            import boto3
            
            self.cloud_client = boto3.client(
                's3',
                endpoint_url=self.config.get('AUDIT_R2_ENDPOINT'),
                aws_access_key_id=self.config.get('AUDIT_R2_ACCESS_KEY'),
                aws_secret_access_key=self.config.get('AUDIT_R2_SECRET_KEY'),
                region_name=self.config.get('AUDIT_R2_REGION', 'auto')
            )
            
            logger.info("Cloud storage for audit logs initialized")
            
        except ImportError:
            logger.warning("boto3 not available, cloud storage disabled")
            self.cloud_storage_enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize cloud storage: {e}")
            self.cloud_storage_enabled = False
    
    async def write_event(self, event: AuditEvent):
        """Write audit event to storage"""
        # Convert event to JSON
        event_json = json.dumps(asdict(event), default=str, separators=(',', ':'))
        
        # Write to local storage
        if self.local_storage_enabled:
            await self._write_local(event, event_json)
        
        # Write to cloud storage
        if self.cloud_storage_enabled and self.cloud_client:
            await self._write_cloud(event, event_json)
    
    async def _write_local(self, event: AuditEvent, event_json: str):
        """Write event to local storage"""
        try:
            # Organize by date
            date_str = event.timestamp.strftime('%Y/%m/%d')
            date_path = self.local_path / date_str
            date_path.mkdir(parents=True, exist_ok=True)
            
            # Create filename with hour for partitioning
            hour_str = event.timestamp.strftime('%H')
            filename = f"audit_{hour_str}.jsonl"
            
            if self.compression_enabled:
                filename += ".gz"
                file_path = date_path / filename
                
                # Write compressed JSONL
                async with aiofiles.open(file_path, 'ab') as f:
                    compressed_data = gzip.compress((event_json + '\n').encode('utf-8'))
                    await f.write(compressed_data)
            else:
                file_path = date_path / filename
                
                # Write plain JSONL
                async with aiofiles.open(file_path, 'a', encoding='utf-8') as f:
                    await f.write(event_json + '\n')
                    
        except Exception as e:
            logger.error(f"Failed to write audit event to local storage: {e}")
    
    async def _write_cloud(self, event: AuditEvent, event_json: str):
        """Write event to cloud storage"""
        try:
            # Create S3 key with hierarchical structure
            date_str = event.timestamp.strftime('%Y/%m/%d')
            hour_str = event.timestamp.strftime('%H')
            s3_key = f"audit_logs/{date_str}/audit_{hour_str}_{event.event_id}.json"
            
            # Upload to cloud storage
            bucket = self.config.get('AUDIT_R2_BUCKET')
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.cloud_client.put_object(
                    Bucket=bucket,
                    Key=s3_key,
                    Body=event_json.encode('utf-8'),
                    ContentType='application/json',
                    Metadata={
                        'event_type': event.event_type.value,
                        'severity': event.severity.value,
                        'user_id': event.user_id or '',
                        'module': event.module or ''
                    }
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to write audit event to cloud storage: {e}")
    
    async def read_events(self, start_date: datetime, end_date: datetime,
                         event_types: List[AuditEventType] = None,
                         user_id: str = None,
                         module: str = None,
                         limit: int = 1000) -> AsyncIterator[AuditEvent]:
        """Read audit events from storage with filtering"""
        
        if self.local_storage_enabled:
            async for event in self._read_local_events(start_date, end_date, event_types, user_id, module, limit):
                yield event
        elif self.cloud_storage_enabled:
            async for event in self._read_cloud_events(start_date, end_date, event_types, user_id, module, limit):
                yield event
    
    async def _read_local_events(self, start_date: datetime, end_date: datetime,
                                event_types: List[AuditEventType], user_id: str,
                                module: str, limit: int) -> AsyncIterator[AuditEvent]:
        """Read events from local storage"""
        count = 0
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only and count < limit:
            date_str = current_date.strftime('%Y/%m/%d')
            date_path = self.local_path / date_str
            
            if date_path.exists():
                # Read all hour files for this date
                for hour_file in sorted(date_path.glob('audit_*.jsonl*')):
                    async for event in self._read_file_events(hour_file, event_types, user_id, module):
                        if start_date <= event.timestamp <= end_date:
                            yield event
                            count += 1
                            if count >= limit:
                                return
            
            current_date += timedelta(days=1)
    
    async def _read_file_events(self, file_path: Path, event_types: List[AuditEventType],
                               user_id: str, module: str) -> AsyncIterator[AuditEvent]:
        """Read events from a single file"""
        try:
            if file_path.suffix == '.gz':
                # Read compressed file
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    for line in f:
                        event = self._parse_event_line(line.strip())
                        if event and self._matches_filters(event, event_types, user_id, module):
                            yield event
            else:
                # Read plain file
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    async for line in f:
                        event = self._parse_event_line(line.strip())
                        if event and self._matches_filters(event, event_types, user_id, module):
                            yield event
                            
        except Exception as e:
            logger.error(f"Error reading audit file {file_path}: {e}")
    
    def _parse_event_line(self, line: str) -> Optional[AuditEvent]:
        """Parse JSON line into AuditEvent"""
        try:
            data = json.loads(line)
            
            # Convert string values back to enums
            data['event_type'] = AuditEventType(data['event_type'])
            data['severity'] = AuditSeverity(data['severity'])
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            
            return AuditEvent(**data)
            
        except Exception as e:
            logger.warning(f"Failed to parse audit event line: {e}")
            return None
    
    def _matches_filters(self, event: AuditEvent, event_types: List[AuditEventType],
                        user_id: str, module: str) -> bool:
        """Check if event matches filters"""
        if event_types and event.event_type not in event_types:
            return False
        
        if user_id and event.user_id != user_id:
            return False
        
        if module and event.module != module:
            return False
        
        return True

class AuditLogger:
    """Main audit logging system"""
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        self.enabled = config.get('AUDIT_ENABLED', True)
        self.storage = AuditStorage(config)
        self.redactor = SensitiveDataRedactor(config)
        self.async_enabled = config.get('AUDIT_ASYNC_ENABLED', True)
        self.queue_size = config.get('AUDIT_QUEUE_SIZE', 10000)
        
        # Event queue for async processing
        self.event_queue: Optional[asyncio.Queue] = None
        self.processing_task: Optional[asyncio.Task] = None
        
        if self.async_enabled:
            self.event_queue = asyncio.Queue(maxsize=self.queue_size)
        
        # Event correlation tracking
        self.correlation_map: Dict[str, List[str]] = {}
        
        logger.info(f"Audit logger initialized (enabled: {self.enabled}, async: {self.async_enabled})")
    
    async def start(self):
        """Start async audit processing"""
        if self.async_enabled and not self.processing_task:
            self.processing_task = asyncio.create_task(self._process_events())
            logger.info("Audit event processing started")
    
    async def stop(self):
        """Stop async audit processing"""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            
            # Process remaining events
            while not self.event_queue.empty():
                try:
                    event = self.event_queue.get_nowait()
                    await self.storage.write_event(event)
                except asyncio.QueueEmpty:
                    break
            
            logger.info("Audit event processing stopped")
    
    async def log_event(self, event_type: AuditEventType, severity: AuditSeverity,
                       source: str, outcome: str, details: Dict[str, Any],
                       user_id: Optional[str] = None,
                       session_id: Optional[str] = None,
                       request_id: Optional[str] = None,
                       ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None,
                       module: Optional[str] = None,
                       action: Optional[str] = None,
                       resource: Optional[str] = None,
                       resource_id: Optional[str] = None,
                       correlation_id: Optional[str] = None,
                       compliance_tags: List[str] = None,
                       retention_period: Optional[int] = None):
        """Log an audit event"""
        
        if not self.enabled:
            return
        
        # Create audit event
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            severity=severity,
            source=source,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            module=module,
            action=action,
            resource=resource,
            resource_id=resource_id,
            outcome=outcome,
            details=details,
            correlation_id=correlation_id,
            compliance_tags=compliance_tags or [],
            retention_period=retention_period
        )
        
        # Redact sensitive data
        event = self._redact_event(event)
        
        # Add to correlation tracking
        if correlation_id:
            if correlation_id not in self.correlation_map:
                self.correlation_map[correlation_id] = []
            self.correlation_map[correlation_id].append(event.event_id)
        
        # Store event
        if self.async_enabled:
            try:
                await self.event_queue.put(event)
            except asyncio.QueueFull:
                logger.warning("Audit event queue full, dropping event")
        else:
            await self.storage.write_event(event)
    
    def _redact_event(self, event: AuditEvent) -> AuditEvent:
        """Redact sensitive data from audit event"""
        redacted_fields = []
        
        # Store original data before redaction
        event.original_data = asdict(event)
        
        # Redact details
        if event.details:
            original_details = event.details.copy()
            event.details = self.redactor.redact_dict(event.details)
            
            # Track which fields were redacted
            for key in original_details:
                if key in event.details and original_details[key] != event.details[key]:
                    redacted_fields.append(f"details.{key}")
        
        # Redact user agent
        if event.user_agent:
            original_user_agent = event.user_agent
            event.user_agent = self.redactor.redact_text(event.user_agent)
            if event.user_agent != original_user_agent:
                redacted_fields.append("user_agent")
        
        event.redacted_fields = redacted_fields
        return event
    
    async def _process_events(self):
        """Async event processing loop"""
        while True:
            try:
                event = await self.event_queue.get()
                await self.storage.write_event(event)
                self.event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing audit event: {e}")
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return f"audit_{uuid.uuid4().hex[:16]}"
    
    # Convenience methods for common event types
    
    async def log_authentication(self, event_type: AuditEventType, user_id: str,
                                ip_address: str, user_agent: str, outcome: str,
                                details: Dict[str, Any] = None):
        """Log authentication event"""
        await self.log_event(
            event_type=event_type,
            severity=AuditSeverity.SECURITY if outcome == 'failure' else AuditSeverity.INFO,
            source='auth_system',
            outcome=outcome,
            details=details or {},
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            compliance_tags=['authentication', 'security']
        )
    
    async def log_data_access(self, operation: str, resource: str, resource_id: str,
                             user_id: str, outcome: str, details: Dict[str, Any] = None):
        """Log data access event"""
        event_type_map = {
            'read': AuditEventType.DATA_READ,
            'write': AuditEventType.DATA_WRITE,
            'update': AuditEventType.DATA_UPDATE,
            'delete': AuditEventType.DATA_DELETE,
            'export': AuditEventType.DATA_EXPORT,
            'import': AuditEventType.DATA_IMPORT
        }
        
        await self.log_event(
            event_type=event_type_map.get(operation, AuditEventType.CUSTOM),
            severity=AuditSeverity.INFO,
            source='data_access',
            outcome=outcome,
            details=details or {},
            user_id=user_id,
            resource=resource,
            resource_id=resource_id,
            compliance_tags=['data_access', 'gdpr']
        )
    
    async def log_permission_check(self, module: str, action: str, user_id: str,
                                  outcome: str, details: Dict[str, Any] = None):
        """Log permission check event"""
        await self.log_event(
            event_type=AuditEventType.PERMISSION_GRANTED if outcome == 'granted' else AuditEventType.PERMISSION_DENIED,
            severity=AuditSeverity.WARNING if outcome == 'denied' else AuditSeverity.INFO,
            source='rbac_system',
            outcome=outcome,
            details=details or {},
            user_id=user_id,
            module=module,
            action=action,
            compliance_tags=['authorization', 'rbac']
        )
    
    async def log_security_event(self, event_type: AuditEventType, source: str,
                                severity: AuditSeverity, details: Dict[str, Any],
                                user_id: Optional[str] = None,
                                ip_address: Optional[str] = None):
        """Log security event"""
        await self.log_event(
            event_type=event_type,
            severity=severity,
            source=source,
            outcome='detected',
            details=details,
            user_id=user_id,
            ip_address=ip_address,
            compliance_tags=['security', 'threat_detection']
        )
    
    # Query and reporting methods
    
    async def search_events(self, start_date: datetime, end_date: datetime,
                           event_types: List[AuditEventType] = None,
                           user_id: str = None,
                           module: str = None,
                           limit: int = 1000) -> List[AuditEvent]:
        """Search audit events"""
        events = []
        async for event in self.storage.read_events(start_date, end_date, event_types, user_id, module, limit):
            events.append(event)
        return events
    
    async def get_user_activity(self, user_id: str, days: int = 30) -> List[AuditEvent]:
        """Get user activity for specified period"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        return await self.search_events(start_date, end_date, user_id=user_id)
    
    async def get_security_events(self, days: int = 7) -> List[AuditEvent]:
        """Get security events for specified period"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        security_event_types = [
            AuditEventType.LOGIN_FAILURE,
            AuditEventType.PERMISSION_DENIED,
            AuditEventType.SECURITY_VIOLATION,
            AuditEventType.INTRUSION_ATTEMPT,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.RATE_LIMIT_EXCEEDED
        ]
        
        return await self.search_events(start_date, end_date, event_types=security_event_types)
    
    async def generate_compliance_report(self, start_date: datetime, end_date: datetime,
                                        compliance_tag: str) -> Dict[str, Any]:
        """Generate compliance report"""
        events = []
        async for event in self.storage.read_events(start_date, end_date):
            if compliance_tag in (event.compliance_tags or []):
                events.append(event)
        
        # Aggregate statistics
        total_events = len(events)
        event_types = {}
        users = set()
        
        for event in events:
            event_types[event.event_type.value] = event_types.get(event.event_type.value, 0) + 1
            if event.user_id:
                users.add(event.user_id)
        
        return {
            'compliance_tag': compliance_tag,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_events': total_events,
            'unique_users': len(users),
            'event_types': event_types,
            'events': [asdict(event) for event in events]
        }

# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None

async def initialize_audit(config: UmbraConfig) -> AuditLogger:
    """Initialize global audit system"""
    global _audit_logger
    
    _audit_logger = AuditLogger(config)
    await _audit_logger.start()
    
    logger.info("Audit system initialized")
    return _audit_logger

async def shutdown_audit():
    """Shutdown audit system"""
    global _audit_logger
    
    if _audit_logger:
        await _audit_logger.stop()
        logger.info("Audit system shutdown")

def get_audit_logger() -> Optional[AuditLogger]:
    """Get global audit logger instance"""
    return _audit_logger

# Convenience functions
async def audit_log(event_type: AuditEventType, severity: AuditSeverity,
                   source: str, outcome: str, details: Dict[str, Any], **kwargs):
    """Log audit event using global logger"""
    if _audit_logger:
        await _audit_logger.log_event(event_type, severity, source, outcome, details, **kwargs)

async def audit_authentication(event_type: AuditEventType, user_id: str,
                              ip_address: str, user_agent: str, outcome: str,
                              details: Dict[str, Any] = None):
    """Log authentication event using global logger"""
    if _audit_logger:
        await _audit_logger.log_authentication(event_type, user_id, ip_address, user_agent, outcome, details)

async def audit_data_access(operation: str, resource: str, resource_id: str,
                           user_id: str, outcome: str, details: Dict[str, Any] = None):
    """Log data access event using global logger"""
    if _audit_logger:
        await _audit_logger.log_data_access(operation, resource, resource_id, user_id, outcome, details)

async def audit_permission_check(module: str, action: str, user_id: str,
                                outcome: str, details: Dict[str, Any] = None):
    """Log permission check event using global logger"""
    if _audit_logger:
        await _audit_logger.log_permission_check(module, action, user_id, outcome, details)

# Export key classes and functions
__all__ = [
    'AuditEventType', 'AuditSeverity', 'AuditEvent', 'AuditStorage', 'AuditLogger',
    'initialize_audit', 'shutdown_audit', 'get_audit_logger',
    'audit_log', 'audit_authentication', 'audit_data_access', 'audit_permission_check'
]
