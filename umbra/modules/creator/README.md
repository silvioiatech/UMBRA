# Creator v1 (CRT4) - Advanced Content Creation System

![Creator v1](https://img.shields.io/badge/Creator-v1.0.0-blue.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)

**Creator v1 (CRT4)** is a comprehensive, enterprise-grade content creation system that combines advanced AI capabilities with robust infrastructure components to deliver scalable, secure, and intelligent content generation.

## 🚀 Features

### Core Capabilities
- **Multi-Provider AI Integration** - Seamlessly work with OpenAI, Anthropic, Stability AI, and more
- **Intelligent Content Orchestration** - Auto-route and optimize content generation workflows
- **Brand Voice Management** - Maintain consistent brand voice across all content
- **Platform-Specific Optimization** - Tailored content for social media platforms
- **Advanced Analytics & Metrics** - Comprehensive tracking and performance monitoring

### Enterprise Features
- **Security & Authentication** - JWT-based auth, role-based permissions, audit logging
- **Rate Limiting & Quotas** - Intelligent rate limiting with burst handling
- **Caching System** - Multi-level caching with TTL and tag-based invalidation
- **Health Monitoring** - Real-time system health checks and alerting
- **Plugin Architecture** - Extensible plugin system for custom functionality

### Advanced Systems
- **Workflow Management** - Visual workflow builder with dependency management
- **Intelligent Batching** - Optimize API calls through smart request batching
- **Dynamic Configuration** - Hot-reload configuration without restarts
- **Content Validation** - Automated content quality and compliance checking
- **Template System** - Reusable content templates with variable substitution

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [System Architecture](#-system-architecture)
- [Configuration](#-configuration)
- [Components](#-components)
- [API Reference](#-api-reference)
- [Examples](#-examples)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Contributing](#-contributing)

## 🛠 Installation

### Prerequisites
- Python 3.8+
- Redis (optional, for distributed caching)
- PostgreSQL (optional, for persistent storage)

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/your-org/umbra.git
cd umbra

# Install dependencies
pip install -r requirements.txt

# Install Creator v1
pip install -e .
```

### Docker Installation

```bash
# Using Docker Compose
docker-compose up -d creator-v1

# Or build manually
docker build -t creator-v1 .
docker run -p 8000:8000 creator-v1
```

## 🚀 Quick Start

### Basic Setup

```python
import asyncio
from umbra.core.config import UmbraConfig
from umbra.ai.agent import UmbraAIAgent
from umbra.modules.creator import create_creator_system

async def main():
    # Configure the system
    config = UmbraConfig({
        "CREATOR_V1_ENABLED": True,
        "CREATOR_OPENAI_API_KEY": "your-openai-key",
        "CREATOR_SECURITY_ENABLED": False,  # Disable for quick start
    })
    
    # Create AI agent
    ai_agent = UmbraAIAgent(config)
    
    # Initialize Creator v1 system
    creator_system = await create_creator_system(config, ai_agent)
    
    # Generate content
    request = {
        "action": "generate_post",
        "topic": "The future of AI in healthcare",
        "platform": "linkedin",
        "tone": "professional"
    }
    
    result = await creator_system.generate_content(request, user_id="demo_user")
    print(f"Generated content: {result['content']}")
    
    # Cleanup
    await creator_system.shutdown()

# Run the example
asyncio.run(main())
```

### Generate a Complete Content Pack

```python
# Generate a comprehensive content pack
request = {
    "action": "generate_content_pack",
    "topic": "Sustainable technology innovations",
    "platform": "instagram",
    "tone": "engaging"
}

result = await creator_system.generate_content(request)

# Access generated content
pack = result['pack']
print(f"Caption: {pack['caption']}")
print(f"Hashtags: {pack['hashtags']}")
print(f"Call to Action: {pack['cta']}")
print(f"Title Variations: {pack['titles']}")
```

## 🏗 System Architecture

Creator v1 follows a modular, microservices-inspired architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Creator v1 (CRT4)                       │
├─────────────────────────────────────────────────────────────┤
│  🎯 Main Service Layer                                      │
│  ├── CreatorService (Orchestration)                        │
│  ├── Auto-Orchestration Engine                             │
│  └── Content Generation Pipeline                           │
├─────────────────────────────────────────────────────────────┤
│  🤖 AI Provider Layer                                       │
│  ├── Enhanced Model Provider Manager                       │
│  ├── Failover & Load Balancing                            │
│  └── Provider Health Monitoring                            │
├─────────────────────────────────────────────────────────────┤
│  🎨 Content Management Layer                               │
│  ├── Brand Voice Manager                                   │
│  ├── Platform Presets                                      │
│  ├── Content Validator                                     │
│  └── Template System                                       │
├─────────────────────────────────────────────────────────────┤
│  🔧 Infrastructure Layer                                   │
│  ├── Advanced Analytics & Metrics                          │
│  ├── Multi-Level Caching                                   │
│  ├── Intelligent Batching                                  │
│  ├── Rate Limiting                                         │
│  └── Health Monitoring                                     │
├─────────────────────────────────────────────────────────────┤
│  🔒 Security & Management Layer                            │
│  ├── Security Manager                                      │
│  ├── Dynamic Configuration                                 │
│  ├── Workflow Engine                                       │
│  └── Plugin System                                         │
├─────────────────────────────────────────────────────────────┤
│  📡 Integration Layer                                       │
│  ├── Connector Manager                                     │
│  ├── External APIs                                         │
│  └── Webhook System                                        │
└─────────────────────────────────────────────────────────────┘
```

## ⚙️ Configuration

Creator v1 uses a comprehensive configuration system with environment-based overrides:

### Basic Configuration

```python
config = UmbraConfig({
    # Core Settings
    "CREATOR_V1_ENABLED": True,
    "CREATOR_MAX_OUTPUT_TOKENS": 2000,
    "CREATOR_DEFAULT_TONE": "professional",
    
    # Provider Settings
    "CREATOR_OPENAI_API_KEY": "your-api-key",
    "CREATOR_OPENAI_MODEL": "gpt-4",
    "CREATOR_PROVIDER_FAILOVER_ENABLED": True,
    
    # Performance Settings
    "CREATOR_CACHE_ENABLED": True,
    "CREATOR_BATCHING_ENABLED": True,
    "CREATOR_RATE_LIMITING_ENABLED": True,
    
    # Security Settings
    "CREATOR_SECURITY_ENABLED": True,
    "CREATOR_JWT_SECRET": "your-secret-key",
    
    # Monitoring Settings
    "CREATOR_ANALYTICS_ENABLED": True,
    "CREATOR_HEALTH_MONITORING_ENABLED": True,
})
```

### Environment Variables

```bash
# Core Settings
export CREATOR_V1_ENABLED=true
export CREATOR_OPENAI_API_KEY=your-api-key

# Performance Tuning
export CREATOR_MAX_CONCURRENT_REQUESTS=100
export CREATOR_CACHE_DEFAULT_TTL_SECONDS=3600

# Security
export CREATOR_JWT_SECRET=your-secret-key
export CREATOR_ENCRYPTION_PASSWORD=your-encryption-password
```

### Configuration File

```yaml
# config/creator.yaml
creator:
  v1:
    enabled: true
    debug: false
    
  providers:
    openai:
      api_key: ${CREATOR_OPENAI_API_KEY}
      model: gpt-4
      enabled: true
    
    stability:
      api_key: ${CREATOR_STABILITY_API_KEY}
      enabled: false
  
  performance:
    cache:
      enabled: true
      ttl_seconds: 3600
      max_memory_mb: 100
    
    rate_limiting:
      enabled: true
      requests_per_minute: 60
      strict_mode: false
  
  security:
    enabled: true
    session_timeout_hours: 24
    max_login_attempts: 5
```

## 🧩 Components

### Core Service Layer

#### CreatorService
The main orchestration service that coordinates all content generation:

```python
# Get the main service
creator_service = creator_system.get_component("creator_service")

# Generate content
result = await creator_service.generate_post(
    topic="AI in education",
    platform="twitter",
    tone="casual",
    user_id="user123"
)
```

#### Auto-Orchestration Engine
Intelligently routes complex requests to appropriate workflows:

```python
# Complex orchestration request
result = await creator_service.auto_orchestrate(
    input_data={
        "brief": "Create social media campaign for product launch",
        "products": ["Product A", "Product B"],
        "budget": "$10000"
    },
    goal="social_media_campaign",
    platform="multi"
)
```

### AI Provider Layer

#### Enhanced Model Provider Manager
Manages multiple AI providers with failover and load balancing:

```python
# Get provider manager
provider_manager = creator_system.get_component("provider_manager")

# Check provider status
status = await provider_manager.get_provider_status("openai")
print(f"OpenAI Status: {status}")

# Get best available provider
provider = await provider_manager.get_text_provider()
```

### Content Management Layer

#### Brand Voice Manager
Maintains consistent brand voice across all content:

```python
# Get brand voice manager
brand_voice = creator_system.get_component("brand_voice")

# Set brand guidelines
await brand_voice.update_brand_voice("default", {
    "tone_default": "friendly",
    "personality_traits": ["helpful", "expert", "approachable"],
    "communication_style": "conversational",
    "required_phrases": ["Contact us for more info"],
    "discouraged_words": ["maybe", "perhaps", "might"]
})
```

#### Content Validator
Automated content quality and compliance checking:

```python
# Get validator
validator = creator_system.get_component("validator")

# Validate content
validation_result = await validator.validate_content(
    content="Your content here",
    metadata={"platform": "linkedin"},
    platform="linkedin"
)

print(f"Valid: {validation_result['valid']}")
print(f"Issues: {validation_result['issues']}")
```

### Infrastructure Layer

#### Advanced Analytics & Metrics
Comprehensive tracking and performance monitoring:

```python
# Get analytics components
analytics = creator_system.get_component("analytics")
metrics = creator_system.get_component("advanced_metrics")

# Track custom metrics
metrics.record_metric("custom_metric", 42.0, {"source": "api"})
metrics.increment_counter("api_calls", 1)

# Get analytics data
daily_stats = analytics.get_daily_stats()
action_stats = analytics.get_action_stats()
```

#### Multi-Level Caching
Intelligent caching with TTL and tag-based invalidation:

```python
# Get cache
cache = creator_system.get_component("cache")

# Cache with tags
await cache.set("user_123_prefs", user_data, tags=["user", "preferences"])

# Invalidate by tags
await cache.invalidate_by_tags(["user"])

# Get cache statistics
stats = cache.get_stats()
```

#### Intelligent Batching
Optimize API calls through smart request batching:

```python
# Get batching system
batching = creator_system.get_component("batching")

# Add requests to batch
request_id = await batching.add_request(
    action="generate_hashtags",
    params={"topic": "AI technology"},
    user_id="user123"
)

# Check batching statistics
stats = batching.get_batch_stats()
```

### Security & Management Layer

#### Security Manager
JWT-based authentication with role-based permissions:

```python
# Get security manager
security = creator_system.get_component("security")

# Authenticate user
token = await security.authenticate_user("username", "password")

# Validate session
session = security.validate_session(token)

# Check permissions
has_permission = security.check_permission(session, Permission.WRITE)
```

#### Workflow Engine
Visual workflow builder with dependency management:

```python
# Create workflow
workflow_definition = {
    "name": "Content Creation Pipeline",
    "steps": [
        {
            "id": "research",
            "action": "research_topic",
            "params": {"topic": "${input.topic}"}
        },
        {
            "id": "generate",
            "action": "generate_content_pack",
            "dependencies": ["research"]
        }
    ]
}

workflow_id = await creator_system.create_workflow(workflow_definition)
result = await creator_system.execute_workflow(workflow_id, {"topic": "AI"})
```

#### Plugin System
Extensible plugin architecture for custom functionality:

```python
# Get plugin manager
plugin_manager = creator_system.get_component("plugin_manager")

# Load plugins from directory
await plugin_manager.scan_and_load_directory(Path("plugins"))

# Get available plugins
plugins = plugin_manager.get_all_plugins_info()

# Execute plugin method
result = await plugin_manager.call_plugin_method(
    "text_enhancer", "process_content", 
    content="Your content here", style="professional"
)
```

## 📚 API Reference

### Core Methods

#### `generate_content(request, user_id=None)`
Main content generation endpoint.

**Parameters:**
- `request` (dict): Content generation request
- `user_id` (str, optional): User identifier for tracking

**Request Format:**
```python
{
    "action": "generate_post|generate_content_pack|auto_orchestrate",
    "topic": "Content topic",
    "platform": "twitter|linkedin|instagram|facebook",
    "tone": "professional|casual|friendly|creative",
    "audience": "target audience description",
    "length": "short|medium|long"
}
```

**Response Format:**
```python
{
    "content": "Generated content",
    "platform": "target platform",
    "provider_used": "openai",
    "model_used": "gpt-4",
    "validation": {"valid": True, "issues": []},
    "metadata": {
        "word_count": 150,
        "char_count": 800,
        "generation_time": 1200
    }
}
```

#### `create_workflow(definition, user_id=None)`
Create a new workflow.

#### `execute_workflow(workflow_id, context=None)`
Execute an existing workflow.

#### `get_system_status()`
Get comprehensive system status.

#### `health_check()`
Perform system health check.

### Component-Specific APIs

Each component provides its own API. See individual component documentation for details.

## 💡 Examples

### Example 1: Multi-Platform Campaign

```python
async def create_multi_platform_campaign():
    platforms = ["twitter", "linkedin", "instagram", "facebook"]
    topic = "Launch of our new AI-powered app"
    
    results = {}
    
    for platform in platforms:
        request = {
            "action": "generate_content_pack",
            "topic": topic,
            "platform": platform,
            "tone": "exciting"
        }
        
        result = await creator_system.generate_content(request)
        results[platform] = result
    
    return results
```

### Example 2: Automated Content Pipeline

```python
async def automated_content_pipeline():
    workflow = {
        "name": "Blog to Social Pipeline",
        "steps": [
            {
                "id": "extract_key_points",
                "action": "extract_key_points",
                "params": {"content": "${blog_content}"}
            },
            {
                "id": "generate_twitter_thread",
                "action": "generate_twitter_thread",
                "params": {"key_points": "${extract_key_points.result}"},
                "dependencies": ["extract_key_points"]
            },
            {
                "id": "generate_linkedin_post",
                "action": "generate_post",
                "params": {
                    "topic": "${extract_key_points.summary}",
                    "platform": "linkedin"
                },
                "dependencies": ["extract_key_points"]
            }
        ]
    }
    
    workflow_id = await creator_system.create_workflow(workflow)
    return await creator_system.execute_workflow(
        workflow_id, 
        {"blog_content": "Your blog content here..."}
    )
```

### Example 3: Real-time Content Monitoring

```python
async def setup_content_monitoring():
    # Setup custom metrics
    metrics = creator_system.get_component("advanced_metrics")
    
    # Create alert for high error rate
    metrics.create_alert(
        name="high_error_rate",
        metric_name="request_errors",
        condition=">",
        threshold=10.0,
        duration_minutes=5,
        severity="critical"
    )
    
    # Add custom alert handler
    async def content_alert_handler(alert_data):
        print(f"ALERT: {alert_data['alert_name']}")
        # Send to monitoring system, Slack, etc.
    
    metrics.add_alert_handler(content_alert_handler)
```

## 🚢 Deployment

### Production Deployment

#### Docker Compose
```yaml
version: '3.8'
services:
  creator-v1:
    image: creator-v1:latest
    ports:
      - "8000:8000"
    environment:
      - CREATOR_V1_ENABLED=true
      - CREATOR_OPENAI_API_KEY=${OPENAI_API_KEY}
      - CREATOR_REDIS_HOST=redis
    depends_on:
      - redis
      - postgres
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: creator
      POSTGRES_USER: creator
      POSTGRES_PASSWORD: ${DB_PASSWORD}
```

#### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: creator-v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: creator-v1
  template:
    metadata:
      labels:
        app: creator-v1
    spec:
      containers:
      - name: creator-v1
        image: creator-v1:latest
        ports:
        - containerPort: 8000
        env:
        - name: CREATOR_V1_ENABLED
          value: "true"
        - name: CREATOR_OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: creator-secrets
              key: openai-api-key
```

### Environment-Specific Configurations

#### Development
```python
CREATOR_V1_DEBUG = True
CREATOR_LOG_LEVEL = "DEBUG"
CREATOR_SECURITY_ENABLED = False
CREATOR_RATE_LIMITING_ENABLED = False
CREATOR_CACHE_ENABLED = False
```

#### Staging
```python
CREATOR_V1_DEBUG = False
CREATOR_LOG_LEVEL = "INFO"
CREATOR_SECURITY_ENABLED = True
CREATOR_RATE_LIMITING_ENABLED = True
CREATOR_CACHE_REDIS_ENABLED = True
```

#### Production
```python
CREATOR_V1_DEBUG = False
CREATOR_LOG_LEVEL = "WARNING"
CREATOR_SECURITY_ENABLED = True
CREATOR_RATE_LIMITING_STRICT = True
CREATOR_HEALTH_ALERTS_ENABLED = True
CREATOR_BACKUP_ENABLED = True
```

## 📊 Monitoring

### Health Monitoring

Creator v1 provides comprehensive health monitoring:

```python
# Check overall system health
health_report = await creator_system.health_check()

# Monitor specific components
health_monitor = creator_system.get_component("health_monitor")
component_health = await health_monitor.health_check_all_plugins()
```

### Metrics & Analytics

```python
# Get system metrics
metrics = creator_system.get_component("advanced_metrics")
system_metrics = metrics.get_metrics_summary()

# Export metrics for external monitoring
report_data = metrics.generate_report("system_performance")
metrics.export_report(report_data, format=ReportFormat.JSON)
```

### Alerting

Set up alerts for critical system events:

```python
# Setup performance alerts
metrics.create_alert("high_latency", "response_time", ">", 5000.0)
metrics.create_alert("high_error_rate", "error_count", ">", 10.0)

# Add notification handlers
async def slack_alert_handler(alert_data):
    # Send to Slack
    pass

metrics.add_alert_handler(slack_alert_handler)
```

## 🔧 Troubleshooting

### Common Issues

#### API Key Issues
```python
# Check provider configuration
provider_manager = creator_system.get_component("provider_manager")
status = await provider_manager.get_provider_status("openai")

if not status.get("available"):
    print("Check your OpenAI API key configuration")
```

#### Performance Issues
```python
# Check cache performance
cache = creator_system.get_component("cache")
cache_stats = cache.get_stats()

if cache_stats["hit_rate"] < 0.8:
    print("Consider increasing cache TTL or size")
```

#### Memory Issues
```python
# Monitor system resources
health_monitor = creator_system.get_component("health_monitor")
system_summary = health_monitor.get_health_report()["system_summary"]

if system_summary["memory_percent"] > 85:
    print("Consider scaling up or optimizing memory usage")
```

### Debug Mode

Enable debug mode for detailed logging:

```python
config.update({
    "CREATOR_V1_DEBUG": True,
    "CREATOR_LOG_LEVEL": "DEBUG",
    "CREATOR_DEBUG_SAVE_REQUESTS": True,
    "CREATOR_DEBUG_TIMING_ENABLED": True
})
```

## 🤝 Contributing

We welcome contributions to Creator v1! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/umbra.git
cd umbra

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest umbra/modules/creator/test_creator_v1.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m "not integration"  # Unit tests only
pytest -m integration        # Integration tests only

# Run with coverage
pytest --cov=umbra.modules.creator
```

## 📄 License

Creator v1 is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 📞 Support

- **Documentation**: [https://docs.creator-v1.com](https://docs.creator-v1.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/umbra/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/umbra/discussions)
- **Email**: support@creator-v1.com

## 🔄 Changelog

### v1.0.0 (Current)
- ✨ Initial release of Creator v1 (CRT4)
- 🚀 Complete content creation pipeline
- 🔒 Enterprise security features
- 📊 Advanced analytics and monitoring
- 🔌 Plugin architecture
- 🌊 Workflow management system

---

**Creator v1 (CRT4)** - Advanced Content Creation for the Modern Enterprise
