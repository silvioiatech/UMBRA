"""
Image Generation and Editing - AI-powered image creation, editing, and processing
"""

import logging
import base64
import hashlib
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from ...ai.agent import UmbraAIAgent
from ...core.config import UmbraConfig
from .model_provider import ModelProviderManager
from .errors import MediaError, ProviderError

logger = logging.getLogger(__name__)

@dataclass
class ImageGenerationRequest:
    """Image generation request parameters"""
    prompt: str
    refs: List[str] = None
    size: str = "1024x1024"
    style: str = None
    negative: List[str] = None
    seed: int = None
    model: str = None

@dataclass
class ImageResult:
    """Image generation result"""
    image_url: str
    meta: Dict[str, Any]
    provider: str
    model_used: str
    generation_time: float
    cost_estimate: float = 0.0

class ImageGenerator:
    """AI-powered image generation and editing"""
    
    def __init__(self, ai_agent: UmbraAIAgent, config: UmbraConfig):
        self.ai_agent = ai_agent
        self.config = config
        self.provider_manager = ModelProviderManager(config)
        
        # Image generation settings
        self.default_size = config.get("CREATOR_DEFAULT_IMAGE_SIZE", "1024x1024")
        self.max_images_per_request = config.get("CREATOR_MAX_IMAGES_PER_REQUEST", 4)
        self.quality_mode = config.get("CREATOR_IMAGE_QUALITY", "standard")
        
        # Supported image sizes
        self.supported_sizes = [
            "512x512", "768x768", "1024x1024", "1024x1792", "1792x1024",
            "1:1", "4:5", "16:9", "9:16", "3:2", "2:3"
        ]
        
        logger.info("Image generator initialized")
    
    async def generate_image(self, prompt: str, refs: Optional[List[str]] = None, 
                           size: Optional[str] = None, style: Optional[str] = None, 
                           negative: Optional[List[str]] = None, 
                           seed: Optional[int] = None) -> Dict[str, Any]:
        """Generate image from prompt"""
        try:
            # Validate and prepare request
            request = ImageGenerationRequest(
                prompt=prompt,
                refs=refs or [],
                size=size or self.default_size,
                style=style,
                negative=negative or [],
                seed=seed
            )
            
            # Validate size
            if request.size not in self.supported_sizes:
                raise MediaError(f"Unsupported image size: {request.size}", "image", "generation")
            
            # Enhance prompt with style if provided
            enhanced_prompt = self._enhance_prompt(request.prompt, request.style, request.negative)
            
            # Get available providers
            providers = await self.provider_manager.get_available_providers("image")
            if not providers:
                raise ProviderError("No image generation providers available", "image")
            
            # Try providers in order of preference
            last_error = None
            for provider in providers:
                try:
                    result = await self._generate_with_provider(provider, enhanced_prompt, request)
                    if result:
                        return {
                            "image_url": result.image_url,
                            "meta": result.meta
                        }
                except Exception as e:
                    last_error = e
                    logger.warning(f"Provider {provider} failed: {e}")
                    continue
            
            # If all providers failed
            if last_error:
                raise last_error
            else:
                raise MediaError("All image generation providers failed", "image", "generation")
                
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise MediaError(f"Image generation failed: {e}", "image", "generation")
    
    async def edit_image(self, media_id: str, instructions: str, 
                        mask: Optional[str] = None, size: Optional[str] = None, 
                        style: Optional[str] = None) -> Dict[str, Any]:
        """Edit existing image with AI"""
        try:
            # Get image data
            image_data = await self._get_image_data(media_id)
            if not image_data:
                raise MediaError(f"Image not found: {media_id}", "image", "editing")
            
            # Enhance instructions
            enhanced_instructions = self._enhance_edit_instructions(instructions, style)
            
            # Get available providers for editing
            providers = await self.provider_manager.get_available_providers("image_edit")
            if not providers:
                raise ProviderError("No image editing providers available", "image_edit")
            
            # Try providers
            for provider in providers:
                try:
                    result = await self._edit_with_provider(
                        provider, image_data, enhanced_instructions, mask, size
                    )
                    if result:
                        return {
                            "image_url": result.image_url,
                            "meta": result.meta
                        }
                except Exception as e:
                    logger.warning(f"Provider {provider} failed for editing: {e}")
                    continue
            
            raise MediaError("All image editing providers failed", "image", "editing")
            
        except Exception as e:
            logger.error(f"Image editing failed: {e}")
            raise MediaError(f"Image editing failed: {e}", "image", "editing")
    
    async def upscale_image(self, media_id: str, scale_factor: int = 2) -> Dict[str, Any]:
        """Upscale image using AI"""
        try:
            if scale_factor not in [2, 4]:
                raise MediaError("Scale factor must be 2 or 4", "image", "upscaling")
            
            image_data = await self._get_image_data(media_id)
            if not image_data:
                raise MediaError(f"Image not found: {media_id}", "image", "upscaling")
            
            # Get upscaling providers
            providers = await self.provider_manager.get_available_providers("image_upscale")
            
            for provider in providers:
                try:
                    result = await self._upscale_with_provider(provider, image_data, scale_factor)
                    if result:
                        return {
                            "image_url": result.image_url,
                            "meta": result.meta
                        }
                except Exception as e:
                    logger.warning(f"Upscaling provider {provider} failed: {e}")
                    continue
            
            raise MediaError("All upscaling providers failed", "image", "upscaling")
            
        except Exception as e:
            logger.error(f"Image upscaling failed: {e}")
            raise MediaError(f"Image upscaling failed: {e}", "image", "upscaling")
    
    async def generate_variations(self, media_id: str, count: int = 3, 
                                variation_strength: float = 0.7) -> Dict[str, Any]:
        """Generate variations of an existing image"""
        try:
            if count > self.max_images_per_request:
                raise MediaError(f"Maximum {self.max_images_per_request} variations allowed", "image", "variation")
            
            image_data = await self._get_image_data(media_id)
            if not image_data:
                raise MediaError(f"Image not found: {media_id}", "image", "variation")
            
            providers = await self.provider_manager.get_available_providers("image_variation")
            
            for provider in providers:
                try:
                    results = await self._generate_variations_with_provider(
                        provider, image_data, count, variation_strength
                    )
                    if results:
                        return {
                            "variations": [{"image_url": r.image_url, "meta": r.meta} for r in results],
                            "count": len(results)
                        }
                except Exception as e:
                    logger.warning(f"Variation provider {provider} failed: {e}")
                    continue
            
            raise MediaError("All variation providers failed", "image", "variation")
            
        except Exception as e:
            logger.error(f"Image variation failed: {e}")
            raise MediaError(f"Image variation failed: {e}", "image", "variation")
    
    async def remove_background(self, media_id: str) -> Dict[str, Any]:
        """Remove background from image"""
        try:
            image_data = await self._get_image_data(media_id)
            if not image_data:
                raise MediaError(f"Image not found: {media_id}", "image", "background_removal")
            
            providers = await self.provider_manager.get_available_providers("background_removal")
            
            for provider in providers:
                try:
                    result = await self._remove_background_with_provider(provider, image_data)
                    if result:
                        return {
                            "image_url": result.image_url,
                            "meta": result.meta
                        }
                except Exception as e:
                    logger.warning(f"Background removal provider {provider} failed: {e}")
                    continue
            
            raise MediaError("All background removal providers failed", "image", "background_removal")
            
        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            raise MediaError(f"Background removal failed: {e}", "image", "background_removal")
    
    def _enhance_prompt(self, prompt: str, style: Optional[str], negative: List[str]) -> str:
        """Enhance prompt with style and negative prompts"""
        enhanced = prompt
        
        # Add style guidance
        if style:
            style_prompts = {
                "photorealistic": ", photorealistic, high detail, professional photography",
                "artistic": ", artistic, creative, expressive, fine art",
                "cartoon": ", cartoon style, animated, colorful, cheerful",
                "minimalist": ", minimalist, clean, simple, elegant",
                "vintage": ", vintage, retro, aged, classic style",
                "modern": ", modern, contemporary, sleek, stylish",
                "abstract": ", abstract, geometric, conceptual, artistic",
                "cinematic": ", cinematic, dramatic lighting, movie poster style"
            }
            
            if style.lower() in style_prompts:
                enhanced += style_prompts[style.lower()]
        
        # Add quality enhancers
        enhanced += ", high quality, detailed, professional"
        
        # Handle negative prompts (implementation depends on provider)
        if negative:
            # This would be passed to the provider separately
            pass
        
        return enhanced
    
    def _enhance_edit_instructions(self, instructions: str, style: Optional[str]) -> str:
        """Enhance editing instructions"""
        enhanced = instructions
        
        if style:
            enhanced += f" Apply {style} style."
        
        enhanced += " Maintain image quality and coherence."
        
        return enhanced
    
    async def _generate_with_provider(self, provider: str, prompt: str, 
                                    request: ImageGenerationRequest) -> Optional[ImageResult]:
        """Generate image with specific provider"""
        import time
        start_time = time.time()
        
        try:
            if provider == "stability":
                return await self._generate_with_stability(prompt, request)
            elif provider == "dalle":
                return await self._generate_with_dalle(prompt, request)
            elif provider == "midjourney":
                return await self._generate_with_midjourney(prompt, request)
            elif provider == "replicate":
                return await self._generate_with_replicate(prompt, request)
            else:
                logger.warning(f"Unknown image provider: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"Provider {provider} generation failed: {e}")
            raise ProviderError(f"Provider {provider} failed: {e}", provider, str(e))
    
    async def _generate_with_stability(self, prompt: str, request: ImageGenerationRequest) -> Optional[ImageResult]:
        """Generate image using Stability AI"""
        import httpx
        import time
        
        api_key = self.config.get("CREATOR_STABILITY_API_KEY")
        if not api_key:
            raise ProviderError("Stability AI API key not configured", "stability")
        
        start_time = time.time()
        
        # Convert size format
        size_map = {
            "512x512": (512, 512),
            "768x768": (768, 768),
            "1024x1024": (1024, 1024),
            "1024x1792": (1024, 1792),
            "1792x1024": (1792, 1024)
        }
        
        width, height = size_map.get(request.size, (1024, 1024))
        
        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "steps": 30,
            "samples": 1
        }
        
        if request.seed:
            payload["seed"] = request.seed
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("artifacts"):
                    artifact = result["artifacts"][0]
                    
                    # Create image URL (in real implementation, would upload to storage)
                    image_url = await self._store_image_data(
                        base64.b64decode(artifact["base64"]),
                        f"stability_{int(time.time())}.png"
                    )
                    
                    return ImageResult(
                        image_url=image_url,
                        meta={
                            "provider": "stability",
                            "model": "stable-diffusion-xl",
                            "size": request.size,
                            "seed": artifact.get("seed"),
                            "cfg_scale": 7,
                            "steps": 30
                        },
                        provider="stability",
                        model_used="stable-diffusion-xl",
                        generation_time=time.time() - start_time,
                        cost_estimate=0.05
                    )
            else:
                raise ProviderError(f"Stability AI API error: {response.status_code}", "stability", response.text)
        
        return None
    
    async def _generate_with_dalle(self, prompt: str, request: ImageGenerationRequest) -> Optional[ImageResult]:
        """Generate image using DALL-E"""
        import httpx
        import time
        
        api_key = self.config.get("CREATOR_OPENAI_API_KEY")
        if not api_key:
            raise ProviderError("OpenAI API key not configured", "dalle")
        
        start_time = time.time()
        
        # DALL-E size format
        dalle_size = "1024x1024"  # Default for DALL-E 3
        if request.size in ["512x512", "1024x1024", "1792x1024", "1024x1792"]:
            dalle_size = request.size
        
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "size": dalle_size,
            "quality": self.quality_mode,
            "n": 1
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("data"):
                    image_data = result["data"][0]
                    
                    return ImageResult(
                        image_url=image_data["url"],
                        meta={
                            "provider": "dalle",
                            "model": "dall-e-3",
                            "size": dalle_size,
                            "quality": self.quality_mode,
                            "revised_prompt": image_data.get("revised_prompt")
                        },
                        provider="dalle",
                        model_used="dall-e-3",
                        generation_time=time.time() - start_time,
                        cost_estimate=0.08
                    )
            else:
                raise ProviderError(f"DALL-E API error: {response.status_code}", "dalle", response.text)
        
        return None
    
    async def _generate_with_midjourney(self, prompt: str, request: ImageGenerationRequest) -> Optional[ImageResult]:
        """Generate image using Midjourney (via API)"""
        # Placeholder implementation - would integrate with Midjourney API when available
        logger.info("Midjourney integration not yet implemented")
        return None
    
    async def _generate_with_replicate(self, prompt: str, request: ImageGenerationRequest) -> Optional[ImageResult]:
        """Generate image using Replicate"""
        import httpx
        import time
        
        api_key = self.config.get("CREATOR_REPLICATE_API_TOKEN")
        if not api_key:
            raise ProviderError("Replicate API token not configured", "replicate")
        
        start_time = time.time()
        
        # Use SDXL model on Replicate
        payload = {
            "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            "input": {
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "num_outputs": 1,
                "scheduler": "K_EULER",
                "num_inference_steps": 50,
                "guidance_scale": 7.5
            }
        }
        
        if request.seed:
            payload["input"]["seed"] = request.seed
        
        async with httpx.AsyncClient(timeout=120) as client:
            # Start prediction
            response = await client.post(
                "https://api.replicate.com/v1/predictions",
                json=payload,
                headers={
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 201:
                prediction = response.json()
                prediction_id = prediction["id"]
                
                # Poll for completion
                for _ in range(30):  # Max 5 minutes
                    await asyncio.sleep(10)
                    
                    status_response = await client.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers={"Authorization": f"Token {api_key}"}
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data["status"] == "succeeded":
                            output_urls = status_data["output"]
                            if output_urls:
                                return ImageResult(
                                    image_url=output_urls[0],
                                    meta={
                                        "provider": "replicate",
                                        "model": "sdxl",
                                        "prediction_id": prediction_id,
                                        "guidance_scale": 7.5,
                                        "steps": 50
                                    },
                                    provider="replicate",
                                    model_used="sdxl",
                                    generation_time=time.time() - start_time,
                                    cost_estimate=0.03
                                )
                        elif status_data["status"] == "failed":
                            raise ProviderError("Replicate prediction failed", "replicate", status_data.get("error"))
                
                raise ProviderError("Replicate prediction timeout", "replicate")
            else:
                raise ProviderError(f"Replicate API error: {response.status_code}", "replicate", response.text)
        
        return None
    
    async def _edit_with_provider(self, provider: str, image_data: bytes, 
                                instructions: str, mask: Optional[str], 
                                size: Optional[str]) -> Optional[ImageResult]:
        """Edit image with specific provider"""
        if provider == "dalle":
            return await self._edit_with_dalle(image_data, instructions, mask, size)
        else:
            logger.warning(f"Image editing not supported for provider: {provider}")
            return None
    
    async def _edit_with_dalle(self, image_data: bytes, instructions: str, 
                             mask: Optional[str], size: Optional[str]) -> Optional[ImageResult]:
        """Edit image using DALL-E"""
        # Placeholder implementation
        # Would implement DALL-E image editing API
        logger.info("DALL-E image editing not yet implemented")
        return None
    
    async def _get_image_data(self, media_id: str) -> Optional[bytes]:
        """Get image data by media ID"""
        # Placeholder implementation
        # Would retrieve image data from storage
        logger.info(f"Getting image data for media_id: {media_id}")
        return None
    
    async def _store_image_data(self, image_data: bytes, filename: str) -> str:
        """Store image data and return URL"""
        # Placeholder implementation
        # Would upload to R2 or other storage and return URL
        image_hash = hashlib.md5(image_data).hexdigest()
        return f"https://storage.example.com/images/{image_hash}_{filename}"
    
    def get_supported_sizes(self) -> List[str]:
        """Get list of supported image sizes"""
        return self.supported_sizes.copy()
    
    def get_supported_styles(self) -> List[str]:
        """Get list of supported styles"""
        return [
            "photorealistic", "artistic", "cartoon", "minimalist", 
            "vintage", "modern", "abstract", "cinematic"
        ]
    
    async def get_generation_cost_estimate(self, size: str, provider: str = "auto") -> float:
        """Get cost estimate for image generation"""
        cost_map = {
            "stability": {
                "512x512": 0.02,
                "1024x1024": 0.05,
                "1024x1792": 0.08,
                "1792x1024": 0.08
            },
            "dalle": {
                "1024x1024": 0.08,
                "1024x1792": 0.12,
                "1792x1024": 0.12
            },
            "replicate": {
                "512x512": 0.01,
                "1024x1024": 0.03,
                "1024x1792": 0.05
            }
        }
        
        if provider == "auto":
            providers = await self.provider_manager.get_available_providers("image")
            if providers:
                provider = providers[0]
            else:
                return 0.05  # Default estimate
        
        provider_costs = cost_map.get(provider, cost_map["stability"])
        return provider_costs.get(size, 0.05)
