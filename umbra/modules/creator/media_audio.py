"""
Audio Generation and Processing - TTS, music generation, ASR, and audio processing
Enhanced for CRT4 compatibility with provider interfaces
"""

import logging
import asyncio
import hashlib
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from ...ai.agent import UmbraAIAgent
from ...core.config import UmbraConfig
from .model_provider_enhanced import EnhancedModelProviderManager
from .errors import MediaError, ProviderError, ConsentError

logger = logging.getLogger(__name__)

@dataclass
class AudioResult:
    """Audio generation result"""
    audio_url: str
    meta: Dict[str, Any]
    provider: str
    model_used: str
    generation_time: float
    cost_estimate: float = 0.0

@dataclass
class TranscriptionResult:
    """Audio transcription result"""
    text: str
    srt_url: Optional[str]
    vtt_url: Optional[str]
    meta: Dict[str, Any]
    segments: Optional[List[Dict]] = None
    speakers: Optional[List[Dict]] = None

class AudioGenerator:
    """AI-powered audio generation and processing"""
    
    def __init__(self, ai_agent: UmbraAIAgent, config: UmbraConfig):
        self.ai_agent = ai_agent
        self.config = config
        self.provider_manager = EnhancedModelProviderManager(config)
        
        # Audio settings
        self.default_voice = config.get("CREATOR_DEFAULT_VOICE", "alloy")
        self.max_text_length = config.get("CREATOR_MAX_TTS_LENGTH", 4000)
        self.max_audio_duration = config.get("CREATOR_MAX_AUDIO_DURATION", 300)  # 5 minutes
        self.supported_formats = ["mp3", "wav", "ogg", "m4a"]
        
        # Voice registry (for consent management)
        self.voice_registry = {}
        
        logger.info("Audio generator initialized")
    
    async def text_to_speech(self, text: str, voice_id: Optional[str] = None, 
                           style: Optional[str] = None, speed: Optional[float] = None) -> Dict[str, Any]:
        """Convert text to speech"""
        try:
            if len(text) > self.max_text_length:
                raise MediaError(f"Text too long (max {self.max_text_length} characters)", "audio", "tts")
            
            # Check if voice requires consent
            if voice_id and voice_id != self.default_voice:
                if not await self._check_voice_consent(voice_id):
                    raise ConsentError("Voice requires consent for usage", "voice_usage")
            
            # Get TTS provider
            provider = await self.provider_manager.get_tts_provider()
            if not provider:
                raise ProviderError("No TTS providers available", "tts")
            
            # Generate TTS
            result = await provider.text_to_speech(
                text=text,
                voice_id=voice_id or self.default_voice,
                style=style,
                speed=speed
            )
            
            if not result.success:
                raise MediaError(f"TTS generation failed: {result.error}", "audio", "tts")
            
            # Save audio data if needed
            audio_data = result.data.get("audio_data")
            if audio_data:
                audio_url = await self._store_audio_data(audio_data, f"tts_{self._get_timestamp()}.mp3")
            else:
                audio_url = result.data.get("audio_url", "")
            
            return {
                "audio_url": audio_url,
                "meta": {
                    "provider": result.provider,
                    "voice_id": voice_id or self.default_voice,
                    "character_count": len(text),
                    "style": style,
                    "speed": speed,
                    "format": result.data.get("format", "mp3"),
                    "generation_time": result.metadata.get("generation_time", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise MediaError(f"TTS generation failed: {e}", "audio", "tts")
    
    async def generate_music(self, brief: str, duration_s: int = 30, genre: Optional[str] = None, 
                           bpm: Optional[int] = None, structure: Optional[str] = None, 
                           refs: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate music from brief"""
        try:
            if duration_s > 60:  # As per CRT3 requirements
                raise MediaError("Music duration must be ≤ 60 seconds", "audio", "music")
            
            # Get music provider
            provider = await self.provider_manager.get_music_provider()
            if not provider:
                raise ProviderError("No music generation providers available", "music")
            
            # Generate music
            result = await provider.generate_music(
                prompt=brief,
                duration=duration_s,
                genre=genre,
                bpm=bpm,
                structure=structure,
                refs=refs
            )
            
            if not result.success:
                raise MediaError(f"Music generation failed: {result.error}", "audio", "music")
            
            return {
                "audio_url": result.data.get("audio_url", ""),
                "meta": {
                    "provider": result.provider,
                    "model": result.model,
                    "brief": brief,
                    "duration": duration_s,
                    "genre": genre,
                    "bpm": bpm,
                    "structure": structure,
                    "format": result.data.get("format", "mp3"),
                    "generation_time": result.metadata.get("generation_time", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Music generation failed: {e}")
            raise MediaError(f"Music generation failed: {e}", "audio", "music")
    
    async def transcribe_media(self, media_id: str, diarization: bool = False) -> Dict[str, Any]:
        """Transcribe audio or video media"""
        try:
            # Get media data
            media_data = await self._get_media_data(media_id)
            if not media_data:
                raise MediaError(f"Media not found: {media_id}", "audio", "transcription")
            
            # Get ASR provider
            provider = await self.provider_manager.get_asr_provider()
            if not provider:
                raise ProviderError("No transcription providers available", "transcription")
            
            # Choose transcription method based on diarization need
            if diarization:
                result = await provider.transcribe_with_diarization(media_data)
            else:
                result = await provider.transcribe_audio(media_data)
            
            if not result.success:
                raise MediaError(f"Transcription failed: {result.error}", "audio", "transcription")
            
            # Extract transcription data
            transcription_data = result.data
            text = transcription_data.get("text", "")
            
            # Generate subtitle files
            srt_content = await self._generate_srt_from_segments(
                transcription_data.get("segments", []), text
            )
            vtt_content = await self._generate_vtt_from_segments(
                transcription_data.get("segments", []), text
            )
            
            # Store subtitle files
            srt_url = await self._store_subtitle_file(srt_content, "srt")
            vtt_url = await self._store_subtitle_file(vtt_content, "vtt")
            
            return {
                "text": text,
                "srt_url": srt_url,
                "vtt_url": vtt_url,
                "meta": {
                    "provider": result.provider,
                    "model": result.model,
                    "language": transcription_data.get("language", "en"),
                    "diarization": diarization,
                    "duration": transcription_data.get("duration"),
                    "confidence": transcription_data.get("confidence")
                }
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise MediaError(f"Transcription failed: {e}", "audio", "transcription")
    
    async def generate_subtitles(self, media_id: Optional[str] = None, text: Optional[str] = None, 
                               style: Optional[str] = None) -> Dict[str, Any]:
        """Generate subtitles from media or text"""
        try:
            if media_id:
                # Transcribe first, then generate subtitles
                transcription = await self.transcribe_media(media_id)
                text = transcription["text"]
            elif not text:
                raise MediaError("Either media_id or text is required", "audio", "subtitles")
            
            # Generate subtitle files
            srt_content = self._generate_srt_from_text(text, style)
            vtt_content = self._generate_vtt_from_text(text, style)
            
            # Store subtitle files
            srt_url = await self._store_subtitle_file(srt_content, "srt")
            vtt_url = await self._store_subtitle_file(vtt_content, "vtt")
            
            return {
                "srt_url": srt_url,
                "vtt_url": vtt_url,
                "text": text,
                "meta": {
                    "style": style,
                    "character_count": len(text),
                    "estimated_duration": len(text.split()) * 0.5  # ~0.5 seconds per word
                }
            }
            
        except Exception as e:
            logger.error(f"Subtitle generation failed: {e}")
            raise MediaError(f"Subtitle generation failed: {e}", "audio", "subtitles")
    
    async def register_voice(self, sample_url: str, consent_token: str) -> Dict[str, str]:
        """Register custom voice with consent"""
        try:
            # Validate consent token
            if not self._validate_consent_token(consent_token):
                raise ConsentError("Invalid consent token", "voice_registration")
            
            # Generate voice ID
            voice_id = self._generate_voice_id(sample_url)
            
            # Get TTS provider that supports voice registration
            provider = await self.provider_manager.get_tts_provider()
            if not provider:
                raise ProviderError("No TTS providers available", "voice_registration")
            
            # Try to register voice
            result = await provider.register_voice(sample_url, consent_token)
            
            if result.success:
                # Store consent record
                self.voice_registry[voice_id] = {
                    "sample_url": sample_url,
                    "consent_token": consent_token,
                    "provider": result.provider,
                    "created_at": self._get_timestamp(),
                    "status": "active",
                    "provider_voice_id": result.data.get("voice_id")
                }
                
                return {"voice_id": voice_id}
            else:
                raise MediaError(f"Voice registration failed: {result.error}", "audio", "voice_registration")
            
        except Exception as e:
            logger.error(f"Voice registration failed: {e}")
            raise MediaError(f"Voice registration failed: {e}", "audio", "voice_registration")
    
    async def list_voices(self) -> Dict[str, Any]:
        """List available voices"""
        try:
            # Get voices from TTS provider
            provider = await self.provider_manager.get_tts_provider()
            voices = {"default": [], "custom": []}
            
            if provider:
                result = await provider.list_voices()
                if result.success:
                    voices["default"] = result.data
            
            # Add custom voices
            voices["custom"] = [
                {
                    "voice_id": voice_id,
                    "created_at": voice_data["created_at"],
                    "status": voice_data["status"]
                }
                for voice_id, voice_data in self.voice_registry.items()
                if voice_data["status"] == "active"
            ]
            
            return voices
            
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return {"default": [], "custom": []}
    
    async def _generate_srt_from_text(self, text: str, style: Optional[str] = None) -> str:
        """Generate SRT subtitle format from plain text"""
        # Simple implementation - splits text into chunks
        words = text.split()
        chunks = []
        current_chunk = []
        
        words_per_chunk = 8  # ~2 seconds of reading
        for i, word in enumerate(words):
            current_chunk.append(word)
            if len(current_chunk) >= words_per_chunk or i == len(words) - 1:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
        
        srt_content = ""
        for i, chunk in enumerate(chunks):
            start_time = i * 2  # 2 seconds per chunk
            end_time = (i + 1) * 2
            
            srt_content += f"{i + 1}\n"
            srt_content += f"{self._seconds_to_srt_time(start_time)} --> {self._seconds_to_srt_time(end_time)}\n"
            srt_content += f"{chunk}\n\n"
        
        return srt_content
    
    async def _generate_srt_from_segments(self, segments: List[Dict], fallback_text: str) -> str:
        """Generate SRT from transcription segments"""
        if not segments:
            return self._generate_srt_from_text(fallback_text)
        
        # Group segments into subtitle chunks
        chunks = []
        current_chunk = []
        current_start = None
        
        for segment in segments:
            if current_start is None:
                current_start = segment.get("start", 0)
            
            current_chunk.append(segment.get("word", segment.get("text", "")))
            
            # Create chunk every ~3 seconds or ~8 words
            chunk_duration = segment.get("end", 0) - current_start
            if len(current_chunk) >= 8 or chunk_duration >= 3:
                chunks.append({
                    "text": " ".join(current_chunk),
                    "start": current_start,
                    "end": segment.get("end", current_start + 2)
                })
                current_chunk = []
                current_start = None
        
        # Handle remaining words
        if current_chunk and segments:
            chunks.append({
                "text": " ".join(current_chunk),
                "start": current_start or 0,
                "end": segments[-1].get("end", 0)
            })
        
        # Generate SRT
        srt_content = ""
        for i, chunk in enumerate(chunks):
            srt_content += f"{i + 1}\n"
            srt_content += f"{self._float_to_srt_time(chunk['start'])} --> {self._float_to_srt_time(chunk['end'])}\n"
            srt_content += f"{chunk['text']}\n\n"
        
        return srt_content
    
    async def _generate_vtt_from_text(self, text: str, style: Optional[str] = None) -> str:
        """Generate VTT subtitle format from plain text"""
        srt_content = self._generate_srt_from_text(text, style)
        return "WEBVTT\n\n" + srt_content.replace(',', '.')
    
    async def _generate_vtt_from_segments(self, segments: List[Dict], fallback_text: str) -> str:
        """Generate VTT from transcription segments"""
        srt_content = await self._generate_srt_from_segments(segments, fallback_text)
        return "WEBVTT\n\n" + srt_content.replace(',', '.')
    
    def _seconds_to_srt_time(self, seconds: int) -> str:
        """Convert seconds to SRT timestamp format"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d},000"
    
    def _float_to_srt_time(self, seconds: float) -> str:
        """Convert float seconds to SRT timestamp"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    async def _store_audio_data(self, audio_data: bytes, filename: str) -> str:
        """Store audio data and return URL"""
        # In a real implementation, would upload to R2 storage
        audio_hash = hashlib.md5(audio_data).hexdigest()
        return f"https://storage.example.com/audio/{audio_hash}_{filename}"
    
    async def _store_subtitle_file(self, content: str, format_type: str) -> str:
        """Store subtitle file and return URL"""
        # In a real implementation, would upload to R2 storage
        import time
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"https://storage.example.com/subtitles/{content_hash}_{int(time.time())}.{format_type}"
    
    async def _get_media_data(self, media_id: str) -> Optional[bytes]:
        """Get media data by ID"""
        # Placeholder implementation - would fetch from storage
        logger.info(f"Getting media data for media_id: {media_id}")
        return None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def _generate_voice_id(self, sample_url: str) -> str:
        """Generate unique voice ID"""
        return f"voice_{hashlib.md5(sample_url.encode()).hexdigest()[:8]}"
    
    def _validate_consent_token(self, consent_token: str) -> bool:
        """Validate consent token"""
        # Placeholder implementation - would validate JWT or similar
        return len(consent_token) > 10
    
    async def _check_voice_consent(self, voice_id: str) -> bool:
        """Check if voice has valid consent"""
        return voice_id in self.voice_registry and self.voice_registry[voice_id]["status"] == "active"
    
    def get_supported_audio_formats(self) -> List[str]:
        """Get supported audio formats"""
        return self.supported_formats.copy()
    
    async def get_audio_generation_cost_estimate(self, operation: str, **kwargs) -> float:
        """Get cost estimate for audio operations"""
        cost_map = {
            "tts": {
                "elevenlabs": lambda chars: chars * 0.0001,
                "openai": lambda chars: chars * 0.000015
            },
            "music": {
                "suno": lambda duration: 0.1,
                "udio": lambda duration: 0.08,
                "replicate": lambda duration: 0.03
            },
            "transcription": {
                "deepgram": lambda minutes: minutes * 0.0125,
                "whisper": lambda minutes: minutes * 0.006
            }
        }
        
        if operation in cost_map:
            provider = kwargs.get("provider", list(cost_map[operation].keys())[0])
            cost_func = cost_map[operation].get(provider)
            if cost_func:
                if operation == "tts":
                    return cost_func(kwargs.get("character_count", 1000))
                elif operation == "music":
                    return cost_func(kwargs.get("duration", 30))
                elif operation == "transcription":
                    return cost_func(kwargs.get("duration_minutes", 5))
        
        return 0.05  # Default estimate
    
    async def enhance_audio(self, media_id: str, enhancement_type: str = "normalize") -> Dict[str, Any]:
        """Enhance audio quality"""
        try:
            # Get audio data
            audio_data = await self._get_media_data(media_id)
            if not audio_data:
                raise MediaError(f"Audio not found: {media_id}", "audio", "enhancement")
            
            # Apply enhancement based on type
            if enhancement_type == "normalize":
                enhanced_data = await self._normalize_audio(audio_data)
            elif enhancement_type == "denoise":
                enhanced_data = await self._denoise_audio(audio_data)
            elif enhancement_type == "lufs":
                enhanced_data = await self._apply_lufs_normalization(audio_data)
            else:
                raise MediaError(f"Unknown enhancement type: {enhancement_type}", "audio", "enhancement")
            
            # Store enhanced audio
            enhanced_url = await self._store_audio_data(enhanced_data, f"enhanced_{media_id}.mp3")
            
            return {
                "audio_url": enhanced_url,
                "meta": {
                    "original_media_id": media_id,
                    "enhancement_type": enhancement_type,
                    "processing_time": 0  # Placeholder
                }
            }
            
        except Exception as e:
            logger.error(f"Audio enhancement failed: {e}")
            raise MediaError(f"Audio enhancement failed: {e}", "audio", "enhancement")
    
    async def _normalize_audio(self, audio_data: bytes) -> bytes:
        """Normalize audio levels"""
        # Placeholder implementation
        # In production, would use audio processing libraries
        logger.info("Applying audio normalization")
        return audio_data
    
    async def _denoise_audio(self, audio_data: bytes) -> bytes:
        """Remove noise from audio"""
        # Placeholder implementation
        logger.info("Applying audio denoising")
        return audio_data
    
    async def _apply_lufs_normalization(self, audio_data: bytes) -> bytes:
        """Apply LUFS loudness normalization"""
        # Placeholder implementation
        logger.info("Applying LUFS normalization")
        return audio_data
    
    def get_audio_stats(self) -> Dict[str, Any]:
        """Get audio generation statistics"""
        return {
            "registered_voices": len(self.voice_registry),
            "active_voices": len([v for v in self.voice_registry.values() if v["status"] == "active"]),
            "supported_formats": self.supported_formats,
            "max_text_length": self.max_text_length,
            "max_audio_duration": self.max_audio_duration,
            "default_voice": self.default_voice
        }
