"""
Creator Error Classes and Exception Handling
"""

class CreatorError(Exception):
    """Base exception for Creator module"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code or "CREATOR_ERROR"
        self.details = details or {}

class ValidationError(CreatorError):
    """Content validation failed"""
    def __init__(self, message: str, validation_details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", validation_details)

class PlatformError(CreatorError):
    """Platform-specific constraint violation"""
    def __init__(self, message: str, platform: str = None, constraint: str = None):
        super().__init__(message, "PLATFORM_ERROR", {
            "platform": platform,
            "constraint": constraint
        })

class ProviderError(CreatorError):
    """External provider API error"""
    def __init__(self, message: str, provider: str = None, api_error: str = None):
        super().__init__(message, "PROVIDER_ERROR", {
            "provider": provider,
            "api_error": api_error
        })

class TokenLimitError(CreatorError):
    """Token limit exceeded"""
    def __init__(self, message: str, tokens_used: int = None, limit: int = None):
        super().__init__(message, "TOKEN_LIMIT_ERROR", {
            "tokens_used": tokens_used,
            "limit": limit
        })

class ConsentError(CreatorError):
    """Consent required for operation"""
    def __init__(self, message: str, consent_type: str = None):
        super().__init__(message, "CONSENT_ERROR", {
            "consent_type": consent_type
        })

class ContentError(CreatorError):
    """Content generation or processing error"""
    def __init__(self, message: str, content_type: str = None):
        super().__init__(message, "CONTENT_ERROR", {
            "content_type": content_type
        })

class BrandVoiceError(CreatorError):
    """Brand voice configuration error"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, "BRAND_VOICE_ERROR", {
            "field": field
        })

class ExportError(CreatorError):
    """Export operation error"""
    def __init__(self, message: str, export_format: str = None):
        super().__init__(message, "EXPORT_ERROR", {
            "export_format": export_format
        })

class MediaError(CreatorError):
    """Media processing error"""
    def __init__(self, message: str, media_type: str = None, operation: str = None):
        super().__init__(message, "MEDIA_ERROR", {
            "media_type": media_type,
            "operation": operation
        })

# Error code mappings for API responses
ERROR_CODES = {
    "CREATOR_ERROR": {
        "status": 500,
        "message": "Internal creator error"
    },
    "VALIDATION_ERROR": {
        "status": 400,
        "message": "Content validation failed"
    },
    "PLATFORM_ERROR": {
        "status": 400,
        "message": "Platform constraint violation"
    },
    "PROVIDER_ERROR": {
        "status": 502,
        "message": "External provider error"
    },
    "TOKEN_LIMIT_ERROR": {
        "status": 413,
        "message": "Token limit exceeded"
    },
    "CONSENT_ERROR": {
        "status": 403,
        "message": "Consent required"
    },
    "CONTENT_ERROR": {
        "status": 422,
        "message": "Content processing error"
    },
    "BRAND_VOICE_ERROR": {
        "status": 400,
        "message": "Brand voice configuration error"
    },
    "EXPORT_ERROR": {
        "status": 500,
        "message": "Export operation failed"
    },
    "MEDIA_ERROR": {
        "status": 422,
        "message": "Media processing error"
    }
}

def format_error_response(error: CreatorError) -> dict:
    """Format error for API response"""
    error_info = ERROR_CODES.get(error.error_code, ERROR_CODES["CREATOR_ERROR"])
    
    return {
        "error": {
            "code": error.error_code,
            "message": str(error),
            "status": error_info["status"],
            "details": error.details
        }
    }
