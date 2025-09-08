"""
Creator v1 (CRT4) - Utilities and Tools
Additional utilities for system management, migration, and development
"""

import asyncio
import json
import csv
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import yaml
import hashlib
import subprocess
import sys

from umbra.core.config import UmbraConfig
from umbra.ai.agent import UmbraAIAgent
from umbra.modules.creator import create_creator_system, CreatorV1System
from umbra.modules.creator.errors import CreatorError

logger = logging.getLogger(__name__)

class SystemMigrator:
    """System migration and upgrade utilities"""
    
    def __init__(self, source_version: str = "0.9", target_version: str = "1.0"):
        self.source_version = source_version
        self.target_version = target_version
        self.migration_log = []
    
    def migrate_configuration(self, old_config_path: str, new_config_path: str) -> bool:
        """Migrate configuration from older version"""
        try:
            # Load old configuration
            old_config_file = Path(old_config_path)
            if not old_config_file.exists():
                raise FileNotFoundError(f"Source config not found: {old_config_path}")
            
            with open(old_config_file, 'r') as f:
                if old_config_file.suffix in ['.yaml', '.yml']:
                    old_config = yaml.safe_load(f)
                else:
                    old_config = json.load(f)
            
            # Migrate configuration keys
            new_config = self._migrate_config_keys(old_config)
            
            # Validate new configuration
            validation_errors = self._validate_migrated_config(new_config)
            if validation_errors:
                self.migration_log.extend(validation_errors)
                logger.warning(f"Configuration validation issues: {len(validation_errors)}")
            
            # Save new configuration
            new_config_file = Path(new_config_path)
            new_config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(new_config_file, 'w') as f:
                if new_config_file.suffix in ['.yaml', '.yml']:
                    yaml.dump(new_config, f, default_flow_style=False)
                else:
                    json.dump(new_config, f, indent=2, default=str)
            
            self.migration_log.append(f"✅ Configuration migrated: {old_config_path} -> {new_config_path}")
            return True
            
        except Exception as e:
            error_msg = f"❌ Configuration migration failed: {e}"
            self.migration_log.append(error_msg)
            logger.error(error_msg)
            return False
    
    def _migrate_config_keys(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate configuration keys to new format"""
        new_config = {}
        
        # Key mappings from old to new
        key_mappings = {
            # Old -> New key mappings
            "CREATOR_ENABLED": "CREATOR_V1_ENABLED",
            "CREATOR_DEBUG": "CREATOR_V1_DEBUG",
            "AI_PROVIDER_OPENAI_KEY": "CREATOR_OPENAI_API_KEY",
            "AI_PROVIDER_ANTHROPIC_KEY": "CREATOR_ANTHROPIC_API_KEY",
            "CACHE_ENABLED": "CREATOR_CACHE_ENABLED",
            "CACHE_TTL": "CREATOR_CACHE_DEFAULT_TTL_SECONDS",
            "ANALYTICS_ENABLED": "CREATOR_ANALYTICS_ENABLED",
            "RATE_LIMIT_ENABLED": "CREATOR_RATE_LIMITING_ENABLED",
            "RATE_LIMIT_REQUESTS": "CREATOR_USER_REQUESTS_PER_MINUTE",
        }
        
        # Migrate mapped keys
        for old_key, new_key in key_mappings.items():
            if old_key in old_config:
                new_config[new_key] = old_config[old_key]
                self.migration_log.append(f"🔄 Migrated key: {old_key} -> {new_key}")
        
        # Copy keys that remain the same
        for key, value in old_config.items():
            if key.startswith("CREATOR_") and key not in key_mappings:
                new_config[key] = value
        
        # Add new default values for v1 features
        new_defaults = {
            "CREATOR_HEALTH_MONITORING_ENABLED": True,
            "CREATOR_BATCHING_ENABLED": True,
            "CREATOR_WORKFLOW_MAX_CONCURRENT": 10,
            "CREATOR_PLUGIN_AUTO_LOAD": True,
            "CREATOR_SECURITY_ENABLED": False,  # Conservative default
        }
        
        for key, default_value in new_defaults.items():
            if key not in new_config:
                new_config[key] = default_value
                self.migration_log.append(f"➕ Added new key: {key} = {default_value}")
        
        return new_config
    
    def _validate_migrated_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate migrated configuration"""
        errors = []
        
        # Required keys check
        required_keys = [
            "CREATOR_V1_ENABLED",
            "CREATOR_OPENAI_API_KEY",
        ]
        
        for key in required_keys:
            if key not in config:
                errors.append(f"Missing required key: {key}")
            elif not config[key]:
                errors.append(f"Empty required key: {key}")
        
        # Type validation
        type_checks = {
            "CREATOR_V1_ENABLED": bool,
            "CREATOR_MAX_OUTPUT_TOKENS": int,
            "CREATOR_CACHE_DEFAULT_TTL_SECONDS": int,
            "CREATOR_USER_REQUESTS_PER_MINUTE": int,
        }
        
        for key, expected_type in type_checks.items():
            if key in config and not isinstance(config[key], expected_type):
                errors.append(f"Invalid type for {key}: expected {expected_type.__name__}")
        
        return errors
    
    def migrate_data(self, source_dir: str, target_dir: str) -> bool:
        """Migrate data files"""
        try:
            source_path = Path(source_dir)
            target_path = Path(target_dir)
            
            if not source_path.exists():
                raise FileNotFoundError(f"Source directory not found: {source_dir}")
            
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Copy analytics data
            analytics_source = source_path / "analytics"
            if analytics_source.exists():
                analytics_target = target_path / "analytics"
                shutil.copytree(analytics_source, analytics_target, dirs_exist_ok=True)
                self.migration_log.append("✅ Migrated analytics data")
            
            # Copy cache data (if exists)
            cache_source = source_path / "cache"
            if cache_source.exists():
                cache_target = target_path / "cache"
                shutil.copytree(cache_source, cache_target, dirs_exist_ok=True)
                self.migration_log.append("✅ Migrated cache data")
            
            # Copy templates
            templates_source = source_path / "templates"
            if templates_source.exists():
                templates_target = target_path / "templates"
                shutil.copytree(templates_source, templates_target, dirs_exist_ok=True)
                self.migration_log.append("✅ Migrated templates")
            
            return True
            
        except Exception as e:
            error_msg = f"❌ Data migration failed: {e}"
            self.migration_log.append(error_msg)
            logger.error(error_msg)
            return False
    
    def generate_migration_report(self, output_path: str) -> bool:
        """Generate migration report"""
        try:
            report = {
                "migration_info": {
                    "source_version": self.source_version,
                    "target_version": self.target_version,
                    "migration_date": datetime.now().isoformat(),
                    "total_steps": len(self.migration_log)
                },
                "migration_log": self.migration_log,
                "summary": {
                    "successful_steps": len([log for log in self.migration_log if log.startswith("✅")]),
                    "failed_steps": len([log for log in self.migration_log if log.startswith("❌")]),
                    "warnings": len([log for log in self.migration_log if log.startswith("⚠️")])
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate migration report: {e}")
            return False

class SystemBackup:
    """System backup and restore utilities"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, system_data_dir: str, include_cache: bool = False) -> str:
        """Create system backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"creator_v1_backup_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                system_path = Path(system_data_dir)
                
                if system_path.exists():
                    for file_path in system_path.rglob('*'):
                        if file_path.is_file():
                            # Skip cache files unless requested
                            if not include_cache and 'cache' in str(file_path):
                                continue
                            
                            # Skip temporary files
                            if file_path.suffix in ['.tmp', '.lock', '.pid']:
                                continue
                            
                            # Add file to backup
                            arcname = file_path.relative_to(system_path)
                            backup_zip.write(file_path, arcname)
                
                # Add metadata
                metadata = {
                    "backup_date": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "include_cache": include_cache,
                    "system_data_dir": str(system_path)
                }
                
                backup_zip.writestr("backup_metadata.json", 
                                  json.dumps(metadata, indent=2))
            
            logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise
    
    def restore_backup(self, backup_path: str, restore_dir: str, 
                      verify_checksum: bool = True) -> bool:
        """Restore from backup"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            restore_path = Path(restore_dir)
            restore_path.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(backup_file, 'r') as backup_zip:
                # Extract metadata
                metadata_content = backup_zip.read("backup_metadata.json")
                metadata = json.loads(metadata_content)
                
                logger.info(f"Restoring backup from {metadata['backup_date']}")
                
                # Extract all files
                backup_zip.extractall(restore_path)
                
                # Verify if requested
                if verify_checksum:
                    if not self._verify_backup_integrity(backup_zip, restore_path):
                        logger.warning("Backup integrity verification failed")
                        return False
            
            logger.info(f"Backup restored to: {restore_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return False
    
    def _verify_backup_integrity(self, backup_zip: zipfile.ZipFile, 
                               restore_path: Path) -> bool:
        """Verify backup integrity"""
        try:
            for info in backup_zip.infolist():
                if info.filename == "backup_metadata.json":
                    continue
                
                extracted_file = restore_path / info.filename
                if not extracted_file.exists():
                    return False
                
                # Verify file size
                if extracted_file.stat().st_size != info.file_size:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("creator_v1_backup_*.zip"):
            try:
                with zipfile.ZipFile(backup_file, 'r') as backup_zip:
                    metadata_content = backup_zip.read("backup_metadata.json")
                    metadata = json.loads(metadata_content)
                    
                    backups.append({
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "date": metadata.get("backup_date"),
                        "version": metadata.get("version"),
                        "size_mb": backup_file.stat().st_size / (1024 * 1024),
                        "include_cache": metadata.get("include_cache", False)
                    })
            
            except Exception as e:
                logger.warning(f"Could not read backup metadata from {backup_file}: {e}")
        
        return sorted(backups, key=lambda x: x["date"], reverse=True)

class DataExporter:
    """Data export utilities"""
    
    def __init__(self, creator_system: CreatorV1System):
        self.creator_system = creator_system
    
    async def export_analytics(self, output_dir: str, format: str = "json") -> bool:
        """Export analytics data"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            analytics = self.creator_system.get_component("analytics")
            if not analytics:
                logger.error("Analytics component not available")
                return False
            
            # Export daily stats
            daily_stats = analytics.get_daily_stats()
            action_stats = analytics.get_action_stats()
            
            export_data = {
                "export_date": datetime.now().isoformat(),
                "daily_stats": daily_stats,
                "action_stats": action_stats
            }
            
            if format == "json":
                output_file = output_path / "analytics_export.json"
                with open(output_file, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            
            elif format == "csv":
                # Export action stats as CSV
                output_file = output_path / "action_stats.csv"
                with open(output_file, 'w', newline='') as csvfile:
                    if action_stats:
                        fieldnames = ["action"] + list(next(iter(action_stats.values())).keys())
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        for action, stats in action_stats.items():
                            row = {"action": action, **stats}
                            writer.writerow(row)
            
            logger.info(f"Analytics exported to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Analytics export failed: {e}")
            return False
    
    async def export_metrics(self, output_dir: str, days: int = 7) -> bool:
        """Export metrics data"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            advanced_metrics = self.creator_system.get_component("advanced_metrics")
            if not advanced_metrics:
                logger.error("Advanced metrics component not available")
                return False
            
            # Generate comprehensive report
            report_data = advanced_metrics.generate_report(
                "system_metrics_export",
                {"time_range": f"last_{days}d"}
            )
            
            # Export as JSON
            output_file = output_path / f"metrics_export_{days}d.json"
            with open(output_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Metrics exported to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Metrics export failed: {e}")
            return False
    
    async def export_configuration(self, output_dir: str) -> bool:
        """Export system configuration"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            dynamic_config = self.creator_system.get_component("dynamic_config")
            if not dynamic_config:
                logger.error("Dynamic config component not available")
                return False
            
            # Export configuration
            config_data = dynamic_config.export_config(include_sensitive=False)
            
            # Add export metadata
            export_data = {
                "export_date": datetime.now().isoformat(),
                "version": "1.0.0",
                "configuration": config_data
            }
            
            # Save as JSON
            json_file = output_path / "configuration_export.json"
            with open(json_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            # Save as YAML
            yaml_file = output_path / "configuration_export.yaml"
            with open(yaml_file, 'w') as f:
                yaml.dump(export_data, f, default_flow_style=False)
            
            logger.info(f"Configuration exported to: {json_file} and {yaml_file}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration export failed: {e}")
            return False

class DevelopmentTools:
    """Development and debugging tools"""
    
    @staticmethod
    def generate_test_data(output_dir: str, num_requests: int = 100) -> bool:
        """Generate test data for development"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate test requests
            test_requests = []
            topics = [
                "Artificial Intelligence trends",
                "Sustainable technology",
                "Remote work benefits",
                "Digital transformation",
                "Cloud computing advantages",
                "Cybersecurity best practices",
                "Data science applications",
                "Mobile app development",
                "E-commerce strategies",
                "Social media marketing"
            ]
            
            platforms = ["twitter", "linkedin", "instagram", "facebook"]
            tones = ["professional", "casual", "friendly", "creative"]
            
            import random
            
            for i in range(num_requests):
                request = {
                    "id": f"test_request_{i+1}",
                    "action": "generate_post",
                    "topic": random.choice(topics),
                    "platform": random.choice(platforms),
                    "tone": random.choice(tones),
                    "timestamp": datetime.now().isoformat()
                }
                test_requests.append(request)
            
            # Save test data
            test_file = output_path / "test_requests.json"
            with open(test_file, 'w') as f:
                json.dump(test_requests, f, indent=2)
            
            logger.info(f"Generated {num_requests} test requests: {test_file}")
            return True
            
        except Exception as e:
            logger.error(f"Test data generation failed: {e}")
            return False
    
    @staticmethod
    def validate_system_integrity(system_dir: str) -> Dict[str, Any]:
        """Validate system file integrity"""
        results = {
            "valid": True,
            "files_checked": 0,
            "issues": []
        }
        
        try:
            system_path = Path(system_dir)
            if not system_path.exists():
                results["valid"] = False
                results["issues"].append(f"System directory not found: {system_dir}")
                return results
            
            # Check required files
            required_files = [
                "__init__.py",
                "service.py",
                "analytics.py",
                "cache.py",
                "health.py"
            ]
            
            for required_file in required_files:
                file_path = system_path / required_file
                if not file_path.exists():
                    results["valid"] = False
                    results["issues"].append(f"Missing required file: {required_file}")
                else:
                    results["files_checked"] += 1
            
            # Check Python syntax
            for py_file in system_path.glob("*.py"):
                try:
                    with open(py_file, 'r') as f:
                        compile(f.read(), str(py_file), 'exec')
                    results["files_checked"] += 1
                except SyntaxError as e:
                    results["valid"] = False
                    results["issues"].append(f"Syntax error in {py_file.name}: {e}")
            
            return results
            
        except Exception as e:
            results["valid"] = False
            results["issues"].append(f"Integrity validation failed: {e}")
            return results
    
    @staticmethod
    def run_system_diagnostics() -> Dict[str, Any]:
        """Run comprehensive system diagnostics"""
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "system_checks": {},
            "dependency_checks": {},
            "performance_checks": {}
        }
        
        # Check Python version
        if sys.version_info < (3, 8):
            diagnostics["system_checks"]["python_version"] = {
                "status": "error",
                "message": f"Python 3.8+ required, found {sys.version}"
            }
        else:
            diagnostics["system_checks"]["python_version"] = {
                "status": "ok",
                "message": f"Python version: {sys.version}"
            }
        
        # Check required dependencies
        required_packages = [
            "fastapi", "uvicorn", "click", "pydantic", 
            "asyncio", "psutil", "cryptography"
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                diagnostics["dependency_checks"][package] = {
                    "status": "ok",
                    "message": "Available"
                }
            except ImportError:
                diagnostics["dependency_checks"][package] = {
                    "status": "error",
                    "message": "Not installed"
                }
        
        # Performance checks
        try:
            import psutil
            diagnostics["performance_checks"]["memory"] = {
                "status": "ok" if psutil.virtual_memory().percent < 80 else "warning",
                "value": f"{psutil.virtual_memory().percent:.1f}%"
            }
            
            diagnostics["performance_checks"]["cpu"] = {
                "status": "ok" if psutil.cpu_percent(interval=1) < 80 else "warning",
                "value": f"{psutil.cpu_percent(interval=1):.1f}%"
            }
        except ImportError:
            diagnostics["performance_checks"]["system_resources"] = {
                "status": "warning",
                "message": "psutil not available"
            }
        
        return diagnostics

class MaintenanceScheduler:
    """Automated maintenance tasks scheduler"""
    
    def __init__(self, creator_system: CreatorV1System):
        self.creator_system = creator_system
        self.maintenance_tasks = []
        self.running = False
    
    def add_task(self, name: str, function: callable, interval_hours: int):
        """Add maintenance task"""
        self.maintenance_tasks.append({
            "name": name,
            "function": function,
            "interval_hours": interval_hours,
            "last_run": None,
            "next_run": datetime.now() + timedelta(hours=interval_hours)
        })
    
    async def start_scheduler(self):
        """Start maintenance scheduler"""
        self.running = True
        
        # Add default tasks
        self.add_task("cache_cleanup", self._cleanup_cache, 6)
        self.add_task("metrics_aggregation", self._aggregate_metrics, 1)
        self.add_task("health_check", self._system_health_check, 0.5)
        self.add_task("log_rotation", self._rotate_logs, 24)
        
        logger.info("Maintenance scheduler started")
        
        while self.running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_time = datetime.now()
                
                for task in self.maintenance_tasks:
                    if current_time >= task["next_run"]:
                        logger.info(f"Running maintenance task: {task['name']}")
                        
                        try:
                            if asyncio.iscoroutinefunction(task["function"]):
                                await task["function"]()
                            else:
                                task["function"]()
                            
                            task["last_run"] = current_time
                            task["next_run"] = current_time + timedelta(hours=task["interval_hours"])
                            
                            logger.info(f"Completed maintenance task: {task['name']}")
                            
                        except Exception as e:
                            logger.error(f"Maintenance task {task['name']} failed: {e}")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Maintenance scheduler error: {e}")
    
    def stop_scheduler(self):
        """Stop maintenance scheduler"""
        self.running = False
        logger.info("Maintenance scheduler stopped")
    
    async def _cleanup_cache(self):
        """Cache cleanup task"""
        cache = self.creator_system.get_component("cache")
        if cache:
            await cache.optimize()
    
    async def _aggregate_metrics(self):
        """Metrics aggregation task"""
        advanced_metrics = self.creator_system.get_component("advanced_metrics")
        if advanced_metrics:
            # Metrics are automatically aggregated by the component
            pass
    
    async def _system_health_check(self):
        """System health check task"""
        try:
            health_report = await self.creator_system.health_check()
            overall_status = health_report.get("overall_health", {}).get("status", "unknown")
            
            if overall_status in ["critical", "degraded"]:
                logger.warning(f"System health status: {overall_status}")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def _rotate_logs(self):
        """Log rotation task"""
        try:
            log_dir = Path("logs")
            if log_dir.exists():
                # Compress old log files
                for log_file in log_dir.glob("*.log"):
                    if log_file.stat().st_size > 50 * 1024 * 1024:  # 50MB
                        compressed_name = f"{log_file.stem}_{datetime.now().strftime('%Y%m%d')}.gz"
                        # In a real implementation, would compress the file
                        logger.info(f"Log file {log_file.name} should be rotated")
        except Exception as e:
            logger.error(f"Log rotation failed: {e}")

# Utility functions
def calculate_file_hash(file_path: str) -> str:
    """Calculate file hash for integrity verification"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def check_disk_space(path: str, min_space_gb: float = 1.0) -> bool:
    """Check available disk space"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024**3)
        return free_gb >= min_space_gb
    except Exception:
        return False

def cleanup_temp_files(temp_dir: str = "/tmp", max_age_hours: int = 24) -> int:
    """Clean up temporary files"""
    cleaned_count = 0
    try:
        temp_path = Path(temp_dir)
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for temp_file in temp_path.glob("creator_*"):
            if temp_file.is_file():
                file_time = datetime.fromtimestamp(temp_file.stat().st_mtime)
                if file_time < cutoff_time:
                    temp_file.unlink()
                    cleaned_count += 1
    
    except Exception as e:
        logger.error(f"Temp cleanup failed: {e}")
    
    return cleaned_count

def create_system_report(creator_system: CreatorV1System, output_path: str) -> bool:
    """Create comprehensive system report"""
    try:
        report = {
            "report_date": datetime.now().isoformat(),
            "system_version": "1.0.0",
            "system_status": creator_system.get_system_status(),
            "diagnostics": DevelopmentTools.run_system_diagnostics(),
            "component_details": {}
        }
        
        # Get detailed component information
        component_names = [
            "analytics", "cache", "security", "health_monitor",
            "advanced_metrics", "rate_limiter", "batching",
            "workflow_manager", "plugin_manager"
        ]
        
        for name in component_names:
            component = creator_system.get_component(name)
            if component:
                component_info = {"available": True}
                
                if hasattr(component, 'get_stats'):
                    try:
                        component_info["stats"] = component.get_stats()
                    except Exception:
                        component_info["stats_error"] = "Failed to retrieve stats"
                
                report["component_details"][name] = component_info
            else:
                report["component_details"][name] = {"available": False}
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"System report created: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"System report creation failed: {e}")
        return False

# Export all utilities
__all__ = [
    "SystemMigrator",
    "SystemBackup", 
    "DataExporter",
    "DevelopmentTools",
    "MaintenanceScheduler",
    "calculate_file_hash",
    "check_disk_space",
    "cleanup_temp_files",
    "create_system_report"
]
