"""
Brand Voice Management - KV store for brand consistency and voice guidelines
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from ...core.config import UmbraConfig
from .errors import BrandVoiceError

logger = logging.getLogger(__name__)

@dataclass
class BrandVoice:
    """Brand voice configuration"""
    brand_name: str = ""
    bio: str = ""
    audience: str = ""
    tone_default: str = "professional"
    do: List[str] = None
    dont: List[str] = None
    banned_phrases: List[str] = None
    cta_style: str = "engaging"
    emoji_policy: str = "moderate"  # none, minimal, moderate, liberal
    link_policy: str = "end"  # beginning, end, anywhere, none
    required_phrases: List[str] = None
    discouraged_words: List[str] = None
    reading_level: str = "intermediate"  # elementary, intermediate, advanced
    voice_personality: str = "friendly"  # formal, friendly, casual, authoritative
    content_themes: List[str] = None
    target_demographics: Dict[str, Any] = None
    compliance_rules: List[str] = None
    
    def __post_init__(self):
        # Initialize empty lists if None
        if self.do is None:
            self.do = []
        if self.dont is None:
            self.dont = []
        if self.banned_phrases is None:
            self.banned_phrases = []
        if self.required_phrases is None:
            self.required_phrases = []
        if self.discouraged_words is None:
            self.discouraged_words = []
        if self.content_themes is None:
            self.content_themes = []
        if self.target_demographics is None:
            self.target_demographics = {}
        if self.compliance_rules is None:
            self.compliance_rules = []

class BrandVoiceManager:
    """Manager for brand voice configuration and guidelines"""
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        self.kv_namespace = "creator:voice"
        self.max_kv_size = 8192  # 8KB limit as specified
        self.current_brand_id = "default"
        
        # Cache for brand voice
        self._brand_voice_cache = {}
        
        logger.info("Brand voice manager initialized")
    
    async def set_brand_voice(self, meta_json: Dict[str, Any], brand_id: str = "default") -> bool:
        """Set brand voice configuration"""
        try:
            # Validate the meta_json structure
            self._validate_brand_voice_data(meta_json)
            
            # Create BrandVoice object for validation
            brand_voice = BrandVoice(**meta_json)
            
            # Serialize and check size
            serialized = json.dumps(asdict(brand_voice))
            if len(serialized.encode('utf-8')) > self.max_kv_size:
                raise BrandVoiceError(f"Brand voice data exceeds {self.max_kv_size} bytes limit")
            
            # Store in KV (simulated with local storage for now)
            key = f"{self.kv_namespace}:{brand_id}"
            await self._store_kv(key, asdict(brand_voice))
            
            # Update cache
            self._brand_voice_cache[brand_id] = brand_voice
            
            logger.info(f"Brand voice set for brand_id: {brand_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set brand voice: {e}")
            raise BrandVoiceError(f"Failed to set brand voice: {e}")
    
    async def get_brand_voice(self, brand_id: str = "default") -> Dict[str, Any]:
        """Get brand voice configuration"""
        try:
            # Check cache first
            if brand_id in self._brand_voice_cache:
                return asdict(self._brand_voice_cache[brand_id])
            
            # Load from KV store
            key = f"{self.kv_namespace}:{brand_id}"
            data = await self._load_kv(key)
            
            if data:
                brand_voice = BrandVoice(**data)
                self._brand_voice_cache[brand_id] = brand_voice
                return asdict(brand_voice)
            else:
                # Return default brand voice
                default_voice = self._get_default_brand_voice()
                self._brand_voice_cache[brand_id] = default_voice
                return asdict(default_voice)
                
        except Exception as e:
            logger.error(f"Failed to get brand voice: {e}")
            # Return default on error
            return asdict(self._get_default_brand_voice())
    
    def _get_default_brand_voice(self) -> BrandVoice:
        """Get default brand voice configuration"""
        return BrandVoice(
            brand_name="Brand",
            bio="A modern, engaging brand",
            audience="general",
            tone_default="friendly",
            do=["be authentic", "engage with audience", "provide value"],
            dont=["use jargon", "be overly promotional", "ignore feedback"],
            banned_phrases=["guaranteed", "free money", "click here"],
            cta_style="engaging",
            emoji_policy="moderate",
            link_policy="end",
            required_phrases=[],
            discouraged_words=["obviously", "literally", "actually"],
            reading_level="intermediate",
            voice_personality="friendly",
            content_themes=["helpful", "informative", "engaging"],
            target_demographics={
                "age_range": "25-45",
                "interests": ["technology", "lifestyle"],
                "platforms": ["instagram", "linkedin", "twitter"]
            },
            compliance_rules=["no medical claims", "include disclaimers"]
        )
    
    def _validate_brand_voice_data(self, data: Dict[str, Any]) -> None:
        """Validate brand voice data structure"""
        required_fields = ["brand_name"]
        
        for field in required_fields:
            if field not in data:
                raise BrandVoiceError(f"Missing required field: {field}")
        
        # Validate enum values
        valid_tones = ["formal", "professional", "friendly", "casual", "authoritative", "playful"]
        if "tone_default" in data and data["tone_default"] not in valid_tones:
            raise BrandVoiceError(f"Invalid tone_default. Must be one of: {valid_tones}")
        
        valid_emoji_policies = ["none", "minimal", "moderate", "liberal"]
        if "emoji_policy" in data and data["emoji_policy"] not in valid_emoji_policies:
            raise BrandVoiceError(f"Invalid emoji_policy. Must be one of: {valid_emoji_policies}")
        
        valid_link_policies = ["beginning", "end", "anywhere", "none"]
        if "link_policy" in data and data["link_policy"] not in valid_link_policies:
            raise BrandVoiceError(f"Invalid link_policy. Must be one of: {valid_link_policies}")
        
        valid_reading_levels = ["elementary", "intermediate", "advanced"]
        if "reading_level" in data and data["reading_level"] not in valid_reading_levels:
            raise BrandVoiceError(f"Invalid reading_level. Must be one of: {valid_reading_levels}")
    
    async def merge_brand_voice_with_request(self, request_overrides: Dict[str, Any], 
                                           platform_defaults: Dict[str, Any],
                                           brand_id: str = "default") -> Dict[str, Any]:
        """Merge brand voice with request overrides and platform defaults"""
        try:
            # Get brand voice (lowest priority)
            brand_voice = await self.get_brand_voice(brand_id)
            
            # Merge order: request > brand_kv > platform default
            merged = {}
            
            # Start with platform defaults
            merged.update(platform_defaults)
            
            # Override with brand voice
            merged.update(brand_voice)
            
            # Finally override with request-specific settings
            merged.update(request_overrides)
            
            return merged
            
        except Exception as e:
            logger.error(f"Failed to merge brand voice: {e}")
            return request_overrides  # Fallback to request only
    
    def apply_brand_voice_to_prompt(self, base_prompt: str, brand_voice: Dict[str, Any]) -> str:
        """Apply brand voice guidelines to generation prompt"""
        try:
            # Extract key brand voice elements
            brand_name = brand_voice.get("brand_name", "Brand")
            tone = brand_voice.get("tone_default", "friendly")
            voice_personality = brand_voice.get("voice_personality", "friendly")
            do_list = brand_voice.get("do", [])
            dont_list = brand_voice.get("dont", [])
            required_phrases = brand_voice.get("required_phrases", [])
            discouraged_words = brand_voice.get("discouraged_words", [])
            reading_level = brand_voice.get("reading_level", "intermediate")
            
            # Build enhanced prompt
            enhanced_prompt = f"""{base_prompt}
            
Brand Voice Guidelines for {brand_name}:
- Tone: {tone}
- Personality: {voice_personality}
- Reading level: {reading_level}"""
            
            if do_list:
                enhanced_prompt += f"\n- DO: {', '.join(do_list)}"
            
            if dont_list:
                enhanced_prompt += f"\n- DON'T: {', '.join(dont_list)}"
            
            if required_phrases:
                enhanced_prompt += f"\n- Include phrases: {', '.join(required_phrases)}"
            
            if discouraged_words:
                enhanced_prompt += f"\n- Avoid words: {', '.join(discouraged_words)}"
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Failed to apply brand voice to prompt: {e}")
            return base_prompt  # Return original prompt on error
    
    def validate_content_against_brand_voice(self, content: str, brand_voice: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content against brand voice guidelines"""
        issues = []
        warnings = []
        suggestions = []
        
        try:
            content_lower = content.lower()
            
            # Check banned phrases
            banned_phrases = brand_voice.get("banned_phrases", [])
            for phrase in banned_phrases:
                if phrase.lower() in content_lower:
                    issues.append(f"Contains banned phrase: '{phrase}'")
            
            # Check required phrases
            required_phrases = brand_voice.get("required_phrases", [])
            for phrase in required_phrases:
                if phrase.lower() not in content_lower:
                    warnings.append(f"Missing required phrase: '{phrase}'")
            
            # Check discouraged words
            discouraged_words = brand_voice.get("discouraged_words", [])
            for word in discouraged_words:
                if word.lower() in content_lower:
                    suggestions.append(f"Consider replacing discouraged word: '{word}'")
            
            # Check tone alignment (simplified)
            tone = brand_voice.get("tone_default", "friendly")
            tone_score = self._analyze_tone_alignment(content, tone)
            if tone_score < 0.7:
                suggestions.append(f"Content tone may not align with brand tone: {tone}")
            
            # Check reading level (simplified)
            reading_level = brand_voice.get("reading_level", "intermediate")
            level_score = self._analyze_reading_level(content, reading_level)
            if level_score < 0.7:
                suggestions.append(f"Content may not match target reading level: {reading_level}")
            
            return {
                "compliant": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "suggestions": suggestions,
                "scores": {
                    "tone_alignment": tone_score,
                    "reading_level_match": level_score
                }
            }
            
        except Exception as e:
            logger.error(f"Brand voice validation failed: {e}")
            return {
                "compliant": True,  # Default to compliant on error
                "issues": [],
                "warnings": [],
                "suggestions": [],
                "scores": {}
            }
    
    def _analyze_tone_alignment(self, content: str, target_tone: str) -> float:
        """Analyze how well content aligns with target tone (simplified)"""
        content_lower = content.lower()
        
        tone_indicators = {
            "formal": ["therefore", "furthermore", "consequently", "nevertheless"],
            "professional": ["expertise", "solutions", "optimize", "strategic"],
            "friendly": ["great", "awesome", "love", "excited", "happy"],
            "casual": ["hey", "cool", "stuff", "things", "pretty"],
            "authoritative": ["proven", "established", "definitive", "conclusive"],
            "playful": ["fun", "amazing", "wow", "incredible", "fantastic"]
        }
        
        indicators = tone_indicators.get(target_tone, [])
        if not indicators:
            return 0.8  # Default score for unknown tones
        
        matches = sum(1 for indicator in indicators if indicator in content_lower)
        return min(matches / len(indicators) + 0.5, 1.0)
    
    def _analyze_reading_level(self, content: str, target_level: str) -> float:
        """Analyze reading level match (simplified)"""
        words = content.split()
        sentences = content.count('.') + content.count('!') + content.count('?')
        
        if not sentences:
            sentences = 1
        
        avg_words_per_sentence = len(words) / sentences
        
        # Simplified reading level scoring
        if target_level == "elementary":
            ideal_range = (5, 12)
        elif target_level == "intermediate":
            ideal_range = (12, 20)
        else:  # advanced
            ideal_range = (20, 30)
        
        if ideal_range[0] <= avg_words_per_sentence <= ideal_range[1]:
            return 1.0
        elif avg_words_per_sentence < ideal_range[0]:
            return max(0.5, avg_words_per_sentence / ideal_range[0])
        else:
            return max(0.5, ideal_range[1] / avg_words_per_sentence)
    
    async def _store_kv(self, key: str, value: Dict[str, Any]) -> None:
        """Store value in KV store (simulated)"""
        # In a real implementation, this would use a proper KV store
        # For now, we'll use a simple file-based approach
        import os
        import tempfile
        
        kv_dir = os.path.join(tempfile.gettempdir(), "umbra_kv")
        os.makedirs(kv_dir, exist_ok=True)
        
        safe_key = key.replace(":", "_").replace("/", "_")
        file_path = os.path.join(kv_dir, f"{safe_key}.json")
        
        with open(file_path, 'w') as f:
            json.dump(value, f, indent=2)
    
    async def _load_kv(self, key: str) -> Optional[Dict[str, Any]]:
        """Load value from KV store (simulated)"""
        import os
        import tempfile
        
        kv_dir = os.path.join(tempfile.gettempdir(), "umbra_kv")
        safe_key = key.replace(":", "_").replace("/", "_")
        file_path = os.path.join(kv_dir, f"{safe_key}.json")
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load KV data: {e}")
        
        return None
    
    def get_brand_voice_template(self) -> Dict[str, Any]:
        """Get a template for brand voice configuration"""
        template = asdict(self._get_default_brand_voice())
        
        # Add helpful comments
        template["_comments"] = {
            "brand_name": "The name of your brand or organization",
            "bio": "A brief description of your brand's mission and values",
            "audience": "Your primary target audience description",
            "tone_default": "Options: formal, professional, friendly, casual, authoritative, playful",
            "do": "List of things your brand should do in communications",
            "dont": "List of things your brand should avoid",
            "banned_phrases": "Specific phrases that should never be used",
            "cta_style": "Style of call-to-action (engaging, direct, soft, etc.)",
            "emoji_policy": "Options: none, minimal, moderate, liberal",
            "link_policy": "Where to place links: beginning, end, anywhere, none",
            "reading_level": "Options: elementary, intermediate, advanced"
        }
        
        return template
    
    async def export_brand_voice(self, brand_id: str = "default") -> str:
        """Export brand voice configuration as JSON"""
        brand_voice = await self.get_brand_voice(brand_id)
        return json.dumps(brand_voice, indent=2)
    
    async def import_brand_voice(self, json_data: str, brand_id: str = "default") -> bool:
        """Import brand voice configuration from JSON"""
        try:
            data = json.loads(json_data)
            return await self.set_brand_voice(data, brand_id)
        except json.JSONDecodeError as e:
            raise BrandVoiceError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise BrandVoiceError(f"Import failed: {e}")
    
    def list_brand_ids(self) -> List[str]:
        """List all available brand IDs"""
        # In a real implementation, this would query the KV store
        # For now, return the cached brand IDs
        return list(self._brand_voice_cache.keys()) or ["default"]
    
    async def delete_brand_voice(self, brand_id: str) -> bool:
        """Delete brand voice configuration"""
        try:
            if brand_id == "default":
                raise BrandVoiceError("Cannot delete default brand voice")
            
            # Remove from cache
            if brand_id in self._brand_voice_cache:
                del self._brand_voice_cache[brand_id]
            
            # Remove from KV store (simulated)
            import os
            import tempfile
            
            kv_dir = os.path.join(tempfile.gettempdir(), "umbra_kv")
            key = f"{self.kv_namespace}:{brand_id}"
            safe_key = key.replace(":", "_").replace("/", "_")
            file_path = os.path.join(kv_dir, f"{safe_key}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            logger.info(f"Brand voice deleted: {brand_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete brand voice: {e}")
            raise BrandVoiceError(f"Delete failed: {e}")
