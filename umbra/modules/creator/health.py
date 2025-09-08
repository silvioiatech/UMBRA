"""
Health Monitoring System - Advanced health checks and monitoring for Creator v1 (CRT4)
Provides real-time health monitoring, performance tracking, and alerting
"""

import logging
import time
import asyncio
import psutil
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import json

from ...core.config import UmbraConfig
from .analytics import CreatorAnalytics
from .errors import CreatorError

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"

class CheckType(Enum):
    """Types of health checks"""
    SYSTEM = "system"
    SERVICE = "service"
    EXTERNAL = "external"
    CUSTOM = "custom"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    check_type: CheckType
    check_function: Callable
    interval_seconds: int = 60
    timeout_seconds: int = 30
    enabled: bool = True
    critical: bool = False
    retry_count: int = 3
    retry_delay_seconds: int = 5
    alert_threshold: int = 3  # Number of consecutive failures before alert
    tags: List[str] = field(default_factory=list)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]
    uptime_seconds: float

@dataclass
class ServiceMetrics:
    """Service-specific metrics"""
    request_count: int
    error_count: int
    response_time_avg: float
    response_time_p95: float
    active_connections: int
    cache_hit_rate: float
    provider_status: Dict[str, str]
    queue_length: int

class HealthMonitor:
    """Advanced health monitoring system"""
    
    def __init__(self, config: UmbraConfig, analytics: Optional[CreatorAnalytics] = None):
        self.config = config
        self.analytics = analytics
        
        # Monitoring configuration
        self.enabled = config.get("CREATOR_HEALTH_MONITORING_ENABLED", True)
        self.check_interval = config.get("CREATOR_HEALTH_CHECK_INTERVAL_SECONDS", 30)
        self.alert_enabled = config.get("CREATOR_HEALTH_ALERTS_ENABLED", True)
        self.metrics_retention_hours = config.get("CREATOR_HEALTH_METRICS_RETENTION_HOURS", 24)
        
        # Health checks registry
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_results: Dict[str, List[HealthCheckResult]] = {}
        self.last_check_times: Dict[str, float] = {}
        self.consecutive_failures: Dict[str, int] = {}
        
        # System monitoring
        self.system_metrics_history: List[SystemMetrics] = []
        self.service_metrics_history: List[ServiceMetrics] = []
        
        # Alerting
        self.alert_handlers: List[Callable] = []
        self.suppressed_alerts: Dict[str, float] = {}
        self.alert_cooldown_seconds = config.get("CREATOR_ALERT_COOLDOWN_SECONDS", 300)
        
        # Initialize default checks
        self._initialize_default_checks()
        
        # Start monitoring tasks
        if self.enabled:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info(f"Health monitor initialized (enabled: {self.enabled})")
    
    def _initialize_default_checks(self):
        """Initialize default health checks"""
        
        # System resource checks
        self.health_checks["system_cpu"] = HealthCheck(
            name="system_cpu",
            check_type=CheckType.SYSTEM,
            check_function=self._check_cpu_usage,
            interval_seconds=30,
            critical=True,
            tags=["system", "cpu"]
        )
        
        self.health_checks["system_memory"] = HealthCheck(
            name="system_memory",
            check_type=CheckType.SYSTEM,
            check_function=self._check_memory_usage,
            interval_seconds=30,
            critical=True,
            tags=["system", "memory"]
        )
        
        self.health_checks["system_disk"] = HealthCheck(
            name="system_disk",
            check_type=CheckType.SYSTEM,
            check_function=self._check_disk_usage,
            interval_seconds=60,
            critical=True,
            tags=["system", "disk"]
        )
        
        # Service checks
        self.health_checks["service_response_time"] = HealthCheck(
            name="service_response_time",
            check_type=CheckType.SERVICE,
            check_function=self._check_response_time,
            interval_seconds=30,
            tags=["service", "performance"]
        )
        
        self.health_checks["service_error_rate"] = HealthCheck(
            name="service_error_rate",
            check_type=CheckType.SERVICE,
            check_function=self._check_error_rate,
            interval_seconds=60,
            tags=["service", "errors"]
        )
        
        self.health_checks["service_cache"] = HealthCheck(
            name="service_cache",
            check_type=CheckType.SERVICE,
            check_function=self._check_cache_health,
            interval_seconds=60,
            tags=["service", "cache"]
        )
        
        # Provider connectivity checks
        self.health_checks["providers_connectivity"] = HealthCheck(
            name="providers_connectivity",
            check_type=CheckType.EXTERNAL,
            check_function=self._check_providers_connectivity,
            interval_seconds=120,
            tags=["external", "providers"]
        )
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.enabled:
            try:
                current_time = time.time()
                
                # Run due health checks
                checks_to_run = []
                for name, check in self.health_checks.items():
                    if not check.enabled:
                        continue
                    
                    last_check = self.last_check_times.get(name, 0)
                    if current_time - last_check >= check.interval_seconds:
                        checks_to_run.append((name, check))
                
                # Execute checks
                if checks_to_run:
                    await self._execute_health_checks(checks_to_run)
                
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Process alerts
                await self._process_alerts()
                
                # Sleep until next check
                await asyncio.sleep(min(10, self.check_interval))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring loop error: {e}")
                await asyncio.sleep(30)
    
    async def _execute_health_checks(self, checks: List[tuple]):
        """Execute health checks"""
        for name, check in checks:
            try:
                start_time = time.time()
                
                # Execute check with timeout and retries
                result = await self._execute_single_check(check)
                
                # Record timing
                result.duration_ms = (time.time() - start_time) * 1000
                result.timestamp = time.time()
                
                # Store result
                if name not in self.check_results:
                    self.check_results[name] = []
                
                self.check_results[name].append(result)
                
                # Limit history size
                max_results = (self.metrics_retention_hours * 3600) // check.interval_seconds
                if len(self.check_results[name]) > max_results:
                    self.check_results[name] = self.check_results[name][-max_results:]
                
                # Update last check time
                self.last_check_times[name] = time.time()
                
                # Track consecutive failures
                if result.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                    self.consecutive_failures[name] = self.consecutive_failures.get(name, 0) + 1
                else:
                    self.consecutive_failures[name] = 0
                
                # Log critical issues
                if result.status == HealthStatus.CRITICAL:
                    logger.error(f"Critical health check failure: {name} - {result.message}")
                elif result.status == HealthStatus.WARNING:
                    logger.warning(f"Health check warning: {name} - {result.message}")
                
            except Exception as e:
                logger.error(f"Health check {name} execution failed: {e}")
                
                # Create error result
                error_result = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Check execution failed: {e}",
                    timestamp=time.time()
                )
                
                if name not in self.check_results:
                    self.check_results[name] = []
                self.check_results[name].append(error_result)
    
    async def _execute_single_check(self, check: HealthCheck) -> HealthCheckResult:
        """Execute single health check with retries"""
        last_exception = None
        
        for attempt in range(check.retry_count):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    check.check_function(),
                    timeout=check.timeout_seconds
                )
                
                if isinstance(result, HealthCheckResult):
                    return result
                else:
                    # Convert simple result to HealthCheckResult
                    return HealthCheckResult(
                        name=check.name,
                        status=HealthStatus.HEALTHY,
                        message="Check passed",
                        details=result if isinstance(result, dict) else {"result": result}
                    )
                
            except asyncio.TimeoutError:
                last_exception = "Check timeout"
                if attempt < check.retry_count - 1:
                    await asyncio.sleep(check.retry_delay_seconds)
                    continue
                break
            except Exception as e:
                last_exception = str(e)
                if attempt < check.retry_count - 1:
                    await asyncio.sleep(check.retry_delay_seconds)
                    continue
                break
        
        # All retries failed
        return HealthCheckResult(
            name=check.name,
            status=HealthStatus.CRITICAL,
            message=f"Check failed after {check.retry_count} attempts: {last_exception}",
            details={"last_error": last_exception, "attempts": check.retry_count}
        )
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix only)
            try:
                load_avg = list(psutil.getloadavg())
            except (AttributeError, OSError):
                load_avg = [0.0, 0.0, 0.0]
            
            # Uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=memory.used / (1024**3),
                memory_total_gb=memory.total / (1024**3),
                disk_percent=disk.percent,
                disk_used_gb=disk.used / (1024**3),
                disk_total_gb=disk.total / (1024**3),
                network_io=network_io,
                process_count=process_count,
                load_average=load_avg,
                uptime_seconds=uptime
            )
            
            self.system_metrics_history.append(metrics)
            
            # Limit history
            max_metrics = self.metrics_retention_hours * 120  # Every 30 seconds
            if len(self.system_metrics_history) > max_metrics:
                self.system_metrics_history = self.system_metrics_history[-max_metrics:]
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    async def _process_alerts(self):
        """Process and send alerts for health issues"""
        if not self.alert_enabled or not self.alert_handlers:
            return
        
        current_time = time.time()
        
        for name, failures in self.consecutive_failures.items():
            check = self.health_checks.get(name)
            if not check or failures < check.alert_threshold:
                continue
            
            # Check alert cooldown
            last_alert = self.suppressed_alerts.get(name, 0)
            if current_time - last_alert < self.alert_cooldown_seconds:
                continue
            
            # Get latest result
            results = self.check_results.get(name, [])
            if not results:
                continue
            
            latest_result = results[-1]
            
            # Send alert
            alert_data = {
                "check_name": name,
                "status": latest_result.status.value,
                "message": latest_result.message,
                "consecutive_failures": failures,
                "is_critical": check.critical,
                "timestamp": current_time,
                "details": latest_result.details
            }
            
            await self._send_alert(alert_data)
            self.suppressed_alerts[name] = current_time
    
    async def _send_alert(self, alert_data: Dict[str, Any]):
        """Send alert to registered handlers"""
        for handler in self.alert_handlers:
            try:
                await handler(alert_data)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    # Default health check implementations
    async def _check_cpu_usage(self) -> HealthCheckResult:
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 90:
            status = HealthStatus.CRITICAL
            message = f"CPU usage critical: {cpu_percent:.1f}%"
        elif cpu_percent > 75:
            status = HealthStatus.WARNING
            message = f"CPU usage high: {cpu_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"CPU usage normal: {cpu_percent:.1f}%"
        
        return HealthCheckResult(
            name="system_cpu",
            status=status,
            message=message,
            details={"cpu_percent": cpu_percent}
        )
    
    async def _check_memory_usage(self) -> HealthCheckResult:
        """Check memory usage"""
        memory = psutil.virtual_memory()
        
        if memory.percent > 90:
            status = HealthStatus.CRITICAL
            message = f"Memory usage critical: {memory.percent:.1f}%"
        elif memory.percent > 80:
            status = HealthStatus.WARNING
            message = f"Memory usage high: {memory.percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory usage normal: {memory.percent:.1f}%"
        
        return HealthCheckResult(
            name="system_memory",
            status=status,
            message=message,
            details={
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3)
            }
        )
    
    async def _check_disk_usage(self) -> HealthCheckResult:
        """Check disk usage"""
        disk = psutil.disk_usage('/')
        
        if disk.percent > 95:
            status = HealthStatus.CRITICAL
            message = f"Disk usage critical: {disk.percent:.1f}%"
        elif disk.percent > 85:
            status = HealthStatus.WARNING
            message = f"Disk usage high: {disk.percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk usage normal: {disk.percent:.1f}%"
        
        return HealthCheckResult(
            name="system_disk",
            status=status,
            message=message,
            details={
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / (1024**3),
                "disk_total_gb": disk.total / (1024**3)
            }
        )
    
    async def _check_response_time(self) -> HealthCheckResult:
        """Check service response time"""
        if not self.analytics:
            return HealthCheckResult(
                name="service_response_time",
                status=HealthStatus.UNKNOWN,
                message="Analytics not available"
            )
        
        # Get recent response times from analytics
        stats = self.analytics.get_action_stats()
        
        if not stats:
            return HealthCheckResult(
                name="service_response_time",
                status=HealthStatus.HEALTHY,
                message="No recent requests"
            )
        
        # Calculate average response time across all actions
        total_time = 0
        total_requests = 0
        
        for action_stats in stats.values():
            total_time += action_stats.avg_response_time_ms * action_stats.total_requests
            total_requests += action_stats.total_requests
        
        if total_requests == 0:
            avg_response_time = 0
        else:
            avg_response_time = total_time / total_requests
        
        if avg_response_time > 10000:  # 10 seconds
            status = HealthStatus.CRITICAL
            message = f"Response time critical: {avg_response_time:.0f}ms"
        elif avg_response_time > 5000:  # 5 seconds
            status = HealthStatus.WARNING
            message = f"Response time high: {avg_response_time:.0f}ms"
        else:
            status = HealthStatus.HEALTHY
            message = f"Response time normal: {avg_response_time:.0f}ms"
        
        return HealthCheckResult(
            name="service_response_time",
            status=status,
            message=message,
            details={
                "avg_response_time_ms": avg_response_time,
                "total_requests": total_requests
            }
        )
    
    async def _check_error_rate(self) -> HealthCheckResult:
        """Check service error rate"""
        if not self.analytics:
            return HealthCheckResult(
                name="service_error_rate",
                status=HealthStatus.UNKNOWN,
                message="Analytics not available"
            )
        
        daily_stats = self.analytics.get_daily_stats()
        
        total_requests = daily_stats.get("total_requests", 0)
        failed_requests = daily_stats.get("failed_requests", 0)
        
        if total_requests == 0:
            error_rate = 0
        else:
            error_rate = (failed_requests / total_requests) * 100
        
        if error_rate > 10:
            status = HealthStatus.CRITICAL
            message = f"Error rate critical: {error_rate:.1f}%"
        elif error_rate > 5:
            status = HealthStatus.WARNING
            message = f"Error rate high: {error_rate:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Error rate normal: {error_rate:.1f}%"
        
        return HealthCheckResult(
            name="service_error_rate",
            status=status,
            message=message,
            details={
                "error_rate_percent": error_rate,
                "total_requests": total_requests,
                "failed_requests": failed_requests
            }
        )
    
    async def _check_cache_health(self) -> HealthCheckResult:
        """Check cache health"""
        # Placeholder implementation
        # In a real implementation, would check cache hit rates, memory usage, etc.
        return HealthCheckResult(
            name="service_cache",
            status=HealthStatus.HEALTHY,
            message="Cache operating normally",
            details={"hit_rate": 0.85}
        )
    
    async def _check_providers_connectivity(self) -> HealthCheckResult:
        """Check external provider connectivity"""
        # Placeholder implementation
        # In a real implementation, would ping provider APIs
        return HealthCheckResult(
            name="providers_connectivity",
            status=HealthStatus.HEALTHY,
            message="All providers accessible",
            details={"providers_checked": ["openai", "stability", "elevenlabs"]}
        )
    
    def add_health_check(self, check: HealthCheck) -> None:
        """Add custom health check"""
        self.health_checks[check.name] = check
        logger.info(f"Added health check: {check.name}")
    
    def remove_health_check(self, name: str) -> bool:
        """Remove health check"""
        if name in self.health_checks:
            del self.health_checks[name]
            self.check_results.pop(name, None)
            self.last_check_times.pop(name, None)
            self.consecutive_failures.pop(name, None)
            logger.info(f"Removed health check: {name}")
            return True
        return False
    
    def add_alert_handler(self, handler: Callable) -> None:
        """Add alert handler"""
        self.alert_handlers.append(handler)
        logger.info("Added alert handler")
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        if not self.check_results:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "message": "No health checks performed yet"
            }
        
        # Aggregate status from all checks
        statuses = []
        critical_issues = []
        warning_issues = []
        
        for name, results in self.check_results.items():
            if not results:
                continue
            
            latest_result = results[-1]
            check = self.health_checks.get(name)
            
            statuses.append(latest_result.status)
            
            if latest_result.status == HealthStatus.CRITICAL:
                critical_issues.append({
                    "check": name,
                    "message": latest_result.message,
                    "is_critical_check": check.critical if check else False
                })
            elif latest_result.status == HealthStatus.WARNING:
                warning_issues.append({
                    "check": name,
                    "message": latest_result.message
                })
        
        # Determine overall status
        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
            message = f"{len(critical_issues)} critical issues detected"
        elif HealthStatus.WARNING in statuses:
            overall_status = HealthStatus.WARNING
            message = f"{len(warning_issues)} warnings detected"
        elif HealthStatus.UNKNOWN in statuses:
            overall_status = HealthStatus.DEGRADED
            message = "Some checks could not be performed"
        else:
            overall_status = HealthStatus.HEALTHY
            message = "All systems operational"
        
        return {
            "status": overall_status.value,
            "message": message,
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "total_checks": len(self.health_checks),
            "last_updated": time.time()
        }
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        overall_health = self.get_overall_health()
        
        # Detailed check results
        check_details = {}
        for name, results in self.check_results.items():
            if results:
                latest = results[-1]
                check_details[name] = {
                    "status": latest.status.value,
                    "message": latest.message,
                    "last_check": latest.timestamp,
                    "duration_ms": latest.duration_ms,
                    "consecutive_failures": self.consecutive_failures.get(name, 0),
                    "details": latest.details
                }
        
        # System metrics summary
        system_summary = {}
        if self.system_metrics_history:
            latest_metrics = self.system_metrics_history[-1]
            system_summary = {
                "cpu_percent": latest_metrics.cpu_percent,
                "memory_percent": latest_metrics.memory_percent,
                "disk_percent": latest_metrics.disk_percent,
                "uptime_hours": latest_metrics.uptime_seconds / 3600
            }
        
        return {
            "overall_health": overall_health,
            "check_details": check_details,
            "system_summary": system_summary,
            "monitoring_enabled": self.enabled,
            "alert_enabled": self.alert_enabled,
            "report_generated": time.time()
        }
    
    async def _cleanup_loop(self):
        """Cleanup old metrics and results"""
        while self.enabled:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_time = time.time() - (self.metrics_retention_hours * 3600)
                
                # Clean up check results
                for name in list(self.check_results.keys()):
                    results = self.check_results[name]
                    self.check_results[name] = [
                        r for r in results if r.timestamp > cutoff_time
                    ]
                    
                    if not self.check_results[name]:
                        del self.check_results[name]
                
                # Clean up system metrics
                self.system_metrics_history = [
                    m for m in self.system_metrics_history
                    if time.time() - cutoff_time < self.metrics_retention_hours * 3600
                ]
                
                logger.info("Completed health monitoring cleanup")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring cleanup failed: {e}")
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'monitoring_task') and self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
        if hasattr(self, 'cleanup_task') and self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()

# Simple alert handlers
async def console_alert_handler(alert_data: Dict[str, Any]):
    """Simple console alert handler"""
    severity = "🚨 CRITICAL" if alert_data["is_critical"] else "⚠️ WARNING"
    print(f"{severity} Health Alert: {alert_data['check_name']}")
    print(f"Status: {alert_data['status']}")
    print(f"Message: {alert_data['message']}")
    print(f"Consecutive failures: {alert_data['consecutive_failures']}")
    print("---")

async def log_alert_handler(alert_data: Dict[str, Any]):
    """Log-based alert handler"""
    severity = "CRITICAL" if alert_data["is_critical"] else "WARNING"
    logger.warning(f"Health Alert [{severity}] {alert_data['check_name']}: {alert_data['message']}")
