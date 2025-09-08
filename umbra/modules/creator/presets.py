"""
Platform Presets - Per-platform limits, CTA styles, hashtag rules, emoji policy
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ...core.config import UmbraConfig

logger = logging.getLogger(__name__)

@dataclass
class PlatformPreset:
    """Platform-specific content constraints and preferences"""
    name: str
    char_limit: int
    max_hashtags: int
    max_title_length: int
    emoji_density_limit: float  # Max emojis per 100 characters
    link_placement: str  # "beginning", "end", "anywhere"
    cta_style: str  # "direct", "question", "soft"
    hashtag_style: str  # "inline", "grouped", "comment"
    line_break_style: str  # "minimal", "moderate", "liberal"
    banned_content: List[str]
    required_elements: List[str]
    optimal_posting_times: List[str]
    engagement_features: List[str]

class PlatformPresets:
    """Manager for platform-specific presets and constraints"""
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        self.presets = self._load_presets()
        
        logger.info(f"Platform presets loaded: {list(self.presets.keys())}")
    
    def _load_presets(self) -> Dict[str, PlatformPreset]:
        """Load all platform presets"""
        return {
            "telegram": self._create_telegram_preset(),
            "instagram": self._create_instagram_preset(),
            "linkedin": self._create_linkedin_preset(),
            "twitter": self._create_twitter_preset(),
            "x": self._create_twitter_preset(),  # Alias for Twitter/X
            "facebook": self._create_facebook_preset(),
            "youtube": self._create_youtube_preset(),
            "tiktok": self._create_tiktok_preset(),
            "threads": self._create_threads_preset(),
            "mastodon": self._create_mastodon_preset(),
            "bluesky": self._create_bluesky_preset(),
            "general": self._create_general_preset()
        }
    
    def _create_telegram_preset(self) -> PlatformPreset:
        """Telegram platform preset"""
        return PlatformPreset(
            name="telegram",
            char_limit=4096,
            max_hashtags=5,
            max_title_length=100,
            emoji_density_limit=10.0,
            link_placement="anywhere",
            cta_style="direct",
            hashtag_style="inline",
            line_break_style="moderate",
            banned_content=["spam_links", "excessive_caps"],
            required_elements=[],
            optimal_posting_times=["09:00", "18:00", "21:00"],
            engagement_features=["polls", "inline_keyboards", "media_groups"]
        )
    
    def _create_instagram_preset(self) -> PlatformPreset:
        """Instagram platform preset"""
        return PlatformPreset(
            name="instagram",
            char_limit=2200,
            max_hashtags=30,
            max_title_length=125,
            emoji_density_limit=15.0,
            link_placement="bio_only",
            cta_style="engaging",
            hashtag_style="comment",
            line_break_style="liberal",
            banned_content=["external_links", "promotional_language"],
            required_elements=["visual_content"],
            optimal_posting_times=["11:00", "13:00", "17:00"],
            engagement_features=["stories", "reels", "igtv", "polls", "questions"]
        )
    
    def _create_linkedin_preset(self) -> PlatformPreset:
        """LinkedIn platform preset"""
        return PlatformPreset(
            name="linkedin",
            char_limit=3000,
            max_hashtags=5,
            max_title_length=150,
            emoji_density_limit=5.0,
            link_placement="end",
            cta_style="professional",
            hashtag_style="grouped",
            line_break_style="minimal",
            banned_content=["casual_language", "personal_opinions"],
            required_elements=["professional_tone"],
            optimal_posting_times=["08:00", "12:00", "17:00"],
            engagement_features=["articles", "polls", "events", "newsletters"]
        )
    
    def _create_twitter_preset(self) -> PlatformPreset:
        """Twitter/X platform preset"""
        return PlatformPreset(
            name="twitter",
            char_limit=280,
            max_hashtags=3,
            max_title_length=280,  # Same as char limit
            emoji_density_limit=8.0,
            link_placement="end",
            cta_style="concise",
            hashtag_style="inline",
            line_break_style="minimal",
            banned_content=["hate_speech", "misinformation"],
            required_elements=[],
            optimal_posting_times=["09:00", "15:00", "19:00"],
            engagement_features=["threads", "polls", "spaces", "communities"]
        )
    
    def _create_facebook_preset(self) -> PlatformPreset:
        """Facebook platform preset"""
        return PlatformPreset(
            name="facebook",
            char_limit=63206,
            max_hashtags=10,
            max_title_length=255,
            emoji_density_limit=12.0,
            link_placement="anywhere",
            cta_style="friendly",
            hashtag_style="grouped",
            line_break_style="moderate",
            banned_content=["clickbait", "misleading_content"],
            required_elements=[],
            optimal_posting_times=["09:00", "15:00", "20:00"],
            engagement_features=["events", "groups", "pages", "marketplace"]
        )
    
    def _create_youtube_preset(self) -> PlatformPreset:
        """YouTube platform preset"""
        return PlatformPreset(
            name="youtube",
            char_limit=5000,
            max_hashtags=15,
            max_title_length=100,
            emoji_density_limit=8.0,
            link_placement="description",
            cta_style="subscribe_focused",
            hashtag_style="grouped",
            line_break_style="moderate",
            banned_content=["copyright_content", "inappropriate_content"],
            required_elements=["video_content"],
            optimal_posting_times=["14:00", "17:00", "20:00"],
            engagement_features=["thumbnails", "end_screens", "cards", "chapters"]
        )
    
    def _create_tiktok_preset(self) -> PlatformPreset:
        """TikTok platform preset"""
        return PlatformPreset(
            name="tiktok",
            char_limit=2200,
            max_hashtags=20,
            max_title_length=100,
            emoji_density_limit=20.0,
            link_placement="bio_only",
            cta_style="trendy",
            hashtag_style="inline",
            line_break_style="minimal",
            banned_content=["inappropriate_content", "copyrighted_music"],
            required_elements=["video_content", "trending_sounds"],
            optimal_posting_times=["09:00", "16:00", "19:00"],
            engagement_features=["duets", "stitches", "effects", "sounds"]
        )
    
    def _create_threads_preset(self) -> PlatformPreset:
        """Threads platform preset"""
        return PlatformPreset(
            name="threads",
            char_limit=500,
            max_hashtags=5,
            max_title_length=500,
            emoji_density_limit=10.0,
            link_placement="anywhere",
            cta_style="conversational",
            hashtag_style="inline",
            line_break_style="moderate",
            banned_content=["spam", "harassment"],
            required_elements=[],
            optimal_posting_times=["10:00", "14:00", "18:00"],
            engagement_features=["replies", "reposts", "quotes"]
        )
    
    def _create_mastodon_preset(self) -> PlatformPreset:
        """Mastodon platform preset"""
        return PlatformPreset(
            name="mastodon",
            char_limit=500,
            max_hashtags=10,
            max_title_length=500,
            emoji_density_limit=15.0,
            link_placement="anywhere",
            cta_style="community_focused",
            hashtag_style="inline",
            line_break_style="liberal",
            banned_content=["commercial_spam"],
            required_elements=["content_warnings_when_needed"],
            optimal_posting_times=["11:00", "16:00", "21:00"],
            engagement_features=["content_warnings", "polls", "boosts"]
        )
    
    def _create_bluesky_preset(self) -> PlatformPreset:
        """Bluesky platform preset"""
        return PlatformPreset(
            name="bluesky",
            char_limit=300,
            max_hashtags=5,
            max_title_length=300,
            emoji_density_limit=8.0,
            link_placement="anywhere",
            cta_style="authentic",
            hashtag_style="inline",
            line_break_style="minimal",
            banned_content=["hate_speech", "spam"],
            required_elements=[],
            optimal_posting_times=["09:00", "15:00", "19:00"],
            engagement_features=["custom_feeds", "lists", "moderation"]
        )
    
    def _create_general_preset(self) -> PlatformPreset:
        """General/universal platform preset"""
        return PlatformPreset(
            name="general",
            char_limit=2000,
            max_hashtags=10,
            max_title_length=100,
            emoji_density_limit=10.0,
            link_placement="end",
            cta_style="engaging",
            hashtag_style="grouped",
            line_break_style="moderate",
            banned_content=["spam", "inappropriate_content"],
            required_elements=[],
            optimal_posting_times=["09:00", "15:00", "18:00"],
            engagement_features=["engagement", "shares", "comments"]
        )
    
    def get_platform_preset(self, platform: Optional[str]) -> Dict[str, Any]:
        """Get platform preset by name"""
        if not platform:
            platform = "general"
        
        preset = self.presets.get(platform.lower())
        if not preset:
            logger.warning(f"Unknown platform '{platform}', using general preset")
            preset = self.presets["general"]
        
        return {
            "name": preset.name,
            "char_limit": preset.char_limit,
            "max_hashtags": preset.max_hashtags,
            "max_title_length": preset.max_title_length,
            "emoji_density_limit": preset.emoji_density_limit,
            "link_placement": preset.link_placement,
            "cta_style": preset.cta_style,
            "hashtag_style": preset.hashtag_style,
            "line_break_style": preset.line_break_style,
            "banned_content": preset.banned_content,
            "required_elements": preset.required_elements,
            "optimal_posting_times": preset.optimal_posting_times,
            "engagement_features": preset.engagement_features
        }
    
    def validate_content_for_platform(self, content: str, platform: str) -> Dict[str, Any]:
        """Validate content against platform constraints"""
        preset = self.get_platform_preset(platform)
        issues = []
        warnings = []
        
        # Character limit check
        if len(content) > preset["char_limit"]:
            issues.append(f"Content exceeds {platform} character limit ({len(content)}/{preset['char_limit']})")
        
        # Emoji density check
        emoji_count = sum(1 for char in content if ord(char) > 127)  # Simple emoji detection
        emoji_density = (emoji_count / len(content)) * 100 if content else 0
        if emoji_density > preset["emoji_density_limit"]:
            warnings.append(f"High emoji density ({emoji_density:.1f}%, limit: {preset['emoji_density_limit']}%)")
        
        # Hashtag count check
        hashtag_count = content.count('#')
        if hashtag_count > preset["max_hashtags"]:
            issues.append(f"Too many hashtags ({hashtag_count}/{preset['max_hashtags']})")
        
        # Banned content check
        content_lower = content.lower()
        for banned in preset["banned_content"]:
            if banned.replace("_", " ") in content_lower:
                issues.append(f"Contains banned content type: {banned}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "stats": {
                "character_count": len(content),
                "character_limit": preset["char_limit"],
                "hashtag_count": hashtag_count,
                "hashtag_limit": preset["max_hashtags"],
                "emoji_density": emoji_density,
                "emoji_limit": preset["emoji_density_limit"]
            }
        }
    
    def get_cta_examples(self, platform: str) -> List[str]:
        """Get CTA examples for platform"""
        preset = self.get_platform_preset(platform)
        cta_style = preset["cta_style"]
        
        cta_examples = {
            "direct": [
                "Learn more →",
                "Get started today",
                "Download now",
                "Sign up here",
                "Visit our website"
            ],
            "question": [
                "What do you think?",
                "Have you tried this?",
                "Which option do you prefer?",
                "What's your experience?",
                "How would you handle this?"
            ],
            "soft": [
                "You might enjoy this",
                "Worth checking out",
                "Thought you'd find this interesting",
                "Consider giving this a try",
                "Hope this helps"
            ],
            "engaging": [
                "Let's discuss! 💬",
                "Share your thoughts below",
                "Tag someone who needs this",
                "Double tap if you agree",
                "Save this for later"
            ],
            "professional": [
                "I'd value your perspective",
                "Looking forward to your insights",
                "Please share your experience",
                "Connect with me to discuss",
                "What are your thoughts on this?"
            ],
            "concise": [
                "Thoughts?",
                "Agree?",
                "Try it",
                "Share",
                "Discuss"
            ],
            "friendly": [
                "Let me know what you think! 😊",
                "Would love to hear from you",
                "Hope this brightens your day",
                "Share with friends who'd enjoy this",
                "Thanks for reading!"
            ],
            "subscribe_focused": [
                "Subscribe for more content like this",
                "Hit the bell for notifications",
                "Like and subscribe if helpful",
                "More videos coming soon",
                "Support the channel"
            ],
            "trendy": [
                "Check the comments for more",
                "Follow for daily content",
                "Drop a 🔥 if you vibe with this",
                "Tag your bestie",
                "Which trend is next?"
            ],
            "conversational": [
                "What's your take?",
                "Anyone else relate?",
                "Let's chat about this",
                "Your thoughts?",
                "How do you see it?"
            ],
            "community_focused": [
                "What does the community think?",
                "Let's build on this together",
                "Appreciate your perspective",
                "Community input welcome",
                "Together we can discuss this"
            ],
            "authentic": [
                "Being real here",
                "Just my honest thoughts",
                "What's your authentic take?",
                "Genuinely curious",
                "Speaking from experience"
            ]
        }
        
        return cta_examples.get(cta_style, cta_examples["engaging"])
    
    def get_optimal_posting_time(self, platform: str, timezone: str = "UTC") -> str:
        """Get optimal posting time for platform"""
        preset = self.get_platform_preset(platform)
        times = preset["optimal_posting_times"]
        
        # For now, return the first optimal time
        # In a full implementation, this would consider timezone conversion
        return times[0] if times else "12:00"
    
    def get_platform_features(self, platform: str) -> List[str]:
        """Get available engagement features for platform"""
        preset = self.get_platform_preset(platform)
        return preset["engagement_features"]
    
    def list_platforms(self) -> List[Dict[str, Any]]:
        """List all available platforms with basic info"""
        platforms = []
        for name, preset in self.presets.items():
            platforms.append({
                "name": name,
                "char_limit": preset.char_limit,
                "max_hashtags": preset.max_hashtags,
                "cta_style": preset.cta_style,
                "features": preset.engagement_features[:3]  # Top 3 features
            })
        
        return platforms
    
    def get_cross_platform_optimized_content(self, content: str, target_platforms: List[str]) -> Dict[str, str]:
        """Optimize content for multiple platforms"""
        optimized = {}
        
        for platform in target_platforms:
            preset = self.get_platform_preset(platform)
            platform_content = content
            
            # Truncate if needed
            if len(platform_content) > preset["char_limit"]:
                platform_content = platform_content[:preset["char_limit"]-3] + "..."
            
            # Adjust hashtag style if needed
            if preset["hashtag_style"] == "comment" and "#" in platform_content:
                # Move hashtags to separate comment section
                lines = platform_content.split('\n')
                content_lines = [line for line in lines if not line.strip().startswith('#')]
                hashtag_lines = [line for line in lines if line.strip().startswith('#')]
                
                platform_content = '\n'.join(content_lines)
                if hashtag_lines:
                    platform_content += "\n\n[Comment with hashtags]:\n" + '\n'.join(hashtag_lines)
            
            optimized[platform] = platform_content
        
        return optimized
