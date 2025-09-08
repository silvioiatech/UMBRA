"""
Plugin System - Extensible plugin architecture for Creator v1 (CRT4)
Allows dynamic loading and management of custom functionality
"""

import logging
import importlib
import inspect
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable, Type, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
import sys
import json
import traceback

from ...core.config import UmbraConfig
from .analytics import CreatorAnalytics
from .errors import CreatorError, PluginError

logger = logging.getLogger(__name__)

class PluginType(Enum):
    """Types of plugins"""
    CONTENT_GENERATOR = "content_generator"
    CONTENT_PROCESSOR = "content_processor"
    PROVIDER = "provider"
    VALIDATOR = "validator"
    ANALYTICS = "analytics"
    WEBHOOK = "webhook"
    MIDDLEWARE = "middleware"
    CUSTOM = "custom"

class PluginStatus(Enum):
    """Plugin status"""
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"

@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = field(default_factory=list)
    min_creator_version: str = "1.0.0"
    config_schema: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    homepage: Optional[str] = None
    license: Optional[str] = None

@dataclass
class PluginInfo:
    """Complete plugin information"""
    metadata: PluginMetadata
    module_path: str
    class_name: str
    instance: Optional[Any] = None
    status: PluginStatus = PluginStatus.LOADED
    loaded_at: float = field(default_factory=time.time)
    activated_at: Optional[float] = None
    error_message: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    usage_stats: Dict[str, int] = field(default_factory=dict)

class BasePlugin:
    """Base class for all plugins"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"plugin.{self.__class__.__name__}")
        self.enabled = True
    
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        return True
    
    async def activate(self) -> bool:
        """Activate the plugin"""
        return True
    
    async def deactivate(self) -> bool:
        """Deactivate the plugin"""
        return True
    
    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        return True
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata"""
        raise NotImplementedError("Plugin must implement get_metadata()")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        return True
    
    def get_health_info(self) -> Dict[str, Any]:
        """Get plugin health information"""
        return {
            "status": "healthy",
            "enabled": self.enabled,
            "last_check": time.time()
        }

class ContentGeneratorPlugin(BasePlugin):
    """Base class for content generator plugins"""
    
    async def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content based on prompt"""
        raise NotImplementedError("Content generator must implement generate_content()")
    
    def get_supported_formats(self) -> List[str]:
        """Get supported output formats"""
        return ["text"]
    
    def estimate_cost(self, prompt: str, **kwargs) -> float:
        """Estimate generation cost"""
        return 0.0

class ContentProcessorPlugin(BasePlugin):
    """Base class for content processor plugins"""
    
    async def process_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """Process existing content"""
        raise NotImplementedError("Content processor must implement process_content()")
    
    def get_processing_types(self) -> List[str]:
        """Get supported processing types"""
        return ["enhance"]

class ProviderPlugin(BasePlugin):
    """Base class for provider plugins"""
    
    async def make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to provider"""
        raise NotImplementedError("Provider must implement make_request()")
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Get available API endpoints"""
        return {}
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return True

class ValidatorPlugin(BasePlugin):
    """Base class for validator plugins"""
    
    async def validate_content(self, content: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content against rules"""
        raise NotImplementedError("Validator must implement validate_content()")
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get available validation rules"""
        return {}

class PluginManager:
    """Comprehensive plugin management system"""
    
    def __init__(self, config: UmbraConfig, analytics: Optional[CreatorAnalytics] = None):
        self.config = config
        self.analytics = analytics
        
        # Plugin storage
        self.plugins: Dict[str, PluginInfo] = {}
        self.plugin_hooks: Dict[str, List[Callable]] = {}
        self.plugin_types: Dict[PluginType, List[str]] = {ptype: [] for ptype in PluginType}
        
        # Configuration
        self.plugin_dirs = [Path(p) for p in config.get("CREATOR_PLUGIN_DIRECTORIES", ["plugins"])]
        self.auto_load = config.get("CREATOR_PLUGIN_AUTO_LOAD", True)
        self.sandbox_enabled = config.get("CREATOR_PLUGIN_SANDBOX", False)
        self.max_load_time = config.get("CREATOR_PLUGIN_MAX_LOAD_TIME_SECONDS", 30)
        
        # Security settings
        self.allowed_modules = set(config.get("CREATOR_PLUGIN_ALLOWED_MODULES", [
            "json", "time", "datetime", "asyncio", "aiohttp", "requests",
            "numpy", "pandas", "PIL", "cv2", "transformers", "torch"
        ]))
        self.blocked_modules = set(config.get("CREATOR_PLUGIN_BLOCKED_MODULES", [
            "os", "sys", "subprocess", "exec", "eval", "__import__"
        ]))
        
        # Initialize plugin directories
        self._ensure_plugin_directories()
        
        # Load plugins if auto-load enabled
        if self.auto_load:
            asyncio.create_task(self._auto_load_plugins())
        
        logger.info("Plugin manager initialized")
    
    def _ensure_plugin_directories(self):
        """Ensure plugin directories exist"""
        for plugin_dir in self.plugin_dirs:
            plugin_dir.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py if not exists
            init_file = plugin_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# Plugin directory\n")
    
    async def _auto_load_plugins(self):
        """Automatically load plugins from directories"""
        try:
            await asyncio.sleep(1)  # Wait for system initialization
            
            for plugin_dir in self.plugin_dirs:
                await self.scan_and_load_directory(plugin_dir)
            
            logger.info(f"Auto-loaded {len(self.plugins)} plugins")
            
        except Exception as e:
            logger.error(f"Auto-load plugins failed: {e}")
    
    async def scan_and_load_directory(self, directory: Path) -> Dict[str, bool]:
        """Scan directory and load all plugins"""
        results = {}
        
        if not directory.exists():
            logger.warning(f"Plugin directory does not exist: {directory}")
            return results
        
        # Look for Python files
        for py_file in directory.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue  # Skip private files
            
            try:
                plugin_name = py_file.stem
                success = await self.load_plugin_from_file(py_file, plugin_name)
                results[plugin_name] = success
                
            except Exception as e:
                logger.error(f"Failed to load plugin from {py_file}: {e}")
                results[py_file.stem] = False
        
        # Look for plugin packages
        for pkg_dir in directory.iterdir():
            if pkg_dir.is_dir() and not pkg_dir.name.startswith("_"):
                plugin_file = pkg_dir / "__init__.py"
                if plugin_file.exists():
                    try:
                        plugin_name = pkg_dir.name
                        success = await self.load_plugin_from_file(plugin_file, plugin_name)
                        results[plugin_name] = success
                        
                    except Exception as e:
                        logger.error(f"Failed to load plugin package {pkg_dir}: {e}")
                        results[pkg_dir.name] = False
        
        return results
    
    async def load_plugin_from_file(self, file_path: Path, plugin_name: str) -> bool:
        """Load plugin from file"""
        try:
            # Security check
            if self.sandbox_enabled and not self._is_safe_file(file_path):
                raise PluginError(f"Plugin file failed security check: {file_path}")
            
            # Add directory to path temporarily
            plugin_dir = str(file_path.parent)
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)
            
            try:
                # Import module
                if file_path.name == "__init__.py":
                    module_name = file_path.parent.name
                else:
                    module_name = file_path.stem
                
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None or spec.loader is None:
                    raise PluginError(f"Could not create module spec for {file_path}")
                
                module = importlib.util.module_from_spec(spec)
                
                # Load with timeout
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, spec.loader.exec_module, module),
                    timeout=self.max_load_time
                )
                
                # Find plugin class
                plugin_class = self._find_plugin_class(module)
                if not plugin_class:
                    raise PluginError(f"No plugin class found in {file_path}")
                
                # Create plugin info
                plugin_info = PluginInfo(
                    metadata=self._extract_metadata(plugin_class),
                    module_path=str(file_path),
                    class_name=plugin_class.__name__
                )
                
                # Validate dependencies
                if not self._check_dependencies(plugin_info.metadata.dependencies):
                    raise PluginError(f"Missing dependencies: {plugin_info.metadata.dependencies}")
                
                # Create instance
                plugin_instance = plugin_class()
                plugin_info.instance = plugin_instance
                
                # Initialize plugin
                if hasattr(plugin_instance, 'initialize'):
                    success = await plugin_instance.initialize()
                    if not success:
                        raise PluginError("Plugin initialization failed")
                
                # Store plugin
                self.plugins[plugin_name] = plugin_info
                self.plugin_types[plugin_info.metadata.plugin_type].append(plugin_name)
                
                logger.info(f"Loaded plugin: {plugin_name} ({plugin_info.metadata.version})")
                return True
                
            finally:
                # Remove from path
                if plugin_dir in sys.path:
                    sys.path.remove(plugin_dir)
        
        except asyncio.TimeoutError:
            logger.error(f"Plugin load timeout: {plugin_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            if plugin_name in self.plugins:
                self.plugins[plugin_name].status = PluginStatus.ERROR
                self.plugins[plugin_name].error_message = str(e)
            return False
    
    def _find_plugin_class(self, module) -> Optional[Type[BasePlugin]]:
        """Find the plugin class in a module"""
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BasePlugin) and 
                obj != BasePlugin and
                not name.startswith('_')):
                return obj
        return None
    
    def _extract_metadata(self, plugin_class: Type[BasePlugin]) -> PluginMetadata:
        """Extract metadata from plugin class"""
        # Try to get metadata from instance method
        try:
            temp_instance = plugin_class()
            return temp_instance.get_metadata()
        except Exception:
            pass
        
        # Fall back to class attributes
        return PluginMetadata(
            name=getattr(plugin_class, '__plugin_name__', plugin_class.__name__),
            version=getattr(plugin_class, '__version__', '1.0.0'),
            description=getattr(plugin_class, '__doc__', '').strip(),
            author=getattr(plugin_class, '__author__', 'Unknown'),
            plugin_type=getattr(plugin_class, '__plugin_type__', PluginType.CUSTOM)
        )
    
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if all dependencies are available"""
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                logger.warning(f"Missing dependency: {dep}")
                return False
        return True
    
    def _is_safe_file(self, file_path: Path) -> bool:
        """Check if file is safe to load (basic security check)"""
        try:
            content = file_path.read_text()
            
            # Check for dangerous patterns
            dangerous_patterns = [
                "__import__", "exec(", "eval(", "compile(",
                "subprocess", "os.system", "os.popen",
                "open(", "file(", "__file__", "__builtins__"
            ]
            
            for pattern in dangerous_patterns:
                if pattern in content:
                    logger.warning(f"Potentially dangerous code in plugin: {pattern}")
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def activate_plugin(self, plugin_name: str) -> bool:
        """Activate a loaded plugin"""
        if plugin_name not in self.plugins:
            logger.error(f"Plugin not found: {plugin_name}")
            return False
        
        plugin_info = self.plugins[plugin_name]
        
        if plugin_info.status == PluginStatus.ACTIVE:
            return True  # Already active
        
        if plugin_info.status == PluginStatus.ERROR:
            logger.error(f"Cannot activate plugin in error state: {plugin_name}")
            return False
        
        try:
            if plugin_info.instance and hasattr(plugin_info.instance, 'activate'):
                success = await plugin_info.instance.activate()
                if not success:
                    raise PluginError("Plugin activation failed")
            
            plugin_info.status = PluginStatus.ACTIVE
            plugin_info.activated_at = time.time()
            
            # Register hooks if plugin has them
            self._register_plugin_hooks(plugin_name, plugin_info.instance)
            
            logger.info(f"Activated plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate plugin {plugin_name}: {e}")
            plugin_info.status = PluginStatus.ERROR
            plugin_info.error_message = str(e)
            return False
    
    async def deactivate_plugin(self, plugin_name: str) -> bool:
        """Deactivate an active plugin"""
        if plugin_name not in self.plugins:
            return False
        
        plugin_info = self.plugins[plugin_name]
        
        if plugin_info.status != PluginStatus.ACTIVE:
            return True  # Already inactive
        
        try:
            if plugin_info.instance and hasattr(plugin_info.instance, 'deactivate'):
                success = await plugin_info.instance.deactivate()
                if not success:
                    logger.warning(f"Plugin deactivation returned False: {plugin_name}")
            
            plugin_info.status = PluginStatus.INACTIVE
            
            # Unregister hooks
            self._unregister_plugin_hooks(plugin_name)
            
            logger.info(f"Deactivated plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate plugin {plugin_name}: {e}")
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Completely unload a plugin"""
        if plugin_name not in self.plugins:
            return False
        
        plugin_info = self.plugins[plugin_name]
        
        try:
            # Deactivate first
            if plugin_info.status == PluginStatus.ACTIVE:
                await self.deactivate_plugin(plugin_name)
            
            # Cleanup
            if plugin_info.instance and hasattr(plugin_info.instance, 'cleanup'):
                await plugin_info.instance.cleanup()
            
            # Remove from storage
            self.plugin_types[plugin_info.metadata.plugin_type].remove(plugin_name)
            del self.plugins[plugin_name]
            
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def _register_plugin_hooks(self, plugin_name: str, plugin_instance: BasePlugin):
        """Register plugin hooks"""
        # Look for hook methods
        for method_name in dir(plugin_instance):
            if method_name.startswith('hook_'):
                hook_name = method_name[5:]  # Remove 'hook_' prefix
                method = getattr(plugin_instance, method_name)
                
                if callable(method):
                    if hook_name not in self.plugin_hooks:
                        self.plugin_hooks[hook_name] = []
                    
                    self.plugin_hooks[hook_name].append(method)
                    logger.debug(f"Registered hook {hook_name} from plugin {plugin_name}")
    
    def _unregister_plugin_hooks(self, plugin_name: str):
        """Unregister plugin hooks"""
        plugin_info = self.plugins.get(plugin_name)
        if not plugin_info or not plugin_info.instance:
            return
        
        # Remove hooks from this plugin
        for hook_name, hooks in list(self.plugin_hooks.items()):
            hooks_to_remove = []
            for hook in hooks:
                if hasattr(hook, '__self__') and hook.__self__ == plugin_info.instance:
                    hooks_to_remove.append(hook)
            
            for hook in hooks_to_remove:
                hooks.remove(hook)
            
            if not hooks:
                del self.plugin_hooks[hook_name]
    
    async def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all registered hooks for an event"""
        results = []
        
        if hook_name not in self.plugin_hooks:
            return results
        
        for hook in self.plugin_hooks[hook_name]:
            try:
                if asyncio.iscoroutinefunction(hook):
                    result = await hook(*args, **kwargs)
                else:
                    result = hook(*args, **kwargs)
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Hook {hook_name} failed: {e}")
                results.append({"error": str(e)})
        
        return results
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[str]:
        """Get all plugins of a specific type"""
        return self.plugin_types[plugin_type].copy()
    
    def get_active_plugins(self) -> List[str]:
        """Get all active plugins"""
        return [
            name for name, info in self.plugins.items() 
            if info.status == PluginStatus.ACTIVE
        ]
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed plugin information"""
        if plugin_name not in self.plugins:
            return None
        
        plugin_info = self.plugins[plugin_name]
        
        return {
            "name": plugin_name,
            "metadata": asdict(plugin_info.metadata),
            "status": plugin_info.status.value,
            "loaded_at": plugin_info.loaded_at,
            "activated_at": plugin_info.activated_at,
            "error_message": plugin_info.error_message,
            "usage_stats": plugin_info.usage_stats,
            "health": plugin_info.instance.get_health_info() if plugin_info.instance else None
        }
    
    def get_all_plugins_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information for all plugins"""
        return {
            name: self.get_plugin_info(name) 
            for name in self.plugins.keys()
        }
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin"""
        if plugin_name not in self.plugins:
            return False
        
        plugin_info = self.plugins[plugin_name]
        file_path = Path(plugin_info.module_path)
        
        # Unload current plugin
        await self.unload_plugin(plugin_name)
        
        # Load again
        return await self.load_plugin_from_file(file_path, plugin_name)
    
    async def call_plugin_method(self, plugin_name: str, method_name: str, 
                                *args, **kwargs) -> Any:
        """Call a method on a specific plugin"""
        if plugin_name not in self.plugins:
            raise PluginError(f"Plugin not found: {plugin_name}")
        
        plugin_info = self.plugins[plugin_name]
        
        if plugin_info.status != PluginStatus.ACTIVE:
            raise PluginError(f"Plugin not active: {plugin_name}")
        
        if not plugin_info.instance:
            raise PluginError(f"Plugin instance not available: {plugin_name}")
        
        if not hasattr(plugin_info.instance, method_name):
            raise PluginError(f"Method not found: {method_name}")
        
        method = getattr(plugin_info.instance, method_name)
        
        try:
            # Track usage
            plugin_info.usage_stats[method_name] = plugin_info.usage_stats.get(method_name, 0) + 1
            
            if asyncio.iscoroutinefunction(method):
                return await method(*args, **kwargs)
            else:
                return method(*args, **kwargs)
                
        except Exception as e:
            logger.error(f"Plugin method call failed {plugin_name}.{method_name}: {e}")
            raise PluginError(f"Plugin method failed: {e}")
    
    def install_plugin_from_config(self, config: Dict[str, Any]) -> bool:
        """Install plugin from configuration"""
        try:
            plugin_name = config.get("name")
            if not plugin_name:
                raise PluginError("Plugin name required")
            
            # Create plugin info from config
            metadata = PluginMetadata(**config.get("metadata", {}))
            
            plugin_info = PluginInfo(
                metadata=metadata,
                module_path=config.get("module_path", ""),
                class_name=config.get("class_name", ""),
                config=config.get("config", {})
            )
            
            self.plugins[plugin_name] = plugin_info
            self.plugin_types[metadata.plugin_type].append(plugin_name)
            
            logger.info(f"Installed plugin from config: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install plugin from config: {e}")
            return False
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get plugin system statistics"""
        status_counts = {}
        for status in PluginStatus:
            status_counts[status.value] = sum(
                1 for p in self.plugins.values() if p.status == status
            )
        
        type_counts = {}
        for ptype in PluginType:
            type_counts[ptype.value] = len(self.plugin_types[ptype])
        
        return {
            "total_plugins": len(self.plugins),
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "total_hooks": len(self.plugin_hooks),
            "plugin_directories": [str(d) for d in self.plugin_dirs],
            "auto_load_enabled": self.auto_load,
            "sandbox_enabled": self.sandbox_enabled
        }
    
    async def health_check_all_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Run health checks on all plugins"""
        health_results = {}
        
        for plugin_name, plugin_info in self.plugins.items():
            if plugin_info.instance and plugin_info.status == PluginStatus.ACTIVE:
                try:
                    health_info = plugin_info.instance.get_health_info()
                    health_results[plugin_name] = health_info
                except Exception as e:
                    health_results[plugin_name] = {
                        "status": "error",
                        "error": str(e)
                    }
            else:
                health_results[plugin_name] = {
                    "status": "inactive"
                }
        
        return health_results
    
    def export_plugin_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Export plugin configuration"""
        if plugin_name not in self.plugins:
            return None
        
        plugin_info = self.plugins[plugin_name]
        
        return {
            "name": plugin_name,
            "metadata": asdict(plugin_info.metadata),
            "module_path": plugin_info.module_path,
            "class_name": plugin_info.class_name,
            "config": plugin_info.config,
            "status": plugin_info.status.value
        }
    
    def import_plugin_config(self, config: Dict[str, Any]) -> bool:
        """Import plugin configuration"""
        return self.install_plugin_from_config(config)
    
    async def cleanup_all_plugins(self):
        """Cleanup all plugins"""
        for plugin_name in list(self.plugins.keys()):
            try:
                await self.unload_plugin(plugin_name)
            except Exception as e:
                logger.error(f"Failed to cleanup plugin {plugin_name}: {e}")
        
        logger.info("All plugins cleaned up")

# Example plugins

class TextEnhancerPlugin(ContentProcessorPlugin):
    """Example text enhancement plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Text Enhancer",
            version="1.0.0",
            description="Enhances text content with better formatting and style",
            author="Creator Team",
            plugin_type=PluginType.CONTENT_PROCESSOR,
            tags=["text", "enhancement", "formatting"]
        )
    
    async def process_content(self, content: str, **kwargs) -> Dict[str, Any]:
        # Simple text enhancement example
        enhanced = content.strip()
        
        # Capitalize sentences
        sentences = enhanced.split('. ')
        enhanced = '. '.join(s.capitalize() for s in sentences)
        
        # Add formatting
        style = kwargs.get('style', 'professional')
        if style == 'professional':
            enhanced = enhanced.replace('!', '.')
        
        return {
            "success": True,
            "original_content": content,
            "enhanced_content": enhanced,
            "enhancements_applied": ["capitalization", "sentence_formatting"]
        }
    
    def get_processing_types(self) -> List[str]:
        return ["enhance", "format", "style"]

class CustomValidatorPlugin(ValidatorPlugin):
    """Example custom validator plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Custom Validator",
            version="1.0.0",
            description="Custom content validation rules",
            author="Creator Team",
            plugin_type=PluginType.VALIDATOR,
            tags=["validation", "content", "quality"]
        )
    
    async def validate_content(self, content: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        
        # Check length
        min_length = rules.get('min_length', 0)
        max_length = rules.get('max_length', 10000)
        
        if len(content) < min_length:
            issues.append(f"Content too short (minimum {min_length} characters)")
        
        if len(content) > max_length:
            issues.append(f"Content too long (maximum {max_length} characters)")
        
        # Check for required words
        required_words = rules.get('required_words', [])
        for word in required_words:
            if word.lower() not in content.lower():
                issues.append(f"Missing required word: {word}")
        
        # Check for banned words
        banned_words = rules.get('banned_words', [])
        for word in banned_words:
            if word.lower() in content.lower():
                issues.append(f"Contains banned word: {word}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "content_length": len(content),
            "word_count": len(content.split())
        }
    
    def get_validation_rules(self) -> Dict[str, Any]:
        return {
            "min_length": "Minimum content length",
            "max_length": "Maximum content length",
            "required_words": "List of required words",
            "banned_words": "List of banned words"
        }

# Exception classes
class PluginError(CreatorError):
    """Plugin-specific error"""
    pass
