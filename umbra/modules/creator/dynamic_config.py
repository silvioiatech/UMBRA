"""
Dynamic Configuration System - Runtime configuration management for Creator v1 (CRT4)
Allows hot-reloading of configuration without service restart
"""

import logging
import time
import asyncio
import json
import os
from typing import Dict, Any, List, Optional, Callable, Union, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
from pathlib import Path

from ...core.config import UmbraConfig
from .analytics import CreatorAnalytics
from .errors import CreatorError, ConfigurationError

logger = logging.getLogger(__name__)

class ConfigScope(Enum):
    """Configuration scope levels"""
    GLOBAL = "global"
    MODULE = "module"
    USER = "user"
    SESSION = "session"
    REQUEST = "request"

class ConfigType(Enum):
    """Configuration value types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    JSON = "json"

@dataclass
class ConfigRule:
    """Configuration validation rule"""
    key: str
    config_type: ConfigType
    required: bool = False
    default_value: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    description: str = ""
    sensitive: bool = False
    restart_required: bool = False

@dataclass
class ConfigChange:
    """Configuration change event"""
    key: str
    old_value: Any
    new_value: Any
    scope: ConfigScope
    changed_by: Optional[str]
    timestamp: float
    reason: str = ""

@dataclass
class ConfigProfile:
    """Configuration profile for different environments"""
    name: str
    description: str
    config_values: Dict[str, Any]
    created_at: float
    active: bool = False
    tags: List[str] = field(default_factory=list)

class DynamicConfig:
    """Dynamic configuration management system"""
    
    def __init__(self, config: UmbraConfig, analytics: Optional[CreatorAnalytics] = None):
        self.config = config
        self.analytics = analytics
        
        # Configuration storage
        self.values: Dict[str, Any] = {}
        self.overrides: Dict[ConfigScope, Dict[str, Any]] = {scope: {} for scope in ConfigScope}
        self.rules: Dict[str, ConfigRule] = {}
        self.profiles: Dict[str, ConfigProfile] = {}
        
        # Change tracking
        self.change_history: List[ConfigChange] = []
        self.watchers: Dict[str, List[Callable]] = {}
        self.lock = threading.RLock()
        
        # File watching
        self.config_files: Set[str] = set()
        self.file_watchers: Dict[str, float] = {}
        self.watch_enabled = config.get("CREATOR_CONFIG_WATCH_FILES", True)
        
        # Hot reload settings
        self.hot_reload_enabled = config.get("CREATOR_CONFIG_HOT_RELOAD", True)
        self.validation_enabled = config.get("CREATOR_CONFIG_VALIDATION", True)
        self.backup_enabled = config.get("CREATOR_CONFIG_BACKUP", True)
        
        # Initialize configuration rules
        self._initialize_config_rules()
        
        # Load initial configuration
        self._load_initial_config()
        
        # Start file watcher if enabled
        if self.watch_enabled:
            self.file_watcher_task = asyncio.create_task(self._file_watcher_loop())
        
        logger.info("Dynamic configuration system initialized")
    
    def _initialize_config_rules(self):
        """Initialize configuration validation rules"""
        
        # Core service rules
        self.rules.update({
            "CREATOR_MAX_OUTPUT_TOKENS": ConfigRule(
                key="CREATOR_MAX_OUTPUT_TOKENS",
                config_type=ConfigType.INTEGER,
                default_value=2000,
                min_value=100,
                max_value=50000,
                description="Maximum output tokens per request"
            ),
            
            "CREATOR_DEFAULT_TONE": ConfigRule(
                key="CREATOR_DEFAULT_TONE",
                config_type=ConfigType.STRING,
                default_value="professional",
                allowed_values=["professional", "casual", "friendly", "formal", "creative"],
                description="Default tone for content generation"
            ),
            
            "CREATOR_RATE_LIMIT_REQUESTS_PER_MINUTE": ConfigRule(
                key="CREATOR_RATE_LIMIT_REQUESTS_PER_MINUTE",
                config_type=ConfigType.INTEGER,
                default_value=60,
                min_value=1,
                max_value=10000,
                description="Rate limit for requests per minute"
            ),
            
            "CREATOR_CACHE_ENABLED": ConfigRule(
                key="CREATOR_CACHE_ENABLED",
                config_type=ConfigType.BOOLEAN,
                default_value=True,
                description="Enable/disable caching system"
            ),
            
            "CREATOR_CACHE_DEFAULT_TTL_SECONDS": ConfigRule(
                key="CREATOR_CACHE_DEFAULT_TTL_SECONDS",
                config_type=ConfigType.INTEGER,
                default_value=3600,
                min_value=60,
                max_value=86400,
                description="Default cache TTL in seconds"
            ),
            
            "CREATOR_ANALYTICS_ENABLED": ConfigRule(
                key="CREATOR_ANALYTICS_ENABLED",
                config_type=ConfigType.BOOLEAN,
                default_value=True,
                description="Enable/disable analytics collection"
            ),
            
            "CREATOR_HEALTH_MONITORING_ENABLED": ConfigRule(
                key="CREATOR_HEALTH_MONITORING_ENABLED",
                config_type=ConfigType.BOOLEAN,
                default_value=True,
                description="Enable/disable health monitoring"
            ),
            
            "CREATOR_BATCHING_ENABLED": ConfigRule(
                key="CREATOR_BATCHING_ENABLED",
                config_type=ConfigType.BOOLEAN,
                default_value=True,
                description="Enable/disable request batching"
            ),
            
            "CREATOR_WORKFLOW_MAX_CONCURRENT": ConfigRule(
                key="CREATOR_WORKFLOW_MAX_CONCURRENT",
                config_type=ConfigType.INTEGER,
                default_value=10,
                min_value=1,
                max_value=100,
                description="Maximum concurrent workflows"
            ),
            
            # Provider configuration
            "CREATOR_OPENAI_API_KEY": ConfigRule(
                key="CREATOR_OPENAI_API_KEY",
                config_type=ConfigType.STRING,
                sensitive=True,
                description="OpenAI API key"
            ),
            
            "CREATOR_STABILITY_API_KEY": ConfigRule(
                key="CREATOR_STABILITY_API_KEY",
                config_type=ConfigType.STRING,
                sensitive=True,
                description="Stability AI API key"
            ),
            
            "CREATOR_ELEVENLABS_API_KEY": ConfigRule(
                key="CREATOR_ELEVENLABS_API_KEY",
                config_type=ConfigType.STRING,
                sensitive=True,
                description="ElevenLabs API key"
            ),
            
            # Advanced settings
            "CREATOR_PROVIDER_TIMEOUT_SECONDS": ConfigRule(
                key="CREATOR_PROVIDER_TIMEOUT_SECONDS",
                config_type=ConfigType.INTEGER,
                default_value=60,
                min_value=10,
                max_value=300,
                description="Provider API timeout in seconds"
            ),
            
            "CREATOR_COST_ALERT_THRESHOLD_USD": ConfigRule(
                key="CREATOR_COST_ALERT_THRESHOLD_USD",
                config_type=ConfigType.FLOAT,
                default_value=100.0,
                min_value=1.0,
                max_value=10000.0,
                description="Cost alert threshold in USD"
            ),
            
            "CREATOR_FEATURE_FLAGS": ConfigRule(
                key="CREATOR_FEATURE_FLAGS",
                config_type=ConfigType.DICT,
                default_value={},
                description="Feature flags for experimental features"
            )
        })
    
    def _load_initial_config(self):
        """Load initial configuration from various sources"""
        # Load from base config
        for key, rule in self.rules.items():
            value = self.config.get(key, rule.default_value)
            if value is not None:
                self.values[key] = value
        
        # Load from environment variables
        for key in self.rules.keys():
            env_value = os.environ.get(key)
            if env_value is not None:
                try:
                    parsed_value = self._parse_env_value(env_value, self.rules[key])
                    self.values[key] = parsed_value
                except Exception as e:
                    logger.warning(f"Failed to parse environment variable {key}: {e}")
        
        # Load profiles
        self._load_config_profiles()
        
        logger.info(f"Loaded {len(self.values)} configuration values")
    
    def _parse_env_value(self, value: str, rule: ConfigRule) -> Any:
        """Parse environment variable value according to rule type"""
        if rule.config_type == ConfigType.STRING:
            return value
        elif rule.config_type == ConfigType.INTEGER:
            return int(value)
        elif rule.config_type == ConfigType.FLOAT:
            return float(value)
        elif rule.config_type == ConfigType.BOOLEAN:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif rule.config_type == ConfigType.LIST:
            return value.split(',')
        elif rule.config_type == ConfigType.DICT or rule.config_type == ConfigType.JSON:
            return json.loads(value)
        else:
            return value
    
    def get(self, key: str, default: Any = None, scope: ConfigScope = ConfigScope.GLOBAL,
           scope_id: Optional[str] = None) -> Any:
        """Get configuration value with scope precedence"""
        with self.lock:
            # Check scope-specific overrides in priority order
            scope_key = f"{scope_id}:{key}" if scope_id else key
            
            for check_scope in [ConfigScope.REQUEST, ConfigScope.SESSION, 
                              ConfigScope.USER, ConfigScope.MODULE, ConfigScope.GLOBAL]:
                if check_scope in self.overrides:
                    if scope_key in self.overrides[check_scope]:
                        return self.overrides[check_scope][scope_key]
                    if key in self.overrides[check_scope]:
                        return self.overrides[check_scope][key]
                
                if check_scope == scope:
                    break
            
            # Fall back to global value
            if key in self.values:
                return self.values[key]
            
            # Use rule default
            rule = self.rules.get(key)
            if rule and rule.default_value is not None:
                return rule.default_value
            
            return default
    
    def set(self, key: str, value: Any, scope: ConfigScope = ConfigScope.GLOBAL,
           scope_id: Optional[str] = None, changed_by: Optional[str] = None,
           reason: str = "", validate: bool = True) -> bool:
        """Set configuration value with validation"""
        with self.lock:
            try:
                # Validate if enabled
                if validate and self.validation_enabled:
                    self._validate_config_value(key, value)
                
                # Get current value for change tracking
                old_value = self.get(key, scope=scope, scope_id=scope_id)
                
                # Set value in appropriate scope
                if scope == ConfigScope.GLOBAL:
                    self.values[key] = value
                else:
                    scope_key = f"{scope_id}:{key}" if scope_id else key
                    self.overrides[scope][scope_key] = value
                
                # Track change
                change = ConfigChange(
                    key=key,
                    old_value=old_value,
                    new_value=value,
                    scope=scope,
                    changed_by=changed_by,
                    timestamp=time.time(),
                    reason=reason
                )
                
                self.change_history.append(change)
                
                # Limit change history
                if len(self.change_history) > 1000:
                    self.change_history = self.change_history[-500:]
                
                # Notify watchers
                self._notify_watchers(key, old_value, value)
                
                # Log change
                if not self.rules.get(key, ConfigRule(key, ConfigType.STRING)).sensitive:
                    logger.info(f"Configuration changed: {key} = {value} (scope: {scope.value})")
                else:
                    logger.info(f"Configuration changed: {key} = [SENSITIVE] (scope: {scope.value})")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to set configuration {key}: {e}")
                return False
    
    def _validate_config_value(self, key: str, value: Any) -> None:
        """Validate configuration value against rules"""
        rule = self.rules.get(key)
        if not rule:
            return  # No validation rule defined
        
        # Type validation
        if rule.config_type == ConfigType.INTEGER and not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ConfigurationError(f"Invalid integer value for {key}: {value}")
        
        elif rule.config_type == ConfigType.FLOAT and not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ConfigurationError(f"Invalid float value for {key}: {value}")
        
        elif rule.config_type == ConfigType.BOOLEAN and not isinstance(value, bool):
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes', 'on')
            else:
                raise ConfigurationError(f"Invalid boolean value for {key}: {value}")
        
        elif rule.config_type == ConfigType.LIST and not isinstance(value, list):
            raise ConfigurationError(f"Invalid list value for {key}: {value}")
        
        elif rule.config_type == ConfigType.DICT and not isinstance(value, dict):
            raise ConfigurationError(f"Invalid dict value for {key}: {value}")
        
        # Range validation
        if rule.min_value is not None and isinstance(value, (int, float)):
            if value < rule.min_value:
                raise ConfigurationError(f"Value {value} for {key} is below minimum {rule.min_value}")
        
        if rule.max_value is not None and isinstance(value, (int, float)):
            if value > rule.max_value:
                raise ConfigurationError(f"Value {value} for {key} is above maximum {rule.max_value}")
        
        # Allowed values validation
        if rule.allowed_values and value not in rule.allowed_values:
            raise ConfigurationError(f"Value {value} for {key} is not in allowed values: {rule.allowed_values}")
        
        # Pattern validation
        if rule.pattern and isinstance(value, str):
            import re
            if not re.match(rule.pattern, value):
                raise ConfigurationError(f"Value {value} for {key} does not match pattern {rule.pattern}")
    
    def add_watcher(self, key: str, callback: Callable[[str, Any, Any], None]) -> None:
        """Add configuration change watcher"""
        if key not in self.watchers:
            self.watchers[key] = []
        self.watchers[key].append(callback)
        logger.debug(f"Added watcher for configuration key: {key}")
    
    def remove_watcher(self, key: str, callback: Callable) -> bool:
        """Remove configuration change watcher"""
        if key in self.watchers and callback in self.watchers[key]:
            self.watchers[key].remove(callback)
            if not self.watchers[key]:
                del self.watchers[key]
            logger.debug(f"Removed watcher for configuration key: {key}")
            return True
        return False
    
    def _notify_watchers(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify watchers of configuration changes"""
        # Notify specific key watchers
        if key in self.watchers:
            for callback in self.watchers[key]:
                try:
                    callback(key, old_value, new_value)
                except Exception as e:
                    logger.error(f"Configuration watcher failed for {key}: {e}")
        
        # Notify wildcard watchers
        if "*" in self.watchers:
            for callback in self.watchers["*"]:
                try:
                    callback(key, old_value, new_value)
                except Exception as e:
                    logger.error(f"Wildcard configuration watcher failed: {e}")
    
    def create_profile(self, name: str, description: str = "", 
                      config_subset: Optional[Dict[str, Any]] = None,
                      tags: List[str] = None) -> bool:
        """Create configuration profile"""
        try:
            if config_subset is None:
                # Create profile from current configuration
                config_subset = self.values.copy()
            
            profile = ConfigProfile(
                name=name,
                description=description,
                config_values=config_subset,
                created_at=time.time(),
                tags=tags or []
            )
            
            self.profiles[name] = profile
            
            # Save profile to file if backup enabled
            if self.backup_enabled:
                self._save_profile_to_file(profile)
            
            logger.info(f"Created configuration profile: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create profile {name}: {e}")
            return False
    
    def apply_profile(self, name: str, scope: ConfigScope = ConfigScope.GLOBAL,
                     changed_by: Optional[str] = None) -> bool:
        """Apply configuration profile"""
        if name not in self.profiles:
            logger.error(f"Profile not found: {name}")
            return False
        
        try:
            profile = self.profiles[name]
            applied_count = 0
            
            for key, value in profile.config_values.items():
                if self.set(key, value, scope=scope, changed_by=changed_by, 
                          reason=f"Applied profile: {name}"):
                    applied_count += 1
            
            # Mark profile as active
            for p in self.profiles.values():
                p.active = False
            profile.active = True
            
            logger.info(f"Applied profile {name}: {applied_count} configuration values")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply profile {name}: {e}")
            return False
    
    def export_config(self, keys: Optional[List[str]] = None, 
                     include_sensitive: bool = False) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        exported = {}
        
        keys_to_export = keys or list(self.values.keys())
        
        for key in keys_to_export:
            rule = self.rules.get(key)
            
            # Skip sensitive values unless explicitly requested
            if rule and rule.sensitive and not include_sensitive:
                exported[key] = "[SENSITIVE]"
            else:
                exported[key] = self.get(key)
        
        return exported
    
    def import_config(self, config_dict: Dict[str, Any], 
                     scope: ConfigScope = ConfigScope.GLOBAL,
                     changed_by: Optional[str] = None,
                     validate: bool = True) -> Dict[str, bool]:
        """Import configuration from dictionary"""
        results = {}
        
        for key, value in config_dict.items():
            success = self.set(key, value, scope=scope, changed_by=changed_by,
                             reason="Imported configuration", validate=validate)
            results[key] = success
        
        return results
    
    def load_from_file(self, file_path: str, 
                      scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """Load configuration from file"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Configuration file not found: {file_path}")
                return False
            
            with open(path, 'r') as f:
                if path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    # Assume key=value format
                    config_data = {}
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                config_data[key.strip()] = value.strip()
            
            # Import configuration
            results = self.import_config(config_data, scope=scope, 
                                       changed_by="file_load")
            
            # Add to watched files
            if self.watch_enabled:
                self.config_files.add(file_path)
                self.file_watchers[file_path] = path.stat().st_mtime
            
            success_count = sum(1 for success in results.values() if success)
            logger.info(f"Loaded {success_count}/{len(results)} configuration values from {file_path}")
            
            return success_count == len(results)
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")
            return False
    
    def save_to_file(self, file_path: str, keys: Optional[List[str]] = None,
                    include_sensitive: bool = False) -> bool:
        """Save configuration to file"""
        try:
            config_data = self.export_config(keys=keys, include_sensitive=include_sensitive)
            
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                if path.suffix.lower() == '.json':
                    json.dump(config_data, f, indent=2, default=str)
                else:
                    # Save as key=value format
                    for key, value in config_data.items():
                        f.write(f"{key}={value}\n")
            
            logger.info(f"Saved configuration to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {file_path}: {e}")
            return False
    
    async def _file_watcher_loop(self):
        """Watch configuration files for changes"""
        while self.watch_enabled:
            try:
                for file_path in list(self.config_files):
                    try:
                        path = Path(file_path)
                        if path.exists():
                            current_mtime = path.stat().st_mtime
                            last_mtime = self.file_watchers.get(file_path, 0)
                            
                            if current_mtime > last_mtime:
                                logger.info(f"Configuration file changed: {file_path}")
                                
                                if self.hot_reload_enabled:
                                    success = self.load_from_file(file_path)
                                    if success:
                                        logger.info(f"Hot-reloaded configuration from {file_path}")
                                    else:
                                        logger.error(f"Failed to hot-reload configuration from {file_path}")
                                
                                self.file_watchers[file_path] = current_mtime
                        else:
                            # File was deleted
                            logger.warning(f"Configuration file removed: {file_path}")
                            self.config_files.discard(file_path)
                            self.file_watchers.pop(file_path, None)
                    
                    except Exception as e:
                        logger.error(f"Error watching file {file_path}: {e}")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"File watcher loop error: {e}")
                await asyncio.sleep(10)
    
    def _load_config_profiles(self):
        """Load configuration profiles from files"""
        profiles_dir = Path("config/profiles")
        if profiles_dir.exists():
            for profile_file in profiles_dir.glob("*.json"):
                try:
                    with open(profile_file, 'r') as f:
                        profile_data = json.load(f)
                    
                    profile = ConfigProfile(**profile_data)
                    self.profiles[profile.name] = profile
                    
                except Exception as e:
                    logger.error(f"Failed to load profile from {profile_file}: {e}")
    
    def _save_profile_to_file(self, profile: ConfigProfile):
        """Save profile to file"""
        try:
            profiles_dir = Path("config/profiles")
            profiles_dir.mkdir(parents=True, exist_ok=True)
            
            profile_file = profiles_dir / f"{profile.name}.json"
            with open(profile_file, 'w') as f:
                json.dump(asdict(profile), f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Failed to save profile {profile.name} to file: {e}")
    
    def get_change_history(self, key: Optional[str] = None, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        changes = self.change_history
        
        if key:
            changes = [c for c in changes if c.key == key]
        
        # Sort by timestamp, most recent first
        changes = sorted(changes, key=lambda c: c.timestamp, reverse=True)
        
        return [asdict(c) for c in changes[:limit]]
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get comprehensive configuration summary"""
        return {
            "total_values": len(self.values),
            "total_rules": len(self.rules),
            "total_profiles": len(self.profiles),
            "active_profile": next((p.name for p in self.profiles.values() if p.active), None),
            "watchers_count": sum(len(watchers) for watchers in self.watchers.values()),
            "watched_files": len(self.config_files),
            "recent_changes": len(self.change_history),
            "hot_reload_enabled": self.hot_reload_enabled,
            "validation_enabled": self.validation_enabled,
            "file_watching_enabled": self.watch_enabled,
            "scopes": {
                scope.value: len(overrides) 
                for scope, overrides in self.overrides.items()
            }
        }
    
    def validate_all_config(self) -> Dict[str, List[str]]:
        """Validate all current configuration values"""
        validation_errors = {}
        
        for key, value in self.values.items():
            try:
                self._validate_config_value(key, value)
            except ConfigurationError as e:
                if key not in validation_errors:
                    validation_errors[key] = []
                validation_errors[key].append(str(e))
        
        return validation_errors
    
    def reset_to_defaults(self, keys: Optional[List[str]] = None) -> Dict[str, bool]:
        """Reset configuration values to defaults"""
        results = {}
        keys_to_reset = keys or list(self.rules.keys())
        
        for key in keys_to_reset:
            rule = self.rules.get(key)
            if rule and rule.default_value is not None:
                success = self.set(key, rule.default_value, 
                                 reason="Reset to default", 
                                 changed_by="system")
                results[key] = success
            else:
                results[key] = False
        
        return results
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'file_watcher_task') and self.file_watcher_task and not self.file_watcher_task.done():
            self.file_watcher_task.cancel()

# Configuration context manager for temporary overrides
class ConfigOverride:
    """Context manager for temporary configuration overrides"""
    
    def __init__(self, dynamic_config: DynamicConfig, overrides: Dict[str, Any],
                 scope: ConfigScope = ConfigScope.REQUEST):
        self.dynamic_config = dynamic_config
        self.overrides = overrides
        self.scope = scope
        self.original_values = {}
    
    def __enter__(self):
        # Store original values
        for key in self.overrides:
            self.original_values[key] = self.dynamic_config.get(key, scope=self.scope)
        
        # Apply overrides
        for key, value in self.overrides.items():
            self.dynamic_config.set(key, value, scope=self.scope, 
                                  reason="Temporary override")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original values
        for key, original_value in self.original_values.items():
            if original_value is not None:
                self.dynamic_config.set(key, original_value, scope=self.scope,
                                      reason="Restore from override")

# Exception classes
class ConfigurationError(CreatorError):
    """Configuration-specific error"""
    pass
