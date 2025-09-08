# Contributing to Creator v1 (CRT4)

Thank you for your interest in contributing to Creator v1! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Plugin Development](#plugin-development)
- [Performance Guidelines](#performance-guidelines)
- [Security Guidelines](#security-guidelines)
- [Release Process](#release-process)

## 🤝 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement

Instances of unacceptable behavior may be reported by contacting the project team at conduct@creator-v1.com. All complaints will be reviewed and investigated and will result in a response that is deemed necessary and appropriate to the circumstances.

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.8+ installed
- Git installed and configured
- Docker and Docker Compose (for full development environment)
- Basic understanding of async Python programming
- Familiarity with FastAPI, SQLAlchemy, and Redis

### Areas for Contribution

We welcome contributions in:

- **Core Features**: Content generation improvements, new AI provider integrations
- **Infrastructure**: Performance optimizations, monitoring enhancements
- **Documentation**: Tutorials, API documentation, examples
- **Testing**: Unit tests, integration tests, performance tests
- **Plugins**: New functionality through the plugin system
- **Security**: Security audits, vulnerability fixes
- **DevOps**: CI/CD improvements, deployment automation

## 🛠 Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/umbra.git
cd umbra/modules/creator

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/umbra.git
```

### 2. Development Environment

#### Option A: Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .

# Set up pre-commit hooks
pre-commit install
```

#### Option B: Docker Development

```bash
# Build development container
docker-compose -f docker-compose.dev.yml build

# Start development services
docker-compose -f docker-compose.dev.yml up -d

# Enter development container
docker-compose -f docker-compose.dev.yml exec creator-dev bash
```

### 3. Environment Configuration

Create a development configuration file:

```bash
# Copy example config
cp config/creator.example.yaml config/creator.dev.yaml

# Edit with your settings
editor config/creator.dev.yaml
```

Required environment variables:
```bash
export CREATOR_V1_ENABLED=true
export CREATOR_V1_DEBUG=true
export CREATOR_OPENAI_API_KEY=your_dev_key
export CREATOR_DATABASE_URL=postgresql://creator:password@localhost/creator_dev
export CREATOR_CACHE_REDIS_HOST=localhost
```

### 4. Database Setup

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run database migrations
python -m umbra.modules.creator.cli db migrate

# Load sample data
python -m umbra.modules.creator.cli db seed
```

### 5. Verify Setup

```bash
# Run tests
pytest

# Start development server
python -m umbra.modules.creator.dashboard --debug --port 8080

# Check system health
curl http://localhost:8080/api/health
```

## 🔄 Contributing Process

### 1. Create an Issue

Before starting work, create an issue describing:
- The problem you're solving
- Your proposed solution
- Any breaking changes
- Testing approach

### 2. Create Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b bugfix/issue-description
```

### 3. Development Workflow

```bash
# Make your changes
# ...

# Run tests frequently
pytest tests/test_your_changes.py

# Check code quality
black .
isort .
flake8 .
mypy .

# Run security checks
bandit -r .
safety check
```

### 4. Commit Guidelines

Follow conventional commits format:

```bash
# Format: type(scope): description
git commit -m "feat(analytics): add real-time metrics dashboard"
git commit -m "fix(security): resolve JWT token validation issue"
git commit -m "docs(api): update content generation examples"
git commit -m "test(workflow): add integration tests for batch processing"
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `security`: Security-related changes

### 5. Testing Requirements

All contributions must include appropriate tests:

```bash
# Unit tests for new functionality
# Integration tests for component interactions
# Performance tests for critical paths
# Security tests for sensitive features

# Run full test suite
pytest --cov=umbra.modules.creator --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m performance
pytest -m security
```

### 6. Submit Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create pull request on GitHub with:
# - Clear title and description
# - Link to related issues
# - Test results
# - Breaking change notes
# - Documentation updates
```

## 📝 Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

```python
# Line length: 88 characters (Black default)
# Use type hints for all functions
# Use dataclasses for simple data structures
# Use async/await for I/O operations

# Example function
async def generate_content(
    topic: str,
    platform: Optional[str] = None,
    tone: str = "professional"
) -> ContentResult:
    """
    Generate content for specified topic and platform.
    
    Args:
        topic: Content topic
        platform: Target platform (optional)
        tone: Content tone
        
    Returns:
        Generated content result
        
    Raises:
        ContentGenerationError: If generation fails
    """
    # Implementation
    pass
```

### Code Organization

```python
# File structure for new modules
umbra/modules/creator/
├── new_feature/
│   ├── __init__.py          # Public API
│   ├── core.py              # Core functionality  
│   ├── models.py            # Data models
│   ├── service.py           # Service layer
│   ├── errors.py            # Custom exceptions
│   └── tests/
│       ├── test_core.py
│       ├── test_service.py
│       └── test_integration.py
```

### Import Organization

```python
# Standard library imports
import asyncio
import logging
from typing import Dict, List, Optional

# Third-party imports
import aiohttp
from fastapi import FastAPI
from pydantic import BaseModel

# Local imports
from umbra.core.config import UmbraConfig
from umbra.modules.creator.errors import CreatorError
from ..models import ContentRequest
```

### Error Handling

```python
# Custom exceptions inherit from CreatorError
class ValidationError(CreatorError):
    """Raised when input validation fails"""
    pass

# Proper error handling with context
async def process_request(request: ContentRequest) -> ContentResult:
    try:
        result = await generate_content(request)
        return result
    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise CreatorError(f"Processing failed: {e}") from e
```

### Logging Standards

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed debugging information")
logger.info("General information about program execution")
logger.warning("Something unexpected happened")
logger.error("A serious problem occurred")
logger.critical("A very serious problem occurred")

# Include context in log messages
logger.info(
    "Content generated successfully",
    extra={
        "topic": topic,
        "platform": platform,
        "generation_time_ms": duration,
        "user_id": user_id
    }
)
```

## 🧪 Testing Guidelines

### Test Structure

```python
# tests/test_content_generation.py
import pytest
from unittest.mock import AsyncMock, Mock

from umbra.modules.creator.service import CreatorService
from umbra.modules.creator.errors import ValidationError

class TestContentGeneration:
    """Test content generation functionality"""
    
    @pytest.fixture
    async def creator_service(self):
        """Create test creator service"""
        config = Mock()
        ai_agent = AsyncMock()
        service = CreatorService(ai_agent, config)
        return service
    
    @pytest.mark.asyncio
    async def test_generate_post_success(self, creator_service):
        """Test successful post generation"""
        # Arrange
        request = {
            "action": "generate_post",
            "topic": "AI innovations",
            "platform": "linkedin"
        }
        
        # Act
        result = await creator_service.generate_post(**request)
        
        # Assert
        assert result["success"] is True
        assert "content" in result
        assert len(result["content"]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_post_validation_error(self, creator_service):
        """Test post generation with invalid input"""
        # Arrange
        request = {
            "action": "generate_post",
            "topic": "",  # Invalid empty topic
            "platform": "linkedin"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await creator_service.generate_post(**request)
```

### Test Categories

Mark tests with appropriate categories:

```python
# Unit tests (fast, no external dependencies)
@pytest.mark.unit
async def test_content_validation():
    pass

# Integration tests (test component interactions)
@pytest.mark.integration
async def test_workflow_execution():
    pass

# Performance tests (test speed and resource usage)
@pytest.mark.performance
async def test_batch_generation_performance():
    pass

# Security tests (test security features)
@pytest.mark.security
async def test_authentication_security():
    pass
```

### Test Data

```python
# Use fixtures for test data
@pytest.fixture
def sample_content_request():
    return {
        "action": "generate_post",
        "topic": "Test topic",
        "platform": "twitter",
        "tone": "casual"
    }

# Use factories for complex objects
class ContentRequestFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "action": "generate_post",
            "topic": "Default topic",
            "platform": "linkedin",
            "tone": "professional"
        }
        defaults.update(kwargs)
        return defaults
```

## 📚 Documentation

### Code Documentation

```python
class CreatorService:
    """
    Main service for content creation and orchestration.
    
    This service coordinates between AI providers, content validation,
    and various output formats to generate high-quality content.
    
    Attributes:
        ai_agent: AI agent for content generation
        config: System configuration
        
    Example:
        >>> service = CreatorService(ai_agent, config)
        >>> result = await service.generate_post("AI trends", "linkedin")
        >>> print(result["content"])
    """
    
    async def generate_post(
        self,
        topic: str,
        platform: Optional[str] = None,
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Generate a social media post for the specified topic.
        
        Args:
            topic: The main topic or subject for the post
            platform: Target social media platform (twitter, linkedin, etc.)
            tone: Content tone (professional, casual, friendly, creative)
            
        Returns:
            Dictionary containing:
                - content: Generated post content
                - metadata: Generation metadata (word count, etc.)
                - validation: Content validation results
                
        Raises:
            ValidationError: If input parameters are invalid
            GenerationError: If content generation fails
            
        Example:
            >>> result = await service.generate_post(
            ...     "The future of AI",
            ...     platform="linkedin",
            ...     tone="professional"
            ... )
            >>> print(result["content"])
        """
```

### API Documentation

Use OpenAPI/Swagger annotations:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

class ContentRequest(BaseModel):
    """Content generation request model"""
    action: str = Field(..., description="Type of content to generate")
    topic: str = Field(..., description="Content topic or subject")
    platform: Optional[str] = Field(None, description="Target platform")
    tone: str = Field("professional", description="Content tone")

@app.post("/api/content/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest):
    """
    Generate content based on the provided parameters.
    
    This endpoint generates various types of content including social media posts,
    blog articles, and marketing copy. The content is optimized for the specified
    platform and tone.
    
    - **action**: Type of content (generate_post, generate_content_pack, etc.)
    - **topic**: Main subject or topic for the content
    - **platform**: Target platform (twitter, linkedin, instagram, facebook)
    - **tone**: Content tone (professional, casual, friendly, creative)
    
    Returns generated content with metadata and validation results.
    """
```

### Tutorial Documentation

Create comprehensive tutorials:

```markdown
# Tutorial: Creating Your First Content Pack

## Overview
This tutorial will guide you through creating a complete content pack
using Creator v1. You'll learn how to generate multiple content pieces
optimized for different platforms.

## Prerequisites
- Creator v1 system running
- Valid API key for AI provider
- Basic understanding of social media platforms

## Step 1: Basic Setup
[Detailed setup instructions...]

## Step 2: Generate Content Pack
[Code examples and explanations...]

## Step 3: Customize and Optimize
[Advanced configuration options...]
```

## 🔌 Plugin Development

### Plugin Structure

```python
# plugins/my_plugin.py
from umbra.modules.creator.plugins import BasePlugin, plugin_info

@plugin_info(
    name="content_enhancer",
    version="1.0.0",
    description="Enhances content with advanced NLP techniques",
    author="Your Name",
    dependencies=["spacy>=3.0.0"]
)
class ContentEnhancerPlugin(BasePlugin):
    """Plugin for enhancing content quality"""
    
    async def initialize(self):
        """Initialize plugin resources"""
        # Load models, connect to services, etc.
        pass
    
    async def process_content(self, content: str, **kwargs) -> str:
        """Main plugin functionality"""
        # Enhance the content
        enhanced_content = self._enhance_text(content)
        return enhanced_content
    
    def _enhance_text(self, text: str) -> str:
        """Private method for text enhancement"""
        # Implementation details
        return text
    
    async def cleanup(self):
        """Cleanup plugin resources"""
        pass
```

### Plugin Testing

```python
# tests/test_my_plugin.py
import pytest
from plugins.my_plugin import ContentEnhancerPlugin

@pytest.mark.asyncio
async def test_plugin_initialization():
    """Test plugin initializes correctly"""
    plugin = ContentEnhancerPlugin()
    await plugin.initialize()
    
    assert plugin.is_initialized()

@pytest.mark.asyncio
async def test_content_enhancement():
    """Test content enhancement functionality"""
    plugin = ContentEnhancerPlugin()
    await plugin.initialize()
    
    original_content = "This is basic content."
    enhanced_content = await plugin.process_content(original_content)
    
    assert len(enhanced_content) > len(original_content)
    assert enhanced_content != original_content
```

## ⚡ Performance Guidelines

### Async Programming

```python
# Use async/await for I/O operations
async def fetch_data_from_api(url: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Use asyncio.gather for concurrent operations
async def fetch_multiple_sources(urls: List[str]) -> List[Dict[str, Any]]:
    tasks = [fetch_data_from_api(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
```

### Caching

```python
# Use appropriate caching strategies
from functools import lru_cache
from umbra.modules.creator.cache import cache_manager

@lru_cache(maxsize=1000)
def expensive_computation(data: str) -> str:
    """Cache expensive computations"""
    # Expensive operation
    return result

@cache_manager.cached(ttl=3600, tags=["content"])
async def generate_content_cached(topic: str) -> str:
    """Cache content generation results"""
    # Generation logic
    return content
```

### Database Operations

```python
# Use bulk operations when possible
async def save_multiple_records(records: List[Dict[str, Any]]):
    """Bulk insert records for better performance"""
    async with database.transaction():
        await database.execute_many(INSERT_QUERY, records)

# Use database indexes and proper queries
async def get_user_content(user_id: str, limit: int = 10):
    """Optimized query with proper indexing"""
    query = """
    SELECT * FROM content 
    WHERE user_id = $1 
    ORDER BY created_at DESC 
    LIMIT $2
    """
    return await database.fetch_all(query, user_id, limit)
```

## 🔒 Security Guidelines

### Input Validation

```python
from pydantic import BaseModel, validator
import bleach

class ContentRequest(BaseModel):
    """Secure content request model"""
    topic: str
    platform: Optional[str] = None
    
    @validator('topic')
    def validate_topic(cls, v):
        """Validate and sanitize topic"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Topic cannot be empty")
        
        # Sanitize HTML and potentially malicious content
        sanitized = bleach.clean(v, tags=[], strip=True)
        
        if len(sanitized) > 1000:
            raise ValueError("Topic too long")
            
        return sanitized
    
    @validator('platform')
    def validate_platform(cls, v):
        """Validate platform parameter"""
        if v is not None:
            allowed_platforms = ["twitter", "linkedin", "instagram", "facebook"]
            if v not in allowed_platforms:
                raise ValueError(f"Platform must be one of: {allowed_platforms}")
        return v
```

### Authentication and Authorization

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)) -> str:
    """Verify JWT token and return user ID"""
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return user_id
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@app.post("/api/content/generate")
async def generate_content(
    request: ContentRequest,
    user_id: str = Depends(verify_token)
):
    """Protected endpoint requiring authentication"""
    # Implementation
    pass
```

### Data Protection

```python
import secrets
from cryptography.fernet import Fernet

class DataEncryption:
    """Secure data encryption utilities"""
    
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()

# Generate secure secrets
def generate_secure_key() -> str:
    """Generate cryptographically secure key"""
    return secrets.token_urlsafe(32)
```

## 🚀 Release Process

### Version Management

We use semantic versioning (SemVer):

- **MAJOR** version: Incompatible API changes
- **MINOR** version: New functionality (backward compatible)
- **PATCH** version: Bug fixes (backward compatible)

### Release Checklist

1. **Code Review**
   - [ ] All tests passing
   - [ ] Code coverage > 80%
   - [ ] Security scan passed
   - [ ] Performance benchmarks acceptable

2. **Documentation**
   - [ ] API documentation updated
   - [ ] Changelog updated
   - [ ] Migration guide (if needed)
   - [ ] Tutorial updates

3. **Testing**
   - [ ] Unit tests complete
   - [ ] Integration tests passed
   - [ ] Performance tests acceptable
   - [ ] Security tests passed
   - [ ] Manual testing on staging

4. **Deployment**
   - [ ] Staging deployment successful
   - [ ] Production deployment plan ready
   - [ ] Rollback plan prepared
   - [ ] Monitoring alerts configured

### Creating a Release

```bash
# Update version
echo "1.2.0" > VERSION

# Update changelog
editor CHANGELOG.md

# Commit changes
git add .
git commit -m "chore: prepare release v1.2.0"

# Create and push tag
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0

# GitHub Actions will automatically:
# - Run full test suite
# - Build and publish Docker images
# - Deploy to staging and production
# - Create GitHub release with notes
```

## 📞 Getting Help

### Community Resources

- **GitHub Discussions**: Ask questions and share ideas
- **Discord Server**: Real-time chat with the community
- **Documentation**: Comprehensive guides and tutorials
- **Stack Overflow**: Use the `creator-v1` tag

### Reporting Issues

When reporting bugs:

1. Search existing issues first
2. Use the bug report template
3. Include minimal reproduction case
4. Provide system information
5. Attach relevant logs

### Feature Requests

When requesting features:

1. Check if feature already exists
2. Use the feature request template
3. Explain the use case clearly
4. Consider implementation complexity
5. Be open to alternative solutions

## 🙏 Recognition

Contributors will be recognized:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Featured in community highlights
- Invited to contributor events

## 📄 License

By contributing to Creator v1, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Creator v1! Together, we're building the future of content creation. 🚀
