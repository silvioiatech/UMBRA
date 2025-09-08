"""
Model Provider Manager - Handles routing between different AI providers
"""

import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from ...core.config import UmbraConfig
from .errors import ProviderError

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

class ModelProviderManager:
    """Manages multiple AI model providers and routing"""
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        self.providers = {}
        self._load_providers()
        
        logger.info(f"Provider manager initialized with {len(self.providers)} providers")
    
    def _load_providers(self):
        """Load and configure all available providers"""
        
        # Text/AI providers
        self._load_openrouter_provider()
        self._load_openai_provider()
        self._load_anthropic_provider()
        
        # Image providers
        self._load_stability_provider()
        self._load_dalle_provider()
        self._load_replicate_provider()
        
        # Audio providers
        self._load_elevenlabs_provider()
        self._load_openai_audio_provider()
        
        # Video providers
        self._load_runway_provider()
        self._load_pika_provider()
        
        # Music providers
        self._load_suno_provider()
        self._load_udio_provider()
        
        # Speech recognition
        self._load_deepgram_provider()
        self._load_whisper_provider()
    
    def _load_openrouter_provider(self):
        """Load OpenRouter provider"""
        api_key = self.config.get("OPENROUTER_API_KEY")
        if api_key:
            self.providers["openrouter"] = ProviderConfig(
                name="openrouter",
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                capabilities=["text", "chat", "completion"],
                priority=1,
                enabled=True,
                cost_per_token=0.00001
            )
    
    def _load_openai_provider(self):
        """Load OpenAI provider"""
        api_key = self.config.get("CREATOR_OPENAI_API_KEY")
        if api_key:
            self.providers["openai"] = ProviderConfig(
                name="openai",
                api_key=api_key,
                base_url="https://api.openai.com/v1",
                capabilities=["text", "chat", "image", "audio", "tts", "whisper"],
                priority=2,
                enabled=True,
                cost_per_token=0.00002
            )
    
    def _load_anthropic_provider(self):
        """Load Anthropic provider"""
        api_key = self.config.get("CREATOR_ANTHROPIC_API_KEY")
        if api_key:
            self.providers["anthropic"] = ProviderConfig(
                name="anthropic",
                api_key=api_key,
                base_url="https://api.anthropic.com/v1",
                capabilities=["text", "chat", "completion"],
                priority=3,
                enabled=True,
                cost_per_token=0.000015
            )
    
    def _load_stability_provider(self):
        """Load Stability AI provider"""
        api_key = self.config.get("CREATOR_STABILITY_API_KEY")
        if api_key:
            self.providers["stability"] = ProviderConfig(
                name="stability",
                api_key=api_key,
                base_url="https://api.stability.ai/v1",
                capabilities=["image", "image_edit", "image_upscale"],
                priority=1,
                enabled=True,
                cost_per_request=0.05
            )
    
    def _load_dalle_provider(self):
        """Load DALL-E provider"""
        api_key = self.config.get("CREATOR_OPENAI_API_KEY")
        if api_key:
            self.providers["dalle"] = ProviderConfig(
                name="dalle",
                api_key=api_key,
                base_url="https://api.openai.com/v1",
                capabilities=["image", "image_edit", "image_variation"],
                priority=2,
                enabled=True,
                cost_per_request=0.08
            )
    
    def _load_replicate_provider(self):
        """Load Replicate provider"""
        api_token = self.config.get("CREATOR_REPLICATE_API_TOKEN")
        if api_token:
            self.providers["replicate"] = ProviderConfig(
                name="replicate",
                api_key=api_token,
                base_url="https://api.replicate.com/v1",
                capabilities=["image", "video", "audio", "music", "image_upscale", "image_variation"],
                priority=3,
                enabled=True,
                cost_per_request=0.03
            )
    
    def _load_elevenlabs_provider(self):
        """Load ElevenLabs provider"""
        api_key = self.config.get("CREATOR_ELEVENLABS_API_KEY")
        if api_key:
            self.providers["elevenlabs"] = ProviderConfig(
                name="elevenlabs",
                api_key=api_key,
                base_url="https://api.elevenlabs.io/v1",
                capabilities=["tts", "voice_cloning", "audio"],
                priority=1,
                enabled=True,
                cost_per_request=0.02
            )
    
    def _load_openai_audio_provider(self):
        """Load OpenAI audio provider"""
        api_key = self.config.get("CREATOR_OPENAI_API_KEY")
        if api_key:
            self.providers["openai_audio"] = ProviderConfig(
                name="openai_audio",
                api_key=api_key,
                base_url="https://api.openai.com/v1",
                capabilities=["tts", "whisper", "audio_transcription"],
                priority=2,
                enabled=True,
                cost_per_request=0.015
            )
    
    def _load_runway_provider(self):
        """Load Runway ML provider"""
        api_key = self.config.get("CREATOR_RUNWAY_API_KEY")
        if api_key:
            self.providers["runway"] = ProviderConfig(
                name="runway",
                api_key=api_key,
                base_url="https://api.runwayml.com/v1",
                capabilities=["video", "video_edit", "image_to_video"],
                priority=1,
                enabled=True,
                cost_per_request=0.5
            )
    
    def _load_pika_provider(self):
        """Load Pika Labs provider"""
        api_key = self.config.get("CREATOR_PIKA_API_KEY")
        if api_key:
            self.providers["pika"] = ProviderConfig(
                name="pika",
                api_key=api_key,
                base_url="https://api.pika.art/v1",
                capabilities=["video", "image_to_video"],
                priority=2,
                enabled=True,
                cost_per_request=0.3
            )
    
    def _load_suno_provider(self):
        """Load Suno AI provider"""
        api_key = self.config.get("CREATOR_SUNO_API_KEY")
        if api_key:
            self.providers["suno"] = ProviderConfig(
                name="suno",
                api_key=api_key,
                base_url="https://api.suno.ai/v1",
                capabilities=["music", "audio", "vocals"],
                priority=1,
                enabled=True,
                cost_per_request=0.1
            )
    
    def _load_udio_provider(self):
        """Load Udio provider"""
        api_key = self.config.get("CREATOR_UDIO_API_KEY")
        if api_key:
            self.providers["udio"] = ProviderConfig(
                name="udio",
                api_key=api_key,
                base_url="https://api.udio.com/v1",
                capabilities=["music", "audio"],
                priority=2,
                enabled=True,
                cost_per_request=0.08
            )
    
    def _load_deepgram_provider(self):
        """Load Deepgram provider"""
        api_key = self.config.get("CREATOR_DEEPGRAM_API_KEY")
        if api_key:
            self.providers["deepgram"] = ProviderConfig(
                name="deepgram",
                api_key=api_key,
                base_url="https://api.deepgram.com/v1",
                capabilities=["speech_recognition", "transcription", "diarization"],
                priority=1,
                enabled=True,
                cost_per_request=0.005
            )
    
    def _load_whisper_provider(self):
        """Load Whisper provider (via OpenAI)"""
        api_key = self.config.get("CREATOR_OPENAI_API_KEY")
        if api_key:
            self.providers["whisper"] = ProviderConfig(
                name="whisper",
                api_key=api_key,
                base_url="https://api.openai.com/v1",
                capabilities=["speech_recognition", "transcription", "translation"],
                priority=2,
                enabled=True,
                cost_per_request=0.006
            )
    
    async def get_available_providers(self, capability: str) -> List[str]:
        """Get list of providers that support a capability"""
        available = []
        
        for provider_name, provider in self.providers.items():
            if provider.enabled and capability in provider.capabilities:
                available.append(provider_name)
        
        # Sort by priority (lower number = higher priority)
        available.sort(key=lambda p: self.providers[p].priority)
        
        return available
    
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
            # Prefer providers known to be faster (OpenAI, Replicate)
            if provider.name in ["openai", "replicate", "openrouter"]:
                score += 1.5
        
        # Quality preference
        quality_preference = requirements.get("quality_preference", "high")
        
        if quality_preference == "high":
            # Prefer providers known for quality
            if provider.name in ["openai", "anthropic", "elevenlabs", "runway"]:
                score += 1.0
        
        return score
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        
        for provider_name, provider in self.providers.items():
            status[provider_name] = {
                "enabled": provider.enabled,
                "capabilities": provider.capabilities,
                "priority": provider.priority,
                "has_api_key": bool(provider.api_key),
                "cost_per_request": provider.cost_per_request,
                "cost_per_token": provider.cost_per_token
            }
        
        return status
    
    def enable_provider(self, provider_name: str) -> bool:
        """Enable a provider"""
        if provider_name in self.providers:
            self.providers[provider_name].enabled = True
            logger.info(f"Provider {provider_name} enabled")
            return True
        return False
    
    def disable_provider(self, provider_name: str) -> bool:
        """Disable a provider"""
        if provider_name in self.providers:
            self.providers[provider_name].enabled = False
            logger.info(f"Provider {provider_name} disabled")
            return True
        return False
    
    def set_provider_priority(self, provider_name: str, priority: int) -> bool:
        """Set provider priority (lower number = higher priority)"""
        if provider_name in self.providers:
            self.providers[provider_name].priority = priority
            logger.info(f"Provider {provider_name} priority set to {priority}")
            return True
        return False
    
    async def test_provider_connection(self, provider_name: str) -> Dict[str, Any]:
        """Test connection to a provider"""
        if provider_name not in self.providers:
            return {"success": False, "error": "Provider not found"}
        
        provider = self.providers[provider_name]
        
        if not provider.enabled:
            return {"success": False, "error": "Provider disabled"}
        
        if not provider.api_key:
            return {"success": False, "error": "API key not configured"}
        
        try:
            # Perform a simple test based on provider capabilities
            if "text" in provider.capabilities:
                # Test text generation
                result = await self._test_text_provider(provider)
            elif "image" in provider.capabilities:
                # Test image generation
                result = await self._test_image_provider(provider)
            elif "audio" in provider.capabilities:
                # Test audio generation
                result = await self._test_audio_provider(provider)
            else:
                result = {"success": True, "message": "Provider configured but no test available"}
            
            return result
            
        except Exception as e:
            logger.error(f"Provider {provider_name} test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_text_provider(self, provider: ProviderConfig) -> Dict[str, Any]:
        """Test text provider with simple request"""
        import httpx
        
        if provider.name == "openrouter":
            url = f"{provider.base_url}/chat/completions"
            payload = {
                "model": "anthropic/claude-3-haiku",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
        elif provider.name == "openai":
            url = f"{provider.base_url}/chat/completions"
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
        else:
            return {"success": True, "message": "Test not implemented for this provider"}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {provider.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    return {"success": True, "message": "Provider test successful"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_image_provider(self, provider: ProviderConfig) -> Dict[str, Any]:
        """Test image provider with simple request"""
        # Placeholder implementation
        return {"success": True, "message": "Image provider test not implemented"}
    
    async def _test_audio_provider(self, provider: ProviderConfig) -> Dict[str, Any]:
        """Test audio provider with simple request"""
        # Placeholder implementation
        return {"success": True, "message": "Audio provider test not implemented"}
    
    def get_capability_matrix(self) -> Dict[str, List[str]]:
        """Get matrix of capabilities and their providers"""
        capabilities = {}
        
        for provider_name, provider in self.providers.items():
            if provider.enabled:
                for capability in provider.capabilities:
                    if capability not in capabilities:
                        capabilities[capability] = []
                    capabilities[capability].append(provider_name)
        
        # Sort providers by priority for each capability
        for capability in capabilities:
            capabilities[capability].sort(key=lambda p: self.providers[p].priority)
        
        return capabilities
    
    def estimate_cost(self, provider_name: str, operation_type: str, **kwargs) -> float:
        """Estimate cost for an operation"""
        if provider_name not in self.providers:
            return 0.0
        
        provider = self.providers[provider_name]
        
        if operation_type == "text":
            tokens = kwargs.get("tokens", 1000)
            return tokens * provider.cost_per_token
        else:
            return provider.cost_per_request
    
    def get_recommended_providers(self, use_case: str) -> Dict[str, List[str]]:
        """Get recommended providers for specific use cases"""
        recommendations = {
            "high_quality_text": ["openai", "anthropic", "openrouter"],
            "cost_effective_text": ["openrouter", "replicate"],
            "high_quality_images": ["dalle", "stability"],
            "cost_effective_images": ["replicate", "stability"],
            "professional_audio": ["elevenlabs", "openai_audio"],
            "cost_effective_audio": ["openai_audio", "replicate"],
            "high_quality_video": ["runway", "pika"],
            "music_generation": ["suno", "udio", "replicate"],
            "speech_recognition": ["deepgram", "whisper"]
        }
        
        # Filter by available providers
        if use_case in recommendations:
            available = []
            for provider_name in recommendations[use_case]:
                if provider_name in self.providers and self.providers[provider_name].enabled:
                    available.append(provider_name)
            return {use_case: available}
        
        return {}
    
    def get_provider_limits(self, provider_name: str) -> Dict[str, Any]:
        """Get known limits for a provider"""
        limits = {
            "openai": {
                "max_tokens": 4096,
                "rate_limit_rpm": 3500,
                "image_max_size": "1792x1024"
            },
            "stability": {
                "image_max_size": "1024x1024",
                "rate_limit_rpm": 150
            },
            "elevenlabs": {
                "max_characters": 5000,
                "rate_limit_rpm": 120
            },
            "replicate": {
                "rate_limit_rpm": 100
            }
        }
        
        return limits.get(provider_name, {})
