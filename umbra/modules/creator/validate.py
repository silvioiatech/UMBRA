"""
Content Validator - Validates content against platform rules, PII, and guardrails
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from ...core.config import UmbraConfig
from .presets import PlatformPresets
from .errors import ValidationError

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of content validation"""
    ok: bool
    errors: List[str]
    warnings: List[str]
    counts: Dict[str, int]
    pii_detected: List[str]
    banned_phrases: List[str]
    recommendations: List[str]

class ContentValidator:
    """Validates content against platform rules and guardrails"""
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        self.presets = PlatformPresets(config)
        
        # PII settings
        self.pii_enabled = config.get("CREATOR_PII_DEFAULT", True)
        self.mask_char = config.get("CREATOR_PII_MASK_CHAR", "*")
        self.preserve_length = config.get("CREATOR_PII_PRESERVE_LENGTH", True)
        
        # Compile PII patterns
        self.pii_patterns = self._compile_pii_patterns()
        
        # Load banned phrases
        self.global_banned_phrases = self._load_global_banned_phrases()
        
        logger.info("Content validator initialized")
    
    def _compile_pii_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for PII detection"""
        patterns = {
            # Email addresses
            "email": re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Union[Z, a]-z]{2,}\b',
                re.IGNORECASE
            ),
            
            # Phone numbers (E.164 format and common variations)
            "phone": re.compile(
                r'(\+\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
                re.IGNORECASE
            ),
            
            # Credit card numbers (simple pattern)
            "credit_card": re.compile(
                r'\b(?:\d{4}[-.\s]?){3}\d{4}\b'
            ),
            
            # Social security numbers (US format)
            "ssn": re.compile(
                r'\b\d{3}-?\d{2}-?\d{4}\b'
            ),
            
            # IP addresses
            "ip_address": re.compile(
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ),
            
            # API keys (common patterns)
            "api_key": re.compile(
                r'\b(?:api[_-]?Union[key, toke]Union[n, secret])["\s]*[:=]["\s]*[A-Za-z0-9+/]{20,}["\s]*',
                re.IGNORECASE
            )
        }
        
        return patterns
    
    def _load_global_banned_phrases(self) -> List[str]:
        """Load globally banned phrases"""
        return [
            # Spam indicators
            "guaranteed money",
            "free money",
            "click here now",
            "limited time offer",
            "act now",
            
            # Potentially harmful
            "medical advice",
            "financial advice", 
            "investment advice",
            "legal advice",
            
            # Misleading claims
            "proven results",
            "100% guaranteed",
            "scientifically proven",
            "doctors hate this",
            
            # Adult content indicators
            "xxx",
            "adult content",
            "explicit content"
        ]
    
    async def validate_content(self, text: Optional[str] = None, 
                             asset: Optional[Dict] = None, 
                             platform: Optional[str] = None) -> Dict[str, Any]:
        """Validate content against all rules"""
        try:
            if text:
                return await self._validate_text_content(text, platform)
            elif asset:
                return await self._validate_asset_content(asset, platform)
            else:
                return {"ok": False, "errors": ["No content provided for validation"]}
                
        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            raise ValidationError(f"Validation failed: {e}")
    
    async def _validate_text_content(self, text: str, platform: Optional[str] = None) -> Dict[str, Any]:
        """Validate text content"""
        errors = []
        warnings = []
        recommendations = []
        
        # Basic content analysis
        counts = self._analyze_content_counts(text)
        
        # Platform-specific validation
        if platform:
            platform_result = self.presets.validate_content_for_platform(text, platform)
            if not platform_result["valid"]:
                errors.extend(platform_result["issues"])
            warnings.extend(platform_result["warnings"])
        
        # PII detection
        pii_detected = []
        if self.pii_enabled:
            pii_detected = self._detect_pii(text)
            if pii_detected:
                warnings.append(f"PII detected: {', '.join(set(item['type'] for item in pii_detected))}")
        
        # Banned phrase detection
        banned_found = self._detect_banned_phrases(text)
        if banned_found:
            errors.extend([f"Contains banned phrase: '{phrase}'" for phrase in banned_found])
        
        # Content quality checks
        quality_issues = self._check_content_quality(text)
        warnings.extend(quality_issues)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(text, counts, platform)
        
        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "counts": counts,
            "pii_detected": [item['type'] for item in pii_detected],
            "banned_phrases": banned_found,
            "recommendations": recommendations
        }
    
    async def _validate_asset_content(self, asset: Dict, platform: Optional[str] = None) -> Dict[str, Any]:
        """Validate asset content (images, videos, etc.)"""
        errors = []
        warnings = []
        
        asset_type = asset.get("type", "unknown")
        
        # Basic asset validation
        if "url" not in asset and "data" not in asset:
            errors.append("Asset must have either 'url' or 'data'")
        
        # Size checks (if available)
        if "size" in asset:
            max_size = self._get_max_asset_size(asset_type, platform)
            if asset["size"] > max_size:
                errors.append(f"Asset size ({asset['size']} bytes) exceeds limit ({max_size} bytes)")
        
        # Format checks
        if asset_type == "image":
            errors.extend(self._validate_image_asset(asset))
        elif asset_type == "video":
            errors.extend(self._validate_video_asset(asset))
        elif asset_type == "audio":
            errors.extend(self._validate_audio_asset(asset))
        
        return {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "asset_type": asset_type
        }
    
    def _analyze_content_counts(self, text: str) -> Dict[str, int]:
        """Analyze content for various counts"""
        return {
            "characters": len(text),
            "words": len(text.split()),
            "sentences": text.count('.') + text.count('!') + text.count('?'),
            "paragraphs": len([p for p in text.split('\n\n') if p.strip()]),
            "hashtags": text.count('#'),
            "mentions": text.count('@'),
            "urls": len(re.findall(r'https?://\S+', text)),
            "emojis": len([c for c in text if ord(c) > 127]),  # Simple emoji detection
            "line_breaks": text.count('\n'),
            "exclamations": text.count('!'),
            "questions": text.count('?')
        }
    
    def _detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """Detect personally identifiable information"""
        pii_found = []
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                # Skip @handles and URLs for social media
                if pii_type == "email" and (match.startswith('@') or 'bit.ly' in match):
                    continue
                
                pii_found.append({
                    "type": pii_type,
                    "value": match,
                    "position": text.find(match)
                })
        
        return pii_found
    
    def _detect_banned_phrases(self, text: str) -> List[str]:
        """Detect banned phrases in content"""
        text_lower = text.lower()
        found_phrases = []
        
        for phrase in self.global_banned_phrases:
            if phrase.lower() in text_lower:
                found_phrases.append(phrase)
        
        return found_phrases
    
    def _check_content_quality(self, text: str) -> List[str]:
        """Check content quality issues"""
        issues = []
        
        # Check for excessive capitalization
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if caps_ratio > 0.3:
            issues.append("Excessive capitalization detected")
        
        # Check for repeated characters
        if re.search(r'(.)\1{4,}', text):
            issues.append("Excessive character repetition detected")
        
        # Check for excessive punctuation
        punct_count = sum(text.count(p) for p in '!?.')
        if punct_count > len(text.split()) * 0.5:
            issues.append("Excessive punctuation detected")
        
        # Check for very short sentences
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        short_sentences = [s for s in sentences if len(s.split()) < 3]
        if len(short_sentences) > len(sentences) * 0.5:
            issues.append("Many very short sentences detected")
        
        return issues
    
    def _generate_recommendations(self, text: str, counts: Dict[str, int], 
                                platform: Optional[str] = None) -> List[str]:
        """Generate content improvement recommendations"""
        recommendations = []
        
        # Length recommendations
        if platform:
            preset = self.presets.get_platform_preset(platform)
            char_limit = preset["char_limit"]
            
            if counts["characters"] < char_limit * 0.3:
                recommendations.append("Consider adding more content to increase engagement")
            elif counts["characters"] > char_limit * 0.9:
                recommendations.append("Content is approaching character limit")
        
        # Engagement recommendations
        if counts["questions"] == 0 and counts["exclamations"] == 0:
            recommendations.append("Consider adding questions or exclamations to increase engagement")
        
        if counts["hashtags"] == 0 and platform in ["instagram", "twitter", "tiktok"]:
            recommendations.append(f"Consider adding hashtags for {platform} discoverability")
        
        # Readability recommendations
        avg_sentence_length = counts["words"] / max(counts["sentences"], 1)
        if avg_sentence_length > 25:
            recommendations.append("Consider shorter sentences for better readability")
        
        # Platform-specific recommendations
        if platform == "linkedin" and counts["emojis"] > 3:
            recommendations.append("Consider reducing emoji usage for LinkedIn's professional audience")
        
        if platform == "twitter" and counts["hashtags"] > 3:
            recommendations.append("Twitter posts perform better with 1-3 hashtags")
        
        return recommendations
    
    def redact_pii(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Redact PII from text"""
        if not self.pii_enabled:
            return text, []
        
        redacted_text = text
        pii_found = []
        
        # Process each PII type
        for pii_type, pattern in self.pii_patterns.items():
            matches = list(pattern.finditer(redacted_text))
            
            for match in reversed(matches):  # Reverse to maintain positions
                matched_text = match.group()
                
                # Skip social media handles and common URLs
                if pii_type == "email" and (matched_text.startswith('@') or 
                                          any(domain in matched_text.lower() for domain in 
                                              ['bit.ly', 'tinyurl', 'short.link'])):
                    continue
                
                # Create redacted version
                if self.preserve_length:
                    redacted_value = self.mask_char * len(matched_text)
                else:
                    redacted_value = f"[{pii_type.upper()}]"
                
                # Replace in text
                start, end = match.span()
                redacted_text = redacted_text[:start] + redacted_value + redacted_text[end:]
                
                pii_found.append({
                    "type": pii_type,
                    "original": matched_text,
                    "redacted": redacted_value,
                    "position": start
                })
        
        return redacted_text, pii_found
    
    def _get_max_asset_size(self, asset_type: str, platform: Optional[str] = None) -> int:
        """Get maximum asset size for type and platform"""
        # Default limits in bytes
        default_limits = {
            "image": 10 * 1024 * 1024,  # 10MB
            "video": 100 * 1024 * 1024,  # 100MB
            "audio": 50 * 1024 * 1024   # 50MB
        }
        
        # Platform-specific overrides
        platform_limits = {
            "twitter": {
                "image": 5 * 1024 * 1024,  # 5MB
                "video": 512 * 1024 * 1024  # 512MB
            },
            "instagram": {
                "image": 8 * 1024 * 1024,  # 8MB
                "video": 4 * 1024 * 1024 * 1024  # 4GB
            },
            "telegram": {
                "image": 10 * 1024 * 1024,  # 10MB
                "video": 2 * 1024 * 1024 * 1024,  # 2GB
                "audio": 50 * 1024 * 1024   # 50MB
            }
        }
        
        if platform and platform in platform_limits:
            return platform_limits[platform].get(asset_type, default_limits.get(asset_type, 10 * 1024 * 1024))
        
        return default_limits.get(asset_type, 10 * 1024 * 1024)
    
    def _validate_image_asset(self, asset: Dict) -> List[str]:
        """Validate image asset"""
        errors = []
        
        # Check format
        allowed_formats = ["jpg", "jpeg", "png", "gif", "webp"]
        format_val = asset.get("format", "").lower()
        if format_val and format_val not in allowed_formats:
            errors.append(f"Unsupported image format: {format_val}")
        
        # Check dimensions
        width = asset.get("width", 0)
        height = asset.get("height", 0)
        
        if width > 0 and height > 0:
            # Check aspect ratio extremes
            aspect_ratio = width / height
            if aspect_ratio > 10 or aspect_ratio < 0.1:
                errors.append("Extreme aspect ratio may cause display issues")
            
            # Check minimum dimensions
            if width < 100 or height < 100:
                errors.append("Image dimensions too small (minimum 100x100)")
        
        return errors
    
    def _validate_video_asset(self, asset: Dict) -> List[str]:
        """Validate video asset"""
        errors = []
        
        # Check format
        allowed_formats = ["mp4", "mov", "avi", "webm"]
        format_val = asset.get("format", "").lower()
        if format_val and format_val not in allowed_formats:
            errors.append(f"Unsupported video format: {format_val}")
        
        # Check duration
        duration = asset.get("duration", 0)
        if duration > 300:  # 5 minutes
            errors.append("Video duration exceeds 5 minute limit")
        
        return errors
    
    def _validate_audio_asset(self, asset: Dict) -> List[str]:
        """Validate audio asset"""
        errors = []
        
        # Check format
        allowed_formats = ["mp3", "wav", "m4a", "ogg"]
        format_val = asset.get("format", "").lower()
        if format_val and format_val not in allowed_formats:
            errors.append(f"Unsupported audio format: {format_val}")
        
        # Check duration
        duration = asset.get("duration", 0)
        if duration > 600:  # 10 minutes
            errors.append("Audio duration exceeds 10 minute limit")
        
        return errors
    
    def validate_platform_constraints(self, content: str, platform: str) -> Dict[str, Any]:
        """Validate content against specific platform constraints"""
        preset = self.presets.get_platform_preset(platform)
        return self.presets.validate_content_for_platform(content, platform)
    
    def get_content_score(self, content: str, platform: Optional[str] = None) -> Dict[str, float]:
        """Get overall content quality score"""
        counts = self._analyze_content_counts(content)
        
        scores = {
            "readability": self._calculate_readability_score(content),
            "engagement": self._calculate_engagement_score(content),
            "platform_compliance": 1.0,  # Default to compliant
            "pii_safety": 1.0 - (len(self._detect_pii(content)) * 0.2),
            "banned_content": 1.0 - (len(self._detect_banned_phrases(content)) * 0.3)
        }
        
        # Platform compliance score
        if platform:
            validation = self.presets.validate_content_for_platform(content, platform)
            scores["platform_compliance"] = 1.0 if validation["valid"] else 0.5
        
        # Overall score
        scores["overall"] = sum(scores.values()) / len(scores)
        
        return scores
    
    def _calculate_readability_score(self, text: str) -> float:
        """Calculate readability score (simplified Flesch Reading Ease)"""
        words = text.split()
        sentences = text.count('.') + text.count('!') + text.count('?')
        
        if not sentences or not words:
            return 0.5
        
        avg_sentence_length = len(words) / sentences
        
        # Simplified scoring
        if avg_sentence_length <= 15:
            return 1.0
        elif avg_sentence_length <= 25:
            return 0.8
        elif avg_sentence_length <= 35:
            return 0.6
        else:
            return 0.4
    
    def _calculate_engagement_score(self, text: str) -> float:
        """Calculate potential engagement score"""
        engagement_indicators = {
            "questions": text.count('?') * 0.1,
            "exclamations": text.count('!') * 0.05,
            "emojis": len([c for c in text if ord(c) > 127]) * 0.02,
            "calls_to_action": len(re.findall(r'\b(Union[click, shar]Union[e, lik]Union[e, commen]Union[t, follo]Union[w, subscribe])\b', text.lower())) * 0.1
        }
        
        base_score = 0.5
        bonus_score = sum(engagement_indicators.values())
        
        return min(base_score + bonus_score, 1.0)
    
    async def batch_validate(self, contents: List[str], platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Validate multiple pieces of content"""
        results = []
        
        for content in contents:
            try:
                result = await self.validate_content(content, None, platform)
                results.append(result)
            except Exception as e:
                results.append({
                    "ok": False,
                    "errors": [f"Validation error: {e}"],
                    "warnings": [],
                    "counts": {},
                    "pii_detected": [],
                    "banned_phrases": [],
                    "recommendations": []
                })
        
        return results
