"""
Redaction Utilities - SEC1 Implementation
Automatic redaction of sensitive data in logs, audit trails, and responses
"""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Union, Set
from dataclasses import dataclass
from copy import deepcopy

logger = logging.getLogger(__name__)

@dataclass
class RedactionRule:
    """Rule for redacting sensitive data"""
    pattern: re.Pattern
    replacement: str
    description: str
    enabled: bool = True

class SensitiveDataRedactor:
    """
    Redacts sensitive data from strings, objects, and logs
    
    Supports configurable patterns and replacement strategies
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.redaction_char = self.config.get("redaction_char", "*")
        self.preserve_length = self.config.get("preserve_length", True)
        self.min_preserve_length = self.config.get("min_preserve_length", 3)
        
        # Compile redaction patterns
        self.rules = self._compile_redaction_rules()
        
        # Sensitive field names to redact in objects
        self.sensitive_fields = {
            "password", "passwd", "pwd", "secret", "token", "key", "api_key",
            "access_token", "refresh_token", "session_token", "auth_token",
            "private_key", "secret_key", "api_secret", "client_secret",
            "bearer_token", "authorization", "auth", "credential", "credentials",
            "ssh_key", "rsa_key", "certificate", "cert", "signature"
        }
        
        logger.info(f"Redactor initialized with {len(self.rules)} rules")
    
    def _compile_redaction_rules(self) -> List[RedactionRule]:
        """Compile all redaction patterns"""
        rules = []
        
        # API Keys and Tokens
        rules.append(RedactionRule(
            pattern=re.compile(r'\b(?:sk-|pk-|rk-)[A-Za-z0-9]{20,}', re.IGNORECASE),
            replacement="[API_KEY_REDACTED]",
            description="API keys (sk-, pk-, rk- prefixes)"
        ))
        
        rules.append(RedactionRule(
            pattern=re.compile(r'\bBearer\s+[A-Za-z0-9+/=]{20,}', re.IGNORECASE),
            replacement="Bearer [TOKEN_REDACTED]",
            description="Bearer tokens"
        ))
        
        rules.append(RedactionRule(
            pattern=re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}', re.IGNORECASE),
            replacement="[GITHUB_TOKEN_REDACTED]",
            description="GitHub tokens"
        ))
        
        # Email addresses
        rules.append(RedactionRule(
            pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            replacement=self._email_redaction_func,
            description="Email addresses"
        ))
        
        # Phone numbers (various formats)
        rules.append(RedactionRule(
            pattern=re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            replacement=self._phone_redaction_func,
            description="Phone numbers"
        ))
        
        # Credit card numbers
        rules.append(RedactionRule(
            pattern=re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            replacement="[CREDIT_CARD_REDACTED]",
            description="Credit card numbers"
        ))
        
        # Social Security Numbers (US format)
        rules.append(RedactionRule(
            pattern=re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            replacement="[SSN_REDACTED]",
            description="Social Security Numbers"
        ))
        
        # IP Addresses (partial redaction)
        rules.append(RedactionRule(
            pattern=re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
            replacement=self._ip_redaction_func,
            description="IP addresses"
        ))
        
        # AWS Access Keys
        rules.append(RedactionRule(
            pattern=re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
            replacement="[AWS_ACCESS_KEY_REDACTED]",
            description="AWS access keys"
        ))
        
        # Database connection strings
        rules.append(RedactionRule(
            pattern=re.compile(r'://[^:]+:[^@]+@', re.IGNORECASE),
            replacement="://[USER:PASS_REDACTED]@",
            description="Database connection credentials"
        ))
        
        # JWT Tokens (basic pattern)
        rules.append(RedactionRule(
            pattern=re.compile(r'\beyJ[A-Za-z0-9+/=]{20,}\.[A-Za-z0-9+/=]{20,}\.[A-Za-z0-9+/=]{20,}'),
            replacement="[JWT_TOKEN_REDACTED]",
            description="JWT tokens"
        ))
        
        # Private keys
        rules.append(RedactionRule(
            pattern=re.compile(r'-----BEGIN[^-]+PRIVATE KEY-----.*?-----END[^-]+PRIVATE KEY-----', re.DOTALL),
            replacement="[PRIVATE_KEY_REDACTED]",
            description="Private keys"
        ))
        
        # File paths that might contain sensitive info
        rules.append(RedactionRule(
            pattern=re.compile(r'/(?:home|Users)/[^/\s]+/(?:\.ssh|\.aws|\.config)/[^\s]*', re.IGNORECASE),
            replacement=self._filepath_redaction_func,
            description="Sensitive file paths"
        ))
        
        return rules
    
    def _email_redaction_func(self, match) -> str:
        """Redact email while preserving domain for debugging"""
        email = match.group(0)
        parts = email.split('@')
        if len(parts) == 2:
            username, domain = parts
            if len(username) <= 3:
                redacted_username = self.redaction_char * len(username)
            else:
                redacted_username = username[0] + self.redaction_char * (len(username) - 2) + username[-1]
            return f"{redacted_username}@{domain}"
        return "[EMAIL_REDACTED]"
    
    def _phone_redaction_func(self, match) -> str:
        """Redact phone number while preserving format"""
        phone = match.group(0)
        # Keep the format but redact digits
        redacted = re.sub(r'\d', self.redaction_char, phone)
        return redacted
    
    def _ip_redaction_func(self, match) -> str:
        """Partially redact IP address (keep first two octets)"""
        ip = match.group(0)
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{self.redaction_char * len(parts[2])}.{self.redaction_char * len(parts[3])}"
        return "[IP_REDACTED]"
    
    def _filepath_redaction_func(self, match) -> str:
        """Redact sensitive parts of file paths"""
        path = match.group(0)
        # Replace username in path
        return re.sub(r'/(?:home|Users)/[^/]+/', f'/[USER_REDACTED]/', path)
    
    def redact_string(self, text: str) -> str:
        """Redact sensitive data from a string"""
        if not isinstance(text, str) or not text:
            return text
        
        redacted = text
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                if callable(rule.replacement):
                    # Custom redaction function
                    redacted = rule.pattern.sub(rule.replacement, redacted)
                else:
                    # Simple string replacement
                    redacted = rule.pattern.sub(rule.replacement, redacted)
            except Exception as e:
                logger.warning(f"Redaction rule '{rule.description}' failed: {e}")
        
        return redacted
    
    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive data from a dictionary"""
        if not isinstance(data, dict):
            return data
        
        redacted = deepcopy(data)
        
        for key, value in redacted.items():
            # Check if key name indicates sensitive data
            if isinstance(key, str) and key.lower() in self.sensitive_fields:
                redacted[key] = self._redact_value(value)
            elif isinstance(value, str):
                redacted[key] = self.redact_string(value)
            elif isinstance(value, dict):
                redacted[key] = self.redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = self.redact_list(value)
        
        return redacted
    
    def redact_list(self, data: List[Any]) -> List[Any]:
        """Redact sensitive data from a list"""
        if not isinstance(data, list):
            return data
        
        redacted = []
        
        for item in data:
            if isinstance(item, str):
                redacted.append(self.redact_string(item))
            elif isinstance(item, dict):
                redacted.append(self.redact_dict(item))
            elif isinstance(item, list):
                redacted.append(self.redact_list(item))
            else:
                redacted.append(item)
        
        return redacted
    
    def redact_object(self, obj: Any) -> Any:
        """Redact sensitive data from any object"""
        if isinstance(obj, str):
            return self.redact_string(obj)
        elif isinstance(obj, dict):
            return self.redact_dict(obj)
        elif isinstance(obj, list):
            return self.redact_list(obj)
        else:
            return obj
    
    def _redact_value(self, value: Any) -> str:
        """Redact a sensitive value while preserving type info"""
        if value is None:
            return None
        elif isinstance(value, bool):
            return "[BOOL_REDACTED]"
        elif isinstance(value, (int, float)):
            return "[NUMBER_REDACTED]"
        elif isinstance(value, str):
            if len(value) == 0:
                return ""
            elif len(value) <= self.min_preserve_length:
                return self.redaction_char * len(value)
            elif self.preserve_length:
                return self.redaction_char * len(value)
            else:
                return "[VALUE_REDACTED]"
        else:
            return "[OBJECT_REDACTED]"
    
    def redact_json_string(self, json_str: str) -> str:
        """Redact sensitive data from a JSON string"""
        try:
            data = json.loads(json_str)
            redacted_data = self.redact_object(data)
            return json.dumps(redacted_data, ensure_ascii=False)
        except json.JSONDecodeError:
            # If not valid JSON, treat as regular string
            return self.redact_string(json_str)
    
    def redact_log_record(self, record: logging.LogRecord) -> logging.LogRecord:
        """Redact sensitive data from a log record"""
        # Create a copy to avoid modifying the original
        redacted_record = logging.LogRecord(
            record.name, record.levelno, record.pathname, record.lineno,
            record.msg, record.args, record.exc_info, record.funcName,
            record.stack_info
        )
        
        # Redact message
        if isinstance(record.msg, str):
            redacted_record.msg = self.redact_string(record.msg)
        
        # Redact args
        if record.args:
            redacted_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    redacted_args.append(self.redact_string(arg))
                elif isinstance(arg, dict):
                    redacted_args.append(self.redact_dict(arg))
                else:
                    redacted_args.append(arg)
            redacted_record.args = tuple(redacted_args)
        
        # Redact extra fields
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in {'name', 'levelno', 'pathname', 'lineno', 'msg', 'args', 'exc_info', 'funcName', 'stack_info'}:
                    if isinstance(value, str):
                        setattr(redacted_record, key, self.redact_string(value))
                    elif isinstance(value, dict):
                        setattr(redacted_record, key, self.redact_dict(value))
                    else:
                        setattr(redacted_record, key, value)
        
        return redacted_record
    
    def add_custom_rule(self, pattern: str, replacement: str, description: str = "") -> None:
        """Add a custom redaction rule"""
        try:
            compiled_pattern = re.compile(pattern)
            rule = RedactionRule(
                pattern=compiled_pattern,
                replacement=replacement,
                description=description or f"Custom rule: {pattern}"
            )
            self.rules.append(rule)
            logger.info(f"Added custom redaction rule: {description}")
        except Exception as e:
            logger.error(f"Failed to add custom redaction rule: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get redaction statistics"""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules if r.enabled]),
            "sensitive_fields": len(self.sensitive_fields),
            "preserve_length": self.preserve_length,
            "redaction_char": self.redaction_char
        }

# Global redactor instance
_global_redactor: Optional[SensitiveDataRedactor] = None

def initialize_redactor(config: Optional[Dict[str, Any]] = None) -> SensitiveDataRedactor:
    """Initialize global redactor instance"""
    global _global_redactor
    _global_redactor = SensitiveDataRedactor(config)
    return _global_redactor

def get_redactor() -> SensitiveDataRedactor:
    """Get global redactor instance"""
    if _global_redactor is None:
        # Initialize with default config if not already initialized
        return initialize_redactor()
    return _global_redactor

def redact_sensitive_data(obj: Any) -> Any:
    """Convenience function to redact sensitive data from any object"""
    return get_redactor().redact_object(obj)

def redact_string(text: str) -> str:
    """Convenience function to redact sensitive data from a string"""
    return get_redactor().redact_string(text)

def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to redact sensitive data from a dictionary"""
    return get_redactor().redact_dict(data)

# Export
__all__ = [
    "RedactionRule", "SensitiveDataRedactor", 
    "initialize_redactor", "get_redactor",
    "redact_sensitive_data", "redact_string", "redact_dict"
]
