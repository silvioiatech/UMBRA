"""
Creator v1 (CRT4) - Complete Content Creation System
Main integration module that brings together all CRT4 components
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict

from ...core.config import UmbraConfig
from ...ai.agent import UmbraAIAgent

# Import all CRT4 components
from .service import CreatorService
from .model_provider_enhanced import EnhancedModelProviderManager
from .voice import BrandVoiceManager
from .presets import PlatformPresets
from .validate import ContentValidator
from .templates import TemplateManager
from .connectors import ConnectorManager
from .analytics import CreatorAnalytics
from .cache import CreatorCache
from .workflow import WorkflowManager
from .rate_limiter import RateLimiter
from .health import HealthMonitor
from .batching import IntelligentBatcher
from .dynamic_config import DynamicConfig
from .plugins import PluginManager
from .advanced_metrics import AdvancedMetrics
from .security import SecurityManager
from .errors import CreatorError

logger = logging.getLogger(__name__)

@dataclass
class CreatorSystemStatus:
    """Overall system status"""
    version: str
    enabled: bool
    components_status: Dict[str, bool]
    health_status: str
    performance_metrics: Dict[str, Any]
    security_status: Dict[str, Any]
    last_updated: float

class CreatorV1System:
    """
    Complete Creator v1 (CRT4) Content Creation System
    
    This is the main orchestrator that brings together all CRT4 components:
    - Enhanced AI Provider Management
    - Brand Voice & Content Validation
    - Template & Connector Systems
    - Advanced Analytics & Metrics
    - Intelligent Caching & Batching
    - Workflow Orchestration
    - Rate Limiting & Security
    - Health Monitoring & Configuration
    - Plugin Architecture
    """
    
    def __init__(self, config: UmbraConfig, ai_agent: UmbraAIAgent):
        self.config = config
        self.ai_agent = ai_agent
        self.version = "1.0.0"
        
        # Core configuration
        self.enabled = config.get("CREATOR_V1_ENABLED", True)
        self.debug_mode = config.get("CREATOR_V1_DEBUG", False)
        
        # Component initialization order matters
        self.components = {}
        self.initialization_order = [
            "dynamic_config",
            "security",
            "analytics", 
            "cache",
            "rate_limiter",
            "health_monitor",
            "advanced_metrics",
            "provider_manager",
            "brand_voice",
            "presets",
            "validator",
            "template_manager",
            "connector_manager",
            "batching",
            "workflow_manager",
            "plugin_manager",
            "creator_service"
        ]
        
        # System status
        self.status = CreatorSystemStatus(
            version=self.version,
            enabled=self.enabled,
            components_status={},
            health_status="initializing",
            performance_metrics={},
            security_status={},
            last_updated=0
        )
        
        logger.info(f"Initializing Creator v1 System (version {self.version})")
    
    async def initialize(self) -> bool:
        """Initialize all CRT4 components in correct order"""
        if not self.enabled:
            logger.info("Creator v1 System is disabled")
            return False
        
        try:
            # Initialize components in order
            for component_name in self.initialization_order:
                success = await self._initialize_component(component_name)
                self.status.components_status[component_name] = success
                
                if not success:
                    logger.error(f"Failed to initialize component: {component_name}")
                    if component_name in ["security", "analytics"]:
                        # Critical components - fail initialization
                        self.status.health_status = "failed"
                        return False
                    # Non-critical components - continue with warning
                    logger.warning(f"Continuing without component: {component_name}")
            
            # Post-initialization setup
            await self._post_initialization_setup()
            
            # Update system status
            self.status.health_status = "healthy"
            self.status.last_updated = asyncio.get_event_loop().time()
            
            logger.info("Creator v1 System successfully initialized")
            return True
            
        except Exception as e:
            logger.error(f"Creator v1 System initialization failed: {e}")
            self.status.health_status = "failed"
            return False
    
    async def _initialize_component(self, component_name: str) -> bool:
        """Initialize individual component"""
        try:
            if component_name == "dynamic_config":
                self.components["dynamic_config"] = DynamicConfig(
                    self.config, 
                    self.components.get("analytics")
                )
            
            elif component_name == "security":
                self.components["security"] = SecurityManager(
                    self.config,
                    self.components.get("analytics")
                )
            
            elif component_name == "analytics":
                self.components["analytics"] = CreatorAnalytics(self.config)
            
            elif component_name == "cache":
                self.components["cache"] = CreatorCache(self.config)
            
            elif component_name == "rate_limiter":
                self.components["rate_limiter"] = RateLimiter(
                    self.config,
                    self.components.get("analytics")
                )
            
            elif component_name == "health_monitor":
                self.components["health_monitor"] = HealthMonitor(
                    self.config,
                    self.components.get("analytics")
                )
            
            elif component_name == "advanced_metrics":
                self.components["advanced_metrics"] = AdvancedMetrics(
                    self.config,
                    self.components.get("analytics")
                )
            
            elif component_name == "provider_manager":
                self.components["provider_manager"] = EnhancedModelProviderManager(self.config)
            
            elif component_name == "brand_voice":
                self.components["brand_voice"] = BrandVoiceManager(self.config)
            
            elif component_name == "presets":
                self.components["presets"] = PlatformPresets(self.config)
            
            elif component_name == "validator":
                self.components["validator"] = ContentValidator(self.config)
            
            elif component_name == "template_manager":
                self.components["template_manager"] = TemplateManager(self.config)
            
            elif component_name == "connector_manager":
                self.components["connector_manager"] = ConnectorManager(self.config)
            
            elif component_name == "batching":
                self.components["batching"] = IntelligentBatcher(
                    self.config,
                    self.components.get("analytics")
                )
            
            elif component_name == "workflow_manager":
                self.components["workflow_manager"] = WorkflowManager(
                    self.config,
                    self.components.get("analytics")
                )
            
            elif component_name == "plugin_manager":
                self.components["plugin_manager"] = PluginManager(
                    self.config,
                    self.components.get("analytics")
                )
            
            elif component_name == "creator_service":
                self.components["creator_service"] = CreatorService(
                    self.ai_agent,
                    self.config
                )
            
            else:
                logger.warning(f"Unknown component: {component_name}")
                return False
            
            logger.debug(f"Initialized component: {component_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize {component_name}: {e}")
            return False
    
    async def _post_initialization_setup(self):
        """Setup cross-component integrations"""
        try:
            # Connect analytics to all components that support it
            analytics = self.components.get("analytics")
            if analytics:
                # Setup metrics collection
                metrics = self.components.get("advanced_metrics")
                if metrics:
                    # Register common metrics
                    await self._setup_metrics_integration()
            
            # Setup health monitoring for all components
            health_monitor = self.components.get("health_monitor")
            if health_monitor:
                await self._setup_health_monitoring()
            
            # Configure security for all endpoints
            security = self.components.get("security")
            if security:
                await self._setup_security_integration()
            
            # Setup plugin hooks
            plugin_manager = self.components.get("plugin_manager")
            if plugin_manager:
                await self._setup_plugin_integration()
            
            logger.debug("Post-initialization setup completed")
            
        except Exception as e:
            logger.error(f"Post-initialization setup failed: {e}")
            raise
    
    async def _setup_metrics_integration(self):
        """Setup metrics collection across components"""
        metrics = self.components["advanced_metrics"]
        
        # Track system-wide metrics
        metrics.record_metric("system_startup", 1, {"version": self.version})
        
        # Setup automatic metric collection
        for component_name, component in self.components.items():
            if hasattr(component, 'get_stats'):
                try:
                    stats = component.get_stats() if callable(component.get_stats) else component.get_stats
                    if isinstance(stats, dict):
                        for key, value in stats.items():
                            if isinstance(value, (int, float)):
                                metrics.record_metric(
                                    f"{component_name}_{key}",
                                    value,
                                    {"component": component_name}
                                )
                except Exception as e:
                    logger.debug(f"Could not collect stats from {component_name}: {e}")
    
    async def _setup_health_monitoring(self):
        """Setup health monitoring for all components"""
        health_monitor = self.components["health_monitor"]
        
        # Add health checks for each component
        for component_name, component in self.components.items():
            if hasattr(component, 'get_health_status'):
                health_check_func = lambda comp=component: comp.get_health_status()
                
                from .health import HealthCheck, CheckType
                health_check = HealthCheck(
                    name=f"{component_name}_health",
                    check_type=CheckType.SERVICE,
                    check_function=health_check_func,
                    interval_seconds=60,
                    tags=[component_name, "component"]
                )
                
                health_monitor.add_health_check(health_check)
    
    async def _setup_security_integration(self):
        """Setup security integration across components"""
        security = self.components["security"]
        
        # Add security event handlers
        async def security_alert_handler(alert_data):
            logger.warning(f"Security Alert: {alert_data}")
            
            # Record in metrics
            metrics = self.components.get("advanced_metrics")
            if metrics:
                metrics.record_metric(
                    "security_alerts",
                    1,
                    {"severity": alert_data.get("severity", "unknown")}
                )
        
        # Setup rate limiting integration
        rate_limiter = self.components.get("rate_limiter")
        if rate_limiter:
            # Connect rate limiter to security monitoring
            pass
    
    async def _setup_plugin_integration(self):
        """Setup plugin system integration"""
        plugin_manager = self.components["plugin_manager"]
        
        # Register system hooks
        plugin_manager.register_step_executor(
            "generate_content_pack",
            self._plugin_generate_content_pack
        )
        
        plugin_manager.register_step_executor(
            "validate_content",
            self._plugin_validate_content
        )
    
    async def _plugin_generate_content_pack(self, params: Dict[str, Any], context: Dict[str, Any]):
        """Plugin executor for content pack generation"""
        creator_service = self.components.get("creator_service")
        if creator_service:
            return await creator_service.generate_content_pack(**params)
        return {"error": "Creator service not available"}
    
    async def _plugin_validate_content(self, params: Dict[str, Any], context: Dict[str, Any]):
        """Plugin executor for content validation"""
        validator = self.components.get("validator")
        if validator:
            content = params.get("content", "")
            platform = params.get("platform")
            return await validator.validate_content(content, None, platform)
        return {"valid": False, "error": "Validator not available"}
    
    # Public API Methods
    
    async def generate_content(self, request: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main content generation endpoint
        
        Args:
            request: Content generation request
            user_id: Optional user ID for tracking
            
        Returns:
            Generated content and metadata
        """
        try:
            # Security check
            if not await self._check_request_security(request, user_id):
                raise CreatorError("Security check failed")
            
            # Rate limiting
            rate_limiter = self.components.get("rate_limiter")
            if rate_limiter:
                from .rate_limiter import RateLimitedOperation
                async with RateLimitedOperation(
                    rate_limiter, 
                    user_id or "anonymous", 
                    "generate_content",
                    user_id=user_id
                ):
                    return await self._process_content_request(request, user_id)
            else:
                return await self._process_content_request(request, user_id)
                
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            
            # Record error in metrics
            metrics = self.components.get("advanced_metrics")
            if metrics:
                metrics.record_metric("content_generation_errors", 1, {"user_id": user_id})
            
            raise CreatorError(f"Content generation failed: {e}")
    
    async def _process_content_request(self, request: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Process content generation request"""
        creator_service = self.components.get("creator_service")
        if not creator_service:
            raise CreatorError("Creator service not available")
        
        # Extract request parameters
        action = request.get("action", "generate_post")
        topic = request.get("topic", "")
        platform = request.get("platform")
        tone = request.get("tone")
        
        # Track request start
        analytics = self.components.get("analytics")
        if analytics:
            analytics.track_generation_start(action, {"user_id": user_id, "platform": platform})
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Route to appropriate method
            if action == "generate_post":
                result = await creator_service.generate_post(
                    topic=topic,
                    platform=platform,
                    tone=tone,
                    user_id=user_id
                )
            elif action == "generate_content_pack":
                result = await creator_service.generate_content_pack(
                    topic=topic,
                    platform=platform,
                    tone=tone,
                    user_id=user_id
                )
            elif action == "auto_orchestrate":
                result = await creator_service.auto_orchestrate(
                    input_data=request.get("input_data", topic),
                    goal=request.get("goal"),
                    platform=platform,
                    tone=tone,
                    user_id=user_id
                )
            else:
                raise CreatorError(f"Unknown action: {action}")
            
            # Track success
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if analytics:
                analytics.track_generation_complete(
                    action,
                    result.get("provider_used", "unknown"),
                    result.get("model_used", "unknown"),
                    duration,
                    result.get("cost", 0.0),
                    result.get("tokens", 0)
                )
            
            # Record metrics
            metrics = self.components.get("advanced_metrics")
            if metrics:
                metrics.record_metric("content_generated", 1, {
                    "action": action,
                    "platform": platform or "unknown",
                    "user_id": user_id or "anonymous"
                })
                metrics.record_metric("generation_duration", duration, {"action": action})
            
            return result
            
        except Exception as e:
            # Track error
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if analytics:
                analytics.track_generation_error(
                    action,
                    "creator_service",
                    str(e),
                    duration
                )
            
            raise
    
    async def _check_request_security(self, request: Dict[str, Any], user_id: Optional[str]) -> bool:
        """Check request security"""
        security = self.components.get("security")
        if not security:
            return True  # No security component, allow request
        
        # Sanitize input
        sanitized_request = security.sanitize_input(request)
        request.update(sanitized_request)
        
        return True
    
    async def create_workflow(self, workflow_definition: Dict[str, Any], user_id: Optional[str] = None) -> str:
        """Create and execute workflow"""
        workflow_manager = self.components.get("workflow_manager")
        if not workflow_manager:
            raise CreatorError("Workflow manager not available")
        
        workflow_id = await workflow_manager.create_custom_workflow(
            name=workflow_definition.get("name", "Custom Workflow"),
            steps=workflow_definition.get("steps", []),
            description=workflow_definition.get("description", ""),
            user_id=user_id
        )
        
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute workflow"""
        workflow_manager = self.components.get("workflow_manager")
        if not workflow_manager:
            raise CreatorError("Workflow manager not available")
        
        return await workflow_manager.execute_workflow(workflow_id, context)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Update performance metrics
            performance_metrics = {}
            for component_name, component in self.components.items():
                if hasattr(component, 'get_stats'):
                    try:
                        stats = component.get_stats()
                        if isinstance(stats, dict):
                            performance_metrics[component_name] = stats
                    except Exception:
                        performance_metrics[component_name] = {"status": "error"}
            
            # Update security status
            security = self.components.get("security")
            security_status = security.get_security_summary() if security else {"enabled": False}
            
            # Update overall health
            health_monitor = self.components.get("health_monitor")
            if health_monitor:
                overall_health = health_monitor.get_overall_health()
                self.status.health_status = overall_health["status"]
            
            self.status.performance_metrics = performance_metrics
            self.status.security_status = security_status
            self.status.last_updated = asyncio.get_event_loop().time()
            
            return asdict(self.status)
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "version": self.version,
                "enabled": self.enabled,
                "health_status": "error",
                "error": str(e)
            }
    
    async def shutdown(self):
        """Gracefully shutdown the system"""
        logger.info("Shutting down Creator v1 System")
        
        try:
            # Shutdown components in reverse order
            for component_name in reversed(self.initialization_order):
                component = self.components.get(component_name)
                if component and hasattr(component, 'cleanup'):
                    try:
                        if asyncio.iscoroutinefunction(component.cleanup):
                            await component.cleanup()
                        else:
                            component.cleanup()
                        logger.debug(f"Cleaned up component: {component_name}")
                    except Exception as e:
                        logger.error(f"Error cleaning up {component_name}: {e}")
            
            self.status.health_status = "shutdown"
            logger.info("Creator v1 System shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def get_component(self, component_name: str):
        """Get access to specific component"""
        return self.components.get(component_name)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_monitor = self.components.get("health_monitor")
        if health_monitor:
            return health_monitor.get_health_report()
        else:
            return {
                "status": "unknown",
                "message": "Health monitor not available",
                "components": self.status.components_status
            }

# Factory function for easy initialization
async def create_creator_system(config: UmbraConfig, ai_agent: UmbraAIAgent) -> CreatorV1System:
    """
    Factory function to create and initialize Creator v1 System
    
    Args:
        config: UMBRA configuration
        ai_agent: AI agent instance
        
    Returns:
        Initialized Creator v1 system
    """
    system = CreatorV1System(config, ai_agent)
    
    success = await system.initialize()
    if not success:
        raise CreatorError("Failed to initialize Creator v1 System")
    
    return system

# Export main classes and functions
__all__ = [
    'CreatorV1System',
    'CreatorSystemStatus',
    'create_creator_system',
    'CreatorError'
]
