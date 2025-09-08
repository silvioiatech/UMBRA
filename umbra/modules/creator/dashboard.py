"""
Creator v1 (CRT4) - Web Dashboard
Real-time monitoring and administration dashboard for Creator v1 system
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

# Import Creator v1 components
from umbra.core.config import UmbraConfig
from umbra.ai.agent import UmbraAIAgent
from umbra.modules.creator import create_creator_system, CreatorV1System
from umbra.modules.creator.errors import CreatorError

class DashboardConfig(BaseModel):
    """Dashboard configuration"""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    auto_reload: bool = False
    creator_config_file: Optional[str] = None

class ContentGenerationRequest(BaseModel):
    """Content generation request model"""
    action: str
    topic: str
    platform: Optional[str] = None
    tone: Optional[str] = None
    user_id: Optional[str] = "dashboard_user"

class ConfigUpdateRequest(BaseModel):
    """Configuration update request"""
    key: str
    value: Any
    reason: str = "Updated via dashboard"

class CreatorDashboard:
    """Creator v1 Web Dashboard"""
    
    def __init__(self, config: DashboardConfig):
        self.config = config
        self.creator_system: Optional[CreatorV1System] = None
        self.websocket_connections: List[WebSocket] = []
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Creator v1 Dashboard",
            description="Real-time monitoring and administration dashboard",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup templates
        self.templates = Jinja2Templates(directory="templates")
        
        # Setup routes
        self._setup_routes()
        
        # Background tasks
        self.monitoring_task = None
    
    async def initialize_creator_system(self):
        """Initialize Creator v1 system"""
        try:
            if self.config.creator_config_file:
                creator_config = UmbraConfig.from_file(self.config.creator_config_file)
            else:
                creator_config = UmbraConfig({
                    "CREATOR_V1_ENABLED": True,
                    "CREATOR_V1_DEBUG": self.config.debug,
                    "CREATOR_SECURITY_ENABLED": False,  # Disable for dashboard
                    "CREATOR_RATE_LIMITING_ENABLED": False,
                })
            
            ai_agent = UmbraAIAgent(creator_config)
            self.creator_system = await create_creator_system(creator_config, ai_agent)
            
            # Start monitoring task
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize Creator system: {e}")
            return False
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.on_event("startup")
        async def startup_event():
            success = await self.initialize_creator_system()
            if not success:
                print("Warning: Creator system initialization failed")
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            if self.creator_system:
                await self.creator_system.shutdown()
            if self.monitoring_task:
                self.monitoring_task.cancel()
        
        # Main dashboard page
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "title": "Creator v1 Dashboard"
            })
        
        # API Routes
        
        @self.app.get("/api/status")
        async def get_system_status():
            """Get system status"""
            if not self.creator_system:
                raise HTTPException(status_code=503, detail="Creator system not initialized")
            
            return self.creator_system.get_system_status()
        
        @self.app.get("/api/health")
        async def get_health_check():
            """Get system health"""
            if not self.creator_system:
                raise HTTPException(status_code=503, detail="Creator system not initialized")
            
            return await self.creator_system.health_check()
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get system metrics"""
            if not self.creator_system:
                raise HTTPException(status_code=503, detail="Creator system not initialized")
            
            metrics_data = {}
            
            # Get analytics
            analytics = self.creator_system.get_component("analytics")
            if analytics:
                metrics_data["analytics"] = {
                    "daily_stats": analytics.get_daily_stats(),
                    "action_stats": analytics.get_action_stats()
                }
            
            # Get advanced metrics
            advanced_metrics = self.creator_system.get_component("advanced_metrics")
            if advanced_metrics:
                metrics_data["advanced_metrics"] = advanced_metrics.get_metrics_summary()
            
            # Get cache stats
            cache = self.creator_system.get_component("cache")
            if cache:
                metrics_data["cache"] = cache.get_stats()
            
            # Get batching stats
            batching = self.creator_system.get_component("batching")
            if batching:
                metrics_data["batching"] = batching.get_batch_stats()
            
            return metrics_data
        
        @self.app.get("/api/components")
        async def get_components():
            """Get component information"""
            if not self.creator_system:
                raise HTTPException(status_code=503, detail="Creator system not initialized")
            
            components = {}
            component_names = [
                "analytics", "cache", "security", "health_monitor",
                "advanced_metrics", "rate_limiter", "batching",
                "workflow_manager", "plugin_manager", "creator_service"
            ]
            
            for name in component_names:
                component = self.creator_system.get_component(name)
                if component:
                    component_info = {"available": True}
                    
                    # Try to get component stats
                    if hasattr(component, 'get_stats'):
                        try:
                            component_info["stats"] = component.get_stats()
                        except Exception:
                            pass
                    
                    components[name] = component_info
                else:
                    components[name] = {"available": False}
            
            return components
        
        @self.app.post("/api/content/generate")
        async def generate_content(request: ContentGenerationRequest):
            """Generate content"""
            if not self.creator_system:
                raise HTTPException(status_code=503, detail="Creator system not initialized")
            
            try:
                content_request = {
                    "action": request.action,
                    "topic": request.topic,
                    "platform": request.platform,
                    "tone": request.tone
                }
                
                result = await self.creator_system.generate_content(
                    content_request, user_id=request.user_id
                )
                
                return result
                
            except CreatorError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal error: {e}")
        
        @self.app.get("/api/workflows")
        async def get_workflows():
            """Get workflows"""
            if not self.creator_system:
                raise HTTPException(status_code=503, detail="Creator system not initialized")
            
            workflow_manager = self.creator_system.get_component("workflow_manager")
            if workflow_manager:
                return workflow_manager.list_workflows()
            else:
                return []
        
        @self.app.get("/api/plugins")
        async def get_plugins():
            """Get plugins"""
            if not self.creator_system:
                raise HTTPException(status_code=503, detail="Creator system not initialized")
            
            plugin_manager = self.creator_system.get_component("plugin_manager")
            if plugin_manager:
                return plugin_manager.get_all_plugins_info()
            else:
                return {}
        
        @self.app.get("/api/config")
        async def get_config():
            """Get configuration"""
            if not self.creator_system:
                raise HTTPException(status_code=503, detail="Creator system not initialized")
            
            dynamic_config = self.creator_system.get_component("dynamic_config")
            if dynamic_config:
                return dynamic_config.export_config(include_sensitive=False)
            else:
                return {}
        
        @self.app.put("/api/config")
        async def update_config(request: ConfigUpdateRequest):
            """Update configuration"""
            if not self.creator_system:
                raise HTTPException(status_code=503, detail="Creator system not initialized")
            
            dynamic_config = self.creator_system.get_component("dynamic_config")
            if dynamic_config:
                success = dynamic_config.set(
                    request.key, request.value, 
                    changed_by="dashboard", reason=request.reason
                )
                
                if success:
                    return {"success": True, "message": f"Updated {request.key}"}
                else:
                    raise HTTPException(status_code=400, detail="Failed to update configuration")
            else:
                raise HTTPException(status_code=503, detail="Dynamic config not available")
        
        @self.app.get("/api/alerts")
        async def get_alerts():
            """Get recent alerts"""
            if not self.creator_system:
                raise HTTPException(status_code=503, detail="Creator system not initialized")
            
            # Get alerts from various components
            alerts = []
            
            # Health monitor alerts
            health_monitor = self.creator_system.get_component("health_monitor")
            if health_monitor:
                health_report = health_monitor.get_health_report()
                overall_health = health_report.get("overall_health", {})
                
                critical_issues = overall_health.get("critical_issues", [])
                warning_issues = overall_health.get("warning_issues", [])
                
                for issue in critical_issues:
                    alerts.append({
                        "type": "critical",
                        "component": "health_monitor",
                        "message": issue.get("message", ""),
                        "check": issue.get("check", ""),
                        "timestamp": time.time()
                    })
                
                for issue in warning_issues:
                    alerts.append({
                        "type": "warning",
                        "component": "health_monitor", 
                        "message": issue.get("message", ""),
                        "check": issue.get("check", ""),
                        "timestamp": time.time()
                    })
            
            return alerts
        
        # WebSocket endpoint for real-time updates
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                
                if self.websocket_connections and self.creator_system:
                    # Collect real-time data
                    real_time_data = {
                        "timestamp": time.time(),
                        "system_status": self.creator_system.get_system_status(),
                        "metrics": await self._get_real_time_metrics()
                    }
                    
                    # Send to all connected clients
                    disconnected = []
                    for websocket in self.websocket_connections:
                        try:
                            await websocket.send_text(json.dumps(real_time_data, default=str))
                        except Exception:
                            disconnected.append(websocket)
                    
                    # Remove disconnected clients
                    for websocket in disconnected:
                        self.websocket_connections.remove(websocket)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitoring loop error: {e}")
    
    async def _get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics"""
        metrics = {}
        
        try:
            # System resource metrics
            import psutil
            metrics["system"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        except ImportError:
            metrics["system"] = {"error": "psutil not available"}
        
        # Cache metrics
        cache = self.creator_system.get_component("cache")
        if cache:
            metrics["cache"] = cache.get_stats()
        
        # Analytics metrics
        analytics = self.creator_system.get_component("analytics")
        if analytics:
            metrics["analytics"] = analytics.get_daily_stats()
        
        return metrics
    
    def create_dashboard_html(self) -> str:
        """Create dashboard HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Creator v1 Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .card { @apply bg-white rounded-lg shadow-md p-6 mb-6; }
        .metric-card { @apply bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg p-4; }
        .status-healthy { @apply text-green-600; }
        .status-warning { @apply text-yellow-600; }
        .status-critical { @apply text-red-600; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900">Creator v1 Dashboard</h1>
            <p class="text-gray-600">Real-time monitoring and administration</p>
        </div>

        <!-- Status Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="metric-card">
                <h3 class="text-lg font-semibold">System Status</h3>
                <p id="system-status" class="text-2xl font-bold">Loading...</p>
            </div>
            <div class="metric-card">
                <h3 class="text-lg font-semibold">Active Requests</h3>
                <p id="active-requests" class="text-2xl font-bold">0</p>
            </div>
            <div class="metric-card">
                <h3 class="text-lg font-semibold">Cache Hit Rate</h3>
                <p id="cache-hit-rate" class="text-2xl font-bold">0%</p>
            </div>
            <div class="metric-card">
                <h3 class="text-lg font-semibold">Components</h3>
                <p id="components-status" class="text-2xl font-bold">0/0</p>
            </div>
        </div>

        <!-- Main Content Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- System Health -->
            <div class="card">
                <h2 class="text-xl font-bold mb-4">System Health</h2>
                <div id="health-status">
                    <p class="text-gray-600">Loading health information...</p>
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="card">
                <h2 class="text-xl font-bold mb-4">Recent Activity</h2>
                <div id="recent-activity">
                    <p class="text-gray-600">Loading activity...</p>
                </div>
            </div>

            <!-- Performance Metrics -->
            <div class="card">
                <h2 class="text-xl font-bold mb-4">Performance Metrics</h2>
                <canvas id="performance-chart" width="400" height="200"></canvas>
            </div>

            <!-- Component Status -->
            <div class="card">
                <h2 class="text-xl font-bold mb-4">Components</h2>
                <div id="components-list">
                    <p class="text-gray-600">Loading components...</p>
                </div>
            </div>
        </div>

        <!-- Content Generation -->
        <div class="card mt-8">
            <h2 class="text-xl font-bold mb-4">Content Generation</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <form id="content-form" class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Topic</label>
                            <input type="text" id="topic" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Platform</label>
                            <select id="platform" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                                <option value="">Select platform</option>
                                <option value="twitter">Twitter</option>
                                <option value="linkedin">LinkedIn</option>
                                <option value="instagram">Instagram</option>
                                <option value="facebook">Facebook</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Tone</label>
                            <select id="tone" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                                <option value="">Select tone</option>
                                <option value="professional">Professional</option>
                                <option value="casual">Casual</option>
                                <option value="friendly">Friendly</option>
                                <option value="creative">Creative</option>
                            </select>
                        </div>
                        <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">
                            Generate Content
                        </button>
                    </form>
                </div>
                <div>
                    <h3 class="text-lg font-medium mb-2">Generated Content</h3>
                    <div id="generated-content" class="bg-gray-50 p-4 rounded-md min-h-32">
                        <p class="text-gray-500">Content will appear here...</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Alerts -->
        <div class="card mt-8">
            <h2 class="text-xl font-bold mb-4">Alerts</h2>
            <div id="alerts-list">
                <p class="text-gray-600">Loading alerts...</p>
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection for real-time updates
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };

        // Dashboard update functions
        function updateDashboard(data) {
            // Update status cards
            const systemStatus = data.system_status?.health_status || 'unknown';
            document.getElementById('system-status').textContent = systemStatus;
            
            const activeRequests = data.metrics?.analytics?.total_requests || 0;
            document.getElementById('active-requests').textContent = activeRequests;
            
            const cacheHitRate = data.metrics?.cache?.hit_rate || 0;
            document.getElementById('cache-hit-rate').textContent = `${(cacheHitRate * 100).toFixed(1)}%`;
            
            const components = data.system_status?.components_status || {};
            const workingComponents = Object.values(components).filter(status => status).length;
            const totalComponents = Object.keys(components).length;
            document.getElementById('components-status').textContent = `${workingComponents}/${totalComponents}`;
        }

        // Load initial data
        async function loadInitialData() {
            try {
                // Load system status
                const statusResponse = await fetch('/api/status');
                const statusData = await statusResponse.json();
                
                // Load health data
                const healthResponse = await fetch('/api/health');
                const healthData = await healthResponse.json();
                
                // Load components
                const componentsResponse = await fetch('/api/components');
                const componentsData = await componentsResponse.json();
                
                // Load alerts
                const alertsResponse = await fetch('/api/alerts');
                const alertsData = await alertsResponse.json();
                
                // Update UI
                updateSystemHealth(healthData);
                updateComponents(componentsData);
                updateAlerts(alertsData);
                
            } catch (error) {
                console.error('Failed to load initial data:', error);
            }
        }

        function updateSystemHealth(healthData) {
            const healthStatus = document.getElementById('health-status');
            const overallHealth = healthData.overall_health || {};
            
            let html = `<p class="status-${overallHealth.status || 'unknown'}">${overallHealth.message || 'No health data'}</p>`;
            
            if (overallHealth.critical_issues && overallHealth.critical_issues.length > 0) {
                html += '<h4 class="font-semibold text-red-600 mt-2">Critical Issues:</h4>';
                html += '<ul class="list-disc list-inside text-red-600">';
                overallHealth.critical_issues.forEach(issue => {
                    html += `<li>${issue.check}: ${issue.message}</li>`;
                });
                html += '</ul>';
            }
            
            healthStatus.innerHTML = html;
        }

        function updateComponents(componentsData) {
            const componentsList = document.getElementById('components-list');
            let html = '';
            
            for (const [name, info] of Object.entries(componentsData)) {
                const statusIcon = info.available ? '✅' : '❌';
                html += `<div class="flex justify-between items-center py-2 border-b">`;
                html += `<span>${statusIcon} ${name}</span>`;
                html += `<span class="text-sm text-gray-500">${info.available ? 'Available' : 'Unavailable'}</span>`;
                html += `</div>`;
            }
            
            componentsList.innerHTML = html;
        }

        function updateAlerts(alertsData) {
            const alertsList = document.getElementById('alerts-list');
            
            if (alertsData.length === 0) {
                alertsList.innerHTML = '<p class="text-green-600">No active alerts</p>';
                return;
            }
            
            let html = '';
            alertsData.forEach(alert => {
                const alertClass = alert.type === 'critical' ? 'text-red-600' : 'text-yellow-600';
                html += `<div class="border-l-4 border-${alert.type === 'critical' ? 'red' : 'yellow'}-500 pl-4 py-2 mb-2">`;
                html += `<p class="${alertClass} font-semibold">${alert.type.toUpperCase()}: ${alert.message}</p>`;
                html += `<p class="text-sm text-gray-500">Component: ${alert.component}</p>`;
                html += '</div>';
            });
            
            alertsList.innerHTML = html;
        }

        // Content generation form
        document.getElementById('content-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const topic = document.getElementById('topic').value;
            const platform = document.getElementById('platform').value;
            const tone = document.getElementById('tone').value;
            
            if (!topic) {
                alert('Please enter a topic');
                return;
            }
            
            try {
                const response = await fetch('/api/content/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        action: 'generate_post',
                        topic: topic,
                        platform: platform,
                        tone: tone
                    })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    document.getElementById('generated-content').innerHTML = 
                        `<p class="text-gray-900">${result.content || 'No content generated'}</p>`;
                } else {
                    document.getElementById('generated-content').innerHTML = 
                        `<p class="text-red-600">Error: ${result.detail || 'Generation failed'}</p>`;
                }
                
            } catch (error) {
                document.getElementById('generated-content').innerHTML = 
                    `<p class="text-red-600">Error: ${error.message}</p>`;
            }
        });

        // Load initial data when page loads
        loadInitialData();
        
        // Refresh data every 30 seconds
        setInterval(loadInitialData, 30000);
    </script>
</body>
</html>
        """
    
    def run(self):
        """Run the dashboard server"""
        # Create templates directory if it doesn't exist
        templates_dir = Path("templates")
        templates_dir.mkdir(exist_ok=True)
        
        # Create dashboard template
        dashboard_template = templates_dir / "dashboard.html"
        if not dashboard_template.exists():
            dashboard_template.write_text(self.create_dashboard_html())
        
        # Run the server
        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            reload=self.config.auto_reload,
            log_level="info" if not self.config.debug else "debug"
        )

# CLI for running dashboard
def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Creator v1 Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--auto-reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--creator-config", help="Creator configuration file")
    
    args = parser.parse_args()
    
    config = DashboardConfig(
        host=args.host,
        port=args.port,
        debug=args.debug,
        auto_reload=args.auto_reload,
        creator_config_file=args.creator_config
    )
    
    dashboard = CreatorDashboard(config)
    
    print(f"🚀 Starting Creator v1 Dashboard")
    print(f"📊 Dashboard URL: http://{config.host}:{config.port}")
    print(f"🔧 Debug mode: {'ON' if config.debug else 'OFF'}")
    
    dashboard.run()

if __name__ == "__main__":
    main()
