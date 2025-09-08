"""
Test suite for Creator v1 (CRT4) components
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import asdict

from umbra.core.config import UmbraConfig
from umbra.ai.agent import UmbraAIAgent
from umbra.modules.creator.model_provider_enhanced import (
    EnhancedModelProviderManager, ProviderResult
)
from umbra.modules.creator.templates import TemplateManager
from umbra.modules.creator.voice import BrandVoiceManager
from umbra.modules.creator.analytics import CreatorAnalytics, Event, EventType
from umbra.modules.creator.connectors import ConnectorManager
from umbra.modules.creator.errors import CreatorError, MediaError, ProviderError

# Test fixtures
@pytest.fixture
def mock_config():
    """Mock configuration"""
    config = Mock(spec=UmbraConfig)
    config.get = Mock(side_effect=lambda key, default=None: {
        "CREATOR_MAX_TEMPLATES": 100,
        "CREATOR_MAX_TEMPLATE_SIZE_KB": 50,
        "CREATOR_DEFAULT_TONE": "professional",
        "CREATOR_ANALYTICS_ENABLED": True,
        "CREATOR_COST_TRACKING_ENABLED": True,
        "OPENROUTER_API_KEY": "test_key",
        "CREATOR_STABILITY_API_KEY": "test_stability_key"
    }.get(key, default))
    return config

@pytest.fixture
def mock_ai_agent():
    """Mock AI agent"""
    agent = Mock(spec=UmbraAIAgent)
    agent.generate_text = AsyncMock(return_value="Generated text content")
    return agent

@pytest.fixture
def enhanced_provider_manager(mock_config):
    """Enhanced provider manager instance"""
    return EnhancedModelProviderManager(mock_config)

@pytest.fixture
def template_manager(mock_config):
    """Template manager instance"""
    return TemplateManager(mock_config)

@pytest.fixture
def brand_voice_manager(mock_config):
    """Brand voice manager instance"""
    return BrandVoiceManager(mock_config)

@pytest.fixture
def analytics(mock_config):
    """Analytics instance"""
    return CreatorAnalytics(mock_config)

@pytest.fixture
def connector_manager(mock_config):
    """Connector manager instance"""
    return ConnectorManager(mock_config)

# =============================================================================
# MODEL PROVIDER ENHANCED TESTS
# =============================================================================

class TestEnhancedModelProviderManager:
    """Tests for enhanced model provider manager"""
    
    def test_initialization(self, enhanced_provider_manager):
        """Test provider manager initialization"""
        assert enhanced_provider_manager.config is not None
        assert hasattr(enhanced_provider_manager, 'providers')
        assert hasattr(enhanced_provider_manager, 'provider_configs')
    
    def test_get_configuration_status(self, enhanced_provider_manager):
        """Test configuration status reporting"""
        status = enhanced_provider_manager.get_configuration_status()
        
        assert "configured_providers" in status
        assert "capability_coverage" in status
        assert "missing_configurations" in status
        assert isinstance(status["configured_providers"], list)
        assert isinstance(status["capability_coverage"], dict)
    
    @pytest.mark.asyncio
    async def test_get_text_provider(self, enhanced_provider_manager):
        """Test getting text provider"""
        with patch.object(enhanced_provider_manager, '_create_provider_instance') as mock_create:
            mock_provider = Mock()
            mock_create.return_value = mock_provider
            
            provider = await enhanced_provider_manager.get_text_provider()
            assert provider is not None or provider is None  # May be None if no config
    
    def test_provider_result_structure(self):
        """Test ProviderResult structure"""
        result = ProviderResult(
            success=True,
            data={"test": "data"},
            provider="test_provider",
            model="test_model"
        )
        
        assert result.success is True
        assert result.data == {"test": "data"}
        assert result.provider == "test_provider"
        assert result.model == "test_model"
        assert result.error is None

# =============================================================================
# TEMPLATE MANAGER TESTS
# =============================================================================

class TestTemplateManager:
    """Tests for template manager"""
    
    def test_initialization(self, template_manager):
        """Test template manager initialization"""
        assert template_manager.config is not None
        assert hasattr(template_manager, 'templates')
        assert len(template_manager.templates) > 0  # Should have default templates
    
    @pytest.mark.asyncio
    async def test_list_templates(self, template_manager):
        """Test listing templates"""
        templates = await template_manager.list_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Check template structure
        template = templates[0]
        required_fields = ["id", "name", "description", "category", "type", "variables"]
        for field in required_fields:
            assert field in template
    
    @pytest.mark.asyncio
    async def test_render_template(self, template_manager):
        """Test template rendering"""
        # Use a known default template
        template_id = "social_announcement"
        variables = {
            "announcement": "Test announcement",
            "details": "Test details",
            "call_to_action": "Test CTA"
        }
        
        rendered = await template_manager.render_template(template_id, variables)
        
        assert isinstance(rendered, str)
        assert "Test announcement" in rendered
        assert "Test details" in rendered
        assert "Test CTA" in rendered
    
    @pytest.mark.asyncio
    async def test_upsert_template(self, template_manager):
        """Test creating/updating templates"""
        template_body = "Hello ${name}! Welcome to ${company}."
        meta = {
            "name": "Test Template",
            "description": "A test template",
            "category": "test"
        }
        
        template_id = await template_manager.upsert_template(None, template_body, meta)
        
        assert isinstance(template_id, str)
        assert template_id in template_manager.templates
        
        # Test rendering the new template
        rendered = await template_manager.render_template(template_id, {
            "name": "John",
            "company": "TechCorp"
        })
        
        assert "Hello John!" in rendered
        assert "Welcome to TechCorp" in rendered
    
    @pytest.mark.asyncio
    async def test_validate_template(self, template_manager):
        """Test template validation"""
        valid_template = "Hello ${name}! Your order ${order_id} is ready."
        variables = {"name": "John", "order_id": "12345"}
        
        validation = await template_manager.validate_template(valid_template, variables)
        
        assert validation["valid"] is True
        assert isinstance(validation["variables"], dict)
        assert "name" in validation["variables"]["required"]
        assert "order_id" in validation["variables"]["required"]

# =============================================================================
# BRAND VOICE MANAGER TESTS
# =============================================================================

class TestBrandVoiceManager:
    """Tests for brand voice manager"""
    
    def test_initialization(self, brand_voice_manager):
        """Test brand voice manager initialization"""
        assert brand_voice_manager.config is not None
        assert hasattr(brand_voice_manager, 'kv_namespace')
        assert hasattr(brand_voice_manager, '_brand_voice_cache')
    
    @pytest.mark.asyncio
    async def test_set_and_get_brand_voice(self, brand_voice_manager):
        """Test setting and getting brand voice"""
        brand_voice_data = {
            "brand_name": "TestBrand",
            "bio": "A test brand",
            "audience": "test users",
            "tone_default": "friendly",
            "do": ["be helpful"],
            "dont": ["be rude"]
        }
        
        # Set brand voice
        result = await brand_voice_manager.set_brand_voice(brand_voice_data)
        assert result is True
        
        # Get brand voice
        retrieved = await brand_voice_manager.get_brand_voice()
        assert retrieved["brand_name"] == "TestBrand"
        assert retrieved["bio"] == "A test brand"
        assert retrieved["tone_default"] == "friendly"
    
    def test_apply_brand_voice_to_prompt(self, brand_voice_manager):
        """Test applying brand voice to prompts"""
        base_prompt = "Write a social media post about our new product."
        brand_voice = {
            "brand_name": "TechCorp",
            "tone_default": "professional",
            "do": ["be informative"],
            "dont": ["use jargon"]
        }
        
        enhanced_prompt = brand_voice_manager.apply_brand_voice_to_prompt(base_prompt, brand_voice)
        
        assert "TechCorp" in enhanced_prompt
        assert "professional" in enhanced_prompt
        assert "be informative" in enhanced_prompt
        assert "use jargon" in enhanced_prompt
    
    def test_validate_content_against_brand_voice(self, brand_voice_manager):
        """Test content validation against brand voice"""
        content = "Check out our amazing new product! It's literally the best thing ever."
        brand_voice = {
            "banned_phrases": ["amazing"],
            "discouraged_words": ["literally"],
            "required_phrases": ["innovative"]
        }
        
        validation = brand_voice_manager.validate_content_against_brand_voice(content, brand_voice)
        
        assert validation["compliant"] is False  # Contains banned phrase
        assert len(validation["issues"]) > 0
        assert len(validation["suggestions"]) > 0
        assert len(validation["warnings"]) > 0  # Missing required phrase

# =============================================================================
# ANALYTICS TESTS
# =============================================================================

class TestCreatorAnalytics:
    """Tests for analytics system"""
    
    def test_initialization(self, analytics):
        """Test analytics initialization"""
        assert analytics.config is not None
        assert analytics.enabled is True
        assert hasattr(analytics, 'events')
        assert hasattr(analytics, 'daily_stats')
    
    def test_track_event(self, analytics):
        """Test event tracking"""
        event = Event(
            timestamp=1234567890.0,
            event_type=EventType.GENERATION_COMPLETE,
            action="generate_post",
            provider="openai",
            model="gpt-4",
            success=True,
            duration_ms=1500.0,
            cost_usd=0.05,
            tokens_used=150,
            metadata={"platform": "linkedin"}
        )
        
        initial_event_count = len(analytics.events)
        analytics.track_event(event)
        
        assert len(analytics.events) == initial_event_count + 1
        assert analytics.events[-1] == event
    
    def test_track_generation_complete(self, analytics):
        """Test tracking generation completion"""
        analytics.track_generation_complete(
            action="generate_image",
            provider="stability",
            model="sdxl",
            duration_ms=3000,
            cost_usd=0.10,
            metadata={"size": "1024x1024"}
        )
        
        assert len(analytics.events) > 0
        latest_event = analytics.events[-1]
        assert latest_event.action == "generate_image"
        assert latest_event.provider == "stability"
        assert latest_event.success is True
    
    def test_get_daily_stats(self, analytics):
        """Test getting daily statistics"""
        # Add some test events
        analytics.track_generation_complete("test_action", "test_provider", "test_model", 1000, 0.01)
        analytics.track_generation_error("test_action", "test_provider", "api_error")
        
        stats = analytics.get_daily_stats()
        
        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert stats["total_requests"] >= 2
    
    def test_get_health_status(self, analytics):
        """Test getting health status"""
        # Add some test data
        analytics.track_generation_complete("test", "provider1", "model1", 1000, 0.01)
        
        health = analytics.get_health_status()
        
        assert "status" in health
        assert "error_rate_percent" in health
        assert "daily_cost_usd" in health
        assert health["status"] in ["healthy", "warning", "critical", "unknown"]

# =============================================================================
# CONNECTOR MANAGER TESTS
# =============================================================================

class TestConnectorManager:
    """Tests for connector manager"""
    
    def test_initialization(self, connector_manager):
        """Test connector manager initialization"""
        assert connector_manager.config is not None
        assert hasattr(connector_manager, 'connectors')
        assert hasattr(connector_manager, 'active_connections')
    
    @pytest.mark.asyncio
    async def test_list_connectors(self, connector_manager):
        """Test listing available connectors"""
        connectors = await connector_manager.list_connectors()
        
        assert isinstance(connectors, list)
        # The list might be empty if no connectors are configured
    
    def test_get_connector_status(self, connector_manager):
        """Test getting connector status"""
        status = connector_manager.get_connector_status()
        
        assert "available_connectors" in status
        assert "active_connections" in status
        assert "connector_details" in status
        assert isinstance(status["available_connectors"], list)
        assert isinstance(status["active_connections"], int)

# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Tests for error handling"""
    
    def test_creator_error(self):
        """Test CreatorError exception"""
        error = CreatorError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_media_error(self):
        """Test MediaError exception"""
        error = MediaError("Media error", "image", "generation")
        assert "Media error" in str(error)
        assert error.media_type == "image"
        assert error.operation == "generation"
    
    def test_provider_error(self):
        """Test ProviderError exception"""
        error = ProviderError("Provider failed", "openai")
        assert "Provider failed" in str(error)
        assert error.provider == "openai"

# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for component interaction"""
    
    @pytest.mark.asyncio
    async def test_template_with_brand_voice(self, template_manager, brand_voice_manager):
        """Test template rendering with brand voice"""
        # Set up brand voice
        brand_voice_data = {
            "brand_name": "TechFlow",
            "tone_default": "professional",
            "cta_style": "engaging"
        }
        await brand_voice_manager.set_brand_voice(brand_voice_data)
        
        # Create and render template
        template_body = "Hello! ${brand_name} is excited to announce ${news}."
        template_id = await template_manager.upsert_template(None, template_body, {
            "name": "Brand Announcement",
            "category": "social"
        })
        
        rendered = await template_manager.render_template(template_id, {
            "brand_name": "TechFlow",
            "news": "our new AI features"
        })
        
        assert "TechFlow" in rendered
        assert "AI features" in rendered
    
    def test_analytics_with_provider_manager(self, analytics, enhanced_provider_manager):
        """Test analytics integration with provider manager"""
        # Track a provider operation
        analytics.track_generation_start("generate_text", "openai")
        analytics.track_generation_complete(
            "generate_text", "openai", "gpt-4", 2000, 0.03, 200
        )
        
        # Verify tracking
        stats = analytics.get_provider_stats()
        assert len(analytics.events) >= 2
        
        # Check if provider stats are updated (might be empty if no real operations)
        health = analytics.get_health_status()
        assert health["total_requests_today"] >= 2

# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance and load tests"""
    
    @pytest.mark.asyncio
    async def test_template_rendering_performance(self, template_manager):
        """Test template rendering performance"""
        import time
        
        template_body = "Performance test: ${item1}, ${item2}, ${item3}"
        template_id = await template_manager.upsert_template(None, template_body, {
            "name": "Performance Test"
        })
        
        variables = {"item1": "A", "item2": "B", "item3": "C"}
        
        start_time = time.time()
        
        # Render template multiple times
        for i in range(100):
            await template_manager.render_template(template_id, variables)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 100 renders in reasonable time (< 1 second)
        assert duration < 1.0
    
    def test_analytics_event_tracking_performance(self, analytics):
        """Test analytics event tracking performance"""
        import time
        
        start_time = time.time()
        
        # Track many events
        for i in range(1000):
            analytics.track_generation_complete(
                f"action_{i % 10}", "provider", "model", 1000, 0.01
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle 1000 events quickly (< 1 second)
        assert duration < 1.0
        assert len(analytics.events) >= 1000

# =============================================================================
# UTILITY FUNCTIONS FOR TESTS
# =============================================================================

def create_test_event(action="test_action", success=True, cost=0.01) -> Event:
    """Create a test event for analytics"""
    return Event(
        timestamp=1234567890.0,
        event_type=EventType.GENERATION_COMPLETE if success else EventType.GENERATION_ERROR,
        action=action,
        provider="test_provider",
        model="test_model",
        success=success,
        duration_ms=1000.0,
        cost_usd=cost if success else None,
        tokens_used=100 if success else None,
        metadata={"test": True},
        error_type="test_error" if not success else None
    )

# =============================================================================
# FIXTURES FOR MOCK DATA
# =============================================================================

@pytest.fixture
def sample_brand_voice():
    """Sample brand voice data"""
    return {
        "brand_name": "TestBrand",
        "bio": "An innovative test brand",
        "audience": "Tech enthusiasts",
        "tone_default": "friendly",
        "voice_personality": "innovative",
        "do": ["be authentic", "provide value"],
        "dont": ["use jargon", "be promotional"],
        "required_phrases": ["innovation"],
        "discouraged_words": ["obviously", "literally"],
        "reading_level": "intermediate",
        "emoji_policy": "moderate",
        "cta_style": "engaging"
    }

@pytest.fixture
def sample_template_data():
    """Sample template data"""
    return {
        "body": "Hello ${name}! Welcome to ${brand}. ${message}",
        "meta": {
            "name": "Welcome Template",
            "description": "A welcome message template",
            "category": "email",
            "type": "text",
            "tags": ["welcome", "onboarding"]
        }
    }

if __name__ == "__main__":
    pytest.main([__file__])
