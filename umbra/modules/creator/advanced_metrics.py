"""
Advanced Metrics and Reporting System - Comprehensive metrics collection and reporting for Creator v1 (CRT4)
Provides detailed analytics, performance tracking, and business intelligence
"""

import logging
import time
import asyncio
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import statistics
import csv
from pathlib import Path

from ...core.config import UmbraConfig
from .analytics import CreatorAnalytics
from .errors import CreatorError, MetricsError

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"

class AggregationType(Enum):
    """Types of aggregation"""
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    PERCENTILE = "percentile"
    RATE = "rate"

class ReportFormat(Enum):
    """Report output formats"""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    DASHBOARD = "dashboard"

@dataclass
class MetricDataPoint:
    """Individual metric data point"""
    timestamp: float
    value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MetricDefinition:
    """Metric definition and configuration"""
    name: str
    metric_type: MetricType
    description: str
    unit: str = ""
    labels: List[str] = field(default_factory=list)
    retention_hours: int = 168  # 1 week default
    aggregation_interval_seconds: int = 60
    alert_thresholds: Dict[str, float] = field(default_factory=dict)

@dataclass
class ReportDefinition:
    """Report definition and configuration"""
    name: str
    title: str
    description: str
    metrics: List[str]
    time_range: str  # e.g., "last_24h", "last_7d", "last_30d"
    aggregation: AggregationType
    format: ReportFormat
    schedule: Optional[str] = None  # Cron expression
    filters: Dict[str, Any] = field(default_factory=dict)
    charts: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Alert:
    """Metric alert definition"""
    name: str
    metric_name: str
    condition: str  # e.g., ">", "<", ">=", "<=", "=="
    threshold: float
    duration_minutes: int = 5
    severity: str = "warning"  # "info", "warning", "critical"
    enabled: bool = True
    last_triggered: Optional[float] = None
    notification_channels: List[str] = field(default_factory=list)

class AdvancedMetrics:
    """Advanced metrics collection and analysis system"""
    
    def __init__(self, config: UmbraConfig, analytics: Optional[CreatorAnalytics] = None):
        self.config = config
        self.analytics = analytics
        
        # Metrics storage
        self.metrics: Dict[str, List[MetricDataPoint]] = defaultdict(list)
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        self.aggregated_metrics: Dict[str, Dict[str, List[MetricDataPoint]]] = defaultdict(lambda: defaultdict(list))
        
        # Reporting
        self.report_definitions: Dict[str, ReportDefinition] = {}
        self.generated_reports: Dict[str, Dict[str, Any]] = {}
        
        # Alerting
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.alert_handlers: List[callable] = []
        
        # Configuration
        self.collection_enabled = config.get("CREATOR_METRICS_ENABLED", True)
        self.retention_hours = config.get("CREATOR_METRICS_RETENTION_HOURS", 168)
        self.aggregation_interval = config.get("CREATOR_METRICS_AGGREGATION_INTERVAL", 60)
        self.export_enabled = config.get("CREATOR_METRICS_EXPORT_ENABLED", True)
        self.export_directory = Path(config.get("CREATOR_METRICS_EXPORT_DIR", "exports/metrics"))
        
        # Performance tracking
        self.performance_baseline: Dict[str, float] = {}
        self.anomaly_detection_enabled = config.get("CREATOR_METRICS_ANOMALY_DETECTION", True)
        
        # Initialize default metrics
        self._initialize_default_metrics()
        
        # Start background tasks
        if self.collection_enabled:
            self.aggregation_task = asyncio.create_task(self._aggregation_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.alert_task = asyncio.create_task(self._alert_monitoring_loop())
        
        # Ensure export directory exists
        if self.export_enabled:
            self.export_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("Advanced metrics system initialized")
    
    def _initialize_default_metrics(self):
        """Initialize default metric definitions"""
        
        # Request metrics
        self.metric_definitions["requests_total"] = MetricDefinition(
            name="requests_total",
            metric_type=MetricType.COUNTER,
            description="Total number of requests",
            labels=["action", "status", "user_id"],
            alert_thresholds={"high_rate": 1000.0}
        )
        
        self.metric_definitions["request_duration"] = MetricDefinition(
            name="request_duration",
            metric_type=MetricType.HISTOGRAM,
            description="Request duration in milliseconds",
            unit="ms",
            labels=["action", "provider"],
            alert_thresholds={"slow_requests": 5000.0}
        )
        
        self.metric_definitions["request_errors"] = MetricDefinition(
            name="request_errors",
            metric_type=MetricType.COUNTER,
            description="Number of failed requests",
            labels=["action", "error_type"],
            alert_thresholds={"error_rate": 50.0}
        )
        
        # Resource metrics
        self.metric_definitions["tokens_consumed"] = MetricDefinition(
            name="tokens_consumed",
            metric_type=MetricType.COUNTER,
            description="Total tokens consumed",
            unit="tokens",
            labels=["provider", "model", "user_id"],
            alert_thresholds={"high_usage": 100000.0}
        )
        
        self.metric_definitions["cost_incurred"] = MetricDefinition(
            name="cost_incurred",
            metric_type=MetricType.COUNTER,
            description="Total cost incurred",
            unit="USD",
            labels=["provider", "action", "user_id"],
            alert_thresholds={"high_cost": 100.0}
        )
        
        # Performance metrics
        self.metric_definitions["cache_hit_rate"] = MetricDefinition(
            name="cache_hit_rate",
            metric_type=MetricType.GAUGE,
            description="Cache hit rate percentage",
            unit="%",
            alert_thresholds={"low_hit_rate": 80.0}
        )
        
        self.metric_definitions["active_connections"] = MetricDefinition(
            name="active_connections",
            metric_type=MetricType.GAUGE,
            description="Number of active connections",
            alert_thresholds={"high_connections": 1000.0}
        )
        
        # Business metrics
        self.metric_definitions["content_generated"] = MetricDefinition(
            name="content_generated",
            metric_type=MetricType.COUNTER,
            description="Total content pieces generated",
            labels=["content_type", "platform", "user_id"]
        )
        
        self.metric_definitions["user_satisfaction"] = MetricDefinition(
            name="user_satisfaction",
            metric_type=MetricType.GAUGE,
            description="User satisfaction score",
            unit="score",
            labels=["user_id", "content_type"],
            alert_thresholds={"low_satisfaction": 3.0}
        )
        
        # System metrics
        self.metric_definitions["memory_usage"] = MetricDefinition(
            name="memory_usage",
            metric_type=MetricType.GAUGE,
            description="Memory usage percentage",
            unit="%",
            alert_thresholds={"high_memory": 85.0}
        )
        
        self.metric_definitions["cpu_usage"] = MetricDefinition(
            name="cpu_usage",
            metric_type=MetricType.GAUGE,
            description="CPU usage percentage",
            unit="%",
            alert_thresholds={"high_cpu": 80.0}
        )
    
    def record_metric(self, metric_name: str, value: Union[int, float], 
                     labels: Dict[str, str] = None, 
                     metadata: Dict[str, Any] = None) -> bool:
        """Record a metric data point"""
        if not self.collection_enabled:
            return False
        
        try:
            data_point = MetricDataPoint(
                timestamp=time.time(),
                value=value,
                labels=labels or {},
                metadata=metadata or {}
            )
            
            self.metrics[metric_name].append(data_point)
            
            # Limit metric storage to prevent memory issues
            definition = self.metric_definitions.get(metric_name)
            if definition:
                retention_seconds = definition.retention_hours * 3600
                cutoff_time = time.time() - retention_seconds
                
                self.metrics[metric_name] = [
                    dp for dp in self.metrics[metric_name] 
                    if dp.timestamp > cutoff_time
                ]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {e}")
            return False
    
    def increment_counter(self, metric_name: str, increment: Union[int, float] = 1,
                         labels: Dict[str, str] = None) -> bool:
        """Increment a counter metric"""
        return self.record_metric(metric_name, increment, labels)
    
    def set_gauge(self, metric_name: str, value: Union[int, float],
                 labels: Dict[str, str] = None) -> bool:
        """Set a gauge metric value"""
        return self.record_metric(metric_name, value, labels)
    
    def record_timer(self, metric_name: str, duration_ms: float,
                    labels: Dict[str, str] = None) -> bool:
        """Record a timer metric"""
        return self.record_metric(metric_name, duration_ms, labels)
    
    def get_metric_values(self, metric_name: str, 
                         start_time: Optional[float] = None,
                         end_time: Optional[float] = None,
                         labels_filter: Dict[str, str] = None) -> List[MetricDataPoint]:
        """Get metric values with optional filtering"""
        if metric_name not in self.metrics:
            return []
        
        data_points = self.metrics[metric_name]
        
        # Time filtering
        if start_time is not None:
            data_points = [dp for dp in data_points if dp.timestamp >= start_time]
        
        if end_time is not None:
            data_points = [dp for dp in data_points if dp.timestamp <= end_time]
        
        # Label filtering
        if labels_filter:
            filtered_points = []
            for dp in data_points:
                match = True
                for key, value in labels_filter.items():
                    if dp.labels.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_points.append(dp)
            data_points = filtered_points
        
        return data_points
    
    def aggregate_metric(self, metric_name: str, 
                        aggregation: AggregationType,
                        time_window_seconds: int = 3600,
                        labels_filter: Dict[str, str] = None) -> Optional[float]:
        """Aggregate metric values over a time window"""
        end_time = time.time()
        start_time = end_time - time_window_seconds
        
        data_points = self.get_metric_values(
            metric_name, start_time, end_time, labels_filter
        )
        
        if not data_points:
            return None
        
        values = [dp.value for dp in data_points]
        
        if aggregation == AggregationType.SUM:
            return sum(values)
        elif aggregation == AggregationType.AVERAGE:
            return statistics.mean(values)
        elif aggregation == AggregationType.COUNT:
            return len(values)
        elif aggregation == AggregationType.MIN:
            return min(values)
        elif aggregation == AggregationType.MAX:
            return max(values)
        elif aggregation == AggregationType.RATE:
            if time_window_seconds > 0:
                return sum(values) / time_window_seconds
            return 0
        else:
            return None
    
    def get_percentile(self, metric_name: str, percentile: float,
                      time_window_seconds: int = 3600,
                      labels_filter: Dict[str, str] = None) -> Optional[float]:
        """Get percentile value for a metric"""
        end_time = time.time()
        start_time = end_time - time_window_seconds
        
        data_points = self.get_metric_values(
            metric_name, start_time, end_time, labels_filter
        )
        
        if not data_points:
            return None
        
        values = sorted([dp.value for dp in data_points])
        
        if not values:
            return None
        
        index = (percentile / 100.0) * (len(values) - 1)
        
        if index.is_integer():
            return values[int(index)]
        else:
            lower = values[int(index)]
            upper = values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    async def _aggregation_loop(self):
        """Background aggregation loop"""
        while self.collection_enabled:
            try:
                await asyncio.sleep(self.aggregation_interval)
                
                current_time = time.time()
                
                # Perform aggregations for each metric
                for metric_name, definition in self.metric_definitions.items():
                    await self._perform_metric_aggregation(metric_name, definition, current_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Aggregation loop error: {e}")
                await asyncio.sleep(60)
    
    async def _perform_metric_aggregation(self, metric_name: str, 
                                        definition: MetricDefinition,
                                        current_time: float):
        """Perform aggregation for a specific metric"""
        try:
            interval = definition.aggregation_interval_seconds
            window_start = current_time - interval
            
            data_points = self.get_metric_values(metric_name, window_start, current_time)
            
            if not data_points:
                return
            
            # Group by labels
            label_groups = defaultdict(list)
            for dp in data_points:
                label_key = json.dumps(dp.labels, sort_keys=True)
                label_groups[label_key].append(dp.value)
            
            # Create aggregated data points
            for label_key, values in label_groups.items():
                labels = json.loads(label_key)
                
                # Calculate different aggregations
                aggregations = {
                    "sum": sum(values),
                    "avg": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
                
                # Store aggregated values
                for agg_type, agg_value in aggregations.items():
                    agg_point = MetricDataPoint(
                        timestamp=current_time,
                        value=agg_value,
                        labels=labels,
                        metadata={"aggregation": agg_type, "window": interval}
                    )
                    
                    self.aggregated_metrics[metric_name][agg_type].append(agg_point)
            
        except Exception as e:
            logger.error(f"Metric aggregation failed for {metric_name}: {e}")
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while self.collection_enabled:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                current_time = time.time()
                
                # Clean up old metric data
                for metric_name, definition in self.metric_definitions.items():
                    retention_seconds = definition.retention_hours * 3600
                    cutoff_time = current_time - retention_seconds
                    
                    # Clean raw metrics
                    if metric_name in self.metrics:
                        self.metrics[metric_name] = [
                            dp for dp in self.metrics[metric_name]
                            if dp.timestamp > cutoff_time
                        ]
                    
                    # Clean aggregated metrics
                    if metric_name in self.aggregated_metrics:
                        for agg_type in self.aggregated_metrics[metric_name]:
                            self.aggregated_metrics[metric_name][agg_type] = [
                                dp for dp in self.aggregated_metrics[metric_name][agg_type]
                                if dp.timestamp > cutoff_time
                            ]
                
                # Clean up old reports
                report_retention = 30 * 24 * 3600  # 30 days
                cutoff_time = current_time - report_retention
                
                self.generated_reports = {
                    report_id: report for report_id, report in self.generated_reports.items()
                    if report.get("generated_at", 0) > cutoff_time
                }
                
                logger.debug("Completed metrics cleanup")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    async def _alert_monitoring_loop(self):
        """Background alert monitoring loop"""
        while self.collection_enabled:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                for alert_name, alert in self.alerts.items():
                    if not alert.enabled:
                        continue
                    
                    await self._check_alert(alert)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert monitoring error: {e}")
    
    async def _check_alert(self, alert: Alert):
        """Check if an alert condition is met"""
        try:
            # Get recent metric values
            current_value = self.aggregate_metric(
                alert.metric_name,
                AggregationType.AVERAGE,
                alert.duration_minutes * 60
            )
            
            if current_value is None:
                return
            
            # Check condition
            triggered = False
            if alert.condition == ">":
                triggered = current_value > alert.threshold
            elif alert.condition == "<":
                triggered = current_value < alert.threshold
            elif alert.condition == ">=":
                triggered = current_value >= alert.threshold
            elif alert.condition == "<=":
                triggered = current_value <= alert.threshold
            elif alert.condition == "==":
                triggered = abs(current_value - alert.threshold) < 0.001
            
            if triggered:
                await self._trigger_alert(alert, current_value)
            
        except Exception as e:
            logger.error(f"Alert check failed for {alert.name}: {e}")
    
    async def _trigger_alert(self, alert: Alert, current_value: float):
        """Trigger an alert"""
        current_time = time.time()
        
        # Check if recently triggered (avoid spam)
        if (alert.last_triggered and 
            current_time - alert.last_triggered < 300):  # 5 minutes cooldown
            return
        
        alert.last_triggered = current_time
        
        alert_event = {
            "alert_name": alert.name,
            "metric_name": alert.metric_name,
            "condition": f"{alert.condition} {alert.threshold}",
            "current_value": current_value,
            "severity": alert.severity,
            "timestamp": current_time,
            "duration_minutes": alert.duration_minutes
        }
        
        self.alert_history.append(alert_event)
        
        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert_event)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
        
        logger.warning(f"Alert triggered: {alert.name} - {current_value} {alert.condition} {alert.threshold}")
    
    def create_alert(self, name: str, metric_name: str, condition: str,
                    threshold: float, **kwargs) -> bool:
        """Create a new alert"""
        try:
            alert = Alert(
                name=name,
                metric_name=metric_name,
                condition=condition,
                threshold=threshold,
                **kwargs
            )
            
            self.alerts[name] = alert
            logger.info(f"Created alert: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create alert {name}: {e}")
            return False
    
    def add_alert_handler(self, handler: callable):
        """Add alert notification handler"""
        self.alert_handlers.append(handler)
    
    def generate_report(self, report_name: str, 
                       custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a report"""
        if report_name not in self.report_definitions:
            raise MetricsError(f"Report definition not found: {report_name}")
        
        definition = self.report_definitions[report_name]
        params = custom_params or {}
        
        try:
            # Parse time range
            time_range = params.get("time_range", definition.time_range)
            start_time, end_time = self._parse_time_range(time_range)
            
            # Collect metric data
            report_data = {
                "report_name": report_name,
                "title": definition.title,
                "description": definition.description,
                "generated_at": time.time(),
                "time_range": time_range,
                "start_time": start_time,
                "end_time": end_time,
                "metrics": {}
            }
            
            # Process each metric
            for metric_name in definition.metrics:
                metric_data = self._collect_metric_data(
                    metric_name, start_time, end_time, definition.aggregation
                )
                report_data["metrics"][metric_name] = metric_data
            
            # Generate charts if requested
            if definition.charts:
                report_data["charts"] = self._generate_chart_data(
                    definition.charts, report_data["metrics"]
                )
            
            # Store generated report
            report_id = f"{report_name}_{int(time.time())}"
            self.generated_reports[report_id] = report_data
            
            return report_data
            
        except Exception as e:
            logger.error(f"Report generation failed for {report_name}: {e}")
            raise MetricsError(f"Report generation failed: {e}")
    
    def _parse_time_range(self, time_range: str) -> Tuple[float, float]:
        """Parse time range string"""
        end_time = time.time()
        
        if time_range == "last_1h":
            start_time = end_time - 3600
        elif time_range == "last_24h":
            start_time = end_time - 86400
        elif time_range == "last_7d":
            start_time = end_time - 7 * 86400
        elif time_range == "last_30d":
            start_time = end_time - 30 * 86400
        elif time_range == "last_90d":
            start_time = end_time - 90 * 86400
        else:
            # Default to last 24 hours
            start_time = end_time - 86400
        
        return start_time, end_time
    
    def _collect_metric_data(self, metric_name: str, start_time: float,
                           end_time: float, aggregation: AggregationType) -> Dict[str, Any]:
        """Collect metric data for reporting"""
        data_points = self.get_metric_values(metric_name, start_time, end_time)
        
        if not data_points:
            return {"error": "No data available"}
        
        values = [dp.value for dp in data_points]
        
        result = {
            "metric_name": metric_name,
            "data_points_count": len(data_points),
            "time_range": {
                "start": start_time,
                "end": end_time
            }
        }
        
        # Calculate statistics
        if values:
            result.update({
                "min": min(values),
                "max": max(values),
                "avg": statistics.mean(values),
                "sum": sum(values),
                "count": len(values)
            })
            
            if len(values) > 1:
                result["std_dev"] = statistics.stdev(values)
            
            # Percentiles
            result["percentiles"] = {
                "p50": self.get_percentile(metric_name, 50, int(end_time - start_time)),
                "p90": self.get_percentile(metric_name, 90, int(end_time - start_time)),
                "p95": self.get_percentile(metric_name, 95, int(end_time - start_time)),
                "p99": self.get_percentile(metric_name, 99, int(end_time - start_time))
            }
        
        # Time series data (sampled for charts)
        if len(data_points) > 100:
            # Sample data points for visualization
            step = len(data_points) // 100
            sampled_points = data_points[::step]
        else:
            sampled_points = data_points
        
        result["time_series"] = [
            {"timestamp": dp.timestamp, "value": dp.value}
            for dp in sampled_points
        ]
        
        return result
    
    def _generate_chart_data(self, chart_definitions: List[Dict[str, Any]],
                           metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate chart data from metrics"""
        charts = []
        
        for chart_def in chart_definitions:
            chart_type = chart_def.get("type", "line")
            chart_metrics = chart_def.get("metrics", [])
            
            chart_data = {
                "type": chart_type,
                "title": chart_def.get("title", "Chart"),
                "data": []
            }
            
            for metric_name in chart_metrics:
                if metric_name in metrics_data:
                    metric_data = metrics_data[metric_name]
                    if "time_series" in metric_data:
                        chart_data["data"].append({
                            "name": metric_name,
                            "values": metric_data["time_series"]
                        })
            
            charts.append(chart_data)
        
        return charts
    
    def export_report(self, report_data: Dict[str, Any], 
                     format: ReportFormat = ReportFormat.JSON,
                     filename: Optional[str] = None) -> str:
        """Export report to file"""
        if not self.export_enabled:
            raise MetricsError("Export is disabled")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{report_data.get('report_name', 'unknown')}_{timestamp}"
        
        file_path = self.export_directory / f"{filename}.{format.value}"
        
        try:
            if format == ReportFormat.JSON:
                with open(file_path, 'w') as f:
                    json.dump(report_data, f, indent=2, default=str)
            
            elif format == ReportFormat.CSV:
                self._export_csv_report(report_data, file_path)
            
            elif format == ReportFormat.HTML:
                self._export_html_report(report_data, file_path)
            
            else:
                raise MetricsError(f"Unsupported export format: {format}")
            
            logger.info(f"Report exported to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Report export failed: {e}")
            raise MetricsError(f"Export failed: {e}")
    
    def _export_csv_report(self, report_data: Dict[str, Any], file_path: Path):
        """Export report as CSV"""
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(["Metric", "Min", "Max", "Average", "Sum", "Count"])
            
            # Write metric data
            for metric_name, metric_data in report_data.get("metrics", {}).items():
                if isinstance(metric_data, dict) and "avg" in metric_data:
                    writer.writerow([
                        metric_name,
                        metric_data.get("min", ""),
                        metric_data.get("max", ""),
                        metric_data.get("avg", ""),
                        metric_data.get("sum", ""),
                        metric_data.get("count", "")
                    ])
    
    def _export_html_report(self, report_data: Dict[str, Any], file_path: Path):
        """Export report as HTML"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report_data.get('title', 'Metrics Report')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; }}
                .metric {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report_data.get('title', 'Metrics Report')}</h1>
                <p>{report_data.get('description', '')}</p>
                <p>Generated: {datetime.fromtimestamp(report_data.get('generated_at', 0))}</p>
                <p>Time Range: {report_data.get('time_range', '')}</p>
            </div>
        """
        
        # Add metrics table
        html_content += """
            <h2>Metrics Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Average</th>
                    <th>Sum</th>
                    <th>Count</th>
                </tr>
        """
        
        for metric_name, metric_data in report_data.get("metrics", {}).items():
            if isinstance(metric_data, dict) and "avg" in metric_data:
                html_content += f"""
                    <tr>
                        <td>{metric_name}</td>
                        <td>{metric_data.get('min', '')}</td>
                        <td>{metric_data.get('max', '')}</td>
                        <td>{metric_data.get('avg', ''):.2f}</td>
                        <td>{metric_data.get('sum', '')}</td>
                        <td>{metric_data.get('count', '')}</td>
                    </tr>
                """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        with open(file_path, 'w') as f:
            f.write(html_content)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return {
            "total_metrics": len(self.metric_definitions),
            "data_points": sum(len(points) for points in self.metrics.values()),
            "alerts_configured": len(self.alerts),
            "alerts_triggered": len(self.alert_history),
            "reports_available": len(self.report_definitions),
            "reports_generated": len(self.generated_reports),
            "collection_enabled": self.collection_enabled,
            "export_enabled": self.export_enabled,
            "retention_hours": self.retention_hours
        }
    
    def detect_anomalies(self, metric_name: str, 
                        window_hours: int = 24,
                        sensitivity: float = 2.0) -> List[Dict[str, Any]]:
        """Detect anomalies in metric data"""
        if not self.anomaly_detection_enabled:
            return []
        
        end_time = time.time()
        start_time = end_time - (window_hours * 3600)
        
        data_points = self.get_metric_values(metric_name, start_time, end_time)
        
        if len(data_points) < 10:
            return []  # Not enough data
        
        values = [dp.value for dp in data_points]
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        anomalies = []
        threshold = sensitivity * std_dev
        
        for dp in data_points:
            if abs(dp.value - mean_value) > threshold:
                anomalies.append({
                    "timestamp": dp.timestamp,
                    "value": dp.value,
                    "expected_range": [mean_value - threshold, mean_value + threshold],
                    "deviation": abs(dp.value - mean_value),
                    "severity": "high" if abs(dp.value - mean_value) > 2 * threshold else "medium"
                })
        
        return anomalies
    
    def __del__(self):
        """Cleanup on deletion"""
        tasks = ['aggregation_task', 'cleanup_task', 'alert_task']
        for task_name in tasks:
            if hasattr(self, task_name):
                task = getattr(self, task_name)
                if task and not task.done():
                    task.cancel()

# Exception classes
class MetricsError(CreatorError):
    """Metrics-specific error"""
    pass

# Utility functions for common alert handlers
async def console_alert_handler(alert_event: Dict[str, Any]):
    """Simple console alert handler"""
    severity_emoji = {
        "info": "ℹ️",
        "warning": "⚠️", 
        "critical": "🚨"
    }
    
    emoji = severity_emoji.get(alert_event["severity"], "⚠️")
    print(f"{emoji} ALERT: {alert_event['alert_name']}")
    print(f"Metric: {alert_event['metric_name']}")
    print(f"Current Value: {alert_event['current_value']}")
    print(f"Condition: {alert_event['condition']}")
    print(f"Severity: {alert_event['severity']}")
    print("---")

async def log_alert_handler(alert_event: Dict[str, Any]):
    """Log-based alert handler"""
    severity = alert_event["severity"].upper()
    logger.warning(f"ALERT [{severity}] {alert_event['alert_name']}: "
                  f"{alert_event['metric_name']} = {alert_event['current_value']} "
                  f"({alert_event['condition']})")
