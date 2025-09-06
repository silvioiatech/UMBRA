"""
Configuration validation for Umbra Bot.
Provides comprehensive validation for Railway deployment.
"""
from typing import List, NamedTuple, Optional
from .config import config


class ValidationIssue(NamedTuple):
    """Represents a configuration validation issue."""
    level: str  # 'error' or 'warning'
    component: str
    message: str
    suggestion: Optional[str] = None


class ConfigValidator:
    """Validates Umbra configuration with detailed error reporting."""
    
    def __init__(self):
        """Initialize the configuration validator."""
        pass
    
    def validate_all(self) -> List[ValidationIssue]:
        """Validate all configuration and return list of issues."""
        issues = []
        
        # Validate core requirements
        issues.extend(self._validate_core_config())
        
        # Validate optional features
        issues.extend(self._validate_optional_features())
        
        # Validate system configuration
        issues.extend(self._validate_system_config())
        
        return issues
    
    def _validate_core_config(self) -> List[ValidationIssue]:
        """Validate core required configuration."""
        issues = []
        
        # Telegram Bot Token
        if not config.TELEGRAM_BOT_TOKEN:
            issues.append(ValidationIssue(
                level='error',
                component='telegram',
                message='TELEGRAM_BOT_TOKEN is required',
                suggestion='Get token from @BotFather on Telegram'
            ))
        elif config.TELEGRAM_BOT_TOKEN.startswith('your_'):
            issues.append(ValidationIssue(
                level='error',
                component='telegram',
                message='TELEGRAM_BOT_TOKEN contains placeholder value',
                suggestion='Replace with actual bot token from @BotFather'
            ))
        
        # Allowed User IDs
        if not config.ALLOWED_USER_IDS:
            issues.append(ValidationIssue(
                level='error',
                component='access_control',
                message='ALLOWED_USER_IDS is required',
                suggestion='Get user IDs from @userinfobot and set as comma-separated list'
            ))
        
        # Admin User IDs
        if not config.ALLOWED_ADMIN_IDS:
            issues.append(ValidationIssue(
                level='error',
                component='access_control',
                message='ALLOWED_ADMIN_IDS is required',
                suggestion='Set admin user IDs as comma-separated list'
            ))
        
        return issues
    
    def _validate_optional_features(self) -> List[ValidationIssue]:
        """Validate optional feature configurations."""
        issues = []
        
        # AI Integration
        if not config.OPENROUTER_API_KEY:
            issues.append(ValidationIssue(
                level='warning',
                component='ai',
                message='OPENROUTER_API_KEY not set - AI features will be disabled',
                suggestion='Get API key from https://openrouter.ai for AI capabilities'
            ))
        
        # R2 Storage
        r2_vars = [config.R2_ACCOUNT_ID, config.R2_ACCESS_KEY_ID, config.R2_SECRET_ACCESS_KEY, config.R2_BUCKET]
        r2_set_count = sum(1 for var in r2_vars if var)
        
        if r2_set_count > 0 and r2_set_count < 4:
            issues.append(ValidationIssue(
                level='warning',
                component='storage',
                message='Incomplete R2 configuration - missing some R2 environment variables',
                suggestion='Set all R2 variables: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET'
            ))
        elif r2_set_count == 0:
            issues.append(ValidationIssue(
                level='warning',
                component='storage',
                message='R2 storage not configured - using local SQLite storage',
                suggestion='Configure R2 for cloud storage or continue with SQLite for local development'
            ))
        
        return issues
    
    def _validate_system_config(self) -> List[ValidationIssue]:
        """Validate system configuration."""
        issues = []
        
        # Port validation
        if not (1 <= config.PORT <= 65535):
            issues.append(ValidationIssue(
                level='error',
                component='system',
                message=f'PORT value {config.PORT} is invalid',
                suggestion='PORT must be between 1 and 65535'
            ))
        
        # Rate limit validation
        if config.RATE_LIMIT_PER_MIN <= 0:
            issues.append(ValidationIssue(
                level='warning',
                component='system',
                message=f'RATE_LIMIT_PER_MIN value {config.RATE_LIMIT_PER_MIN} is invalid',
                suggestion='Set RATE_LIMIT_PER_MIN to a positive integer'
            ))
        
        # Environment validation
        valid_environments = ['development', 'staging', 'production']
        if config.ENVIRONMENT not in valid_environments:
            issues.append(ValidationIssue(
                level='warning',
                component='system',
                message=f'ENVIRONMENT value "{config.ENVIRONMENT}" is not standard',
                suggestion=f'Consider using one of: {", ".join(valid_environments)}'
            ))
        
        return issues