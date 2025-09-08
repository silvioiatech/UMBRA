"""
Creator Service - Enhanced core service with CRT4 components integration
"""

import logging
import json
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import asyncio

from ...ai.agent import UmbraAIAgent
from ...core.config import UmbraConfig
from .model_provider_enhanced import EnhancedModelProviderManager
from .voice import BrandVoiceManager
from .presets import PlatformPresets
from .validate import ContentValidator
from .templates import TemplateManager
from .connectors import ConnectorManager
from .analytics import CreatorAnalytics, track_operation
from .errors import CreatorError, ProviderError

logger = logging.getLogger(__name__)

@dataclass
class ContentPack:
    """Complete content pack for a topic"""
    caption: str
    cta: str
    titles: List[str]
    hashtags: List[str]
    alt_text: str
    stories: List[str]
    metadata: Dict[str, Any]

@dataclass
class GenerationRequest:
    """Request for content generation"""
    action: str
    topic: str
    platform: Optional[str] = None
    tone: Optional[str] = None
    audience: Optional[str] = None
    length: Optional[str] = None
    brand_id: Optional[str] = None
    template_id: Optional[str] = None
    metadata: Dict[str, Any] = None

class CreatorService:
    """Enhanced core content creation service with CRT4 capabilities"""
    
    def __init__(self, ai_agent: UmbraAIAgent, config: UmbraConfig):
        self.ai_agent = ai_agent
        self.config = config
        
        # Initialize all CRT4 components
        self.provider_manager = EnhancedModelProviderManager(config)
        self.brand_voice = BrandVoiceManager(config)
        self.presets = PlatformPresets(config)
        self.validator = ContentValidator(config)
        self.template_manager = TemplateManager(config)
        self.connector_manager = ConnectorManager(config)
        self.analytics = CreatorAnalytics(config)
        
        # Content limits and settings
        self.max_output_tokens = config.get("CREATOR_MAX_OUTPUT_TOKENS", 2000)
        self.default_tone = config.get("CREATOR_DEFAULT_TONE", "professional")
        self.rate_limit_enabled = config.get("CREATOR_RATE_LIMIT_ENABLED", True)
        self.rate_limit_per_minute = config.get("CREATOR_RATE_LIMIT_REQUESTS_PER_MINUTE", 60)
        
        # Request tracking for rate limiting
        self.request_timestamps = []
        
        # Simple cache for frequently accessed data
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("Enhanced Creator service initialized with CRT4 components")
    
    async def auto_orchestrate(self, input_data: Union[str, Dict], goal: Optional[str] = None, 
                             platform: Optional[str] = None, tone: Optional[str] = None,
                             user_id: Optional[str] = None) -> Dict[str, Any]:
        """Auto-orchestrate content creation from any input with full CRT4 capabilities"""
        with track_operation(self.analytics, "auto_orchestrate", metadata={"goal": goal, "platform": platform}, user_id=user_id):
            try:
                # Check rate limit
                await self._check_rate_limit()
                
                # Detect input type and complexity
                input_analysis = await self._analyze_input(input_data)
                
                # Create orchestration plan
                plan = await self._create_orchestration_plan(input_analysis, goal, platform, tone)
                
                # Execute plan with provider management
                result = await self._execute_orchestration_plan(plan, user_id)
                
                # Track successful orchestration
                self.analytics.track_cost("auto_orchestrate", "creator_service", 
                                        result.get("estimated_cost", 0.0))
                
                return result
                
            except Exception as e:
                logger.error(f"Auto-orchestration failed: {e}")
                raise CreatorError(f"Orchestration failed: {e}")
    
    async def _analyze_input(self, input_data: Union[str, Dict]) -> Dict[str, Any]:
        """Analyze input to determine optimal processing approach"""
        analysis = {
            "input_type": "unknown",
            "complexity": "simple",
            "estimated_tokens": 0,
            "requires_external_data": False,
            "suggested_actions": []
        }
        
        if isinstance(input_data, dict):
            if "media_type" in input_data:
                analysis["input_type"] = "media"
                analysis["complexity"] = "medium"
                analysis["suggested_actions"] = ["generate_caption", "extract_text"]
            elif "url" in input_data:
                analysis["input_type"] = "url"
                analysis["requires_external_data"] = True
                analysis["suggested_actions"] = ["fetch_content", "analyze_page"]
            elif "connector_id" in input_data:
                analysis["input_type"] = "external_data"
                analysis["requires_external_data"] = True
                analysis["suggested_actions"] = ["fetch_assets", "process_documents"]
            else:
                analysis["input_type"] = "structured"
                analysis["complexity"] = "medium"
        
        elif isinstance(input_data, str):
            if input_data.startswith(("http://", "https://")):
                analysis["input_type"] = "url"
                analysis["requires_external_data"] = True
            elif len(input_data.split()) < 10:
                analysis["input_type"] = "topic"
                analysis["complexity"] = "simple"
                analysis["suggested_actions"] = ["generate_post", "content_pack"]
            else:
                analysis["input_type"] = "text"
                analysis["complexity"] = "medium" if len(input_data) > 500 else "simple"
                analysis["suggested_actions"] = ["rewrite", "summarize", "extract_topics"]
            
            analysis["estimated_tokens"] = len(input_data.split()) * 1.3
        
        return analysis
    
    async def _create_orchestration_plan(self, input_analysis: Dict[str, Any], 
                                       goal: Optional[str], platform: Optional[str], 
                                       tone: Optional[str]) -> Dict[str, Any]:
        """Create detailed orchestration plan"""
        plan = {
            "steps": [],
            "estimated_cost": 0.0,
            "estimated_time": 0,
            "required_providers": [],
            "fallback_options": []
        }
        
        input_type = input_analysis["input_type"]
        complexity = input_analysis["complexity"]
        
        # Plan based on goal and input type
        if goal == "social_media_campaign":
            plan["steps"] = [
                {"action": "generate_post", "priority": 1},
                {"action": "generate_hashtags", "priority": 2},
                {"action": "generate_title_variations", "priority": 2},
                {"action": "generate_image", "priority": 3},
                {"action": "validate_content", "priority": 4}
            ]
            plan["required_providers"] = ["text", "image"]
            
        elif goal == "content_pack" or not goal:
            if input_type == "topic":
                plan["steps"] = [
                    {"action": "generate_content_pack", "priority": 1},
                    {"action": "validate_content", "priority": 2}
                ]
            elif input_type == "text":
                plan["steps"] = [
                    {"action": "rewrite", "priority": 1},
                    {"action": "generate_hashtags", "priority": 2},
                    {"action": "validate_content", "priority": 3}
                ]
            plan["required_providers"] = ["text"]
        
        elif goal == "multimedia":
            plan["steps"] = [
                {"action": "generate_content_pack", "priority": 1},
                {"action": "generate_image", "priority": 2},
                {"action": "generate_video", "priority": 3},
                {"action": "validate_content", "priority": 4}
            ]
            plan["required_providers"] = ["text", "image", "video"]
        
        # Estimate costs and time
        plan["estimated_cost"] = len(plan["steps"]) * 0.05  # Base estimate
        plan["estimated_time"] = len(plan["steps"]) * 10   # Seconds
        
        if complexity == "complex":
            plan["estimated_cost"] *= 2
            plan["estimated_time"] *= 1.5
        
        return plan
    
    async def _execute_orchestration_plan(self, plan: Dict[str, Any], 
                                        user_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute orchestration plan with error handling and fallbacks"""
        results = {}
        errors = []
        
        # Check provider availability
        available_providers = await self._check_provider_availability(plan["required_providers"])
        if not available_providers:
            raise ProviderError("No required providers available")
        
        # Execute steps in priority order
        sorted_steps = sorted(plan["steps"], key=lambda x: x["priority"])
        
        for step in sorted_steps:
            try:
                action = step["action"]
                
                if action == "generate_content_pack":
                    result = await self.generate_content_pack(user_id=user_id)
                elif action == "generate_post":
                    result = await self.generate_post(user_id=user_id)
                elif action == "generate_hashtags":
                    result = await self.generate_hashtags("general topic", user_id=user_id)
                elif action == "validate_content":
                    # Validate previous results
                    if "content_pack" in results:
                        result = await self.validator.validate_content(
                            results["content_pack"].get("caption", "")
                        )
                    else:
                        result = {"validation": "skipped"}
                else:
                    # Skip unknown actions
                    continue
                
                results[action] = result
                
            except Exception as e:
                logger.warning(f"Step {action} failed: {e}")
                errors.append({"step": action, "error": str(e)})
        
        return {
            "results": results,
            "errors": errors,
            "plan_executed": plan,
            "execution_time": plan["estimated_time"],
            "estimated_cost": plan["estimated_cost"]
        }
    
    async def _check_provider_availability(self, required_providers: List[str]) -> Dict[str, bool]:
        """Check availability of required providers"""
        availability = {}
        
        for provider_type in required_providers:
            try:
                if provider_type == "text":
                    provider = await self.provider_manager.get_text_provider()
                elif provider_type == "image":
                    provider = await self.provider_manager.get_image_provider()
                elif provider_type == "video":
                    provider = await self.provider_manager.get_video_provider()
                elif provider_type == "audio":
                    provider = await self.provider_manager.get_tts_provider()
                else:
                    provider = None
                
                availability[provider_type] = provider is not None
                
            except Exception as e:
                logger.warning(f"Provider check failed for {provider_type}: {e}")
                availability[provider_type] = False
        
        return availability
    
    async def generate_post(self, topic: str = "general content", platform: Optional[str] = None, 
                          tone: Optional[str] = None, audience: Optional[str] = None, 
                          length: Optional[str] = None, brand_id: Optional[str] = None,
                          template_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Enhanced post generation with full CRT4 integration"""
        with track_operation(self.analytics, "generate_post", metadata={"platform": platform, "tone": tone}, user_id=user_id):
            try:
                await self._check_rate_limit()
                
                # Get brand voice and merge with request
                brand_voice = await self.brand_voice.get_brand_voice(brand_id or "default")
                platform_preset = self.presets.get_platform_preset(platform) if platform else {}
                
                # Merge all configuration sources
                merged_config = await self.brand_voice.merge_brand_voice_with_request(
                    {"tone": tone, "audience": audience, "length": length},
                    platform_preset,
                    brand_id or "default"
                )
                
                # Use template if specified
                if template_id:
                    return await self._generate_from_template(template_id, {"topic": topic}, merged_config)
                
                # Generate post content with enhanced provider management
                text_provider = await self.provider_manager.get_text_provider()
                if not text_provider:
                    raise ProviderError("No text provider available")
                
                # Build enhanced prompt
                prompt = self._build_enhanced_post_prompt(topic, platform, merged_config, brand_voice)
                
                # Generate with provider
                result = await text_provider.generate_text(
                    prompt=prompt,
                    max_tokens=min(self.max_output_tokens, platform_preset.get("max_tokens", 1000)),
                    temperature=0.7
                )
                
                if not result.success:
                    raise CreatorError(f"Text generation failed: {result.error}")
                
                post_content = result.data.get("text", "")
                
                # Post-process and validate
                post_content = self._post_process_content(post_content, platform_preset)
                
                # Enhanced validation
                validation_result = await self.validator.validate_content(post_content, None, platform)
                brand_validation = self.brand_voice.validate_content_against_brand_voice(post_content, brand_voice)
                
                # Track usage
                self.analytics.track_cost("generate_post", result.provider, 
                                        result.metadata.get("cost", 0.01))
                
                return {
                    "content": post_content,
                    "platform": platform,
                    "tone": merged_config.get("tone_default", self.default_tone),
                    "validation": validation_result,
                    "brand_validation": brand_validation,
                    "provider_used": result.provider,
                    "model_used": result.model,
                    "metadata": {
                        "topic": topic,
                        "word_count": len(post_content.split()),
                        "char_count": len(post_content),
                        "generated_at": self._get_timestamp(),
                        "template_id": template_id,
                        "brand_id": brand_id,
                        "generation_time": result.metadata.get("generation_time", 0)
                    }
                }
                
            except Exception as e:
                logger.error(f"Enhanced post generation failed: {e}")
                raise CreatorError(f"Post generation failed: {e}")
    
    async def generate_content_pack(self, topic: str = "general content", platform: Optional[str] = None, 
                                  tone: Optional[str] = None, audience: Optional[str] = None,
                                  brand_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Enhanced content pack generation"""
        with track_operation(self.analytics, "generate_content_pack", metadata={"platform": platform}, user_id=user_id):
            try:
                await self._check_rate_limit()
                
                # Generate all components in parallel with error handling
                tasks = [
                    self.generate_post(topic, platform, tone, audience, "medium", brand_id, user_id=user_id),
                    self._generate_cta(topic, platform, tone, brand_id),
                    self.generate_title_variations(topic, 3, platform, user_id=user_id),
                    self.generate_hashtags(topic, platform, 10, user_id=user_id),
                    self._generate_alt_text(topic),
                    self._generate_story_captions(topic, platform, tone, 3)
                ]
                
                try:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                except Exception as e:
                    logger.error(f"Parallel generation failed: {e}")
                    # Fallback to sequential generation
                    results = []
                    for task in tasks:
                        try:
                            result = await task
                            results.append(result)
                        except Exception as task_error:
                            logger.warning(f"Task failed: {task_error}")
                            results.append({"error": str(task_error)})
                
                # Process results
                caption_result = results[0] if not isinstance(results[0], Exception) else {"content": "Failed to generate caption"}
                cta = results[1] if not isinstance(results[1], Exception) else "Learn more!"
                titles = results[2] if not isinstance(results[2], Exception) else ["Title unavailable"]
                hashtags = results[3] if not isinstance(results[3], Exception) else ["#content"]
                alt_text = results[4] if not isinstance(results[4], Exception) else "Content image"
                stories = results[5] if not isinstance(results[5], Exception) else ["Story unavailable"]
                
                content_pack = ContentPack(
                    caption=caption_result.get("content", ""),
                    cta=cta,
                    titles=titles,
                    hashtags=hashtags,
                    alt_text=alt_text,
                    stories=stories,
                    metadata={
                        "topic": topic,
                        "platform": platform,
                        "tone": tone,
                        "brand_id": brand_id,
                        "generated_at": self._get_timestamp(),
                        "generation_success_rate": sum(1 for r in results if not isinstance(r, Exception)) / len(results)
                    }
                )
                
                return {
                    "pack": asdict(content_pack),
                    "validation": caption_result.get("validation", {}),
                    "brand_validation": caption_result.get("brand_validation", {}),
                    "provider_used": caption_result.get("provider_used", "unknown"),
                    "errors": [str(r) for r in results if isinstance(r, Exception)]
                }
                
            except Exception as e:
                logger.error(f"Enhanced content pack generation failed: {e}")
                raise CreatorError(f"Content pack generation failed: {e}")
    
    async def _generate_from_template(self, template_id: str, variables: Dict[str, Any], 
                                    config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content from template"""
        try:
            # Track template usage
            self.analytics.track_event(
                event_type="template_used",
                action="render_template",
                metadata={"template_id": template_id}
            )
            
            rendered_content = await self.template_manager.render_template(template_id, variables)
            
            # Apply brand voice validation
            brand_voice = await self.brand_voice.get_brand_voice()
            brand_validation = self.brand_voice.validate_content_against_brand_voice(rendered_content, brand_voice)
            
            return {
                "content": rendered_content,
                "template_id": template_id,
                "variables_used": variables,
                "brand_validation": brand_validation,
                "metadata": {
                    "generation_method": "template",
                    "generated_at": self._get_timestamp()
                }
            }
            
        except Exception as e:
            logger.error(f"Template generation failed: {e}")
            raise CreatorError(f"Template generation failed: {e}")
    
    async def _generate_story_captions(self, topic: str, platform: Optional[str], 
                                     tone: Optional[str], count: int = 3) -> List[str]:
        """Generate story captions for platforms that support them"""
        try:
            if platform not in ["instagram", "facebook", "snapchat"]:
                return []  # Platform doesn't support stories
            
            text_provider = await self.provider_manager.get_text_provider()
            if not text_provider:
                return []
            
            prompt = f"""Generate {count} engaging story captions for {platform} about: {topic}
            
            Requirements:
            - Short and punchy (1-2 sentences each)
            - Tone: {tone or 'engaging'}
            - Optimized for story format
            - Include call-to-action
            
            Story captions:"""
            
            result = await text_provider.generate_text(prompt, max_tokens=200, temperature=0.8)
            
            if result.success:
                stories = []
                for line in result.data.get("text", "").strip().split('\n'):
                    caption = line.strip()
                    if caption and not caption.startswith('#'):
                        stories.append(caption)
                return stories[:count]
            
            return []
            
        except Exception as e:
            logger.warning(f"Story caption generation failed: {e}")
            return []
    
    async def generate_hashtags(self, topic: str, platform: Optional[str] = None, 
                              count: int = 10, user_id: Optional[str] = None) -> List[str]:
        """Enhanced hashtag generation with analytics tracking"""
        with track_operation(self.analytics, "generate_hashtags", metadata={"platform": platform}, user_id=user_id):
            try:
                await self._check_rate_limit()
                
                # Check cache first
                cache_key = f"hashtags_{hash(topic)}_{platform}_{count}"
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    return cached_result
                
                platform_preset = self.presets.get_platform_preset(platform) if platform else {}
                max_hashtags = platform_preset.get("max_hashtags", count)
                
                text_provider = await self.provider_manager.get_text_provider()
                if not text_provider:
                    raise ProviderError("No text provider available")
                
                prompt = f"""Generate {min(count, max_hashtags)} relevant hashtags for: {topic}
                
                Platform: {platform or 'general social media'}
                
                Requirements:
                - Popular and discoverable hashtags
                - Mix of broad and specific tags
                - Follow {platform or 'general'} best practices
                - Return only hashtags, one per line, with # symbol
                
                Hashtags:"""
                
                result = await text_provider.generate_text(prompt, max_tokens=300, temperature=0.7)
                
                if not result.success:
                    raise CreatorError(f"Hashtag generation failed: {result.error}")
                
                # Parse hashtags
                hashtags = []
                for line in result.data.get("text", "").strip().split('\n'):
                    tag = line.strip()
                    if tag and tag.startswith('#'):
                        hashtags.append(tag)
                    elif tag and not tag.startswith('#'):
                        hashtags.append(f'#{tag}')
                
                final_hashtags = hashtags[:count]
                
                # Cache result
                self._cache_result(cache_key, final_hashtags)
                
                return final_hashtags
                
            except Exception as e:
                logger.error(f"Enhanced hashtag generation failed: {e}")
                raise CreatorError(f"Hashtag generation failed: {e}")
    
    async def generate_title_variations(self, topic: str, count: int = 3, 
                                      platform: Optional[str] = None, 
                                      user_id: Optional[str] = None) -> List[str]:
        """Enhanced title generation with analytics"""
        with track_operation(self.analytics, "generate_title_variations", metadata={"platform": platform}, user_id=user_id):
            try:
                await self._check_rate_limit()
                
                platform_preset = self.presets.get_platform_preset(platform) if platform else {}
                max_title_length = platform_preset.get("max_title_length", 100)
                
                text_provider = await self.provider_manager.get_text_provider()
                if not text_provider:
                    raise ProviderError("No text provider available")
                
                prompt = f"""Generate {count} engaging title variations for: {topic}
                
                Platform: {platform or 'general'}
                Max length: {max_title_length} characters
                
                Requirements:
                - Engaging and click-worthy
                - Different angles/approaches
                - Appropriate for {platform or 'general'} audience
                - Stay within character limit
                
                Titles:"""
                
                result = await text_provider.generate_text(prompt, max_tokens=400, temperature=0.8)
                
                if not result.success:
                    raise CreatorError(f"Title generation failed: {result.error}")
                
                # Parse titles
                titles = []
                for line in result.data.get("text", "").strip().split('\n'):
                    title = line.strip()
                    if title and not title.startswith(('#', '-', '*')):
                        titles.append(title[:max_title_length])
                    elif title.startswith(('-', '*')):
                        titles.append(title[1:].strip()[:max_title_length])
                
                return titles[:count]
                
            except Exception as e:
                logger.error(f"Enhanced title generation failed: {e}")
                raise CreatorError(f"Title generation failed: {e}")
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting"""
        if not self.rate_limit_enabled:
            return
        
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 60
        ]
        
        # Check if rate limit exceeded
        if len(self.request_timestamps) >= self.rate_limit_per_minute:
            self.analytics.track_event(
                event_type="rate_limit",
                action="rate_limit_exceeded",
                metadata={"requests_per_minute": len(self.request_timestamps)}
            )
            raise CreatorError("Rate limit exceeded. Please wait before making more requests.")
        
        # Add current request
        self.request_timestamps.append(current_time)
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired"""
        if key in self.cache:
            item, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return item
            else:
                del self.cache[key]
        return None
    
    def _cache_result(self, key: str, value: Any) -> None:
        """Cache result with timestamp"""
        self.cache[key] = (value, time.time())
        
        # Simple cache cleanup - remove oldest items if cache gets too large
        if len(self.cache) > 1000:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
    
    def _build_enhanced_post_prompt(self, topic: str, platform: Optional[str], 
                                  config: Dict[str, Any], brand_voice: Dict[str, Any]) -> str:
        """Build enhanced post generation prompt with brand voice integration"""
        base_prompt = f"Create a {platform or 'social media'} post about: {topic}"
        
        # Apply brand voice to prompt
        enhanced_prompt = self.brand_voice.apply_brand_voice_to_prompt(base_prompt, brand_voice)
        
        # Add platform-specific guidance
        char_limit = config.get("char_limit", 2000)
        enhanced_prompt += f"\n\nCharacter limit: {char_limit}"
        
        # Add additional constraints
        if config.get("emoji_policy") == "none":
            enhanced_prompt += "\n- Do not use emojis"
        elif config.get("emoji_policy") == "liberal":
            enhanced_prompt += "\n- Use emojis generously for engagement"
        
        if config.get("link_policy") == "end":
            enhanced_prompt += "\n- Place any links at the end"
        
        enhanced_prompt += "\n\nPost content:"
        
        return enhanced_prompt
    
    def _post_process_content(self, content: str, platform_preset: Dict) -> str:
        """Enhanced post-processing with platform-specific rules"""
        # Trim to character limit
        char_limit = platform_preset.get("char_limit")
        if char_limit and len(content) > char_limit:
            content = content[:char_limit-3] + "..."
        
        # Clean up formatting
        content = content.strip()
        
        # Platform-specific adjustments
        if platform_preset.get("name") == "twitter":
            # Ensure content works for Twitter's character limit
            content = content.replace("\n\n", "\n")  # Reduce double line breaks
        
        return content
    
    async def _generate_cta(self, topic: str, platform: Optional[str] = None, 
                          tone: Optional[str] = None, brand_id: Optional[str] = None) -> str:
        """Enhanced CTA generation"""
        try:
            brand_voice = await self.brand_voice.get_brand_voice(brand_id or "default")
            cta_style = brand_voice.get("cta_style", "engaging")
            
            text_provider = await self.provider_manager.get_text_provider()
            if not text_provider:
                return "Learn more!"
            
            prompt = f"""Generate a compelling call-to-action for: {topic}
            
            Platform: {platform or 'general'}
            Style: {cta_style}
            Tone: {tone or 'engaging'}
            
            Requirements:
            - Single sentence or phrase
            - Action-oriented
            - Appropriate for {platform or 'social media'}
            
            CTA:"""
            
            result = await text_provider.generate_text(prompt, max_tokens=50, temperature=0.7)
            
            if result.success:
                return result.data.get("text", "").strip()
            else:
                return "Learn more!"
                
        except Exception as e:
            logger.warning(f"CTA generation failed: {e}")
            return "Learn more!"
    
    async def _generate_alt_text(self, topic: str) -> str:
        """Enhanced alt text generation"""
        try:
            text_provider = await self.provider_manager.get_text_provider()
            if not text_provider:
                return f"Image related to {topic}"
            
            prompt = f"""Generate descriptive alt text for an image about: {topic}
            
            Requirements:
            - Concise but descriptive
            - Accessible for screen readers
            - Focus on key visual elements
            - 125 characters or less
            
            Alt text:"""
            
            result = await text_provider.generate_text(prompt, max_tokens=50, temperature=0.5)
            
            if result.success:
                alt_text = result.data.get("text", "").strip()
                return alt_text[:125]  # Enforce character limit
            else:
                return f"Image related to {topic}"
                
        except Exception as e:
            logger.warning(f"Alt text generation failed: {e}")
            return f"Image related to {topic}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_hit_rate": 0.0,  # Would need tracking for real implementation
            "rate_limit_enabled": self.rate_limit_enabled,
            "current_rate_limit_usage": len(self.request_timestamps),
            "max_rate_limit": self.rate_limit_per_minute,
            "provider_manager_status": self.provider_manager.get_configuration_status(),
            "analytics_enabled": self.analytics.enabled,
            "health_status": self.analytics.get_health_status()
        }
    
    async def clear_cache(self) -> bool:
        """Clear service cache"""
        try:
            self.cache.clear()
            logger.info("Service cache cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    # Legacy methods for backward compatibility
    async def ingest_media(self, file_data: Optional[bytes] = None, 
                         url: Optional[str] = None) -> Dict[str, Any]:
        """Legacy media ingestion (maintained for compatibility)"""
        return await self._ingest_media_legacy(file_data, url)
    
    async def estimate_requirements(self, brief: Optional[str] = None, 
                                  media: Optional[Dict] = None, 
                                  text: Optional[str] = None, 
                                  platform: Optional[str] = None) -> Dict[str, Any]:
        """Legacy requirements estimation (maintained for compatibility)"""
        return await self._estimate_requirements_legacy(brief, media, text, platform)
    
    async def batch_generate(self, task_spec: Dict[str, Any], variations: int) -> List[Dict[str, Any]]:
        """Legacy batch generation (maintained for compatibility)"""
        return await self._batch_generate_legacy(task_spec, variations)
    
    async def generate_ab_variants(self, brief: str, k: int = 3) -> Dict[str, Any]:
        """Legacy A/B variant generation (maintained for compatibility)"""
        return await self._generate_ab_variants_legacy(brief, k)
    
    # Helper methods for legacy support
    async def _ingest_media_legacy(self, file_data: Optional[bytes], url: Optional[str]) -> Dict[str, Any]:
        """Legacy media ingestion implementation"""
        # Simplified implementation for backward compatibility
        if url:
            media_id = f"url_{hash(url)}"
            return {"media_id": media_id, "type": "url", "source_url": url}
        elif file_data:
            import hashlib
            file_hash = hashlib.md5(file_data).hexdigest()
            media_id = f"file_{file_hash}"
            return {"media_id": media_id, "type": "file", "file_hash": file_hash}
        else:
            raise CreatorError("No file or URL provided")
    
    async def _estimate_requirements_legacy(self, brief: Optional[str], media: Optional[Dict], 
                                          text: Optional[str], platform: Optional[str]) -> Dict[str, Any]:
        """Legacy requirements estimation"""
        return {
            "token_estimate": 100,
            "time_estimate_seconds": 30,
            "cost_estimate_usd": 0.05,
            "complexity": "medium"
        }
    
    async def _batch_generate_legacy(self, task_spec: Dict[str, Any], variations: int) -> List[Dict[str, Any]]:
        """Legacy batch generation"""
        # Simplified batch generation for compatibility
        results = []
        for i in range(min(variations, 10)):  # Limit to 10 for safety
            try:
                result = await self.generate_post(f"Topic {i+1}")
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        return results
    
    async def _generate_ab_variants_legacy(self, brief: str, k: int = 3) -> Dict[str, Any]:
        """Legacy A/B variant generation"""
        variants = []
        for i in range(min(k, 5)):  # Limit to 5 for safety
            try:
                result = await self.generate_post(f"{brief} (variant {i+1})")
                variants.append({
                    "variant_id": f"variant_{i+1}",
                    "content": result.get("content", ""),
                    "scores": {"combined": 0.8 - (i * 0.1)}  # Mock scoring
                })
            except Exception as e:
                variants.append({
                    "variant_id": f"variant_{i+1}",
                    "content": f"Error: {e}",
                    "scores": {"combined": 0.0}
                })
        
        return {
            "variants": variants,
            "best_variant": variants[0] if variants else None,
            "metadata": {"brief": brief, "variant_count": k}
        }
