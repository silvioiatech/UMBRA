"""
Metrics Collection - SEC1 Implementation
Prometheus-compatible metrics for observability and monitoring
"""

import time
import threading
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum
import json

class MetricType(Enum):
    """Types of metrics supported"""
    COUNTER = "counter"
    GAUGE = "gauge"  
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class MetricSample:
    """Individual metric sample"""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class HistogramBucket:
    """Histogram bucket definition"""
    upper_bound: float
    count: int = 0

class BaseMetric:
    """Base class for all metrics"""
    
    def __init__(self, name: str, description: str = "", labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.lock = threading.Lock()
    
    def _validate_labels(self, labels: Dict[str, str]) -> Dict[str, str]:
        """Validate and sanitize labels"""
        if not labels:
            return {}
        
        # Ensure all expected labels are present
        sanitized = {}
        for label in self.labels:
            sanitized[label] = str(labels.get(label, ""))
        
        return sanitized

class Counter(BaseMetric):
    """Counter metric - monotonically increasing"""
    
    def __init__(self, name: str, description: str = "", labels: Optional[List[str]] = None):
        super().__init__(name, description, labels)
        self.values: Dict[str, float] = defaultdict(float)
    
    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment counter"""
        if value < 0:
            raise ValueError("Counter values must be non-negative")
        
        labels = self._validate_labels(labels or {})
        label_key = json.dumps(labels, sort_keys=True)
        
        with self.lock:
            self.values[label_key] += value
    
    def get_samples(self) -> List[MetricSample]:
        """Get current metric samples"""
        samples = []
        with self.lock:
            for label_key, value in self.values.items():
                labels = json.loads(label_key) if label_key else {}
                samples.append(MetricSample(self.name, value, labels))
        return samples

class Gauge(BaseMetric):
    """Gauge metric - can go up and down"""
    
    def __init__(self, name: str, description: str = "", labels: Optional[List[str]] = None):
        super().__init__(name, description, labels)
        self.values: Dict[str, float] = {}
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge value"""
        labels = self._validate_labels(labels or {})
        label_key = json.dumps(labels, sort_keys=True)
        
        with self.lock:
            self.values[label_key] = value
    
    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment gauge"""
        labels = self._validate_labels(labels or {})
        label_key = json.dumps(labels, sort_keys=True)
        
        with self.lock:
            self.values[label_key] = self.values.get(label_key, 0) + value
    
    def dec(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Decrement gauge"""
        self.inc(-value, labels)
    
    def get_samples(self) -> List[MetricSample]:
        """Get current metric samples"""
        samples = []
        with self.lock:
            for label_key, value in self.values.items():
                labels = json.loads(label_key) if label_key else {}
                samples.append(MetricSample(self.name, value, labels))
        return samples

class Histogram(BaseMetric):
    """Histogram metric - tracks distribution of values"""
    
    def __init__(self, name: str, description: str = "", 
                 buckets: Optional[List[float]] = None, labels: Optional[List[str]] = None):
        super().__init__(name, description, labels)
        
        # Default bucket boundaries
        self.bucket_bounds = buckets or [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')]
        
        # Bucket counts for each label combination
        self.buckets: Dict[str, List[int]] = defaultdict(lambda: [0] * len(self.bucket_bounds))
        self.sums: Dict[str, float] = defaultdict(float)
        self.counts: Dict[str, int] = defaultdict(int)
    
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value"""
        labels = self._validate_labels(labels or {})
        label_key = json.dumps(labels, sort_keys=True)
        
        with self.lock:
            # Update sum and count
            self.sums[label_key] += value
            self.counts[label_key] += 1
            
            # Update buckets
            buckets = self.buckets[label_key]
            for i, bound in enumerate(self.bucket_bounds):
                if value <= bound:
                    buckets[i] += 1
    
    def time(self, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        class Timer:
            def __init__(self, histogram: Histogram, labels: Optional[Dict[str, str]]):
                self.histogram = histogram
                self.labels = labels
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.start_time:
                    duration = time.time() - self.start_time
                    self.histogram.observe(duration, self.labels)
        
        return Timer(self, labels)
    
    def get_samples(self) -> List[MetricSample]:
        """Get current metric samples"""
        samples = []
        
        with self.lock:
            for label_key in self.buckets.keys():
                labels = json.loads(label_key) if label_key else {}
                
                # Bucket samples
                buckets = self.buckets[label_key]
                for i, (bound, count) in enumerate(zip(self.bucket_bounds, buckets)):
                    bucket_labels = labels.copy()
                    bucket_labels['le'] = str(bound) if bound != float('inf') else '+Inf'
                    samples.append(MetricSample(f"{self.name}_bucket", count, bucket_labels))
                
                # Sum and count samples
                samples.append(MetricSample(f"{self.name}_sum", self.sums[label_key], labels))
                samples.append(MetricSample(f"{self.name}_count", self.counts[label_key], labels))
        
        return samples

class MetricsRegistry:
    """
    Registry for all metrics
    
    Provides centralized metric management and Prometheus-compatible export.
    """
    
    def __init__(self):
        self.metrics: Dict[str, BaseMetric] = {}
        self.lock = threading.Lock()
        
        # Initialize core system metrics
        self._initialize_core_metrics()
    
    def _initialize_core_metrics(self):
        """Initialize core system metrics"""
        
        # Request metrics
        self.requests_total = self.counter(
            "umbra_requests_total",
            "Total number of requests processed",
            ["module", "action", "status", "user_type"]
        )
        
        self.request_duration = self.histogram(
            "umbra_request_duration_seconds",
            "Request duration in seconds",
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, float('inf')],
            labels=["module", "action"]
        )
        
        # User metrics
        self.active_users = self.gauge(
            "umbra_active_users",
            "Number of active users"
        )
        
        self.user_actions = self.counter(
            "umbra_user_actions_total",
            "Total user actions by type",
            ["user_id", "action", "module"]
        )
        
        # System metrics
        self.module_health = self.gauge(
            "umbra_module_health",
            "Module health status (1=healthy, 0=unhealthy)",
            ["module"]
        )
        
        self.api_errors = self.counter(
            "umbra_api_errors_total",
            "Total API errors",
            ["module", "error_type"]
        )
        
        # Creator-specific metrics
        self.creator_operations = self.counter(
            "umbra_creator_operations_total",
            "Creator operations by type",
            ["operation", "provider", "status"]
        )
        
        self.creator_costs = self.histogram(
            "umbra_creator_costs_usd",
            "Creator operation costs in USD",
            buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, float('inf')],
            labels=["operation", "provider"]
        )
        
        # RBAC metrics
        self.rbac_checks = self.counter(
            "umbra_rbac_checks_total",
            "RBAC authorization checks",
            ["module", "action", "result"]
        )
        
        # R2 storage metrics
        self.r2_operations = self.counter(
            "umbra_r2_operations_total",
            "R2 storage operations",
            ["operation", "status"]
        )
        
        self.r2_bytes = self.histogram(
            "umbra_r2_bytes",
            "R2 operation bytes",
            labels=["operation"]
        )
    
    def counter(self, name: str, description: str = "", labels: Optional[List[str]] = None) -> Counter:
        """Register a counter metric"""
        with self.lock:
            if name in self.metrics:
                metric = self.metrics[name]
                if not isinstance(metric, Counter):
                    raise ValueError(f"Metric {name} already registered as different type")
                return metric
            
            metric = Counter(name, description, labels)
            self.metrics[name] = metric
            return metric
    
    def gauge(self, name: str, description: str = "", labels: Optional[List[str]] = None) -> Gauge:
        """Register a gauge metric"""
        with self.lock:
            if name in self.metrics:
                metric = self.metrics[name]
                if not isinstance(metric, Gauge):
                    raise ValueError(f"Metric {name} already registered as different type")
                return metric
            
            metric = Gauge(name, description, labels)
            self.metrics[name] = metric
            return metric
    
    def histogram(self, name: str, description: str = "", 
                 buckets: Optional[List[float]] = None, labels: Optional[List[str]] = None) -> Histogram:
        """Register a histogram metric"""
        with self.lock:
            if name in self.metrics:
                metric = self.metrics[name]
                if not isinstance(metric, Histogram):
                    raise ValueError(f"Metric {name} already registered as different type")
                return metric
            
            metric = Histogram(name, description, buckets, labels)
            self.metrics[name] = metric
            return metric
    
    def collect(self) -> List[MetricSample]:
        """Collect all metric samples"""
        all_samples = []
        
        with self.lock:
            for metric in self.metrics.values():
                all_samples.extend(metric.get_samples())
        
        return all_samples
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        output = []
        samples = self.collect()
        
        # Group samples by metric name
        metrics_by_name = defaultdict(list)
        for sample in samples:
            metrics_by_name[sample.name].append(sample)
        
        for metric_name, metric_samples in metrics_by_name.items():
            # Add metric metadata
            metric = self._get_metric_by_sample_name(metric_name)
            if metric and metric.description:
                output.append(f"# HELP {metric_name} {metric.description}")
                output.append(f"# TYPE {metric_name} {self._get_prometheus_type(metric)}")
            
            # Add samples
            for sample in metric_samples:
                labels_str = ""
                if sample.labels:
                    label_parts = [f'{k}="{v}"' for k, v in sample.labels.items()]
                    labels_str = "{" + ",".join(label_parts) + "}"
                
                output.append(f"{sample.name}{labels_str} {sample.value}")
            
            output.append("")  # Empty line between metrics
        
        return "\n".join(output)
    
    def _get_metric_by_sample_name(self, sample_name: str) -> Optional[BaseMetric]:
        """Get metric object by sample name (handles suffixes like _bucket, _sum)"""
        # Try exact match first
        if sample_name in self.metrics:
            return self.metrics[sample_name]
        
        # Try removing common suffixes
        for suffix in ["_bucket", "_sum", "_count", "_total"]:
            if sample_name.endswith(suffix):
                base_name = sample_name[:-len(suffix)]
                if base_name in self.metrics:
                    return self.metrics[base_name]
        
        return None
    
    def _get_prometheus_type(self, metric: BaseMetric) -> str:
        """Get Prometheus metric type"""
        if isinstance(metric, Counter):
            return "counter"
        elif isinstance(metric, Gauge):
            return "gauge"
        elif isinstance(metric, Histogram):
            return "histogram"
        else:
            return "untyped"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        with self.lock:
            return {
                "total_metrics": len(self.metrics),
                "metric_types": {
                    "counters": len([m for m in self.metrics.values() if isinstance(m, Counter)]),
                    "gauges": len([m for m in self.metrics.values() if isinstance(m, Gauge)]),
                    "histograms": len([m for m in self.metrics.values() if isinstance(m, Histogram)])
                },
                "total_samples": len(self.collect())
            }

class MetricsCollector:
    """
    High-level metrics collector with convenience methods
    
    Provides easy-to-use methods for common metric patterns.
    """
    
    def __init__(self, registry: Optional[MetricsRegistry] = None):
        self.registry = registry or get_metrics_registry()
    
    def record_request(self, module: str, action: str, duration: float, 
                      status: str = "success", user_type: str = "user"):
        """Record a request with duration and status"""
        
        # Record request count
        self.registry.requests_total.inc(labels={
            "module": module,
            "action": action,
            "status": status,
            "user_type": user_type
        })
        
        # Record request duration
        self.registry.request_duration.observe(duration, labels={
            "module": module,
            "action": action
        })
    
    def record_user_action(self, user_id: int, action: str, module: str):
        """Record user action"""
        self.registry.user_actions.inc(labels={
            "user_id": str(user_id),
            "action": action,
            "module": module
        })
    
    def record_api_error(self, module: str, error_type: str):
        """Record API error"""
        self.registry.api_errors.inc(labels={
            "module": module,
            "error_type": error_type
        })
    
    def record_creator_operation(self, operation: str, provider: str, 
                               cost: float = 0.0, status: str = "success"):
        """Record Creator operation"""
        self.registry.creator_operations.inc(labels={
            "operation": operation,
            "provider": provider,
            "status": status
        })
        
        if cost > 0:
            self.registry.creator_costs.observe(cost, labels={
                "operation": operation,
                "provider": provider
            })
    
    def record_rbac_check(self, module: str, action: str, allowed: bool):
        """Record RBAC authorization check"""
        result = "allowed" if allowed else "denied"
        self.registry.rbac_checks.inc(labels={
            "module": module,
            "action": action,
            "result": result
        })
    
    def record_r2_operation(self, operation: str, bytes_transferred: int = 0, 
                          status: str = "success"):
        """Record R2 storage operation"""
        self.registry.r2_operations.inc(labels={
            "operation": operation,
            "status": status
        })
        
        if bytes_transferred > 0:
            self.registry.r2_bytes.observe(bytes_transferred, labels={
                "operation": operation
            })
    
    def set_active_users(self, count: int):
        """Set active user count"""
        self.registry.active_users.set(count)
    
    def set_module_health(self, module: str, healthy: bool):
        """Set module health status"""
        self.registry.module_health.set(1.0 if healthy else 0.0, labels={
            "module": module
        })

# Global registry instance
_global_registry: Optional[MetricsRegistry] = None
_global_collector: Optional[MetricsCollector] = None

def initialize_metrics() -> MetricsRegistry:
    """Initialize global metrics registry"""
    global _global_registry, _global_collector
    
    _global_registry = MetricsRegistry()
    _global_collector = MetricsCollector(_global_registry)
    
    return _global_registry

def get_metrics_registry() -> MetricsRegistry:
    """Get global metrics registry"""
    if _global_registry is None:
        return initialize_metrics()
    return _global_registry

def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    if _global_collector is None:
        initialize_metrics()
    return _global_collector

# Convenience functions
def record_request(module: str, action: str, duration: float, status: str = "success", user_type: str = "user"):
    """Record a request metric"""
    get_metrics_collector().record_request(module, action, duration, status, user_type)

def record_user_action(user_id: int, action: str, module: str):
    """Record user action metric"""
    get_metrics_collector().record_user_action(user_id, action, module)

def record_api_error(module: str, error_type: str):
    """Record API error metric"""
    get_metrics_collector().record_api_error(module, error_type)

# Export
__all__ = [
    "MetricType", "MetricSample", "BaseMetric", "Counter", "Gauge", "Histogram",
    "MetricsRegistry", "MetricsCollector", "initialize_metrics", 
    "get_metrics_registry", "get_metrics_collector",
    "record_request", "record_user_action", "record_api_error"
]
