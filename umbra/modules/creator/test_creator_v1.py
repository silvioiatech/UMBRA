"""
Creator v1 (CRT4) - Comprehensive Test Suite
Tests all components and integration points of the Creator system
"""

import pytest
import asyncio
import logging
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import Creator v1 components
from umbra.core.config import UmbraConfig
from umbra.ai.agent import UmbraAIAgent
from umbra.modules.creator import create_creator_system, CreatorV1System
from umbra.modules.creator.errors import CreatorError, SecurityError, RateLimitError

# Setup test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test fixtures
@pytest.fixture
def test_config():
    """Test configuration"""
    return UmbraConfig({
        "CREATOR_V1_ENABLED": True,
        "CREATOR_V1_DEBUG": True,
        "CREATOR_OPENAI_API_KEY": "test-key",
        "CREATOR_SECURITY_ENABLED": False,
        "CREATOR_RATE_LIMITING_ENABLED": False,
        "CREATOR_CACHE_ENABLED": True,
        "CREATOR_ANALYTICS_ENABLED": True,
        "CREATOR_BATCHING_ENABLED": True,
        "CREATOR_HEALTH_MONITORING_ENABLED": True,
    })

@pytest.fixture
def mock_ai_agent():
    """Mock AI agent for testing"""
    agent = Mock(spec=UmbraAIAgent)
    agent.generate_response = AsyncMock(return_value="Test generated content")
    return agent

@pytest.fixture
async def creator_system(test_config, mock_ai_agent):
    """Creator system fixture"""
    system = await create_creator_system(test_config, mock_ai_agent)
    yield system
    await system.shutdown()

class TestCreatorV1System:
    """Test the main Creator v1 system"""
    
    async def test_system_initialization(self, test_config, mock_ai_agent):
        """Test system initialization"""
        system = CreatorV1System(test_config, mock_ai_agent)
        
        assert system.version == "1.0.0"
        assert system.enabled == True
        assert system.status.health_status == "initializing"
        
        # Test initialization
        success = await system.initialize()
        assert success == True
        assert system.status.health_status == "healthy"
        
        await system.shutdown()
    
    async def test_component_initialization_order(self, test_config, mock_ai_agent):
        """Test that components are initialized in correct order"""
        system = CreatorV1System(test_config, mock_ai_agent)
        
        expected_order = [
            "dynamic_config", "security", "analytics", "cache",
            "rate_limiter", "health_monitor", "advanced_metrics",
            "provider_manager", "brand_voice", "presets",
            "validator", "template_manager", "connector_manager",
            "batching", "workflow_manager", "plugin_manager",
            "creator_service"
        ]
        
        assert system.initialization_order == expected_order
        
        await system.initialize()
        
        # Check that all components were initialized
        for component_name in expected_order:
            assert component_name in system.status.components_status
        
        await system.shutdown()
    
    async def test_system_status(self, creator_system):
        """Test system status retrieval"""
        status = creator_system.get_system_status()
        
        assert "version" in status
        assert "enabled" in status
        assert "health_status" in status
        assert "components_status" in status
        assert "performance_metrics" in status
        
        assert status["version"] == "1.0.0"
        assert status["enabled"] == True
    
    async def test_component_access(self, creator_system):
        """Test component access"""
        analytics = creator_system.get_component("analytics")
        assert analytics is not None
        
        cache = creator_system.get_component("cache")
        assert cache is not None
        
        non_existent = creator_system.get_component("non_existent")
        assert non_existent is None

class TestContentGeneration:
    """Test content generation functionality"""
    
    async def test_basic_post_generation(self, creator_system):
        """Test basic post generation"""
        request = {
            "action": "generate_post",
            "topic": "Test topic",
            "platform": "twitter",
            "tone": "casual"
        }
        
        result = await creator_system.generate_content(request, user_id="test_user")
        
        assert "content" in result
        assert "platform" in result
        assert result["platform"] == "twitter"
    
    async def test_content_pack_generation(self, creator_system):
        """Test content pack generation"""
        request = {
            "action": "generate_content_pack",
            "topic": "AI technology",
            "platform": "linkedin",
            "tone": "professional"
        }
        
        result = await creator_system.generate_content(request, user_id="test_user")
        
        assert "pack" in result
        pack = result["pack"]
        assert "caption" in pack
        assert "cta" in pack
        assert "titles" in pack
        assert "hashtags" in pack
        assert "alt_text" in pack
    
    async def test_auto_orchestration(self, creator_system):
        """Test auto-orchestration"""
        input_data = {
            "brief": "Create social media content",
            "target": "young professionals"
        }
        
        request = {
            "action": "auto_orchestrate",
            "input_data": input_data,
            "goal": "social_media_campaign"
        }
        
        result = await creator_system.generate_content(request, user_id="test_user")
        
        assert "results" in result or "success" in result
    
    async def test_invalid_action(self, creator_system):
        """Test handling of invalid actions"""
        request = {
            "action": "invalid_action",
            "topic": "Test topic"
        }
        
        with pytest.raises(CreatorError):
            await creator_system.generate_content(request, user_id="test_user")

class TestAnalyticsSystem:
    """Test analytics and metrics components"""
    
    async def test_analytics_tracking(self, creator_system):
        """Test analytics tracking"""
        analytics = creator_system.get_component("analytics")
        
        if analytics:
            # Track some events
            analytics.track_generation_start("test_action", {"test": "data"})
            analytics.track_generation_complete(
                "test_action", "test_provider", "test_model", 100, 0.01, 50
            )
            
            # Get stats
            daily_stats = analytics.get_daily_stats()
            assert isinstance(daily_stats, dict)
            
            action_stats = analytics.get_action_stats()
            assert isinstance(action_stats, dict)
    
    async def test_advanced_metrics(self, creator_system):
        """Test advanced metrics system"""
        metrics = creator_system.get_component("advanced_metrics")
        
        if metrics:
            # Record metrics
            metrics.record_metric("test_metric", 42.0, {"source": "test"})
            metrics.increment_counter("test_counter", 5)
            metrics.set_gauge("test_gauge", 85.5)
            
            # Get metrics
            values = metrics.get_metric_values("test_metric")
            assert len(values) > 0
            
            # Test aggregation
            avg = metrics.aggregate_metric("test_metric", metrics.AggregationType.AVERAGE)
            assert avg is not None
            
            # Get summary
            summary = metrics.get_metrics_summary()
            assert isinstance(summary, dict)

class TestCachingSystem:
    """Test caching functionality"""
    
    async def test_cache_operations(self, creator_system):
        """Test basic cache operations"""
        cache = creator_system.get_component("cache")
        
        if cache:
            # Test set/get
            await cache.set("test_key", "test_value")
            value = await cache.get("test_key")
            assert value == "test_value"
            
            # Test TTL
            await cache.set("ttl_key", "ttl_value", ttl_seconds=1)
            await asyncio.sleep(1.1)
            expired_value = await cache.get("ttl_key")
            assert expired_value is None
            
            # Test tags
            await cache.set("tagged_key", "tagged_value", tags=["test"])
            invalidated = await cache.invalidate_by_tags(["test"])
            assert invalidated > 0
    
    async def test_cache_stats(self, creator_system):
        """Test cache statistics"""
        cache = creator_system.get_component("cache")
        
        if cache:
            # Perform some operations
            await cache.set("stats_key", "stats_value")
            await cache.get("stats_key")
            await cache.get("non_existent_key")
            
            # Get stats
            stats = cache.get_stats()
            assert isinstance(stats, dict)
            assert "hit_count" in stats
            assert "miss_count" in stats

class TestSecuritySystem:
    """Test security functionality"""
    
    async def test_security_disabled(self, creator_system):
        """Test system behavior with security disabled"""
        security = creator_system.get_component("security")
        
        if security:
            assert security.enabled == False
            
            # Should allow requests without authentication
            request = {
                "action": "generate_post",
                "topic": "Test topic"
            }
            
            result = await creator_system.generate_content(request)
            assert "content" in result
    
    @pytest.mark.asyncio
    async def test_security_enabled(self, test_config, mock_ai_agent):
        """Test security when enabled"""
        # Enable security for this test
        test_config.update({"CREATOR_SECURITY_ENABLED": True})
        
        system = await create_creator_system(test_config, mock_ai_agent)
        
        try:
            security = system.get_component("security")
            assert security.enabled == True
            
            # Test authentication
            token = await security.authenticate_user("admin", "admin")
            assert token is not None
            
            # Test session validation
            session = security.validate_session(token)
            assert session is not None
            assert session.user_id == "admin"
            
        finally:
            await system.shutdown()
    
    async def test_input_sanitization(self, creator_system):
        """Test input sanitization"""
        security = creator_system.get_component("security")
        
        if security:
            # Test malicious input
            malicious_input = "<script>alert('xss')</script>"
            sanitized = security.sanitize_input(malicious_input)
            assert "<script>" not in sanitized
            assert "alert" not in sanitized

class TestHealthMonitoring:
    """Test health monitoring system"""
    
    async def test_health_checks(self, creator_system):
        """Test health check functionality"""
        health_monitor = creator_system.get_component("health_monitor")
        
        if health_monitor:
            # Get overall health
            overall_health = health_monitor.get_overall_health()
            assert "status" in overall_health
            assert "message" in overall_health
            
            # Get detailed report
            health_report = health_monitor.get_health_report()
            assert "overall_health" in health_report
            assert "check_details" in health_report
    
    async def test_system_health_endpoint(self, creator_system):
        """Test system health check endpoint"""
        health_result = await creator_system.health_check()
        
        assert isinstance(health_result, dict)
        assert "status" in health_result

class TestWorkflowSystem:
    """Test workflow management"""
    
    async def test_workflow_creation(self, creator_system):
        """Test workflow creation"""
        workflow_definition = {
            "name": "Test Workflow",
            "description": "Test workflow description",
            "steps": [
                {
                    "id": "step1",
                    "name": "Test Step",
                    "action": "test_action",
                    "params": {"test": "value"}
                }
            ]
        }
        
        workflow_id = await creator_system.create_workflow(
            workflow_definition, user_id="test_user"
        )
        
        assert workflow_id is not None
        assert isinstance(workflow_id, str)
    
    async def test_workflow_execution(self, creator_system):
        """Test workflow execution"""
        # Create simple workflow
        workflow_definition = {
            "name": "Simple Test Workflow",
            "steps": [
                {
                    "id": "generate",
                    "name": "Generate Content",
                    "action": "generate_content_pack",
                    "params": {"topic": "test"}
                }
            ]
        }
        
        workflow_id = await creator_system.create_workflow(workflow_definition)
        
        # Execute workflow
        result = await creator_system.execute_workflow(workflow_id)
        
        assert "workflow_id" in result
        assert "success" in result

class TestBatchingSystem:
    """Test intelligent batching"""
    
    async def test_batching_disabled(self, creator_system):
        """Test system behavior with batching disabled"""
        batching = creator_system.get_component("batching")
        
        if batching:
            # Test adding requests
            request_id = await batching.add_request(
                action="test_action",
                params={"test": "value"},
                user_id="test_user"
            )
            
            assert request_id is not None
    
    async def test_batching_stats(self, creator_system):
        """Test batching statistics"""
        batching = creator_system.get_component("batching")
        
        if batching:
            stats = batching.get_batch_stats()
            assert isinstance(stats, dict)
            assert "enabled" in stats

class TestPluginSystem:
    """Test plugin architecture"""
    
    async def test_plugin_manager(self, creator_system):
        """Test plugin manager functionality"""
        plugin_manager = creator_system.get_component("plugin_manager")
        
        if plugin_manager:
            # Get plugin stats
            stats = plugin_manager.get_plugin_stats()
            assert isinstance(stats, dict)
            assert "total_plugins" in stats
            
            # List plugins
            plugins = plugin_manager.get_all_plugins_info()
            assert isinstance(plugins, dict)

class TestRateLimiting:
    """Test rate limiting system"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_disabled(self, creator_system):
        """Test system with rate limiting disabled"""
        rate_limiter = creator_system.get_component("rate_limiter")
        
        if rate_limiter:
            # Should allow requests when disabled
            from umbra.modules.creator.rate_limiter import BatchPriority
            
            result = await rate_limiter.check_rate_limit(
                "test_user", "test_action", user_id="test_user"
            )
            
            assert result.allowed == True
    
    @pytest.mark.asyncio
    async def test_rate_limiting_enabled(self, test_config, mock_ai_agent):
        """Test rate limiting when enabled"""
        # Enable rate limiting for this test
        test_config.update({
            "CREATOR_RATE_LIMITING_ENABLED": True,
            "CREATOR_USER_REQUESTS_PER_MINUTE": 2
        })
        
        system = await create_creator_system(test_config, mock_ai_agent)
        
        try:
            rate_limiter = system.get_component("rate_limiter")
            
            # First request should be allowed
            result1 = await rate_limiter.check_rate_limit(
                "test_user", "test_action", user_id="test_user"
            )
            assert result1.allowed == True
            
            # Record the request
            await rate_limiter.record_request(
                "test_user", "test_action", user_id="test_user"
            )
            
        finally:
            await system.shutdown()

class TestDynamicConfiguration:
    """Test dynamic configuration system"""
    
    async def test_configuration_management(self, creator_system):
        """Test configuration management"""
        config_manager = creator_system.get_component("dynamic_config")
        
        if config_manager:
            # Test getting configuration
            value = config_manager.get("CREATOR_MAX_OUTPUT_TOKENS")
            assert value is not None
            
            # Test setting configuration
            success = config_manager.set(
                "TEST_CONFIG_KEY", "test_value", 
                changed_by="test", reason="testing"
            )
            assert success == True
            
            # Test getting the set value
            retrieved_value = config_manager.get("TEST_CONFIG_KEY")
            assert retrieved_value == "test_value"

class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    async def test_end_to_end_content_generation(self, creator_system):
        """Test complete content generation flow"""
        # This test simulates a real user workflow
        
        # 1. Generate initial content
        request = {
            "action": "generate_post",
            "topic": "End-to-end testing",
            "platform": "linkedin",
            "tone": "professional"
        }
        
        result = await creator_system.generate_content(request, user_id="e2e_user")
        assert "content" in result
        
        # 2. Check analytics were recorded
        analytics = creator_system.get_component("analytics")
        if analytics:
            daily_stats = analytics.get_daily_stats()
            assert daily_stats.get("total_requests", 0) > 0
        
        # 3. Check metrics were recorded
        metrics = creator_system.get_component("advanced_metrics")
        if metrics:
            summary = metrics.get_metrics_summary()
            assert summary.get("data_points", 0) > 0
        
        # 4. Check system health
        health_result = await creator_system.health_check()
        assert health_result.get("status") in ["healthy", "unknown"]
    
    async def test_error_handling_and_recovery(self, creator_system):
        """Test error handling and system recovery"""
        # Test with invalid request
        invalid_request = {
            "action": "invalid_action",
            "topic": None  # Invalid topic
        }
        
        with pytest.raises(CreatorError):
            await creator_system.generate_content(invalid_request)
        
        # System should still be healthy after error
        status = creator_system.get_system_status()
        assert status.get("health_status") == "healthy"
    
    async def test_concurrent_requests(self, creator_system):
        """Test handling of concurrent requests"""
        # Create multiple concurrent requests
        requests = []
        for i in range(5):
            request = {
                "action": "generate_post",
                "topic": f"Concurrent test {i+1}",
                "platform": "twitter"
            }
            task = creator_system.generate_content(request, user_id=f"user_{i}")
            requests.append(task)
        
        # Execute all requests concurrently
        results = await asyncio.gather(*requests, return_exceptions=True)
        
        # Check that most requests succeeded
        successful = sum(1 for r in results if not isinstance(r, Exception))
        assert successful >= 3  # At least 60% success rate

class TestPerformance:
    """Test performance characteristics"""
    
    async def test_response_time(self, creator_system):
        """Test response time performance"""
        start_time = time.time()
        
        request = {
            "action": "generate_post",
            "topic": "Performance test",
            "platform": "twitter"
        }
        
        result = await creator_system.generate_content(request)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should complete within reasonable time (adjust based on actual performance)
        assert response_time < 10.0  # 10 seconds max
        assert "content" in result
    
    async def test_memory_usage(self, creator_system):
        """Test memory usage during operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform multiple operations
        for i in range(10):
            request = {
                "action": "generate_post",
                "topic": f"Memory test {i+1}",
                "platform": "twitter"
            }
            await creator_system.generate_content(request)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust based on expected usage)
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase

# Utility functions for testing
def create_test_config(overrides: Dict[str, Any] = None) -> UmbraConfig:
    """Create test configuration with optional overrides"""
    base_config = {
        "CREATOR_V1_ENABLED": True,
        "CREATOR_V1_DEBUG": True,
        "CREATOR_OPENAI_API_KEY": "test-key",
        "CREATOR_SECURITY_ENABLED": False,
        "CREATOR_RATE_LIMITING_ENABLED": False,
    }
    
    if overrides:
        base_config.update(overrides)
    
    return UmbraConfig(base_config)

async def run_basic_system_test():
    """Run basic system functionality test"""
    print("Running basic Creator v1 system test...")
    
    config = create_test_config()
    ai_agent = Mock(spec=UmbraAIAgent)
    ai_agent.generate_response = AsyncMock(return_value="Test response")
    
    try:
        system = await create_creator_system(config, ai_agent)
        
        # Test basic functionality
        request = {
            "action": "generate_post",
            "topic": "Basic test",
            "platform": "twitter"
        }
        
        result = await system.generate_content(request)
        assert "content" in result
        
        # Test system status
        status = system.get_system_status()
        assert status["enabled"] == True
        
        print("✅ Basic system test passed!")
        
    except Exception as e:
        print(f"❌ Basic system test failed: {e}")
        raise
    
    finally:
        if 'system' in locals():
            await system.shutdown()

# Test execution
if __name__ == "__main__":
    # Run basic test if executed directly
    asyncio.run(run_basic_system_test())
