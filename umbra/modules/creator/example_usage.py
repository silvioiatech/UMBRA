"""
Creator v1 (CRT4) - Complete Usage Example
Demonstrates all major features and components of the Creator system
"""

import asyncio
import logging
import json
from pathlib import Path

# Import Creator v1 system
from umbra.core.config import UmbraConfig
from umbra.ai.agent import UmbraAIAgent
from umbra.modules.creator import create_creator_system, CreatorV1System

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CreatorV1Demo:
    """Complete demonstration of Creator v1 capabilities"""
    
    def __init__(self):
        self.config = None
        self.ai_agent = None
        self.creator_system = None
    
    async def setup(self):
        """Setup the Creator v1 system"""
        logger.info("Setting up Creator v1 Demo...")
        
        # Create configuration
        self.config = UmbraConfig({
            # Enable all components for demo
            "CREATOR_V1_ENABLED": True,
            "CREATOR_V1_DEBUG": True,
            
            # Provider settings (add your API keys)
            "CREATOR_OPENAI_API_KEY": "your-openai-key-here",
            "CREATOR_OPENAI_ENABLED": True,
            
            # System settings
            "CREATOR_CACHE_ENABLED": True,
            "CREATOR_ANALYTICS_ENABLED": True,
            "CREATOR_HEALTH_MONITORING_ENABLED": True,
            "CREATOR_BATCHING_ENABLED": True,
            "CREATOR_WORKFLOW_MAX_CONCURRENT": 5,
            
            # Security (disable for demo)
            "CREATOR_SECURITY_ENABLED": False,
            "CREATOR_RATE_LIMITING_ENABLED": False,
            
            # Features
            "CREATOR_FEATURE_FLAGS": {
                "debug_mode": True,
                "verbose_logging": True
            }
        })
        
        # Create AI agent (simplified for demo)
        self.ai_agent = UmbraAIAgent(self.config)
        
        # Initialize Creator v1 system
        self.creator_system = await create_creator_system(self.config, self.ai_agent)
        
        logger.info("Creator v1 system initialized successfully!")
    
    async def demo_basic_content_generation(self):
        """Demo basic content generation"""
        logger.info("\n=== DEMO: Basic Content Generation ===")
        
        # Simple post generation
        request = {
            "action": "generate_post",
            "topic": "The future of sustainable technology",
            "platform": "linkedin",
            "tone": "professional"
        }
        
        result = await self.creator_system.generate_content(request, user_id="demo_user")
        
        logger.info("Generated Post:")
        logger.info(f"Content: {result.get('content', 'N/A')}")
        logger.info(f"Platform: {result.get('platform', 'N/A')}")
        logger.info(f"Provider: {result.get('provider_used', 'N/A')}")
        logger.info(f"Validation: {result.get('validation', {})}")
        
        return result
    
    async def demo_content_pack_generation(self):
        """Demo content pack generation"""
        logger.info("\n=== DEMO: Content Pack Generation ===")
        
        request = {
            "action": "generate_content_pack",
            "topic": "AI-powered productivity tools",
            "platform": "instagram",
            "tone": "engaging"
        }
        
        result = await self.creator_system.generate_content(request, user_id="demo_user")
        
        logger.info("Generated Content Pack:")
        pack = result.get('pack', {})
        logger.info(f"Caption: {pack.get('caption', 'N/A')}")
        logger.info(f"CTA: {pack.get('cta', 'N/A')}")
        logger.info(f"Titles: {pack.get('titles', [])}")
        logger.info(f"Hashtags: {pack.get('hashtags', [])}")
        logger.info(f"Alt Text: {pack.get('alt_text', 'N/A')}")
        
        return result
    
    async def demo_auto_orchestration(self):
        """Demo auto-orchestration capabilities"""
        logger.info("\n=== DEMO: Auto-Orchestration ===")
        
        # Complex input that requires orchestration
        input_data = {
            "brief": "Create a social media campaign for our new eco-friendly product line",
            "target_audience": "environmentally conscious millennials",
            "budget": "$5000",
            "timeline": "2 weeks"
        }
        
        request = {
            "action": "auto_orchestrate",
            "input_data": input_data,
            "goal": "social_media_campaign",
            "platform": "multi"
        }
        
        result = await self.creator_system.generate_content(request, user_id="demo_user")
        
        logger.info("Auto-Orchestration Result:")
        logger.info(f"Success: {result.get('success', False)}")
        logger.info(f"Results: {json.dumps(result.get('results', {}), indent=2)}")
        
        return result
    
    async def demo_workflow_system(self):
        """Demo workflow management"""
        logger.info("\n=== DEMO: Workflow System ===")
        
        # Define a content creation workflow
        workflow_definition = {
            "name": "Blog Post Creation Workflow",
            "description": "Complete blog post creation with SEO optimization",
            "steps": [
                {
                    "id": "research",
                    "name": "Topic Research",
                    "action": "research_topic",
                    "params": {"topic": "${topic}", "depth": "comprehensive"}
                },
                {
                    "id": "outline",
                    "name": "Create Outline",
                    "action": "create_outline",
                    "params": {"topic": "${topic}", "target_length": "2000"},
                    "dependencies": ["research"]
                },
                {
                    "id": "content",
                    "name": "Generate Content",
                    "action": "generate_blog_post",
                    "params": {"outline": "${outline.result}", "tone": "informative"},
                    "dependencies": ["outline"]
                },
                {
                    "id": "seo",
                    "name": "SEO Optimization",
                    "action": "optimize_seo",
                    "params": {"content": "${content.result}"},
                    "dependencies": ["content"]
                },
                {
                    "id": "validate",
                    "name": "Validate Content",
                    "action": "validate_content",
                    "params": {"content": "${seo.result}"},
                    "dependencies": ["seo"]
                }
            ]
        }
        
        # Create workflow
        workflow_id = await self.creator_system.create_workflow(
            workflow_definition, 
            user_id="demo_user"
        )
        
        logger.info(f"Created workflow: {workflow_id}")
        
        # Execute workflow
        context = {"topic": "Machine Learning in Healthcare"}
        execution_result = await self.creator_system.execute_workflow(workflow_id, context)
        
        logger.info("Workflow Execution Result:")
        logger.info(f"Success: {execution_result.get('success', False)}")
        logger.info(f"Steps Completed: {execution_result.get('steps_completed', 0)}")
        logger.info(f"Duration: {execution_result.get('duration_seconds', 0):.2f}s")
        
        return execution_result
    
    async def demo_analytics_and_metrics(self):
        """Demo analytics and metrics collection"""
        logger.info("\n=== DEMO: Analytics and Metrics ===")
        
        # Get analytics component
        analytics = self.creator_system.get_component("analytics")
        advanced_metrics = self.creator_system.get_component("advanced_metrics")
        
        if analytics:
            # Get analytics summary
            daily_stats = analytics.get_daily_stats()
            action_stats = analytics.get_action_stats()
            
            logger.info("Analytics Summary:")
            logger.info(f"Daily Stats: {daily_stats}")
            logger.info(f"Action Stats: {list(action_stats.keys())}")
        
        if advanced_metrics:
            # Record some demo metrics
            advanced_metrics.record_metric("demo_metric", 42.0, {"type": "demo"})
            advanced_metrics.increment_counter("demo_counter", 5)
            advanced_metrics.set_gauge("demo_gauge", 85.5)
            
            # Get metrics summary
            metrics_summary = advanced_metrics.get_metrics_summary()
            logger.info(f"Metrics Summary: {metrics_summary}")
    
    async def demo_caching_system(self):
        """Demo caching capabilities"""
        logger.info("\n=== DEMO: Caching System ===")
        
        cache = self.creator_system.get_component("cache")
        
        if cache:
            # Test cache operations
            await cache.set("demo_key", "demo_value", ttl_seconds=300)
            
            cached_value = await cache.get("demo_key")
            logger.info(f"Cached value: {cached_value}")
            
            # Get cache statistics
            cache_stats = cache.get_stats()
            logger.info(f"Cache Stats: {cache_stats}")
            
            # Test cache invalidation by tags
            await cache.set("tagged_key", "tagged_value", tags=["demo", "test"])
            await cache.invalidate_by_tags(["demo"])
            
            logger.info("Cache operations completed")
    
    async def demo_health_monitoring(self):
        """Demo health monitoring"""
        logger.info("\n=== DEMO: Health Monitoring ===")
        
        health_monitor = self.creator_system.get_component("health_monitor")
        
        if health_monitor:
            # Get overall health
            overall_health = health_monitor.get_overall_health()
            logger.info(f"Overall Health: {overall_health['status']}")
            logger.info(f"Health Message: {overall_health['message']}")
            
            # Get detailed health report
            health_report = health_monitor.get_health_report()
            logger.info("Health Report Summary:")
            logger.info(f"- Total Checks: {len(health_report.get('check_details', {}))}")
            logger.info(f"- System Summary: {health_report.get('system_summary', {})}")
            
            # Run health checks on all plugins
            plugin_health = await health_monitor.health_check_all_plugins()
            logger.info(f"Plugin Health: {len(plugin_health)} plugins checked")
    
    async def demo_plugin_system(self):
        """Demo plugin system"""
        logger.info("\n=== DEMO: Plugin System ===")
        
        plugin_manager = self.creator_system.get_component("plugin_manager")
        
        if plugin_manager:
            # Get plugin stats
            plugin_stats = plugin_manager.get_plugin_stats()
            logger.info(f"Plugin Stats: {plugin_stats}")
            
            # List available plugins
            all_plugins = plugin_manager.get_all_plugins_info()
            logger.info(f"Available Plugins: {list(all_plugins.keys())}")
            
            # Demo plugin execution if any plugins are available
            active_plugins = plugin_manager.get_active_plugins()
            if active_plugins:
                plugin_name = active_plugins[0]
                logger.info(f"Testing plugin: {plugin_name}")
                
                try:
                    # Test plugin health
                    plugin_info = plugin_manager.get_plugin_info(plugin_name)
                    logger.info(f"Plugin Info: {plugin_info}")
                except Exception as e:
                    logger.info(f"Plugin test failed: {e}")
    
    async def demo_security_features(self):
        """Demo security features (if enabled)"""
        logger.info("\n=== DEMO: Security Features ===")
        
        security = self.creator_system.get_component("security")
        
        if security and security.enabled:
            # Get security summary
            security_summary = security.get_security_summary()
            logger.info(f"Security Summary: {security_summary}")
            
            # Demo authentication (would normally use real credentials)
            try:
                token = await security.authenticate_user("demo_user", "demo_password")
                logger.info(f"Authentication successful: {token[:20]}...")
                
                # Validate session
                session = security.validate_session(token)
                if session:
                    logger.info(f"Session valid for user: {session.user_id}")
            except Exception as e:
                logger.info(f"Authentication demo failed: {e}")
        else:
            logger.info("Security is disabled for this demo")
    
    async def demo_system_status(self):
        """Demo system status monitoring"""
        logger.info("\n=== DEMO: System Status ===")
        
        # Get comprehensive system status
        system_status = self.creator_system.get_system_status()
        
        logger.info("System Status:")
        logger.info(f"- Version: {system_status.get('version')}")
        logger.info(f"- Enabled: {system_status.get('enabled')}")
        logger.info(f"- Health: {system_status.get('health_status')}")
        logger.info(f"- Components: {len(system_status.get('components_status', {}))}")
        
        # Component status
        components_status = system_status.get('components_status', {})
        working_components = sum(1 for status in components_status.values() if status)
        total_components = len(components_status)
        
        logger.info(f"- Working Components: {working_components}/{total_components}")
        
        # Performance metrics
        performance = system_status.get('performance_metrics', {})
        logger.info(f"- Performance Data: {len(performance)} component metrics")
        
        return system_status
    
    async def run_complete_demo(self):
        """Run the complete demonstration"""
        logger.info("🚀 Starting Creator v1 (CRT4) Complete Demo")
        
        try:
            # Setup
            await self.setup()
            
            # Run all demos
            await self.demo_basic_content_generation()
            await self.demo_content_pack_generation()
            await self.demo_auto_orchestration()
            await self.demo_workflow_system()
            await self.demo_analytics_and_metrics()
            await self.demo_caching_system()
            await self.demo_health_monitoring()
            await self.demo_plugin_system()
            await self.demo_security_features()
            
            # Final system status
            await self.demo_system_status()
            
            logger.info("✅ Creator v1 Demo completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise
        
        finally:
            # Cleanup
            if self.creator_system:
                await self.creator_system.shutdown()
                logger.info("🔄 System shutdown completed")

async def run_quick_demo():
    """Quick demo for basic testing"""
    logger.info("🏃 Running Quick Creator v1 Demo")
    
    # Simple configuration
    config = UmbraConfig({
        "CREATOR_V1_ENABLED": True,
        "CREATOR_OPENAI_API_KEY": "demo-key",  # Replace with real key
        "CREATOR_SECURITY_ENABLED": False,
        "CREATOR_RATE_LIMITING_ENABLED": False
    })
    
    # Create AI agent
    ai_agent = UmbraAIAgent(config)
    
    try:
        # Initialize system
        creator_system = await create_creator_system(config, ai_agent)
        
        # Quick content generation test
        request = {
            "action": "generate_post",
            "topic": "Hello Creator v1!",
            "platform": "twitter",
            "tone": "friendly"
        }
        
        result = await creator_system.generate_content(request)
        logger.info(f"Quick demo result: {result.get('content', 'No content generated')}")
        
        # System status
        status = creator_system.get_system_status()
        logger.info(f"System health: {status.get('health_status', 'unknown')}")
        
        logger.info("✅ Quick demo completed!")
        
    except Exception as e:
        logger.error(f"❌ Quick demo failed: {e}")
    
    finally:
        if 'creator_system' in locals():
            await creator_system.shutdown()

async def benchmark_performance():
    """Benchmark Creator v1 performance"""
    logger.info("⚡ Running Creator v1 Performance Benchmark")
    
    config = UmbraConfig({
        "CREATOR_V1_ENABLED": True,
        "CREATOR_ANALYTICS_ENABLED": True,
        "CREATOR_CACHE_ENABLED": True,
        "CREATOR_BATCHING_ENABLED": True,
        "CREATOR_SECURITY_ENABLED": False
    })
    
    ai_agent = UmbraAIAgent(config)
    
    try:
        creator_system = await create_creator_system(config, ai_agent)
        
        # Benchmark parameters
        num_requests = 10
        start_time = asyncio.get_event_loop().time()
        
        # Generate multiple content pieces
        tasks = []
        for i in range(num_requests):
            request = {
                "action": "generate_post",
                "topic": f"Benchmark topic {i+1}",
                "platform": "linkedin",
                "tone": "professional"
            }
            
            task = creator_system.generate_content(request, user_id=f"benchmark_user_{i}")
            tasks.append(task)
        
        # Execute all requests
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate performance metrics
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        successful_requests = sum(1 for r in results if not isinstance(r, Exception))
        failed_requests = num_requests - successful_requests
        
        logger.info("📊 Benchmark Results:")
        logger.info(f"- Total Requests: {num_requests}")
        logger.info(f"- Successful: {successful_requests}")
        logger.info(f"- Failed: {failed_requests}")
        logger.info(f"- Total Time: {total_time:.2f}s")
        logger.info(f"- Average Time per Request: {total_time/num_requests:.2f}s")
        logger.info(f"- Requests per Second: {num_requests/total_time:.2f}")
        
        # Get system performance data
        status = creator_system.get_system_status()
        performance_metrics = status.get('performance_metrics', {})
        
        for component, metrics in performance_metrics.items():
            if isinstance(metrics, dict):
                logger.info(f"- {component}: {metrics}")
        
        logger.info("✅ Performance benchmark completed!")
        
    except Exception as e:
        logger.error(f"❌ Benchmark failed: {e}")
    
    finally:
        if 'creator_system' in locals():
            await creator_system.shutdown()

# Demo execution functions
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Creator v1 Demo")
    parser.add_argument("--mode", choices=["full", "quick", "benchmark"], 
                       default="quick", help="Demo mode to run")
    
    args = parser.parse_args()
    
    if args.mode == "full":
        demo = CreatorV1Demo()
        asyncio.run(demo.run_complete_demo())
    elif args.mode == "quick":
        asyncio.run(run_quick_demo())
    elif args.mode == "benchmark":
        asyncio.run(benchmark_performance())
