"""
Infographic Generator - Create data visualizations and branded infographics
"""

import logging
import json
import base64
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import asyncio

from ...ai.agent import UmbraAIAgent
from ...core.config import UmbraConfig
from .model_provider_enhanced import EnhancedModelProviderManager
from .voice import BrandVoiceManager
from .errors import ContentError

logger = logging.getLogger(__name__)

@dataclass
class InfographicRequest:
    """Infographic generation request"""
    data_spec: Dict[str, Any]  # Data specification or actual data
    brand_prefs: Optional[Dict[str, Any]] = None
    layout_hint: Optional[str] = None  # "vertical", "horizontal", "grid", "flow"
    chart_type: Optional[str] = None  # "bar", "pie", "line", "scatter", "timeline"
    size: str = "1080x1080"  # Default Instagram size

@dataclass
class InfographicResult:
    """Infographic generation result"""
    image_url: str
    meta: Dict[str, Any]
    svg_data: Optional[str] = None
    data_points: List[Dict[str, Any]] = None

class InfographicGenerator:
    """AI-powered infographic and data visualization generator"""
    
    def __init__(self, ai_agent: UmbraAIAgent, config: UmbraConfig):
        self.ai_agent = ai_agent
        self.config = config
        self.provider_manager = EnhancedModelProviderManager(config)
        self.brand_voice = BrandVoiceManager(config)
        
        # Infographic settings
        self.default_size = config.get("CREATOR_DEFAULT_INFOGRAPHIC_SIZE", "1080x1080")
        self.max_data_points = config.get("CREATOR_MAX_DATA_POINTS", 50)
        
        # Supported chart types and layouts
        self.chart_types = [
            "bar", "column", "pie", "donut", "line", "area", "scatter", 
            "bubble", "timeline", "funnel", "gauge", "treemap"
        ]
        
        self.layout_types = [
            "vertical", "horizontal", "grid", "flow", "comparison", 
            "process", "hierarchy", "network"
        ]
        
        # Color palettes
        self.color_palettes = {
            "professional": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D"],
            "modern": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
            "corporate": ["#1B365D", "#2E5266", "#4F6D7A", "#7D8597", "#A8A8A8"],
            "vibrant": ["#FF5733", "#33FF57", "#3357FF", "#FF33F1", "#F1FF33"],
            "minimal": ["#2C3E50", "#3498DB", "#E74C3C", "#F39C12", "#9B59B6"],
            "earth": ["#8D5524", "#C68642", "#E0AC69", "#F1C27D", "#FFDBAC"]
        }
        
        logger.info("Infographic generator initialized")
    
    async def generate_infographic(self, data_spec: Dict[str, Any], 
                                 brand_prefs: Optional[Dict[str, Any]] = None,
                                 layout_hint: Optional[str] = None) -> Dict[str, Any]:
        """Generate infographic from data specification"""
        try:
            # Parse and validate data
            processed_data = await self._process_data_spec(data_spec)
            
            # Get brand preferences
            brand_prefs = brand_prefs or await self.brand_voice.get_brand_voice()
            
            # Determine optimal chart type and layout
            chart_type = await self._determine_chart_type(processed_data)
            layout = layout_hint or await self._determine_layout(processed_data, chart_type)
            
            # Create infographic request
            request = InfographicRequest(
                data_spec=data_spec,
                brand_prefs=brand_prefs,
                layout_hint=layout,
                chart_type=chart_type,
                size=self.default_size
            )
            
            # Generate infographic
            result = await self._generate_infographic_image(request, processed_data)
            
            return {
                "image_url": result.image_url,
                "meta": {
                    "chart_type": chart_type,
                    "layout": layout,
                    "data_points": len(processed_data.get("data", [])),
                    "brand_applied": bool(brand_prefs),
                    "size": request.size
                }
            }
            
        except Exception as e:
            logger.error(f"Infographic generation failed: {e}")
            raise ContentError(f"Infographic generation failed: {e}", "infographic")
    
    async def generate_chart(self, data: List[Dict[str, Any]], chart_type: str,
                           title: str = "", **kwargs) -> Dict[str, Any]:
        """Generate simple chart from data"""
        try:
            if chart_type not in self.chart_types:
                raise ContentError(f"Unsupported chart type: {chart_type}", "chart")
            
            # Create simple data spec
            data_spec = {
                "type": "chart",
                "chart_type": chart_type,
                "data": data,
                "title": title,
                "config": kwargs
            }
            
            return await self.generate_infographic(data_spec)
            
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            raise ContentError(f"Chart generation failed: {e}", "chart")
    
    async def generate_comparison_chart(self, categories: List[str], 
                                      datasets: List[Dict[str, Any]],
                                      title: str = "Comparison") -> Dict[str, Any]:
        """Generate comparison chart"""
        try:
            data_spec = {
                "type": "comparison",
                "categories": categories,
                "datasets": datasets,
                "title": title,
                "layout": "comparison"
            }
            
            return await self.generate_infographic(data_spec, layout_hint="comparison")
            
        except Exception as e:
            logger.error(f"Comparison chart generation failed: {e}")
            raise ContentError(f"Comparison chart generation failed: {e}", "comparison")
    
    async def generate_timeline(self, events: List[Dict[str, Any]], 
                              title: str = "Timeline") -> Dict[str, Any]:
        """Generate timeline infographic"""
        try:
            # Sort events by date if date field exists
            sorted_events = sorted(events, key=lambda x: x.get('date', x.get('year', 0)))
            
            data_spec = {
                "type": "timeline",
                "events": sorted_events,
                "title": title,
                "layout": "timeline"
            }
            
            return await self.generate_infographic(data_spec, layout_hint="horizontal")
            
        except Exception as e:
            logger.error(f"Timeline generation failed: {e}")
            raise ContentError(f"Timeline generation failed: {e}", "timeline")
    
    async def generate_process_flow(self, steps: List[Dict[str, Any]], 
                                  title: str = "Process Flow") -> Dict[str, Any]:
        """Generate process flow diagram"""
        try:
            data_spec = {
                "type": "process",
                "steps": steps,
                "title": title,
                "layout": "flow"
            }
            
            return await self.generate_infographic(data_spec, layout_hint="flow")
            
        except Exception as e:
            logger.error(f"Process flow generation failed: {e}")
            raise ContentError(f"Process flow generation failed: {e}", "process")
    
    async def _process_data_spec(self, data_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate data specification"""
        # Handle different data specification formats
        if "data" in data_spec and isinstance(data_spec["data"], list):
            # Direct data format
            return data_spec
        
        elif "csv_data" in data_spec:
            # CSV data - parse it
            return await self._parse_csv_data(data_spec["csv_data"])
        
        elif "database_query" in data_spec:
            # Database query - execute it (placeholder)
            return await self._execute_database_query(data_spec["database_query"])
        
        elif "url" in data_spec:
            # External data source - fetch it
            return await self._fetch_external_data(data_spec["url"])
        
        else:
            # Try to infer structure
            return data_spec
    
    async def _parse_csv_data(self, csv_data: str) -> Dict[str, Any]:
        """Parse CSV data into structured format"""
        try:
            import csv
            import io
            
            reader = csv.DictReader(io.StringIO(csv_data))
            data = list(reader)
            
            return {
                "type": "csv",
                "data": data,
                "columns": reader.fieldnames
            }
            
        except Exception as e:
            raise ContentError(f"Failed to parse CSV data: {e}", "data_parsing")
    
    async def _execute_database_query(self, query: str) -> Dict[str, Any]:
        """Execute database query (placeholder)"""
        # Placeholder implementation
        # In a real implementation, this would connect to a database
        return {
            "type": "database",
            "data": [],
            "query": query
        }
    
    async def _fetch_external_data(self, url: str) -> Dict[str, Any]:
        """Fetch data from external URL"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    # Try to parse as JSON
                    try:
                        data = response.json()
                        return {
                            "type": "external",
                            "data": data,
                            "source": url
                        }
                    except:
                        # Treat as CSV
                        return await self._parse_csv_data(response.text)
                else:
                    raise ContentError(f"Failed to fetch data from {url}: {response.status_code}", "data_fetch")
                    
        except Exception as e:
            raise ContentError(f"Failed to fetch external data: {e}", "data_fetch")
    
    async def _determine_chart_type(self, data: Dict[str, Any]) -> str:
        """Determine optimal chart type for data"""
        data_type = data.get("type", "unknown")
        data_points = data.get("data", [])
        
        if not data_points:
            return "bar"
        
        # Analyze data structure
        sample_point = data_points[0] if data_points else {}
        numeric_fields = [k for k, v in sample_point.items() if isinstance(v, (int, float))]
        
        # Simple heuristics for chart type selection
        if data_type == "timeline":
            return "timeline"
        elif data_type == "comparison":
            return "bar"
        elif len(data_points) > 20:
            return "line"
        elif len(numeric_fields) >= 2:
            return "scatter"
        elif len(data_points) <= 10:
            return "pie"
        else:
            return "bar"
    
    async def _determine_layout(self, data: Dict[str, Any], chart_type: str) -> str:
        """Determine optimal layout for infographic"""
        data_points = data.get("data", [])
        
        if chart_type == "timeline":
            return "horizontal"
        elif chart_type in ["pie", "donut"]:
            return "grid"
        elif len(data_points) > 10:
            return "vertical"
        else:
            return "grid"
    
    async def _generate_infographic_image(self, request: InfographicRequest, 
                                        processed_data: Dict[str, Any]) -> InfographicResult:
        """Generate the actual infographic image"""
        # Get image provider
        image_provider = await self.provider_manager.get_image_provider()
        if not image_provider:
            raise ContentError("No image provider available for infographic generation", "infographic")
        
        # Generate comprehensive prompt for infographic
        prompt = await self._create_infographic_prompt(request, processed_data)
        
        # Generate image
        result = await image_provider.generate_image(
            prompt,
            size=request.size,
            style="infographic"
        )
        
        if not result.success:
            raise ContentError(f"Failed to generate infographic image: {result.error}", "infographic")
        
        # Extract image data and create URL
        image_data = result.data.get("image_data")
        if image_data:
            # Save to storage and get URL
            image_url = await self._save_infographic_image(image_data, request)
        else:
            image_url = result.data.get("image_url", "")
        
        return InfographicResult(
            image_url=image_url,
            meta={
                "provider": result.provider,
                "model": result.model,
                "generation_time": result.metadata.get("generation_time", 0),
                "prompt_used": prompt[:200] + "..." if len(prompt) > 200 else prompt
            },
            data_points=processed_data.get("data", [])
        )
    
    async def _create_infographic_prompt(self, request: InfographicRequest, 
                                       data: Dict[str, Any]) -> str:
        """Create detailed prompt for infographic generation"""
        prompt_parts = []
        
        # Basic infographic description
        prompt_parts.append(f"Create a professional {request.chart_type} infographic")
        
        # Add layout information
        if request.layout_hint:
            prompt_parts.append(f"using {request.layout_hint} layout")
        
        # Add brand preferences
        brand_prefs = request.brand_prefs or {}
        brand_name = brand_prefs.get("brand_name", "")
        if brand_name:
            prompt_parts.append(f"for {brand_name}")
        
        # Add data description
        data_points = data.get("data", [])
        if data_points:
            prompt_parts.append(f"showing {len(data_points)} data points")
            
            # Describe the data
            sample_point = data_points[0]
            if isinstance(sample_point, dict):
                keys = list(sample_point.keys())[:3]  # First 3 keys
                prompt_parts.append(f"with categories: {', '.join(keys)}")
        
        # Add title if available
        title = data.get("title", "") or request.data_spec.get("title", "")
        if title:
            prompt_parts.append(f"titled '{title}'")
        
        # Add style preferences
        style_parts = ["modern", "clean", "professional"]
        
        # Brand colors
        colors = self._get_brand_colors(brand_prefs)
        if colors:
            style_parts.append(f"using colors {', '.join(colors[:3])}")
        
        # Add visual specifications
        style_parts.extend([
            "high contrast text",
            "clear typography",
            "data visualization",
            "infographic style",
            f"size {request.size}",
            "no background clutter",
            "focus on data clarity"
        ])
        
        # Combine all parts
        main_prompt = " ".join(prompt_parts)
        style_prompt = ", ".join(style_parts)
        
        return f"{main_prompt}, {style_prompt}"
    
    def _get_brand_colors(self, brand_prefs: Dict[str, Any]) -> List[str]:
        """Get brand colors or default palette"""
        # Check for explicit brand colors
        brand_colors = brand_prefs.get("colors", [])
        if brand_colors:
            return brand_colors
        
        # Check for brand tone to select palette
        tone = brand_prefs.get("tone_default", "professional")
        
        palette_map = {
            "professional": "corporate",
            "friendly": "modern",
            "corporate": "corporate",
            "casual": "vibrant",
            "minimal": "minimal",
            "creative": "vibrant"
        }
        
        palette_name = palette_map.get(tone, "professional")
        return self.color_palettes.get(palette_name, self.color_palettes["professional"])
    
    async def _save_infographic_image(self, image_data: bytes, request: InfographicRequest) -> str:
        """Save infographic image and return URL"""
        try:
            # In a real implementation, this would save to R2 storage
            import hashlib
            image_hash = hashlib.md5(image_data).hexdigest()
            filename = f"infographic_{image_hash}.png"
            
            # Placeholder URL - would be actual storage URL
            return f"https://storage.example.com/infographics/{filename}"
            
        except Exception as e:
            logger.error(f"Failed to save infographic image: {e}")
            return ""
    
    def get_supported_chart_types(self) -> List[str]:
        """Get list of supported chart types"""
        return self.chart_types.copy()
    
    def get_supported_layouts(self) -> List[str]:
        """Get list of supported layout types"""
        return self.layout_types.copy()
    
    def get_color_palettes(self) -> Dict[str, List[str]]:
        """Get available color palettes"""
        return self.color_palettes.copy()
    
    async def generate_data_story(self, data: List[Dict[str, Any]], 
                                narrative: str) -> Dict[str, Any]:
        """Generate data story with multiple visualizations"""
        try:
            # Get text provider for narrative generation
            text_provider = await self.provider_manager.get_text_provider()
            if not text_provider:
                raise ContentError("No text provider available for data story", "data_story")
            
            # Analyze data and create multiple visualizations
            charts = []
            
            # Overview chart
            overview_chart = await self.generate_chart(data, "bar", "Overview")
            charts.append({
                "type": "overview",
                "chart": overview_chart,
                "description": "Data overview showing main categories"
            })
            
            # Trend analysis if applicable
            if len(data) > 5:
                trend_chart = await self.generate_chart(data, "line", "Trends")
                charts.append({
                    "type": "trend",
                    "chart": trend_chart,
                    "description": "Trend analysis over time"
                })
            
            # Generate narrative text
            narrative_prompt = f"""
            Create a compelling data story narrative based on this data and context:
            
            Context: {narrative}
            Data points: {len(data)}
            
            Generate 3-4 key insights and a conclusion.
            Make it engaging and data-driven.
            """
            
            narrative_result = await text_provider.generate_text(narrative_prompt, max_tokens=800)
            story_text = narrative_result.data if narrative_result.success else narrative
            
            return {
                "story_text": story_text,
                "charts": charts,
                "meta": {
                    "data_points": len(data),
                    "chart_count": len(charts),
                    "narrative_length": len(story_text.split())
                }
            }
            
        except Exception as e:
            logger.error(f"Data story generation failed: {e}")
            raise ContentError(f"Data story generation failed: {e}", "data_story")
    
    async def generate_dashboard_preview(self, widgets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate dashboard preview with multiple widgets"""
        try:
            # Create a dashboard layout with multiple charts
            dashboard_spec = {
                "type": "dashboard",
                "widgets": widgets,
                "layout": "grid",
                "title": "Dashboard Preview"
            }
            
            return await self.generate_infographic(dashboard_spec, layout_hint="grid")
            
        except Exception as e:
            logger.error(f"Dashboard preview generation failed: {e}")
            raise ContentError(f"Dashboard preview generation failed: {e}", "dashboard")
