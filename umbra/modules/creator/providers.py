"""
Provider Interfaces - Standardized interfaces for different content generation providers
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass

@dataclass
class ProviderResponse:
    """Standardized provider response"""
    success: bool
    data: Any = None
    error: str = None
    cost_estimate: float = 0.0
    provider: str = None
    model: str = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseProvider(ABC):
    """Base interface for all providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unknown")
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "")
        self.enabled = config.get("enabled", True)
    
    @abstractmethod
    async def test_connection(self) -> ProviderResponse:
        """Test provider connection"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get provider capabilities"""
        pass
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.enabled and bool(self.api_key)

class TextProvider(BaseProvider):
    """Interface for text generation providers"""
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> ProviderResponse:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> ProviderResponse:
        """Generate chat completion"""
        pass
    
    def get_capabilities(self) -> List[str]:
        return ["text", "chat", "completion"]

class ImageProvider(BaseProvider):
    """Interface for image generation providers"""
    
    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> ProviderResponse:
        """Generate image from prompt"""
        pass
    
    @abstractmethod
    async def edit_image(self, image_data: bytes, prompt: str, **kwargs) -> ProviderResponse:
        """Edit existing image"""
        pass
    
    async def upscale_image(self, image_data: bytes, scale_factor: int = 2, **kwargs) -> ProviderResponse:
        """Upscale image (optional)"""
        return ProviderResponse(success=False, error="Upscaling not supported by this provider")
    
    async def generate_variations(self, image_data: bytes, count: int = 3, **kwargs) -> ProviderResponse:
        """Generate image variations (optional)"""
        return ProviderResponse(success=False, error="Variations not supported by this provider")
    
    def get_capabilities(self) -> List[str]:
        return ["image", "image_edit"]

class VideoProvider(BaseProvider):
    """Interface for video generation providers"""
    
    @abstractmethod
    async def generate_video(self, prompt: str, **kwargs) -> ProviderResponse:
        """Generate video from prompt"""
        pass
    
    async def image_to_video(self, image_data: bytes, prompt: str = "", **kwargs) -> ProviderResponse:
        """Convert image to video (optional)"""
        return ProviderResponse(success=False, error="Image-to-video not supported by this provider")
    
    async def edit_video(self, video_data: bytes, prompt: str, **kwargs) -> ProviderResponse:
        """Edit existing video (optional)"""
        return ProviderResponse(success=False, error="Video editing not supported by this provider")
    
    def get_capabilities(self) -> List[str]:
        return ["video"]

class TTSProvider(BaseProvider):
    """Interface for text-to-speech providers"""
    
    @abstractmethod
    async def text_to_speech(self, text: str, voice_id: str = "default", **kwargs) -> ProviderResponse:
        """Convert text to speech"""
        pass
    
    @abstractmethod
    async def list_voices(self) -> ProviderResponse:
        """List available voices"""
        pass
    
    async def register_voice(self, voice_data: bytes, consent_token: str, **kwargs) -> ProviderResponse:
        """Register custom voice (optional)"""
        return ProviderResponse(success=False, error="Voice registration not supported by this provider")
    
    def get_capabilities(self) -> List[str]:
        return ["tts", "voice"]

class MusicProvider(BaseProvider):
    """Interface for music generation providers"""
    
    @abstractmethod
    async def generate_music(self, prompt: str, duration: int = 30, **kwargs) -> ProviderResponse:
        """Generate music from prompt"""
        pass
    
    async def generate_stems(self, prompt: str, duration: int = 30, **kwargs) -> ProviderResponse:
        """Generate music with stems (optional)"""
        return ProviderResponse(success=False, error="Stems generation not supported by this provider")
    
    def get_capabilities(self) -> List[str]:
        return ["music", "audio"]

class ASRProvider(BaseProvider):
    """Interface for automatic speech recognition providers"""
    
    @abstractmethod
    async def transcribe_audio(self, audio_data: bytes, **kwargs) -> ProviderResponse:
        """Transcribe audio to text"""
        pass
    
    async def transcribe_with_diarization(self, audio_data: bytes, **kwargs) -> ProviderResponse:
        """Transcribe with speaker diarization (optional)"""
        return ProviderResponse(success=False, error="Diarization not supported by this provider")
    
    async def translate_audio(self, audio_data: bytes, target_language: str = "en", **kwargs) -> ProviderResponse:
        """Translate audio to target language (optional)"""
        return ProviderResponse(success=False, error="Translation not supported by this provider")
    
    def get_capabilities(self) -> List[str]:
        return ["asr", "transcription"]

# Concrete Provider Implementations

class OpenRouterTextProvider(TextProvider):
    """OpenRouter text generation provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get("model", "anthropic/claude-3.5-sonnet:beta")
    
    async def test_connection(self) -> ProviderResponse:
        """Test OpenRouter connection"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 10
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    return ProviderResponse(success=True, provider="openrouter")
                else:
                    return ProviderResponse(
                        success=False, 
                        error=f"HTTP {response.status_code}",
                        provider="openrouter"
                    )
                    
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="openrouter")
    
    async def generate_text(self, prompt: str, **kwargs) -> ProviderResponse:
        """Generate text using OpenRouter"""
        try:
            import httpx
            
            max_tokens = kwargs.get("max_tokens", 1000)
            temperature = kwargs.get("temperature", 0.7)
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result["choices"][0]["message"]["content"]
                    
                    return ProviderResponse(
                        success=True,
                        data=text,
                        provider="openrouter",
                        model=self.model,
                        cost_estimate=result.get("usage", {}).get("total_tokens", 0) * 0.00001
                    )
                else:
                    return ProviderResponse(
                        success=False,
                        error=f"OpenRouter API error: {response.status_code}",
                        provider="openrouter"
                    )
                    
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="openrouter")
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> ProviderResponse:
        """Generate chat completion using OpenRouter"""
        try:
            import httpx
            
            max_tokens = kwargs.get("max_tokens", 1000)
            temperature = kwargs.get("temperature", 0.7)
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_message = result["choices"][0]["message"]
                    
                    return ProviderResponse(
                        success=True,
                        data=response_message,
                        provider="openrouter",
                        model=self.model,
                        metadata=result.get("usage", {})
                    )
                else:
                    return ProviderResponse(
                        success=False,
                        error=f"OpenRouter API error: {response.status_code}",
                        provider="openrouter"
                    )
                    
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="openrouter")

class StabilityImageProvider(ImageProvider):
    """Stability AI image generation provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.engine = config.get("engine", "stable-diffusion-xl-1024-v1-0")
    
    async def test_connection(self) -> ProviderResponse:
        """Test Stability AI connection"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/engines/list",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return ProviderResponse(success=True, provider="stability")
                else:
                    return ProviderResponse(
                        success=False,
                        error=f"HTTP {response.status_code}",
                        provider="stability"
                    )
                    
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="stability")
    
    async def generate_image(self, prompt: str, **kwargs) -> ProviderResponse:
        """Generate image using Stability AI"""
        try:
            import httpx
            import base64
            
            width = kwargs.get("width", 1024)
            height = kwargs.get("height", 1024)
            steps = kwargs.get("steps", 30)
            cfg_scale = kwargs.get("cfg_scale", 7)
            
            payload = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": cfg_scale,
                "height": height,
                "width": width,
                "steps": steps,
                "samples": 1
            }
            
            seed = kwargs.get("seed")
            if seed:
                payload["seed"] = seed
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.base_url}/generation/{self.engine}/text-to-image",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    artifact = result["artifacts"][0]
                    
                    return ProviderResponse(
                        success=True,
                        data={
                            "image_data": base64.b64decode(artifact["base64"]),
                            "seed": artifact.get("seed"),
                            "format": "png"
                        },
                        provider="stability",
                        model=self.engine,
                        cost_estimate=0.05
                    )
                else:
                    return ProviderResponse(
                        success=False,
                        error=f"Stability API error: {response.status_code}",
                        provider="stability"
                    )
                    
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="stability")
    
    async def edit_image(self, image_data: bytes, prompt: str, **kwargs) -> ProviderResponse:
        """Edit image using Stability AI"""
        return ProviderResponse(success=False, error="Image editing not yet implemented", provider="stability")
    
    def get_capabilities(self) -> List[str]:
        return ["image", "image_edit", "image_upscale"]

class ElevenLabsTTSProvider(TTSProvider):
    """ElevenLabs text-to-speech provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_voice = config.get("default_voice", "21m00Tcm4TlvDq8ikWAM")  # Rachel
    
    async def test_connection(self) -> ProviderResponse:
        """Test ElevenLabs connection"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/voices",
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code == 200:
                    return ProviderResponse(success=True, provider="elevenlabs")
                else:
                    return ProviderResponse(
                        success=False,
                        error=f"HTTP {response.status_code}",
                        provider="elevenlabs"
                    )
                    
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="elevenlabs")
    
    async def text_to_speech(self, text: str, voice_id: str = "default", **kwargs) -> ProviderResponse:
        """Convert text to speech using ElevenLabs"""
        try:
            import httpx
            
            if voice_id == "default":
                voice_id = self.default_voice
            
            model_id = kwargs.get("model_id", "eleven_monolingual_v1")
            stability = kwargs.get("stability", 0.5)
            similarity_boost = kwargs.get("similarity_boost", 0.5)
            
            payload = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost
                }
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{voice_id}",
                    json=payload,
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    return ProviderResponse(
                        success=True,
                        data={
                            "audio_data": response.content,
                            "format": "mp3",
                            "voice_id": voice_id
                        },
                        provider="elevenlabs",
                        cost_estimate=len(text) * 0.00018  # Approximate cost per character
                    )
                else:
                    return ProviderResponse(
                        success=False,
                        error=f"ElevenLabs API error: {response.status_code}",
                        provider="elevenlabs"
                    )
                    
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="elevenlabs")
    
    async def list_voices(self) -> ProviderResponse:
        """List available voices"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/voices",
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code == 200:
                    voices_data = response.json()
                    
                    return ProviderResponse(
                        success=True,
                        data=voices_data.get("voices", []),
                        provider="elevenlabs"
                    )
                else:
                    return ProviderResponse(
                        success=False,
                        error=f"ElevenLabs API error: {response.status_code}",
                        provider="elevenlabs"
                    )
                    
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="elevenlabs")

class OpenAIWhisperProvider(ASRProvider):
    """OpenAI Whisper ASR provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get("model", "whisper-1")
    
    async def test_connection(self) -> ProviderResponse:
        """Test OpenAI connection"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return ProviderResponse(success=True, provider="openai_whisper")
                else:
                    return ProviderResponse(
                        success=False,
                        error=f"HTTP {response.status_code}",
                        provider="openai_whisper"
                    )
                    
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="openai_whisper")
    
    async def transcribe_audio(self, audio_data: bytes, **kwargs) -> ProviderResponse:
        """Transcribe audio using OpenAI Whisper"""
        try:
            import httpx
            import tempfile
            
            language = kwargs.get("language")
            response_format = kwargs.get("response_format", "json")
            
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                files = {
                    "file": ("audio.mp3", audio_data, "audio/mpeg"),
                    "model": (None, self.model),
                    "response_format": (None, response_format)
                }
                
                if language:
                    files["language"] = (None, language)
                
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(
                        f"{self.base_url}/audio/transcriptions",
                        files=files,
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        return ProviderResponse(
                            success=True,
                            data={
                                "text": result.get("text", ""),
                                "language": result.get("language"),
                                "duration": result.get("duration"),
                                "segments": result.get("segments", [])
                            },
                            provider="openai_whisper",
                            model=self.model,
                            cost_estimate=len(audio_data) * 0.000001  # Approximate cost per byte
                        )
                    else:
                        return ProviderResponse(
                            success=False,
                            error=f"OpenAI Whisper API error: {response.status_code}",
                            provider="openai_whisper"
                        )
                        
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="openai_whisper")
    
    async def translate_audio(self, audio_data: bytes, target_language: str = "en", **kwargs) -> ProviderResponse:
        """Translate audio using OpenAI Whisper"""
        try:
            import httpx
            import tempfile
            
            response_format = kwargs.get("response_format", "json")
            
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                files = {
                    "file": ("audio.mp3", audio_data, "audio/mpeg"),
                    "model": (None, self.model),
                    "response_format": (None, response_format)
                }
                
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(
                        f"{self.base_url}/audio/translations",
                        files=files,
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        return ProviderResponse(
                            success=True,
                            data={
                                "text": result.get("text", ""),
                                "target_language": target_language,
                                "duration": result.get("duration")
                            },
                            provider="openai_whisper",
                            model=self.model,
                            cost_estimate=len(audio_data) * 0.000001
                        )
                    else:
                        return ProviderResponse(
                            success=False,
                            error=f"OpenAI Whisper API error: {response.status_code}",
                            provider="openai_whisper"
                        )
                        
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="openai_whisper")

class ReplicateVideoProvider(VideoProvider):
    """Replicate video generation provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_model = config.get("model", "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb1a4918c63516c2b0b31b32d803e0c01d2a6e5280")
    
    async def test_connection(self) -> ProviderResponse:
        """Test Replicate connection"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Token {self.api_key}"}
                )
                
                if response.status_code == 200:
                    return ProviderResponse(success=True, provider="replicate")
                else:
                    return ProviderResponse(
                        success=False,
                        error=f"HTTP {response.status_code}",
                        provider="replicate"
                    )
                    
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="replicate")
    
    async def generate_video(self, prompt: str, **kwargs) -> ProviderResponse:
        """Generate video using Replicate"""
        try:
            import httpx
            
            model_version = kwargs.get("model_version", self.default_model)
            duration = kwargs.get("duration", 30)
            width = kwargs.get("width", 1024)
            height = kwargs.get("height", 576)
            
            payload = {
                "version": model_version,
                "input": {
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "duration": duration
                }
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                # Start prediction
                response = await client.post(
                    f"{self.base_url}/predictions",
                    json=payload,
                    headers={
                        "Authorization": f"Token {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 201:
                    prediction = response.json()
                    prediction_id = prediction["id"]
                    
                    # Poll for completion
                    for _ in range(60):  # Max 10 minutes
                        await asyncio.sleep(10)
                        
                        status_response = await client.get(
                            f"{self.base_url}/predictions/{prediction_id}",
                            headers={"Authorization": f"Token {self.api_key}"}
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if status_data["status"] == "succeeded":
                                output_url = status_data["output"]
                                
                                return ProviderResponse(
                                    success=True,
                                    data={
                                        "video_url": output_url,
                                        "prediction_id": prediction_id,
                                        "duration": duration
                                    },
                                    provider="replicate",
                                    model=model_version,
                                    cost_estimate=0.5
                                )
                            elif status_data["status"] == "failed":
                                return ProviderResponse(
                                    success=False,
                                    error=f"Prediction failed: {status_data.get('error')}",
                                    provider="replicate"
                                )
                    
                    return ProviderResponse(
                        success=False,
                        error="Video generation timeout",
                        provider="replicate"
                    )
                else:
                    return ProviderResponse(
                        success=False,
                        error=f"Replicate API error: {response.status_code}",
                        provider="replicate"
                    )
                    
        except Exception as e:
            return ProviderResponse(success=False, error=str(e), provider="replicate")
    
    def get_capabilities(self) -> List[str]:
        return ["video", "image_to_video"]

# Provider Factory

class ProviderFactory:
    """Factory for creating provider instances"""
    
    @staticmethod
    def create_text_provider(provider_name: str, config: Dict[str, Any]) -> Optional[TextProvider]:
        """Create text provider instance"""
        if provider_name == "openrouter":
            return OpenRouterTextProvider(config)
        # Add other text providers here
        return None
    
    @staticmethod
    def create_image_provider(provider_name: str, config: Dict[str, Any]) -> Optional[ImageProvider]:
        """Create image provider instance"""
        if provider_name == "stability":
            return StabilityImageProvider(config)
        # Add other image providers here
        return None
    
    @staticmethod
    def create_video_provider(provider_name: str, config: Dict[str, Any]) -> Optional[VideoProvider]:
        """Create video provider instance"""
        if provider_name == "replicate":
            return ReplicateVideoProvider(config)
        # Add other video providers here
        return None
    
    @staticmethod
    def create_tts_provider(provider_name: str, config: Dict[str, Any]) -> Optional[TTSProvider]:
        """Create TTS provider instance"""
        if provider_name == "elevenlabs":
            return ElevenLabsTTSProvider(config)
        # Add other TTS providers here
        return None
    
    @staticmethod
    def create_asr_provider(provider_name: str, config: Dict[str, Any]) -> Optional[ASRProvider]:
        """Create ASR provider instance"""
        if provider_name == "openai":
            return OpenAIWhisperProvider(config)
        # Add other ASR providers here
        return None
    
    @staticmethod
    def create_music_provider(provider_name: str, config: Dict[str, Any]) -> Optional[MusicProvider]:
        """Create music provider instance"""
        # Add music providers here when implemented
        return None
