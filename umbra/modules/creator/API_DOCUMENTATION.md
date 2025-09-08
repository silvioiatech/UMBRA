# Creator v1 (CRT4) - API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:8080/api`  
**Authentication:** JWT Bearer Token (when security enabled)

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Content Generation](#content-generation)
- [System Management](#system-management)
- [Analytics & Metrics](#analytics--metrics)
- [Workflow Management](#workflow-management)
- [Plugin Management](#plugin-management)
- [Configuration Management](#configuration-management)
- [Webhooks](#webhooks)
- [SDKs and Libraries](#sdks-and-libraries)

## Overview

Creator v1 provides a comprehensive REST API for content generation, system management, and analytics. All endpoints return JSON responses and follow RESTful principles.

### Base Response Format

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": { ... }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Authentication

When security is enabled, API requests require authentication using JWT tokens.

### Login

**POST** `/auth/login`

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user_id": "user_123",
    "permissions": ["read", "write", "admin"]
  }
}
```

### Using Authentication

Include the JWT token in the Authorization header:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Refresh Token

**POST** `/auth/refresh`

```json
{
  "refresh_token": "your_refresh_token"
}
```

## Rate Limiting

API requests are subject to rate limiting when enabled:

- **Default Limit:** 60 requests per minute per user
- **Burst Allowance:** 10 additional requests
- **Global Limit:** 1000 requests per minute

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642248600
```

## Error Handling

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error
- `503` - Service Unavailable

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Invalid input parameters |
| `AUTHENTICATION_ERROR` | Authentication failed |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| `PROVIDER_ERROR` | AI provider error |
| `SYSTEM_ERROR` | Internal system error |
| `CONFIGURATION_ERROR` | Configuration issue |

## Content Generation

### Generate Post

**POST** `/content/generate`

Generate a single social media post.

**Request:**
```json
{
  "action": "generate_post",
  "topic": "The future of artificial intelligence",
  "platform": "linkedin",
  "tone": "professional",
  "audience": "tech professionals",
  "length": "medium",
  "language": "en",
  "include_hashtags": true,
  "include_emojis": false,
  "brand_voice": "default"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "content": "The future of AI is bright! As we advance into 2024, we're seeing unprecedented developments in machine learning that will reshape how businesses operate. From automated decision-making to predictive analytics, AI is becoming an essential tool for competitive advantage. #AI #MachineLearning #Innovation #TechTrends",
    "platform": "linkedin",
    "metadata": {
      "word_count": 45,
      "character_count": 287,
      "hashtag_count": 4,
      "estimated_reach": "high",
      "engagement_prediction": 8.5,
      "generation_time_ms": 1250
    },
    "validation": {
      "valid": true,
      "issues": [],
      "suggestions": [
        "Consider adding a call-to-action"
      ]
    },
    "provider_used": "openai",
    "model_used": "gpt-4",
    "cost_usd": 0.002
  }
}
```

### Generate Content Pack

**POST** `/content/generate`

Generate a complete content pack with multiple elements.

**Request:**
```json
{
  "action": "generate_content_pack",
  "topic": "Sustainable technology innovations",
  "platform": "instagram",
  "tone": "engaging",
  "pack_type": "complete",
  "include_images": true,
  "include_video_script": false,
  "brand_voice": "eco_friendly"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "pack": {
      "caption": "🌱 Revolutionary green tech is changing the world! From solar innovations to carbon capture, sustainability is driving the next wave of technological advancement...",
      "cta": "What sustainable tech excites you most? Share in the comments! 👇",
      "titles": [
        "Green Tech Revolution: 5 Innovations Changing Everything",
        "Sustainable Solutions: Technology for a Better Tomorrow",
        "Eco-Innovation Spotlight: The Future is Green"
      ],
      "hashtags": [
        "#SustainableTech",
        "#GreenInnovation",
        "#CleanEnergy",
        "#EcoTech",
        "#Sustainability"
      ],
      "alt_text": "Infographic showing various sustainable technology innovations including solar panels, wind turbines, and electric vehicles",
      "content_variations": [
        {
          "type": "short_form",
          "content": "🌱 Green tech is revolutionizing our world! #SustainableTech"
        },
        {
          "type": "story",
          "content": "Swipe to see the top 5 sustainable tech innovations of 2024! 👉"
        }
      ],
      "image_prompts": [
        "Modern solar panel installation on a green building with blue sky background",
        "Wind turbines in a field with sunset lighting, representing clean energy"
      ],
      "scheduling_suggestions": {
        "best_times": ["2024-01-15T09:00:00Z", "2024-01-15T17:00:00Z"],
        "optimal_days": ["Tuesday", "Wednesday", "Thursday"]
      }
    },
    "generation_stats": {
      "total_elements": 8,
      "generation_time_ms": 3500,
      "total_cost_usd": 0.015
    }
  }
}
```

### Auto-Orchestration

**POST** `/content/generate`

Let the system automatically determine the best approach for complex content requests.

**Request:**
```json
{
  "action": "auto_orchestrate",
  "input_data": {
    "brief": "Create a social media campaign for our new AI-powered productivity app launch",
    "target_audience": "busy professionals and entrepreneurs",
    "budget": "$5000",
    "timeline": "2 weeks",
    "platforms": ["linkedin", "twitter", "instagram"],
    "goals": ["awareness", "app_downloads", "community_building"]
  },
  "goal": "social_media_campaign",
  "complexity": "high"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "orchestration_plan": {
      "strategy": "multi_platform_campaign",
      "phases": [
        {
          "name": "awareness",
          "duration_days": 5,
          "content_types": ["educational_posts", "teaser_content"],
          "platforms": ["linkedin", "twitter"]
        },
        {
          "name": "launch",
          "duration_days": 3,
          "content_types": ["announcement_posts", "demo_videos"],
          "platforms": ["linkedin", "twitter", "instagram"]
        },
        {
          "name": "engagement",
          "duration_days": 6,
          "content_types": ["user_stories", "tips_and_tricks"],
          "platforms": ["instagram", "linkedin"]
        }
      ]
    },
    "content_calendar": [
      {
        "date": "2024-01-15",
        "platform": "linkedin",
        "content_type": "educational_post",
        "content": "Did you know that professionals waste 2.5 hours daily on repetitive tasks? Our new AI assistant is here to change that! 🚀",
        "scheduled_time": "09:00:00Z"
      }
    ],
    "estimated_results": {
      "reach": 50000,
      "engagement_rate": 0.065,
      "expected_downloads": 1250,
      "confidence_score": 0.82
    }
  }
}
```

### Batch Generation

**POST** `/content/batch`

Generate multiple pieces of content in a single request.

**Request:**
```json
{
  "requests": [
    {
      "id": "req_1",
      "action": "generate_post",
      "topic": "AI in healthcare",
      "platform": "twitter"
    },
    {
      "id": "req_2", 
      "action": "generate_post",
      "topic": "Remote work productivity",
      "platform": "linkedin"
    }
  ],
  "batch_options": {
    "parallel": true,
    "max_retries": 2,
    "timeout_seconds": 300
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "req_1",
        "success": true,
        "content": "AI is revolutionizing healthcare diagnosis and treatment...",
        "generation_time_ms": 1100
      },
      {
        "id": "req_2",
        "success": true,
        "content": "Remote work productivity has become a critical skill...",
        "generation_time_ms": 1350
      }
    ],
    "batch_stats": {
      "total_requests": 2,
      "successful": 2,
      "failed": 0,
      "total_time_ms": 1400,
      "average_time_ms": 1225
    }
  }
}
```

## System Management

### System Status

**GET** `/system/status`

Get comprehensive system status information.

**Response:**
```json
{
  "success": true,
  "data": {
    "version": "1.0.0",
    "enabled": true,
    "health_status": "healthy",
    "uptime_seconds": 86400,
    "components_status": {
      "analytics": true,
      "cache": true,
      "security": true,
      "health_monitor": true,
      "provider_manager": true
    },
    "performance_metrics": {
      "requests_per_minute": 45,
      "average_response_time_ms": 850,
      "cache_hit_rate": 0.75,
      "memory_usage_mb": 512,
      "cpu_usage_percent": 25.5
    },
    "provider_status": {
      "openai": {
        "available": true,
        "response_time_ms": 1200,
        "rate_limit_remaining": 950
      },
      "anthropic": {
        "available": false,
        "error": "API key not configured"
      }
    }
  }
}
```

### Health Check

**GET** `/system/health`

Perform comprehensive health check.

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_health": {
      "status": "healthy",
      "message": "All systems operational",
      "critical_issues": [],
      "warning_issues": [
        {
          "check": "disk_space",
          "message": "Disk space at 80% capacity",
          "severity": "warning"
        }
      ]
    },
    "check_details": {
      "database_connectivity": {
        "status": "ok",
        "response_time_ms": 45
      },
      "cache_connectivity": {
        "status": "ok",
        "response_time_ms": 12
      },
      "ai_providers": {
        "status": "ok",
        "providers_available": 2,
        "providers_total": 3
      }
    },
    "system_summary": {
      "cpu_percent": 25.5,
      "memory_percent": 65.2,
      "disk_percent": 80.1,
      "uptime_hours": 24.5
    }
  }
}
```

### Component Information

**GET** `/system/components`

Get detailed information about system components.

**Response:**
```json
{
  "success": true,
  "data": {
    "analytics": {
      "available": true,
      "version": "1.0.0",
      "status": "active",
      "stats": {
        "total_events": 1250,
        "events_today": 85,
        "retention_days": 30
      }
    },
    "cache": {
      "available": true,
      "type": "redis",
      "stats": {
        "hit_rate": 0.75,
        "memory_usage_mb": 128,
        "total_keys": 450
      }
    }
  }
}
```

## Analytics & Metrics

### Get Analytics

**GET** `/analytics/summary`

Get analytics summary for a specified time period.

**Query Parameters:**
- `days` (optional): Number of days to include (default: 7)
- `include_details` (optional): Include detailed breakdown (default: false)

**Response:**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-01-08T00:00:00Z",
      "end_date": "2024-01-15T00:00:00Z",
      "days": 7
    },
    "summary": {
      "total_requests": 1250,
      "successful_requests": 1195,
      "failed_requests": 55,
      "success_rate": 0.956,
      "average_response_time_ms": 875,
      "total_cost_usd": 15.75,
      "total_tokens": 125000
    },
    "by_action": {
      "generate_post": {
        "count": 800,
        "success_rate": 0.965,
        "avg_cost_usd": 0.008
      },
      "generate_content_pack": {
        "count": 300,
        "success_rate": 0.940,
        "avg_cost_usd": 0.025
      }
    },
    "by_platform": {
      "linkedin": 450,
      "twitter": 380,
      "instagram": 285,
      "facebook": 135
    },
    "trends": {
      "request_trend": "increasing",
      "cost_trend": "stable",
      "quality_trend": "improving"
    }
  }
}
```

### Export Analytics

**POST** `/analytics/export`

Export analytics data in various formats.

**Request:**
```json
{
  "format": "json",
  "date_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-15T23:59:59Z"
  },
  "include_details": true,
  "metrics": ["requests", "costs", "performance", "errors"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "export_id": "exp_123456",
    "download_url": "/analytics/exports/exp_123456.json",
    "expires_at": "2024-01-16T00:00:00Z",
    "file_size_bytes": 2048576,
    "record_count": 15000
  }
}
```

### Real-time Metrics

**GET** `/metrics/realtime`

Get real-time system metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "timestamp": "2024-01-15T10:30:00Z",
    "system": {
      "cpu_percent": 25.5,
      "memory_percent": 65.2,
      "disk_io_rate": 1250000,
      "network_io_rate": 890000
    },
    "application": {
      "active_requests": 12,
      "requests_per_minute": 45,
      "average_response_time_ms": 850,
      "error_rate_percent": 0.5
    },
    "cache": {
      "hit_rate": 0.75,
      "operations_per_second": 125,
      "memory_usage_percent": 60
    },
    "ai_providers": {
      "openai": {
        "requests_per_minute": 25,
        "rate_limit_remaining": 950,
        "average_response_time_ms": 1200
      }
    }
  }
}
```

## Workflow Management

### Create Workflow

**POST** `/workflows`

Create a new content generation workflow.

**Request:**
```json
{
  "name": "Blog Post to Social Media Pipeline",
  "description": "Convert blog posts into multi-platform social media content",
  "steps": [
    {
      "id": "extract_key_points",
      "name": "Extract Key Points",
      "action": "extract_key_points",
      "params": {
        "content": "${input.blog_content}",
        "max_points": 5
      }
    },
    {
      "id": "generate_twitter_thread",
      "name": "Generate Twitter Thread",
      "action": "generate_twitter_thread",
      "params": {
        "key_points": "${extract_key_points.result}",
        "tone": "engaging"
      },
      "dependencies": ["extract_key_points"]
    },
    {
      "id": "generate_linkedin_post",
      "name": "Generate LinkedIn Post",
      "action": "generate_post",
      "params": {
        "topic": "${extract_key_points.summary}",
        "platform": "linkedin",
        "tone": "professional"
      },
      "dependencies": ["extract_key_points"]
    }
  ],
  "triggers": ["manual", "webhook"],
  "schedule": null
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "workflow_id": "wf_123456789",
    "name": "Blog Post to Social Media Pipeline",
    "status": "created",
    "created_at": "2024-01-15T10:30:00Z",
    "step_count": 3,
    "estimated_duration_minutes": 5
  }
}
```

### Execute Workflow

**POST** `/workflows/{workflow_id}/execute`

Execute a workflow with input data.

**Request:**
```json
{
  "input_data": {
    "blog_content": "Artificial Intelligence is transforming the business landscape in unprecedented ways..."
  },
  "execution_options": {
    "timeout_minutes": 10,
    "retry_failed_steps": true,
    "notify_on_completion": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_987654321",
    "workflow_id": "wf_123456789", 
    "status": "running",
    "started_at": "2024-01-15T10:30:00Z",
    "estimated_completion": "2024-01-15T10:35:00Z",
    "progress_url": "/workflows/executions/exec_987654321/progress"
  }
}
```

### Get Workflow Status

**GET** `/workflows/{workflow_id}`

Get workflow information and status.

**Response:**
```json
{
  "success": true,
  "data": {
    "workflow_id": "wf_123456789",
    "name": "Blog Post to Social Media Pipeline", 
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "last_executed": "2024-01-15T14:20:00Z",
    "execution_count": 25,
    "success_rate": 0.96,
    "average_duration_minutes": 4.2,
    "steps": [
      {
        "id": "extract_key_points",
        "name": "Extract Key Points",
        "status": "configured",
        "average_duration_ms": 1200
      }
    ]
  }
}
```

### List Workflows

**GET** `/workflows`

List all workflows with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by status (active, paused, archived)
- `limit` (optional): Number of results (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "workflows": [
      {
        "workflow_id": "wf_123456789",
        "name": "Blog Post to Social Media Pipeline",
        "status": "active",
        "step_count": 3,
        "last_executed": "2024-01-15T14:20:00Z"
      }
    ],
    "pagination": {
      "total": 1,
      "limit": 20,
      "offset": 0,
      "has_more": false
    }
  }
}
```

## Plugin Management

### List Plugins

**GET** `/plugins`

Get information about all available plugins.

**Response:**
```json
{
  "success": true,
  "data": {
    "plugins": [
      {
        "name": "content_enhancer",
        "version": "1.2.0",
        "status": "active",
        "type": "content_processor",
        "description": "Enhances content with advanced NLP techniques",
        "capabilities": ["text_enhancement", "sentiment_analysis"],
        "author": "Creator Team",
        "license": "MIT"
      },
      {
        "name": "social_media_optimizer",
        "version": "1.0.5",
        "status": "inactive",
        "type": "platform_integration",
        "description": "Optimizes content for specific social media platforms"
      }
    ],
    "total_plugins": 2,
    "active_plugins": 1
  }
}
```

### Activate Plugin

**POST** `/plugins/{plugin_name}/activate`

Activate a plugin.

**Response:**
```json
{
  "success": true,
  "data": {
    "plugin_name": "social_media_optimizer",
    "status": "active",
    "activated_at": "2024-01-15T10:30:00Z",
    "capabilities_added": ["platform_optimization", "hashtag_suggestion"]
  }
}
```

### Plugin Configuration

**GET** `/plugins/{plugin_name}/config`

Get plugin configuration.

**Response:**
```json
{
  "success": true,
  "data": {
    "plugin_name": "content_enhancer",
    "configuration": {
      "max_enhancement_level": 5,
      "include_sentiment_analysis": true,
      "language_models": ["en", "es", "fr"],
      "custom_rules": []
    },
    "config_schema": {
      "type": "object",
      "properties": {
        "max_enhancement_level": {
          "type": "integer",
          "minimum": 1,
          "maximum": 10
        }
      }
    }
  }
}
```

**PUT** `/plugins/{plugin_name}/config`

Update plugin configuration.

**Request:**
```json
{
  "configuration": {
    "max_enhancement_level": 7,
    "include_sentiment_analysis": false
  }
}
```

## Configuration Management

### Get Configuration

**GET** `/config`

Get current system configuration (non-sensitive values only).

**Response:**
```json
{
  "success": true,
  "data": {
    "system": {
      "CREATOR_V1_ENABLED": true,
      "CREATOR_MAX_OUTPUT_TOKENS": 2000,
      "CREATOR_DEFAULT_TONE": "professional"
    },
    "features": {
      "CREATOR_CACHE_ENABLED": true,
      "CREATOR_ANALYTICS_ENABLED": true,
      "CREATOR_BATCHING_ENABLED": true
    },
    "providers": {
      "CREATOR_OPENAI_ENABLED": true,
      "CREATOR_ANTHROPIC_ENABLED": false
    },
    "last_updated": "2024-01-15T10:30:00Z"
  }
}
```

### Update Configuration

**PUT** `/config`

Update system configuration.

**Request:**
```json
{
  "updates": {
    "CREATOR_MAX_OUTPUT_TOKENS": 3000,
    "CREATOR_DEFAULT_TONE": "casual"
  },
  "reason": "Increased token limit for longer content generation"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "updated_keys": [
      "CREATOR_MAX_OUTPUT_TOKENS",
      "CREATOR_DEFAULT_TONE"
    ],
    "applied_at": "2024-01-15T10:30:00Z",
    "updated_by": "api_user",
    "requires_restart": false
  }
}
```

## Webhooks

### Register Webhook

**POST** `/webhooks`

Register a webhook for specific events.

**Request:**
```json
{
  "url": "https://your-app.com/webhooks/creator",
  "events": [
    "content.generated",
    "workflow.completed",
    "system.health_alert"
  ],
  "secret": "webhook_secret_for_verification",
  "active": true,
  "description": "Main application webhook"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "webhook_id": "wh_123456789",
    "url": "https://your-app.com/webhooks/creator",
    "events": ["content.generated", "workflow.completed", "system.health_alert"],
    "created_at": "2024-01-15T10:30:00Z",
    "status": "active"
  }
}
```

### Webhook Events

#### Content Generated Event

```json
{
  "event": "content.generated",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "request_id": "req_123456",
    "action": "generate_post",
    "platform": "linkedin",
    "success": true,
    "content_preview": "The future of AI is bright...",
    "generation_time_ms": 1250,
    "cost_usd": 0.002,
    "user_id": "user_123"
  }
}
```

#### Workflow Completed Event

```json
{
  "event": "workflow.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "workflow_id": "wf_123456789",
    "execution_id": "exec_987654321",
    "status": "completed",
    "duration_seconds": 245,
    "steps_completed": 3,
    "steps_failed": 0,
    "results": {
      "twitter_thread": "Generated successfully",
      "linkedin_post": "Generated successfully"
    }
  }
}
```

#### System Health Alert Event

```json
{
  "event": "system.health_alert",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "alert_type": "warning",
    "component": "disk_space",
    "message": "Disk space usage at 85%",
    "severity": "medium",
    "requires_action": true,
    "recommendations": [
      "Clear old log files",
      "Archive old analytics data"
    ]
  }
}
```

## SDKs and Libraries

### Python SDK

```python
from creator_v1_sdk import CreatorClient

# Initialize client
client = CreatorClient(
    base_url="http://localhost:8080/api",
    api_key="your_api_key"  # if security enabled
)

# Generate content
result = client.content.generate_post(
    topic="AI innovations",
    platform="linkedin",
    tone="professional"
)

print(result.content)
```

### JavaScript SDK

```javascript
import { CreatorClient } from 'creator-v1-sdk';

const client = new CreatorClient({
  baseUrl: 'http://localhost:8080/api',
  apiKey: 'your_api_key'  // if security enabled
});

// Generate content
const result = await client.content.generatePost({
  topic: 'AI innovations',
  platform: 'linkedin',
  tone: 'professional'
});

console.log(result.content);
```

### cURL Examples

#### Generate Content

```bash
curl -X POST http://localhost:8080/api/content/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "action": "generate_post",
    "topic": "Sustainable technology",
    "platform": "twitter",
    "tone": "engaging"
  }'
```

#### Get System Status

```bash
curl -X GET http://localhost:8080/api/system/status \
  -H "Authorization: Bearer your_jwt_token"
```

#### Create Workflow

```bash
curl -X POST http://localhost:8080/api/workflows \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "name": "Content Pipeline",
    "steps": [
      {
        "id": "generate",
        "action": "generate_post",
        "params": {"topic": "${input.topic}"}
      }
    ]
  }'
```

## Response Time Guidelines

| Endpoint Category | Expected Response Time |
|------------------|----------------------|
| Content Generation | 1-5 seconds |
| System Status | < 100ms |
| Analytics | < 500ms |
| Configuration | < 200ms |
| Workflow Management | < 1 second |
| Plugin Operations | < 500ms |

## Best Practices

### Request Optimization

1. **Use Batch Requests**: Combine multiple content generation requests into a single batch call
2. **Cache Results**: Cache frequently requested content to reduce API calls
3. **Implement Retry Logic**: Use exponential backoff for failed requests
4. **Monitor Rate Limits**: Track rate limit headers and adjust request frequency

### Error Handling

1. **Always Check Status**: Verify the `success` field in responses
2. **Handle Rate Limits**: Implement proper backoff when receiving 429 responses
3. **Log Request IDs**: Use the `request_id` field for debugging and support
4. **Validate Inputs**: Validate request data before sending to the API

### Security

1. **Secure API Keys**: Store API keys securely and rotate them regularly
2. **Use HTTPS**: Always use HTTPS in production environments
3. **Validate Webhooks**: Verify webhook signatures using the provided secret
4. **Implement Timeouts**: Set appropriate timeouts for API requests

---

For more information and updates, visit the [Creator v1 Documentation](https://docs.creator-v1.com) or contact our [Support Team](mailto:support@creator-v1.com).
