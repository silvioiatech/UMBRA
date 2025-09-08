"""
Enhanced Model Provider Manager - CRT4 Implementation
Handles routing between different AI providers with standardized interfaces
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
import asyncio

from ...core.config import UmbraConfig
from .errors import ProviderError
from .providers import (
    ProviderFactory, TextProvider, ImageProvider, VideoProvider, 
    TTSProvider, MusicProvider, ASRProvider, ProviderResponse
)

logger = logging.getLogger(__name__)

@dataclass
class ProviderConfig:
    """Configuration for a specific provider"""
    name: str
    api_key: str
    base_url: str
    capabilities: List[str]
    priority: int = 5
    enabled: bool = True
    rate_limit: Optional[int] = None
    cost_per_token: float = 0.0
    cost_per_request: float = 0.0

class EnhancedModelProviderManager:
    """Enhanced manager for multiple AI model providers with CRT4 features"""
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        self.providers = {}
        self.provider_instances = {}
        self._load_provider_configs()
        self._initialize_provider_instances()
        
        logger.info(f"Enhanced provider manager initialized with {len(self.providers)} providers")
    
    def _load_provider_configs(self):
        """Load provider configurations from environment"""
        
        # Text providers (OpenRouter first, with Creator overrides)
        openrouter_key = self.config.get("OPENROUTER_API_KEY")
        if openrouter_key:
            # Check for Creator-specific override
            creator_model = self.config.get("CREATOR_OPENROUTER_MODEL_TEXT") or \
                          self.config.get("OPENROUTER_MODEL_CHAT") or \
                          self.config.get("OPENROUTER_DEFAULT_MODEL", "anthropic/claude-3.5-sonnet:beta")
            
            self.providers["openrouter"] = ProviderConfig(
                name="openrouter",
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                capabilities=["text", "chat", "completion"],
                priority=1,
                enabled=True,
                cost_per_token=0.00001
            )
        
        # Image providers
        self._load_image_providers()
        
        # Video providers
        self._load_video_providers()
        
        # Audio/TTS providers
        self._load_audio_providers()
        
        # Music providers
        self._load_music_providers()
        
        # ASR providers
        self._load_asr_providers()
    
    def _load_image_providers(self):
        """Load image generation providers"""
        image_provider = self.config.get("CREATOR_IMAGE_PROVIDER", "stability")
        
        # Stability AI
        stability_key = self.config.get("CREATOR_STABILITY_API_KEY")
        if stability_key:
            priority = 1 if image_provider == "stability" else 2
            self.providers["stability"] = ProviderConfig(
                name="stability",
                api_key=stability_key,
                base_url="https://api.stability.ai/v1",
                capabilities=["image", "image_edit", "image_upscale"],
                priority=priority,
                enabled=True,
                cost_per_request=0.05
            )
        
        # OpenAI DALL-E
        openai_key = self.config.get("CREATOR_OPENAI_API_KEY")
        if openai_key:
            priority = 1 if image_provider == "openai" else 3
            self.providers["dalle"] = ProviderConfig(
                name="dalle",
                api_key=openai_key,
                base_url="https://api.openai.com/v1",
                capabilities=["image", "image_edit", "image_variation"],
                priority=priority,
                enabled=True,
                cost_per_request=0.08
            )
        
        # Replicate
        replicate_token = self.config.get("CREATOR_REPLICATE_API_TOKEN")
        if replicate_token:
            priority = 1 if image_provider == "replicate" else 4
            self.providers["replicate_image"] = ProviderConfig(
                name="replicate_image",
                api_key=replicate_token,
                base_url="https://api.replicate.com/v1",
                capabilities=["image", "image_upscale", "image_variation"],
                priority=priority,
                enabled=True,
                cost_per_request=0.03
            )
    
    def _load_video_providers(self):
        """Load video generation providers"""
        video_provider = self.config.get("CREATOR_VIDEO_PROVIDER", "replicate")
        
        # Pika Labs
        pika_key = self.config.get("CREATOR_PIKA_API_KEY")
        if pika_key:
            priority = 1 if video_provider == "pika" else 2
            self.providers["pika"] = ProviderConfig(
                name="pika",
                api_key=pika_key,
                base_url="https://api.pika.art/v1",
                capabilities=["video", "image_to_video"],
                priority=priority,
                enabled=True,
                cost_per_request=0.3
            )
        
        # Runway ML
        runway_key = self.config.get("CREATOR_RUNWAY_API_KEY")
        if runway_key:
            priority = 1 if video_provider == "runway" else 2
            self.providers["runway"] = ProviderConfig(
                name="runway",
                api_key=runway_key,
                base_url="https://api.runwayml.com/v1",
                capabilities=["video", "video_edit", "image_to_video"],
                priority=priority,
                enabled=True,
                cost_per_request=0.5
            )
        
        # Replicate (video models)
        replicate_token = self.config.get("CREATOR_REPLICATE_API_TOKEN")
        if replicate_token:
            priority = 1 if video_provider == "replicate" else 3
            self.providers["replicate_video"] = ProviderConfig(
                name="replicate_video",
                api_key=replicate_token,
                base_url="https://api.replicate.com/v1",
                capabilities=["video", "image_to_video"],
                priority=priority,
                enabled=True,
                cost_per_request=0.4
            )
    
    def _load_audio_providers(self):
        """Load audio/TTS providers"""
        tts_provider = self.config.get("CREATOR_TTS_PROVIDER", "elevenlabs")
        
        # ElevenLabs
        elevenlabs_key = self.config.get("CREATOR_ELEVENLABS_API_KEY")
        if elevenlabs_key:
            priority = 1 if tts_provider == "elevenlabs" else 2
            self.providers["elevenlabs"] = ProviderConfig(
                name="elevenlabs",
                api_key=elevenlabs_key,
                base_url="https://api.elevenlabs.io/v1",
                capabilities=["tts", "voice_cloning", "audio"],
                priority=priority,
                enabled=True,
                cost_per_request=0.02
            )
        
        # OpenAI TTS
        openai_key = self.config.get("CREATOR_OPENAI_API_KEY")
        if openai_key:
            priority = 1 if tts_provider == "openai" else 2
            self.providers["openai_tts"] = ProviderConfig(
                name="openai_tts",
                api_key=openai_key,
                base_url="https://api.openai.com/v1",
                capabilities=["tts", "audio"],
                priority=priority,
                enabled=True,
                cost_per_request=0.015
            )
    
    def _load_music_providers(self):
        """Load music generation providers"""
        music_provider = self.config.get("CREATOR_MUSIC_PROVIDER", "replicate")
        
        # Suno AI
        suno_key = self.config.get("CREATOR_SUNO_API_KEY")
        if suno_key:
            priority = 1 if music_provider == "suno" else 2
            self.providers["suno"] = ProviderConfig(
                name="suno",
                api_key=suno_key,
                base_url="https://api.suno.ai/v1",
                capabilities=["music", "audio", "vocals"],
                priority=priority,
                enabled=True,
                cost_per_request=0.1
            )
        
        # Replicate music models
        replicate_token = self.config.get("CREATOR_REPLICATE_API_TOKEN")
        if replicate_token:
            priority = 1 if music_provider == "replicate" else 3
            self.providers["replicate_music"] = ProviderConfig(
                name="replicate_music",
                api_key=replicate_token,
                base_url="https://api.replicate.com/v1",
                capabilities=["music", "audio"],
                priority=priority,
                enabled=True,
                cost_per_request=0.08
            )
    
    def _load_asr_providers(self):
        """Load ASR/transcription providers"""
        asr_provider = self.config.get("CREATOR_ASR_PROVIDER", "openai")
        
        # OpenAI Whisper
        openai_key = self.config.get("CREATOR_OPENAI_API_KEY")
        if openai_key:
            priority = 1 if asr_provider == "openai" else 2
            self.providers["whisper"] = ProviderConfig(
                name="whisper",
                api_key=openai_key,
                base_url="https://api.openai.com/v1",
                capabilities=["asr", "transcription", "translation"],
                priority=priority,
                enabled=True,
                cost_per_request=0.006
            )
        
        # Deepgram
        deepgram_key = self.config.get("CREATOR_DEEPGRAM_API_KEY")
        if deepgram_key:
            priority = 1 if asr_provider == "deepgram" else 2
            self.providers["deepgram"] = ProviderConfig(
                name="deepgram",
                api_key=deepgram_key,
                base_url="https://api.deepgram.com/v1",
                capabilities=["asr", "transcription", "diarization"],
                priority=priority,
                enabled=True,
                cost_per_request=0.005
            )
    
    def _initialize_provider_instances(self):
        """Initialize provider instances using factory"""
        for provider_name, provider_config in self.providers.items():
            try:
                if not provider_config.enabled or not provider_config.api_key:
                    continue
                
                config_dict = {
                    "name": provider_config.name,
                    "api_key": provider_config.api_key,
                    "base_url": provider_config.base_url,
                    "enabled": provider_config.enabled
                }
                
                # Create provider instances based on capabilities
                if "text" in provider_config.capabilities:
                    instance = ProviderFactory.create_text_provider(provider_name, config_dict)
                    if instance:
                        self.provider_instances[f"{provider_name}_text"] = instance
                
                if "image" in provider_config.capabilities:
                    base_name = provider_name.replace("_image", "")
                    instance = ProviderFactory.create_image_provider(base_name, config_dict)
                    if instance:
                        self.provider_instances[f"{provider_name}_image"] = instance
                
                if "video" in provider_config.capabilities:
                    base_name = provider_name.replace("_video", "")
                    instance = ProviderFactory.create_video_provider(base_name, config_dict)
                    if instance:
                        self.provider_instances[f"{provider_name}_video"] = instance
                
                if "tts" in provider_config.capabilities:
                    base_name = provider_name.replace("_tts", "")
                    instance = ProviderFactory.create_tts_provider(base_name, config_dict)
                    if instance:
                        self.provider_instances[f"{provider_name}_tts"] = instance
                
                if "music" in provider_config.capabilities:
                    base_name = provider_name.replace("_music", "")
                    instance = ProviderFactory.create_music_provider(base_name, config_dict)
                    if instance:
                        self.provider_instances[f"{provider_name}_music"] = instance
                
                if "asr" in provider_config.capabilities:
                    instance = ProviderFactory.create_asr_provider(provider_name, config_dict)
                    if instance:
                        self.provider_instances[f"{provider_name}_asr"] = instance
                        
            except Exception as e:
                logger.warning(f"Failed to initialize provider {provider_name}: {e}")
    
    async def get_text_provider(self) -> Optional[TextProvider]:
        """Get the best available text provider"""
        providers = await self.get_available_providers("text")
        for provider_name in providers:
            instance_key = f"{provider_name}_text"
            if instance_key in self.provider_instances:
                return self.provider_instances[instance_key]
        return None
    
    async def get_image_provider(self) -> Optional[ImageProvider]:
        """Get the best available image provider"""
        providers = await self.get_available_providers("image")
        for provider_name in providers:
            # Handle different naming patterns
            for suffix in ["_image", ""]:
                instance_key = f"{provider_name}{suffix}_image"
                if instance_key in self.provider_instances:
                    return self.provider_instances[instance_key]
        return None
    
    async def get_video_provider(self) -> Optional[VideoProvider]:
        """Get the best available video provider"""
        providers = await self.get_available_providers("video")
        for provider_name in providers:
            for suffix in ["_video", ""]:
                instance_key = f"{provider_name}{suffix}_video"
                if instance_key in self.provider_instances:
                    return self.provider_instances[instance_key]
        return None
    
    async def get_tts_provider(self) -> Optional[TTSProvider]:
        """Get the best available TTS provider"""
        providers = await self.get_available_providers("tts")
        for provider_name in providers:
            for suffix in ["_tts", ""]:
                instance_key = f"{provider_name}{suffix}_tts"
                if instance_key in self.provider_instances:
                    return self.provider_instances[instance_key]
        return None
    
    async def get_music_provider(self) -> Optional[MusicProvider]:
        """Get the best available music provider"""
        providers = await self.get_available_providers("music")
        for provider_name in providers:
            for suffix in ["_music", ""]:
                instance_key = f"{provider_name}{suffix}_music"
                if instance_key in self.provider_instances:
                    return self.provider_instances[instance_key]
        return None
    
    async def get_asr_provider(self) -> Optional[ASRProvider]:
        """Get the best available ASR provider"""
        providers = await self.get_available_providers("asr")
        for provider_name in providers:
            instance_key = f"{provider_name}_asr"
            if instance_key in self.provider_instances:
                return self.provider_instances[instance_key]
        return None
    
    async def get_available_providers(self, capability: str) -> List[str]:
        """Get list of providers that support a capability"""
        available = []
        
        for provider_name, provider in self.providers.items():
            if provider.enabled and capability in provider.capabilities:
                available.append(provider_name)
        
        # Sort by priority (lower number = higher priority)
        available.sort(key=lambda p: self.providers[p].priority)
        
        return available
    
    async def test_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """Test all configured providers"""
        results = {}
        
        for instance_name, provider_instance in self.provider_instances.items():
            try:
                result = await provider_instance.test_connection()
                results[instance_name] = {
                    "success": result.success,
                    "error": result.error,
                    "provider": result.provider
                }
            except Exception as e:
                results[instance_name] = {
                    "success": False,
                    "error": str(e),
                    "provider": instance_name
                }
        
        return results
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get configuration status for all providers"""
        status = {
            "configured_providers": len(self.providers),
            "active_instances": len(self.provider_instances),
            "capability_coverage": {},
            "provider_details": {},
            "missing_configurations": []
        }
        
        # Check capability coverage
        capabilities = ["text", "image", "video", "tts", "music", "asr"]
        for capability in capabilities:
            providers = [p for p, cfg in self.providers.items() 
                        if cfg.enabled and capability in cfg.capabilities]
            status["capability_coverage"][capability] = {
                "providers": providers,
                "count": len(providers),
                "best_provider": providers[0] if providers else None
            }
        
        # Provider details
        for provider_name, provider_config in self.providers.items():
            status["provider_details"][provider_name] = {
                "enabled": provider_config.enabled,
                "has_api_key": bool(provider_config.api_key),
                "capabilities": provider_config.capabilities,
                "priority": provider_config.priority
            }
        
        # Check for missing configurations
        env_checks = [
            ("CREATOR_STABILITY_API_KEY", "Stability AI image generation"),
            ("CREATOR_ELEVENLABS_API_KEY", "ElevenLabs TTS"),
            ("CREATOR_OPENAI_API_KEY", "OpenAI services"),
            ("CREATOR_REPLICATE_API_TOKEN", "Replicate services"),
            ("OPENROUTER_API_KEY", "OpenRouter text generation")
        ]
        
        for env_var, description in env_checks:
            if not self.config.get(env_var):
                status["missing_configurations"].append({
                    "env_var": env_var,
                    "description": description
                })
        
        return status
    
    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider"""
        return self.providers.get(provider_name)
    
    async def select_best_provider(self, capability: str, requirements: Dict[str, Any] = None) -> Optional[str]:
        """Select the best provider for a capability based on requirements"""
        available_providers = await self.get_available_providers(capability)
        
        if not available_providers:
            return None
        
        # If no specific requirements, return highest priority provider
        if not requirements:
            return available_providers[0]
        
        # Apply requirement-based selection
        scored_providers = []
        
        for provider_name in available_providers:
            provider = self.providers[provider_name]
            score = self._calculate_provider_score(provider, requirements)
            scored_providers.append((provider_name, score))
        
        # Sort by score (higher is better)
        scored_providers.sort(key=lambda x: x[1], reverse=True)
        
        return scored_providers[0][0] if scored_providers else None
    
    def _calculate_provider_score(self, provider: ProviderConfig, requirements: Dict[str, Any]) -> float:
        """Calculate provider score based on requirements"""
        score = 10.0 - provider.priority  # Higher priority = higher score
        
        # Cost preference
        cost_preference = requirements.get("cost_preference", "balanced")  # "low", "balanced", "quality"
        
        if cost_preference == "low":
            # Prefer lower cost providers
            if provider.cost_per_request < 0.05:
                score += 2.0
            elif provider.cost_per_request > 0.2:
                score -= 2.0
        elif cost_preference == "quality":
            # Prefer higher cost (typically higher quality) providers
            if provider.cost_per_request > 0.1:
                score += 2.0
            elif provider.cost_per_request < 0.02:
                score -= 1.0
        
        # Speed preference
        speed_preference = requirements.get("speed_preference", "balanced")  # "fast", "balanced", "quality"
        
        if speed_preference == "fast":
            # Prefer providers known to be faster
            if provider.name in ["openrouter", "openai", "replicate"]:
                score += 1.5
        
        # Quality preference
        quality_preference = requirements.get("quality_preference", "high")
        
        if quality_preference == "high":
            # Prefer providers known for quality
            if provider.name in ["openai", "anthropic", "elevenlabs", "runway"]:
                score += 1.0
        
        return score
    
    def get_provider_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for provider configuration"""
        recommendations = {
            "essential": [],
            "recommended": [],
            "optional": [],
            "cost_effective": [],
            "high_quality": []
        }
        
        # Essential providers
        if not self.config.get("OPENROUTER_API_KEY"):
            recommendations["essential"].append({
                "provider": "OpenRouter",
                "env_var": "OPENROUTER_API_KEY",
                "reason": "Primary text generation for Creator module",
                "capabilities": ["text", "chat"]
            })
        
        # Recommended providers
        if not self.config.get("CREATOR_STABILITY_API_KEY"):
            recommendations["recommended"].append({
                "provider": "Stability AI",
                "env_var": "CREATOR_STABILITY_API_KEY",
                "reason": "High-quality image generation",
                "capabilities": ["image"]
            })
        
        if not self.config.get("CREATOR_ELEVENLABS_API_KEY"):
            recommendations["recommended"].append({
                "provider": "ElevenLabs",
                "env_var": "CREATOR_ELEVENLABS_API_KEY",
                "reason": "High-quality text-to-speech",
                "capabilities": ["tts"]
            })
        
        # Cost-effective options
        if not self.config.get("CREATOR_REPLICATE_API_TOKEN"):
            recommendations["cost_effective"].append({
                "provider": "Replicate",
                "env_var": "CREATOR_REPLICATE_API_TOKEN",
                "reason": "Cost-effective multi-modal AI services",
                "capabilities": ["image", "video", "music"]
            })
        
        return recommendations

# Legacy compatibility
ModelProviderManager = EnhancedModelProviderManager
