"""
Structured Logging Middleware - SEC1 Implementation
Request ID injection, user/module/action tracking, and JSON logging
"""

import json
import time
import uuid
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from contextvars import ContextVar
from dataclasses import dataclass, asdict
from datetime import datetime

from .redaction import get_redactor, SensitiveDataRedactor

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[int]] = ContextVar('user_id', default=None)
module_var: ContextVar[Optional[str]] = ContextVar('module', default=None)
action_var: ContextVar[Optional[str]] = ContextVar('action', default=None)

@dataclass
class RequestContext:
    """Request context information"""
    request_id: str
    user_id: Optional[int] = None
    module: Optional[str] = None
    action: Optional[str] = None
    start_time: float = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = time.time()
        if self.metadata is None:
            self.metadata = {}

class StructuredLogger:
    """
    Structured logging with automatic request tracking and redaction
    
    Provides JSON-formatted logs with consistent fields and automatic
    sensitive data redaction.
    """
    
    def __init__(self, name: str, redactor: Optional[SensitiveDataRedactor] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.redactor = redactor or get_redactor()
        
        # Configure JSON formatter if not already configured
        if not self.logger.handlers:
            self._setup_json_logging()
    
    def _setup_json_logging(self):
        """Setup JSON logging formatter"""
        
        class JSONFormatter(logging.Formatter):
            """Custom JSON formatter for structured logs"""
            
            def __init__(self, redactor: SensitiveDataRedactor):
                super().__init__()
                self.redactor = redactor
            
            def format(self, record: logging.LogRecord) -> str:
                # Get request context
                request_id = request_id_var.get()
                user_id = user_id_var.get()
                module = module_var.get()
                action = action_var.get()
                
                # Build log entry
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "request_id": request_id,
                    "user_id": user_id,
                    "module": module,
                    "action": action,
                    "filename": record.filename,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # Add extra fields from record
                if hasattr(record, '__dict__'):
                    for key, value in record.__dict__.items():
                        if key not in {
                            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                            'filename', 'module', 'lineno', 'funcName', 'created', 
                            'msecs', 'relativeCreated', 'thread', 'threadName', 
                            'processName', 'process', 'exc_info', 'exc_text', 'stack_info'
                        }:
                            log_entry[key] = value
                
                # Add exception info if present
                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)
                
                # Redact sensitive data
                log_entry = self.redactor.redact_dict(log_entry)
                
                return json.dumps(log_entry, ensure_ascii=False, default=str)
        
        # Setup handler with JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter(self.redactor))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.debug(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context"""
        self.logger.critical(message, extra=kwargs)

class RequestTracker:
    """
    Request tracking middleware for automatic context injection
    
    Tracks requests from start to finish and provides timing metrics.
    """
    
    def __init__(self):
        self.active_requests: Dict[str, RequestContext] = {}
        self.logger = StructuredLogger(__name__)
    
    def start_request(self, user_id: Optional[int] = None, module: str = None, 
                     action: str = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start tracking a new request"""
        
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        context = RequestContext(
            request_id=request_id,
            user_id=user_id,
            module=module,
            action=action,
            metadata=metadata or {}
        )
        
        # Set context variables
        request_id_var.set(request_id)
        user_id_var.set(user_id)
        module_var.set(module)
        action_var.set(action)
        
        # Store context
        self.active_requests[request_id] = context
        
        self.logger.info(
            "Request started",
            request_id=request_id,
            user_id=user_id,
            module=module,
            action=action,
            metadata=metadata
        )
        
        return request_id
    
    def end_request(self, request_id: str, status: str = "success", 
                   error: Optional[str] = None, result_metadata: Optional[Dict[str, Any]] = None):
        """End request tracking"""
        
        if request_id not in self.active_requests:
            self.logger.warning(f"Request {request_id} not found in active requests")
            return
        
        context = self.active_requests[request_id]
        duration_ms = (time.time() - context.start_time) * 1000
        
        log_data = {
            "request_id": request_id,
            "user_id": context.user_id,
            "module": context.module,
            "action": context.action,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "metadata": context.metadata
        }
        
        if error:
            log_data["error"] = error
        
        if result_metadata:
            log_data["result_metadata"] = result_metadata
        
        if status == "success":
            self.logger.info("Request completed", **log_data)
        else:
            self.logger.error("Request failed", **log_data)
        
        # Clean up
        del self.active_requests[request_id]
        
        # Clear context variables if this was the current request
        if request_id_var.get() == request_id:
            request_id_var.set(None)
            user_id_var.set(None)
            module_var.set(None)
            action_var.set(None)
    
    def get_current_context(self) -> Optional[RequestContext]:
        """Get current request context"""
        request_id = request_id_var.get()
        if request_id and request_id in self.active_requests:
            return self.active_requests[request_id]
        return None
    
    def update_context(self, **updates):
        """Update current request context"""
        request_id = request_id_var.get()
        if request_id and request_id in self.active_requests:
            context = self.active_requests[request_id]
            for key, value in updates.items():
                if hasattr(context, key):
                    setattr(context, key, value)
                else:
                    context.metadata[key] = value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracking statistics"""
        active_count = len(self.active_requests)
        avg_duration = 0
        
        if active_count > 0:
            total_duration = sum(
                time.time() - ctx.start_time 
                for ctx in self.active_requests.values()
            )
            avg_duration = total_duration / active_count
        
        return {
            "active_requests": active_count,
            "average_duration_seconds": round(avg_duration, 2),
            "requests_by_module": self._group_by_module(),
            "requests_by_user": self._group_by_user()
        }
    
    def _group_by_module(self) -> Dict[str, int]:
        """Group active requests by module"""
        groups = {}
        for context in self.active_requests.values():
            module = context.module or "unknown"
            groups[module] = groups.get(module, 0) + 1
        return groups
    
    def _group_by_user(self) -> Dict[str, int]:
        """Group active requests by user"""
        groups = {}
        for context in self.active_requests.values():
            user_id = str(context.user_id or "anonymous")
            groups[user_id] = groups.get(user_id, 0) + 1
        return groups

class LoggingMiddleware:
    """
    Middleware for automatic request tracking in async functions
    
    Provides decorators and context managers for easy integration.
    """
    
    def __init__(self, tracker: Optional[RequestTracker] = None):
        self.tracker = tracker or get_request_tracker()
    
    def track_request(self, module: str, action: str):
        """Decorator for automatic request tracking"""
        def decorator(func: Callable):
            if asyncio.iscoroutinefunction(func):
                async def async_wrapper(*args, **kwargs):
                    # Extract user_id if available
                    user_id = kwargs.get('user_id') or getattr(args[0] if args else None, 'user_id', None)
                    
                    request_id = self.tracker.start_request(
                        user_id=user_id,
                        module=module,
                        action=action
                    )
                    
                    try:
                        result = await func(*args, **kwargs)
                        self.tracker.end_request(request_id, "success")
                        return result
                    except Exception as e:
                        self.tracker.end_request(request_id, "error", str(e))
                        raise
                
                return async_wrapper
            else:
                def sync_wrapper(*args, **kwargs):
                    # Extract user_id if available
                    user_id = kwargs.get('user_id') or getattr(args[0] if args else None, 'user_id', None)
                    
                    request_id = self.tracker.start_request(
                        user_id=user_id,
                        module=module,
                        action=action
                    )
                    
                    try:
                        result = func(*args, **kwargs)
                        self.tracker.end_request(request_id, "success")
                        return result
                    except Exception as e:
                        self.tracker.end_request(request_id, "error", str(e))
                        raise
                
                return sync_wrapper
        
        return decorator
    
    def request_context(self, user_id: Optional[int] = None, module: str = None, 
                       action: str = None, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for manual request tracking"""
        
        class RequestContextManager:
            def __init__(self, tracker: RequestTracker, user_id: Optional[int], 
                        module: str, action: str, metadata: Optional[Dict[str, Any]]):
                self.tracker = tracker
                self.user_id = user_id
                self.module = module
                self.action = action
                self.metadata = metadata
                self.request_id = None
            
            def __enter__(self):
                self.request_id = self.tracker.start_request(
                    self.user_id, self.module, self.action, self.metadata
                )
                return self.request_id
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    self.tracker.end_request(self.request_id, "success")
                else:
                    self.tracker.end_request(self.request_id, "error", str(exc_val))
            
            async def __aenter__(self):
                return self.__enter__()
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return self.__exit__(exc_type, exc_val, exc_tb)
        
        return RequestContextManager(self.tracker, user_id, module, action, metadata)

# Global instances
_global_tracker: Optional[RequestTracker] = None
_global_middleware: Optional[LoggingMiddleware] = None

def initialize_logging_middleware() -> RequestTracker:
    """Initialize global logging middleware"""
    global _global_tracker, _global_middleware
    
    _global_tracker = RequestTracker()
    _global_middleware = LoggingMiddleware(_global_tracker)
    
    return _global_tracker

def get_request_tracker() -> RequestTracker:
    """Get global request tracker"""
    if _global_tracker is None:
        return initialize_logging_middleware()
    return _global_tracker

def get_middleware() -> LoggingMiddleware:
    """Get global logging middleware"""
    if _global_middleware is None:
        initialize_logging_middleware()
    return _global_middleware

def get_structured_logger(name: str) -> StructuredLogger:
    """Get structured logger for a module"""
    return StructuredLogger(name)

# Convenience functions
def set_request_context(user_id: int, module: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to set request context"""
    return get_request_tracker().start_request(user_id, module, action, metadata)

def clear_request_context():
    """Clear current request context"""
    request_id_var.set(None)
    user_id_var.set(None)
    module_var.set(None)
    action_var.set(None)

def get_current_request_id() -> Optional[str]:
    """Get current request ID"""
    return request_id_var.get()

def log_user_action(logger: logging.Logger, user_id: int, action: str, module: str, 
                   success: bool, metadata: Optional[Dict[str, Any]] = None):
    """Log user action with consistent format"""
    log_data = {
        "user_id": user_id,
        "action": action,
        "module": module,
        "success": success,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if metadata:
        log_data.update(metadata)
    
    if success:
        logger.info(f"User action: {action}", extra=log_data)
    else:
        logger.error(f"User action failed: {action}", extra=log_data)

# Export
__all__ = [
    "RequestContext", "StructuredLogger", "RequestTracker", "LoggingMiddleware",
    "initialize_logging_middleware", "get_request_tracker", "get_middleware",
    "get_structured_logger", "set_request_context", "clear_request_context",
    "get_current_request_id", "log_user_action"
]
