"""
Creator v1 (CRT4) - Default Configuration
Complete configuration template with all available options
"""

# Core Creator v1 Settings
CREATOR_V1_ENABLED = True
CREATOR_V1_DEBUG = False
CREATOR_VERSION = "1.0.0"

# =============================================================================
# CORE SERVICE CONFIGURATION
# =============================================================================

# General Settings
CREATOR_MAX_OUTPUT_TOKENS = 2000
CREATOR_DEFAULT_TONE = "professional"
CREATOR_MAX_CONCURRENT_REQUESTS = 100
CREATOR_REQUEST_TIMEOUT_SECONDS = 300

# =============================================================================
# MODEL PROVIDER CONFIGURATION
# =============================================================================

# Provider Settings
CREATOR_PROVIDER_FAILOVER_ENABLED = True
CREATOR_PROVIDER_HEALTH_CHECK_INTERVAL = 300
CREATOR_PROVIDER_MAX_RETRIES = 3
CREATOR_PROVIDER_RETRY_DELAY_SECONDS = 5
CREATOR_PROVIDER_TIMEOUT_SECONDS = 60

# OpenAI Configuration
CREATOR_OPENAI_API_KEY = ""  # Set your OpenAI API key
CREATOR_OPENAI_MODEL = "gpt-4"
CREATOR_OPENAI_TEMPERATURE = 0.7
CREATOR_OPENAI_MAX_TOKENS = 2000
CREATOR_OPENAI_ENABLED = True

# Anthropic Configuration
CREATOR_ANTHROPIC_API_KEY = ""  # Set your Anthropic API key
CREATOR_ANTHROPIC_MODEL = "claude-3-opus-20240229"
CREATOR_ANTHROPIC_TEMPERATURE = 0.7
CREATOR_ANTHROPIC_MAX_TOKENS = 2000
CREATOR_ANTHROPIC_ENABLED = False

# Stability AI Configuration
CREATOR_STABILITY_API_KEY = ""  # Set your Stability AI API key
CREATOR_STABILITY_ENGINE = "stable-diffusion-xl-1024-v1-0"
CREATOR_STABILITY_ENABLED = False

# ElevenLabs Configuration
CREATOR_ELEVENLABS_API_KEY = ""  # Set your ElevenLabs API key
CREATOR_ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
CREATOR_ELEVENLABS_ENABLED = False

# Hugging Face Configuration
CREATOR_HUGGINGFACE_API_KEY = ""  # Set your Hugging Face API key
CREATOR_HUGGINGFACE_ENABLED = False

# =============================================================================
# ANALYTICS AND METRICS CONFIGURATION
# =============================================================================

# Analytics
CREATOR_ANALYTICS_ENABLED = True
CREATOR_ANALYTICS_RETENTION_DAYS = 30
CREATOR_ANALYTICS_EXPORT_ENABLED = True
CREATOR_ANALYTICS_EXPORT_INTERVAL_HOURS = 24

# Advanced Metrics
CREATOR_METRICS_ENABLED = True
CREATOR_METRICS_RETENTION_HOURS = 168  # 1 week
CREATOR_METRICS_AGGREGATION_INTERVAL = 60
CREATOR_METRICS_EXPORT_ENABLED = True
CREATOR_METRICS_EXPORT_DIR = "exports/metrics"
CREATOR_METRICS_ANOMALY_DETECTION = True

# =============================================================================
# CACHING CONFIGURATION
# =============================================================================

# Cache Settings
CREATOR_CACHE_ENABLED = True
CREATOR_CACHE_DEFAULT_TTL_SECONDS = 3600  # 1 hour
CREATOR_CACHE_MAX_MEMORY_MB = 100
CREATOR_CACHE_MAX_ENTRIES = 10000
CREATOR_CACHE_COMPRESSION_THRESHOLD_BYTES = 1024

# Redis Cache (optional)
CREATOR_CACHE_REDIS_ENABLED = False
CREATOR_CACHE_REDIS_HOST = "localhost"
CREATOR_CACHE_REDIS_PORT = 6379
CREATOR_CACHE_REDIS_DB = 0
CREATOR_CACHE_REDIS_PASSWORD = ""

# Disk Cache (optional)
CREATOR_CACHE_DISK_ENABLED = False
CREATOR_CACHE_DISK_PATH = "cache"

# =============================================================================
# RATE LIMITING CONFIGURATION
# =============================================================================

# Rate Limiting
CREATOR_RATE_LIMITING_ENABLED = True
CREATOR_RATE_LIMITING_STRICT = False
CREATOR_RATE_LIMITING_LOGGING = True

# Global Limits
CREATOR_GLOBAL_REQUESTS_PER_MINUTE = 1000
CREATOR_GLOBAL_REQUESTS_PER_HOUR = 10000
CREATOR_GLOBAL_BURST_ALLOWANCE = 50

# User Limits
CREATOR_USER_REQUESTS_PER_MINUTE = 60
CREATOR_USER_REQUESTS_PER_HOUR = 1000
CREATOR_USER_TOKENS_PER_MINUTE = 50000
CREATOR_USER_COST_LIMIT_USD = 10.0

# Action-Specific Limits
CREATOR_IMAGE_REQUESTS_PER_MINUTE = 10
CREATOR_VIDEO_REQUESTS_PER_HOUR = 20

# IP-Based Limits
CREATOR_IP_RATE_LIMIT_PER_MINUTE = 100

# =============================================================================
# HEALTH MONITORING CONFIGURATION
# =============================================================================

# Health Monitoring
CREATOR_HEALTH_MONITORING_ENABLED = True
CREATOR_HEALTH_CHECK_INTERVAL_SECONDS = 30
CREATOR_HEALTH_ALERTS_ENABLED = True
CREATOR_HEALTH_METRICS_RETENTION_HOURS = 24
CREATOR_ALERT_COOLDOWN_SECONDS = 300

# System Thresholds
CREATOR_CPU_ALERT_THRESHOLD = 80.0
CREATOR_MEMORY_ALERT_THRESHOLD = 85.0
CREATOR_DISK_ALERT_THRESHOLD = 90.0
CREATOR_RESPONSE_TIME_ALERT_MS = 5000.0
CREATOR_ERROR_RATE_ALERT_PERCENT = 5.0

# =============================================================================
# BATCHING CONFIGURATION
# =============================================================================

# Intelligent Batching
CREATOR_BATCHING_ENABLED = True
CREATOR_BATCHING_ADAPTIVE = True
CREATOR_GLOBAL_MAX_BATCH_SIZE = 20
CREATOR_GLOBAL_MAX_WAIT_TIME_MS = 10000

# Default Batch Settings
CREATOR_DEFAULT_BATCH_SIZE = 5
CREATOR_DEFAULT_WAIT_TIME_MS = 3000
CREATOR_DEFAULT_SIMILARITY_THRESHOLD = 0.7

# =============================================================================
# WORKFLOW CONFIGURATION
# =============================================================================

# Workflow Management
CREATOR_WORKFLOW_MAX_CONCURRENT = 10
CREATOR_WORKFLOW_DEFAULT_TIMEOUT_SECONDS = 3600
CREATOR_WORKFLOW_CLEANUP_INTERVAL_SECONDS = 300

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# Security
CREATOR_SECURITY_ENABLED = True
CREATOR_JWT_SECRET = ""  # Set a strong secret key
CREATOR_JWT_ALGORITHM = "HS256"
CREATOR_SESSION_TIMEOUT_HOURS = 24
CREATOR_MAX_LOGIN_ATTEMPTS = 5
CREATOR_LOCKOUT_DURATION_MINUTES = 30
CREATOR_ENCRYPTION_PASSWORD = ""  # Set encryption password

# =============================================================================
# PLUGIN SYSTEM CONFIGURATION
# =============================================================================

# Plugins
CREATOR_PLUGIN_DIRECTORIES = ["plugins"]
CREATOR_PLUGIN_AUTO_LOAD = True
CREATOR_PLUGIN_SANDBOX = False
CREATOR_PLUGIN_MAX_LOAD_TIME_SECONDS = 30

# Plugin Security
CREATOR_PLUGIN_ALLOWED_MODULES = [
    "json", "time", "datetime", "asyncio", "aiohttp", "requests",
    "numpy", "pandas", "PIL", "cv2", "transformers", "torch"
]
CREATOR_PLUGIN_BLOCKED_MODULES = [
    "os", "sys", "subprocess", "exec", "eval", "__import__"
]

# =============================================================================
# DYNAMIC CONFIGURATION
# =============================================================================

# Configuration Management
CREATOR_CONFIG_WATCH_FILES = True
CREATOR_CONFIG_HOT_RELOAD = True
CREATOR_CONFIG_VALIDATION = True
CREATOR_CONFIG_BACKUP = True

# =============================================================================
# BRAND VOICE AND VALIDATION
# =============================================================================

# Brand Voice
CREATOR_BRAND_VOICE_ENABLED = True
CREATOR_BRAND_VOICE_STRICT_MODE = False
CREATOR_BRAND_VOICE_AUTO_LEARN = True

# Content Validation
CREATOR_CONTENT_VALIDATION_ENABLED = True
CREATOR_CONTENT_VALIDATION_STRICT = False
CREATOR_CONTENT_VALIDATION_AUTO_FIX = True

# =============================================================================
# TEMPLATE AND CONNECTOR CONFIGURATION
# =============================================================================

# Templates
CREATOR_TEMPLATES_ENABLED = True
CREATOR_TEMPLATES_AUTO_LOAD = True
CREATOR_TEMPLATES_CACHE_ENABLED = True

# Connectors
CREATOR_CONNECTORS_ENABLED = True
CREATOR_CONNECTORS_TIMEOUT_SECONDS = 30
CREATOR_CONNECTORS_MAX_RETRIES = 3

# Google Drive Connector
CREATOR_GOOGLE_DRIVE_ENABLED = False
CREATOR_GOOGLE_DRIVE_CREDENTIALS_PATH = ""
CREATOR_GOOGLE_DRIVE_FOLDER_ID = ""

# Notion Connector
CREATOR_NOTION_ENABLED = False
CREATOR_NOTION_API_KEY = ""
CREATOR_NOTION_DATABASE_ID = ""

# Airtable Connector
CREATOR_AIRTABLE_ENABLED = False
CREATOR_AIRTABLE_API_KEY = ""
CREATOR_AIRTABLE_BASE_ID = ""

# Slack Connector
CREATOR_SLACK_ENABLED = False
CREATOR_SLACK_BOT_TOKEN = ""
CREATOR_SLACK_CHANNEL = ""

# =============================================================================
# PLATFORM PRESETS CONFIGURATION
# =============================================================================

# Platform Presets
CREATOR_PLATFORM_PRESETS_ENABLED = True

# Social Media Platforms
CREATOR_TWITTER_CHAR_LIMIT = 280
CREATOR_INSTAGRAM_CHAR_LIMIT = 2200
CREATOR_LINKEDIN_CHAR_LIMIT = 3000
CREATOR_FACEBOOK_CHAR_LIMIT = 63206
CREATOR_TIKTOK_CHAR_LIMIT = 150

# Content Optimization
CREATOR_AUTO_HASHTAG_GENERATION = True
CREATOR_AUTO_EMOJI_INSERTION = True
CREATOR_AUTO_LINK_FORMATTING = True

# =============================================================================
# COST AND USAGE MONITORING
# =============================================================================

# Cost Tracking
CREATOR_COST_TRACKING_ENABLED = True
CREATOR_COST_ALERT_THRESHOLD_USD = 100.0
CREATOR_COST_DAILY_LIMIT_USD = 50.0
CREATOR_COST_MONTHLY_LIMIT_USD = 1000.0

# Usage Tracking
CREATOR_USAGE_TRACKING_ENABLED = True
CREATOR_USAGE_EXPORT_ENABLED = True
CREATOR_USAGE_RETENTION_DAYS = 90

# =============================================================================
# LOGGING AND DEBUGGING
# =============================================================================

# Logging
CREATOR_LOG_LEVEL = "INFO"
CREATOR_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
CREATOR_LOG_FILE = "logs/creator.log"
CREATOR_LOG_MAX_SIZE_MB = 100
CREATOR_LOG_BACKUP_COUNT = 5

# Debug Settings
CREATOR_DEBUG_MODE = False
CREATOR_DEBUG_SAVE_REQUESTS = False
CREATOR_DEBUG_SAVE_RESPONSES = False
CREATOR_DEBUG_TIMING_ENABLED = True

# =============================================================================
# FEATURE FLAGS
# =============================================================================

# Experimental Features
CREATOR_FEATURE_FLAGS = {
    "multimodal_generation": False,
    "real_time_collaboration": False,
    "advanced_personalization": False,
    "voice_generation": False,
    "video_generation": False,
    "automated_optimization": False,
    "predictive_content": False,
    "sentiment_analysis": False,
    "content_scheduling": False,
    "a_b_testing": False
}

# =============================================================================
# INTEGRATION SETTINGS
# =============================================================================

# External Integrations
CREATOR_WEBHOOK_ENABLED = False
CREATOR_WEBHOOK_URL = ""
CREATOR_WEBHOOK_SECRET = ""

# API Settings
CREATOR_API_ENABLED = True
CREATOR_API_HOST = "0.0.0.0"
CREATOR_API_PORT = 8000
CREATOR_API_CORS_ENABLED = True
CREATOR_API_DOCS_ENABLED = True

# =============================================================================
# PERFORMANCE OPTIMIZATION
# =============================================================================

# Performance
CREATOR_ASYNC_ENABLED = True
CREATOR_THREAD_POOL_SIZE = 10
CREATOR_CONNECTION_POOL_SIZE = 100
CREATOR_KEEP_ALIVE_TIMEOUT = 300

# Optimization
CREATOR_CONTENT_COMPRESSION = True
CREATOR_RESPONSE_STREAMING = True
CREATOR_PREFETCH_ENABLED = True
CREATOR_LAZY_LOADING = True

# =============================================================================
# BACKUP AND RECOVERY
# =============================================================================

# Backup
CREATOR_BACKUP_ENABLED = False
CREATOR_BACKUP_INTERVAL_HOURS = 24
CREATOR_BACKUP_RETENTION_DAYS = 30
CREATOR_BACKUP_DIRECTORY = "backups"

# Recovery
CREATOR_AUTO_RECOVERY_ENABLED = True
CREATOR_RECOVERY_TIMEOUT_SECONDS = 60
CREATOR_RECOVERY_MAX_ATTEMPTS = 3

# =============================================================================
# ENVIRONMENT-SPECIFIC OVERRIDES
# =============================================================================

# Development Environment
if CREATOR_V1_DEBUG:
    CREATOR_LOG_LEVEL = "DEBUG"
    CREATOR_CACHE_ENABLED = False
    CREATOR_RATE_LIMITING_ENABLED = False
    CREATOR_SECURITY_ENABLED = False
    CREATOR_FEATURE_FLAGS.update({
        "debug_mode": True,
        "verbose_logging": True,
        "request_tracing": True
    })

# Production Environment Recommendations
# CREATOR_CACHE_REDIS_ENABLED = True
# CREATOR_SECURITY_ENABLED = True
# CREATOR_RATE_LIMITING_STRICT = True
# CREATOR_HEALTH_ALERTS_ENABLED = True
# CREATOR_BACKUP_ENABLED = True
# CREATOR_LOG_LEVEL = "WARNING"

# =============================================================================
# CUSTOM CONFIGURATION
# =============================================================================

# Add your custom configuration here
# CREATOR_CUSTOM_SETTING = "value"

# Configuration validation
def validate_configuration():
    """Validate configuration settings"""
    errors = []
    
    # Check required API keys
    if CREATOR_OPENAI_ENABLED and not CREATOR_OPENAI_API_KEY:
        errors.append("OpenAI API key is required when OpenAI is enabled")
    
    if CREATOR_STABILITY_ENABLED and not CREATOR_STABILITY_API_KEY:
        errors.append("Stability AI API key is required when Stability AI is enabled")
    
    # Check numeric ranges
    if CREATOR_MAX_OUTPUT_TOKENS < 100 or CREATOR_MAX_OUTPUT_TOKENS > 50000:
        errors.append("CREATOR_MAX_OUTPUT_TOKENS must be between 100 and 50000")
    
    if CREATOR_USER_REQUESTS_PER_MINUTE < 1:
        errors.append("CREATOR_USER_REQUESTS_PER_MINUTE must be at least 1")
    
    # Check security settings
    if CREATOR_SECURITY_ENABLED and not CREATOR_JWT_SECRET:
        errors.append("JWT secret is required when security is enabled")
    
    return errors

# Validate configuration on import
_validation_errors = validate_configuration()
if _validation_errors:
    import logging
    logger = logging.getLogger(__name__)
    for error in _validation_errors:
        logger.warning(f"Configuration warning: {error}")
