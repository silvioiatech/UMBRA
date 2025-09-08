"""
Graceful Provider Fallbacks - CRT4 Implementation
Handles graceful no-op when providers are not configured
"""

import logging
from typing import Dict, Any, Optional

from .errors import ProviderError
from .providers import ProviderResponse

logger = logging.getLogger(__name__)

class GracefulProviderManager:
    """Manages graceful fallbacks when providers are not configured"""
    
    def __init__(self, provider_manager):
        self.provider_manager = provider_manager
        
    async def get_text_provider_with_fallback(self) -> Optional:
        """Get text provider with graceful fallback"""
        try:
            provider = await self.provider_manager.get_text_provider()
            if provider:
                return provider
            else:
                logger.warning("No text provider configured - operations will use fallback")
                return MockTextProvider()
        except Exception as e:
            logger.error(f"Text provider initialization failed: {e}")
            return MockTextProvider()
    
    async def get_image_provider_with_fallback(self) -> Optional:
        """Get image provider with graceful fallback"""
        try:
            provider = await self.provider_manager.get_image_provider()
            if provider:
                return provider
            else:
                logger.warning("No image provider configured - image generation disabled")
                return None
        except Exception as e:
            logger.error(f"Image provider initialization failed: {e}")
            return None
    
    async def get_video_provider_with_fallback(self) -> Optional:
        """Get video provider with graceful fallback"""
        try:
            provider = await self.provider_manager.get_video_provider()
            if provider:
                return provider
            else:
                logger.warning("No video provider configured - video generation disabled")
                return None
        except Exception as e:
            logger.error(f"Video provider initialization failed: {e}")
            return None
    
    async def get_tts_provider_with_fallback(self) -> Optional:
        """Get TTS provider with graceful fallback"""
        try:
            provider = await self.provider_manager.get_tts_provider()
            if provider:
                return provider
            else:
                logger.warning("No TTS provider configured - TTS disabled")
                return None
        except Exception as e:
            logger.error(f"TTS provider initialization failed: {e}")
            return None
    
    async def get_music_provider_with_fallback(self) -> Optional:
        """Get music provider with graceful fallback"""
        try:
            provider = await self.provider_manager.get_music_provider()
            if provider:
                return provider
            else:
                logger.warning("No music provider configured - music generation disabled")
                return None
        except Exception as e:
            logger.error(f"Music provider initialization failed: {e}")
            return None
    
    async def get_asr_provider_with_fallback(self) -> Optional:
        """Get ASR provider with graceful fallback"""
        try:
            provider = await self.provider_manager.get_asr_provider()
            if provider:
                return provider
            else:
                logger.warning("No ASR provider configured - transcription disabled")
                return None
        except Exception as e:
            logger.error(f"ASR provider initialization failed: {e}")
            return None

class MockTextProvider:
    """Mock text provider for graceful fallback when OpenRouter not configured"""
    
    async def generate_text(self, prompt: str, **kwargs) -> ProviderResponse:
        """Generate fallback text response"""
        fallback_text = (
            f"[Text generation temporarily unavailable - OpenRouter not configured]\n\n"
            f"Your request: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n\n"
            f"To enable text generation, please configure:\n"
            f"• OPENROUTER_API_KEY=your_key\n"
            f"• Optional: CREATOR_OPENROUTER_MODEL_TEXT=your_model"
        )
        
        return ProviderResponse(
            success=True,
            data={"text": fallback_text},
            provider="mock_fallback",
            metadata={"fallback": True, "reason": "no_text_provider_configured"}
        )
    
    async def chat_completion(self, messages, **kwargs) -> ProviderResponse:
        """Generate fallback chat response"""
        last_message = messages[-1].get("content", "") if messages else ""
        
        fallback_text = (
            f"[AI chat temporarily unavailable - OpenRouter not configured]\n\n"
            f"Your message: {last_message[:100]}{'...' if len(last_message) > 100 else ''}\n\n"
            f"To enable AI chat, please configure:\n"
            f"• OPENROUTER_API_KEY=your_key"
        )
        
        return ProviderResponse(
            success=True,
            data={"message": {"content": fallback_text}},
            provider="mock_fallback",
            metadata={"fallback": True, "reason": "no_chat_provider_configured"}
        )
    
    async def test_connection(self) -> ProviderResponse:
        """Mock connection test"""
        return ProviderResponse(
            success=False,
            error="Mock provider - OpenRouter not configured",
            provider="mock_fallback"
        )
    
    def get_capabilities(self):
        return ["text", "chat", "mock"]
    
    def is_available(self):
        return False

def get_missing_provider_message(capability: str, providers_config: Dict[str, Any]) -> str:
    """Get helpful message about missing provider configuration"""
    
    messages = {
        "image": {
            "message": "Image generation is not available. To enable image generation, configure one of:",
            "providers": [
                "• CREATOR_STABILITY_API_KEY=your_key (Stability AI - recommended)",
                "• CREATOR_OPENAI_API_KEY=your_key (DALL-E)",  
                "• CREATOR_REPLICATE_API_TOKEN=your_token (Replicate)",
                "• Set CREATOR_IMAGE_PROVIDER=Union[stability, opena]Union[i, replicate]"
            ]
        },
        "video": {
            "message": "Video generation is not available. To enable video generation, configure one of:",
            "providers": [
                "• CREATOR_REPLICATE_API_TOKEN=your_token (recommended)",
                "• CREATOR_PIKA_API_KEY=your_key (Pika Labs)",
                "• CREATOR_RUNWAY_API_KEY=your_key (Runway ML)",
                "• Set CREATOR_VIDEO_PROVIDER=Union[replicate, pik]Union[a, runway]"
            ]
        },
        "tts": {
            "message": "Text-to-speech is not available. To enable TTS, configure one of:",
            "providers": [
                "• CREATOR_ELEVENLABS_API_KEY=your_key (ElevenLabs - recommended)",
                "• CREATOR_OPENAI_API_KEY=your_key (OpenAI TTS)",
                "• Set CREATOR_TTS_PROVIDER=Union[elevenlabs, openai]"
            ]
        },
        "music": {
            "message": "Music generation is not available. To enable music generation, configure one of:",
            "providers": [
                "• CREATOR_SUNO_API_KEY=your_key (Suno AI)",
                "• CREATOR_REPLICATE_API_TOKEN=your_token (Replicate)",
                "• Set CREATOR_MUSIC_PROVIDER=Union[suno, replicate]"
            ]
        },
        "asr": {
            "message": "Audio transcription is not available. To enable ASR, configure one of:",
            "providers": [
                "• CREATOR_OPENAI_API_KEY=your_key (Whisper - recommended)",
                "• CREATOR_DEEPGRAM_API_KEY=your_key (Deepgram)",
                "• Set CREATOR_ASR_PROVIDER=Union[openai, deepgram]"
            ]
        }
    }
    
    config = messages.get(capability, {
        "message": f"{capability.title()} provider not configured.",
        "providers": ["• Check provider configuration"]
    })
    
    return f"{config['message']}\n" + "\n".join(config['providers'])

async def generate_provider_remediation_hint(capability: str, error: str) -> str:
    """Generate helpful remediation hint for provider errors"""
    
    base_message = f"❌ **{capability.title()} Generation Failed**\n\n"
    
    # Common error patterns and remediation
    if "api" in error.lower() and "key" in error.lower():
        base_message += f"**Issue**: API key authentication failed\n"
        base_message += f"**Solution**: Check your CREATOR_{capability.upper()}_* environment variables\n\n"
    
    elif "quota" in error.lower() or "limit" in error.lower():
        base_message += f"**Issue**: Provider usage limit exceeded\n"
        base_message += f"**Solution**: Check your provider account limits or try later\n\n"
    
    elif "timeout" in error.lower():
        base_message += f"**Issue**: Provider request timeout\n"
        base_message += f"**Solution**: Try again or check provider status\n\n"
    
    elif "not configured" in error.lower():
        base_message += get_missing_provider_message(capability, {})
        return base_message
    
    else:
        base_message += f"**Error**: {error}\n\n"
    
    # Add general help
    base_message += f"💡 **Alternative**: "
    
    if capability == "image":
        base_message += "Try switching to a different image provider (stability/openai/replicate)"
    elif capability == "video":  
        base_message += "Try switching to a different video provider (replicate/pika/runway)"
    elif capability == "tts":
        base_message += "Try switching to a different TTS provider (elevenlabs/openai)"
    else:
        base_message += f"Check provider status and configuration"
    
    return base_message
