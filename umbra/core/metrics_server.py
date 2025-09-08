"""
UMBRA Metrics Endpoint Server
============================

FastAPI server providing Prometheus-compatible metrics endpoint for UMBRA platform.
Serves real-time metrics data for monitoring and alerting systems.

Features:
- Prometheus-compatible `/metrics` endpoint
- Health check endpoints
- Metrics aggregation and filtering
- Real-time metrics updates
- Security and authentication

Version: 1.0.0
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

from ..core.config import UmbraConfig
from ..core.metrics import (
    get_metrics_registry, get_prometheus_output, MetricsRegistry,
    increment_counter, set_gauge, observe_histogram
)
from ..core.rbac import UserContext, Role, check_permission
from ..core.audit import audit_log, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

class MetricsServer:
    """
    Prometheus metrics server for UMBRA
    
    Provides a dedicated FastAPI server for serving metrics data
    to monitoring systems like Prometheus, Grafana, etc.
    """
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        self.app = FastAPI(
            title="UMBRA Metrics Server",
            description="Prometheus-compatible metrics endpoint for UMBRA platform",
            version="1.0.0",
            docs_url="/docs" if config.get('METRICS_DOCS_ENABLED', True) else None,
            redoc_url="/redoc" if config.get('METRICS_DOCS_ENABLED', True) else None
        )
        
        # Configuration
        self.host = config.get('METRICS_SERVER_HOST', '0.0.0.0')
        self.port = config.get('METRICS_SERVER_PORT', 9090)
        self.auth_enabled = config.get('METRICS_AUTH_ENABLED', True)
        self.cors_enabled = config.get('METRICS_CORS_ENABLED', True)
        
        # Security
        self.security = HTTPBearer(auto_error=False) if self.auth_enabled else None
        self.allowed_tokens = set(config.get('METRICS_ALLOWED_TOKENS', []))
        
        # Metrics tracking for the metrics server itself
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        
        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        
        # CORS middleware
        if self.cors_enabled:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.get('METRICS_CORS_ORIGINS', ["*"]),
                allow_credentials=True,
                allow_methods=["GET", "POST"],
                allow_headers=["*"],
            )
        
        # Request tracking middleware
        @self.app.middleware("http")
        async def track_requests(request: Request, call_next):
            start_time = time.time()
            self.request_count += 1
            
            try:
                response = await call_next(request)
                
                # Track successful requests
                duration = time.time() - start_time
                increment_counter("umbra_metrics_server_requests_total", 
                                endpoint=request.url.path, status="success")
                observe_histogram("umbra_metrics_server_request_duration_seconds", 
                                duration, endpoint=request.url.path)
                
                return response
                
            except Exception as e:
                # Track errors
                self.error_count += 1
                duration = time.time() - start_time
                increment_counter("umbra_metrics_server_requests_total", 
                                endpoint=request.url.path, status="error")
                increment_counter("umbra_metrics_server_errors_total", 
                                endpoint=request.url.path, error_type=type(e).__name__)
                observe_histogram("umbra_metrics_server_request_duration_seconds", 
                                duration, endpoint=request.url.path)
                raise
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/metrics", response_class=PlainTextResponse)
        async def prometheus_metrics(
            request: Request,
            auth: Optional[HTTPAuthorizationCredentials] = Depends(self.security) if self.security else None,
            format: str = Query("prometheus", description="Output format (prometheus, json)")
        ):
            """
            Prometheus-compatible metrics endpoint
            
            Returns all UMBRA metrics in Prometheus exposition format
            or JSON format for debugging.
            """
            
            # Authentication check
            if self.auth_enabled and not self._validate_auth(auth, request):
                await audit_log(
                    event_type=AuditEventType.PERMISSION_DENIED,
                    severity=AuditSeverity.WARNING,
                    source="metrics_server",
                    outcome="denied",
                    details={
                        "endpoint": "/metrics",
                        "reason": "invalid_authentication",
                        "user_agent": request.headers.get("user-agent"),
                        "ip_address": request.client.host
                    },
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent")
                )
                raise HTTPException(status_code=401, detail="Authentication required")
            
            try:
                # Get metrics registry
                registry = get_metrics_registry()
                if not registry:
                    raise HTTPException(status_code=503, detail="Metrics system not initialized")
                
                # Update server metrics
                set_gauge("umbra_metrics_server_uptime_seconds", time.time() - self.start_time)
                set_gauge("umbra_metrics_server_active_connections", len(self.app.state.__dict__.get('connections', [])))
                
                if format.lower() == "json":
                    # Return JSON format for debugging
                    metrics_data = self._get_metrics_json(registry)
                    return JSONResponse(content=metrics_data)
                else:
                    # Return Prometheus format
                    prometheus_output = get_prometheus_output()
                    
                    # Add server-specific metrics
                    server_metrics = self._get_server_metrics()
                    
                    return PlainTextResponse(
                        content=prometheus_output + server_metrics,
                        media_type="text/plain; version=0.0.4; charset=utf-8"
                    )
                    
            except Exception as e:
                logger.error(f"Error serving metrics: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            registry = get_metrics_registry()
            
            return {
                "status": "healthy" if registry else "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": time.time() - self.start_time,
                "requests_total": self.request_count,
                "errors_total": self.error_count,
                "metrics_available": registry is not None
            }
        
        @self.app.get("/health/ready")
        async def readiness_check():
            """Kubernetes readiness check"""
            registry = get_metrics_registry()
            
            if not registry:
                raise HTTPException(status_code=503, detail="Metrics system not ready")
            
            return {"status": "ready"}
        
        @self.app.get("/health/live")
        async def liveness_check():
            """Kubernetes liveness check"""
            return {"status": "live"}
        
        @self.app.get("/metrics/summary")
        async def metrics_summary(
            auth: Optional[HTTPAuthorizationCredentials] = Depends(self.security) if self.security else None,
            request: Request = None
        ):
            """
            Get metrics summary in JSON format
            
            Provides a human-readable summary of key metrics
            """
            
            # Authentication check
            if self.auth_enabled and not self._validate_auth(auth, request):
                raise HTTPException(status_code=401, detail="Authentication required")
            
            try:
                registry = get_metrics_registry()
                if not registry:
                    raise HTTPException(status_code=503, detail="Metrics system not initialized")
                
                summary = self._generate_metrics_summary(registry)
                return summary
                
            except Exception as e:
                logger.error(f"Error generating metrics summary: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.app.get("/metrics/query")
        async def query_metrics(
            metric_name: str = Query(..., description="Metric name to query"),
            labels: Optional[str] = Query(None, description="Label filters (key=value,key2=value2)"),
            auth: Optional[HTTPAuthorizationCredentials] = Depends(self.security) if self.security else None,
            request: Request = None
        ):
            """
            Query specific metrics with filtering
            
            Allows querying individual metrics with label filtering
            """
            
            # Authentication check
            if self.auth_enabled and not self._validate_auth(auth, request):
                raise HTTPException(status_code=401, detail="Authentication required")
            
            try:
                registry = get_metrics_registry()
                if not registry:
                    raise HTTPException(status_code=503, detail="Metrics system not initialized")
                
                # Get specific metric
                metric = registry.get_metric(metric_name)
                if not metric:
                    raise HTTPException(status_code=404, detail=f"Metric {metric_name} not found")
                
                # Parse label filters
                label_filters = {}
                if labels:
                    for label_pair in labels.split(','):
                        if '=' in label_pair:
                            key, value = label_pair.split('=', 1)
                            label_filters[key.strip()] = value.strip()
                
                # Get metric data
                metric_data = self._get_metric_data(metric, label_filters)
                
                return {
                    "metric_name": metric_name,
                    "metric_type": type(metric).__name__.lower(),
                    "description": getattr(metric, 'description', ''),
                    "labels": label_filters,
                    "data": metric_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error querying metric {metric_name}: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
    
    def _validate_auth(self, auth: Optional[HTTPAuthorizationCredentials], 
                      request: Request) -> bool:
        """Validate authentication credentials"""
        if not auth:
            return False
        
        # Check against allowed tokens
        if self.allowed_tokens and auth.credentials in self.allowed_tokens:
            return True
        
        # Additional validation logic can be added here
        # For example, JWT validation, API key validation, etc.
        
        return False
    
    def _get_metrics_json(self, registry: MetricsRegistry) -> Dict[str, Any]:
        """Get all metrics in JSON format"""
        metrics_data = {}
        
        for name, metric in registry.get_all_metrics().items():
            metrics_data[name] = {
                "type": type(metric).__name__.lower(),
                "description": getattr(metric, 'description', ''),
                "data": self._get_metric_data(metric)
            }
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics_data
        }
    
    def _get_metric_data(self, metric, label_filters: Dict[str, str] = None):
        """Get data from a specific metric"""
        try:
            if hasattr(metric, 'get_all_values'):
                # Counter or Gauge
                all_values = metric.get_all_values()
                
                if label_filters:
                    # Filter by labels
                    filtered_values = {}
                    for labels, value in all_values.items():
                        if self._matches_labels(labels, label_filters):
                            filtered_values[labels] = value
                    return filtered_values
                else:
                    return all_values
            
            elif hasattr(metric, 'get_buckets'):
                # Histogram
                return {
                    "buckets": metric.get_buckets(),
                    "count": metric.get_count(),
                    "sum": metric.get_sum()
                }
            
            elif hasattr(metric, 'get_quantile'):
                # Summary
                return {
                    "quantiles": {
                        str(q): metric.get_quantile(q) 
                        for q in getattr(metric, 'quantiles', [0.5, 0.9, 0.95, 0.99])
                    },
                    "count": metric.get_count(),
                    "sum": metric.get_sum()
                }
            
            else:
                return {"error": "Unknown metric type"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _matches_labels(self, labels: Dict[str, str], filters: Dict[str, str]) -> bool:
        """Check if metric labels match filters"""
        for key, value in filters.items():
            if labels.get(key) != value:
                return False
        return True
    
    def _get_server_metrics(self) -> str:
        """Get metrics server specific metrics in Prometheus format"""
        return f"""
# HELP umbra_metrics_server_info Metrics server information
# TYPE umbra_metrics_server_info gauge
umbra_metrics_server_info{{version="1.0.0",host="{self.host}",port="{self.port}"}} 1

# HELP umbra_metrics_server_uptime_seconds Metrics server uptime
# TYPE umbra_metrics_server_uptime_seconds gauge
umbra_metrics_server_uptime_seconds {time.time() - self.start_time}

# HELP umbra_metrics_server_requests_served_total Total requests served
# TYPE umbra_metrics_server_requests_served_total counter
umbra_metrics_server_requests_served_total {self.request_count}

# HELP umbra_metrics_server_errors_total Total errors encountered
# TYPE umbra_metrics_server_errors_total counter
umbra_metrics_server_errors_total {self.error_count}
"""
    
    def _generate_metrics_summary(self, registry: MetricsRegistry) -> Dict[str, Any]:
        """Generate human-readable metrics summary"""
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_metrics": len(registry.get_all_metrics()),
            "categories": {},
            "top_metrics": [],
            "server_info": {
                "uptime_seconds": time.time() - self.start_time,
                "requests_served": self.request_count,
                "errors_total": self.error_count
            }
        }
        
        # Categorize metrics
        for name, metric in registry.get_all_metrics().items():
            category = name.split('_')[1] if '_' in name else 'other'
            
            if category not in summary["categories"]:
                summary["categories"][category] = {
                    "count": 0,
                    "metrics": []
                }
            
            summary["categories"][category]["count"] += 1
            summary["categories"][category]["metrics"].append({
                "name": name,
                "type": type(metric).__name__.lower(),
                "description": getattr(metric, 'description', '')
            })
        
        # Get top metrics by activity (if available)
        try:
            requests_metric = registry.get_metric('umbra_requests_total')
            if requests_metric and hasattr(requests_metric, 'get_all_values'):
                values = requests_metric.get_all_values()
                sorted_values = sorted(values.items(), key=lambda x: x[1], reverse=True)
                
                summary["top_metrics"] = [
                    {
                        "labels": dict(labels),
                        "value": value
                    }
                    for labels, value in sorted_values[:10]
                ]
        except Exception:
            pass
        
        return summary
    
    async def start(self):
        """Start the metrics server"""
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info" if self.config.get('DEBUG', False) else "warning",
            access_log=self.config.get('METRICS_ACCESS_LOG_ENABLED', False)
        )
        
        server = uvicorn.Server(config)
        
        logger.info(f"Starting metrics server on {self.host}:{self.port}")
        await server.serve()

# Global metrics server instance
_metrics_server: Optional[MetricsServer] = None

def create_metrics_server(config: UmbraConfig) -> MetricsServer:
    """Create metrics server instance"""
    global _metrics_server
    
    _metrics_server = MetricsServer(config)
    return _metrics_server

def get_metrics_server() -> Optional[MetricsServer]:
    """Get global metrics server instance"""
    return _metrics_server

async def start_metrics_server(config: UmbraConfig = None):
    """Start metrics server"""
    if not _metrics_server and config:
        create_metrics_server(config)
    
    if _metrics_server:
        await _metrics_server.start()

# Standalone function to run metrics server
async def run_metrics_server(config_path: str = None):
    """Run metrics server as standalone application"""
    from ..core.config import UmbraConfig
    
    # Load configuration
    if config_path:
        config = UmbraConfig.from_file(config_path)
    else:
        config = UmbraConfig()
    
    # Initialize metrics system
    from ..core.metrics import initialize_metrics, start_metrics_collection
    initialize_metrics(config)
    await start_metrics_collection()
    
    # Start server
    await start_metrics_server(config)

# Export key classes and functions
__all__ = [
    'MetricsServer',
    'create_metrics_server', 'get_metrics_server', 'start_metrics_server', 'run_metrics_server'
]
