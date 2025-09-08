"""
Creator MCP v1 - Omnimedia Content Generator

Brand-aware omnimedia generator supporting text, images, video, audio/voice, music, 
code/sites, and 3D/AR assets with agent orchestration and platform guardrails.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict

from ..ai.agent import UmbraAIAgent
from ..core.config import UmbraConfig
from ..storage.r2_client import R2Client
from .creator.service import CreatorService
from .creator.media_image import ImageGenerator
from .creator.media_video import VideoGenerator
from .creator.media_audio import AudioGenerator
from .creator.codegen import CodeGenerator
from .creator.infographic import InfographicGenerator
from .creator.rag import RAGManager
from .creator.seo import SEOManager
from .creator.connectors import ConnectorManager
from .creator.templates import TemplateManager
from .creator.voice import BrandVoiceManager
from .creator.presets import PlatformPresets
from .creator.export import ExportManager
from .creator.validate import ContentValidator
from .creator.model_provider_enhanced import EnhancedModelProviderManager
from .creator.errors import CreatorError, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class CreatorCapabilities:
    """Creator module capabilities"""
    name: str = "creator"
    description: str = "Omnimedia content generator with brand awareness"
    version: str = "1.0.0"
    
    actions: List[str] = None
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = [
                # Orchestration & Validation
                "auto",
                "ingest_media", 
                "estimate",
                "validate",
                
                # Text Generation
                "generate_post",
                "content_pack",
                "rewrite",
                "summarize",
                "hashtags",
                "title_variations",
                "render_template",
                "list_templates",
                "upsert_template",
                
                # Image Generation
                "generate_image",
                "edit_image",
                "infographic",
                
                # Audio/Video/Music
                "asr_transcribe",
                "subtitle",
                "video_anonymize",
                "generate_video",
                "tts_register_voice",
                "tts_speak",
                "music_generate",
                
                # Code/Sites & Connectors
                "generate_site",
                "generate_code",
                "connectors_list",
                "connector_link",
                "fetch_assets",
                
                # Knowledge, SEO, Variants
                "rag_ingest",
                "rag_generate",
                "seo_brief",
                "seo_metadata",
                "batch_generate",
                "ab_generate_variants",
                "export_bundle",
                
                # Brand Voice
                "set_brand_voice",
                "get_brand_voice"
            ]

class CreatorModule:
    """Creator MCP Module for omnimedia content generation"""
    
    def __init__(self, ai_agent: UmbraAIAgent, config: UmbraConfig, r2_client: Optional[R2Client] = None):
        self.ai_agent = ai_agent
        self.config = config
        self.r2_client = r2_client
        
        # Initialize core components
        self.service = CreatorService(ai_agent, config)
        self.image_gen = ImageGenerator(ai_agent, config)
        self.video_gen = VideoGenerator(ai_agent, config)
        self.audio_gen = AudioGenerator(ai_agent, config)
        self.code_gen = CodeGenerator(ai_agent, config)
        self.infographic_gen = InfographicGenerator(ai_agent, config)
        self.rag_manager = RAGManager(ai_agent, config, r2_client)
        self.seo_manager = SEOManager(ai_agent, config)
        self.connector_manager = ConnectorManager(config)
        self.template_manager = TemplateManager(config)
        self.brand_voice = BrandVoiceManager(config)
        self.presets = PlatformPresets(config)
        self.export_manager = ExportManager(config, r2_client)
        self.validator = ContentValidator(config)
        self.provider_manager = EnhancedModelProviderManager(config)
        
        logger.info("Creator module v1 initialized")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return module capabilities"""
        capabilities = CreatorCapabilities()
        return asdict(capabilities)
    
    async def execute(self, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a creator action"""
        if params is None:
            params = {}
        
        try:
            # Route to appropriate handler
            if action == "auto":
                return await self._auto_orchestrate(params)
            elif action == "ingest_media":
                return await self._ingest_media(params)
            elif action == "estimate":
                return await self._estimate(params)
            elif action == "validate":
                return await self._validate(params)
                
            # Text actions
            elif action == "generate_post":
                return await self._generate_post(params)
            elif action == "content_pack":
                return await self._content_pack(params)
            elif action == "rewrite":
                return await self._rewrite(params)
            elif action == "summarize":
                return await self._summarize(params)
            elif action == "hashtags":
                return await self._hashtags(params)
            elif action == "title_variations":
                return await self._title_variations(params)
            elif action == "render_template":
                return await self._render_template(params)
            elif action == "list_templates":
                return await self._list_templates(params)
            elif action == "upsert_template":
                return await self._upsert_template(params)
                
            # Image actions
            elif action == "generate_image":
                return await self._generate_image(params)
            elif action == "edit_image":
                return await self._edit_image(params)
            elif action == "infographic":
                return await self._infographic(params)
                
            # Audio/Video/Music actions
            elif action == "asr_transcribe":
                return await self._asr_transcribe(params)
            elif action == "subtitle":
                return await self._subtitle(params)
            elif action == "video_anonymize":
                return await self._video_anonymize(params)
            elif action == "generate_video":
                return await self._generate_video(params)
            elif action == "tts_register_voice":
                return await self._tts_register_voice(params)
            elif action == "tts_speak":
                return await self._tts_speak(params)
            elif action == "music_generate":
                return await self._music_generate(params)
                
            # Code/Sites & Connectors
            elif action == "generate_site":
                return await self._generate_site(params)
            elif action == "generate_code":
                return await self._generate_code(params)
            elif action == "connectors_list":
                return await self._connectors_list(params)
            elif action == "connector_link":
                return await self._connector_link(params)
            elif action == "fetch_assets":
                return await self._fetch_assets(params)
                
            # Knowledge, SEO, Variants
            elif action == "rag_ingest":
                return await self._rag_ingest(params)
            elif action == "rag_generate":
                return await self._rag_generate(params)
            elif action == "seo_brief":
                return await self._seo_brief(params)
            elif action == "seo_metadata":
                return await self._seo_metadata(params)
            elif action == "batch_generate":
                return await self._batch_generate(params)
            elif action == "ab_generate_variants":
                return await self._ab_generate_variants(params)
            elif action == "export_bundle":
                return await self._export_bundle(params)
                
            # Brand Voice
            elif action == "set_brand_voice":
                return await self._set_brand_voice(params)
            elif action == "get_brand_voice":
                return await self._get_brand_voice(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except CreatorError as e:
            logger.error(f"Creator error in {action}: {e}")
            return {"error": str(e), "error_type": "creator_error"}
        except Exception as e:
            logger.error(f"Error executing {action}: {e}")
            return {"error": str(e), "error_type": "internal_error"}
    
    async def _auto_orchestrate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-orchestrate content creation from input"""
        input_data = params.get("input")
        goal = params.get("goal")
        platform = params.get("platform")
        tone = params.get("tone")
        
        if not input_data:
            return {"error": "input is required"}
        
        try:
            # Detect input type and route accordingly
            result = await self.service.auto_orchestrate(input_data, goal, platform, tone)
            return {"result": result, "status": "success"}
        except Exception as e:
            return {"error": f"Auto-orchestration failed: {e}"}
    
    async def _ingest_media(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest media file or URL"""
        file_data = params.get("file")
        url = params.get("url")
        
        if not file_data and not url:
            return {"error": "file or url is required"}
        
        try:
            result = await self.service.ingest_media(file_data, url)
            return result
        except Exception as e:
            return {"error": f"Media ingestion failed: {e}"}
    
    async def _estimate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate content requirements"""
        brief = params.get("brief")
        media = params.get("media")
        text = params.get("text")
        platform = params.get("platform")
        
        try:
            result = await self.service.estimate_requirements(brief, media, text, platform)
            return result
        except Exception as e:
            return {"error": f"Estimation failed: {e}"}
    
    async def _validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content against platform rules"""
        text = params.get("text")
        asset = params.get("asset")
        platform = params.get("platform")
        
        if not text and not asset:
            return {"error": "text or asset is required"}
        
        try:
            result = await self.validator.validate_content(text, asset, platform)
            return result
        except Exception as e:
            return {"error": f"Validation failed: {e}"}
    
    async def _generate_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate social media post"""
        topic = params.get("topic")
        platform = params.get("platform")
        tone = params.get("tone")
        audience = params.get("audience")
        length = params.get("length")
        
        if not topic:
            return {"error": "topic is required"}
        
        try:
            result = await self.service.generate_post(topic, platform, tone, audience, length)
            return {"post": result, "status": "success"}
        except Exception as e:
            return {"error": f"Post generation failed: {e}"}
    
    async def _content_pack(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete content pack"""
        topic = params.get("topic")
        platform = params.get("platform")
        tone = params.get("tone")
        audience = params.get("audience")
        
        if not topic:
            return {"error": "topic is required"}
        
        try:
            result = await self.service.generate_content_pack(topic, platform, tone, audience)
            return result
        except Exception as e:
            return {"error": f"Content pack generation failed: {e}"}
    
    async def _rewrite(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Rewrite text with tone/length adjustments"""
        text = params.get("text")
        tone = params.get("tone")
        length = params.get("length")
        
        if not text:
            return {"error": "text is required"}
        
        try:
            result = await self.service.rewrite_text(text, tone, length)
            return {"rewritten_text": result, "status": "success"}
        except Exception as e:
            return {"error": f"Rewrite failed: {e}"}
    
    async def _summarize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize text content"""
        text = params.get("text")
        target_length = params.get("target_length")
        
        if not text:
            return {"error": "text is required"}
        
        try:
            result = await self.service.summarize_text(text, target_length)
            return {"summary": result, "status": "success"}
        except Exception as e:
            return {"error": f"Summarization failed: {e}"}
    
    async def _hashtags(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hashtags for topic"""
        topic = params.get("topic")
        platform = params.get("platform")
        count = params.get("count", 10)
        
        if not topic:
            return {"error": "topic is required"}
        
        try:
            result = await self.service.generate_hashtags(topic, platform, count)
            return {"hashtags": result, "status": "success"}
        except Exception as e:
            return {"error": f"Hashtag generation failed: {e}"}
    
    async def _title_variations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate title variations"""
        topic = params.get("topic")
        count = params.get("count", 3)
        platform = params.get("platform")
        
        if not topic:
            return {"error": "topic is required"}
        
        try:
            result = await self.service.generate_title_variations(topic, count, platform)
            return {"titles": result, "status": "success"}
        except Exception as e:
            return {"error": f"Title generation failed: {e}"}
    
    async def _render_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Render template with variables"""
        template_id = params.get("template_id")
        variables = params.get("variables", {})
        
        if not template_id:
            return {"error": "template_id is required"}
        
        try:
            result = await self.template_manager.render_template(template_id, variables)
            return {"rendered_text": result, "status": "success"}
        except Exception as e:
            return {"error": f"Template rendering failed: {e}"}
    
    async def _list_templates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available templates"""
        try:
            result = await self.template_manager.list_templates()
            return {"templates": result, "status": "success"}
        except Exception as e:
            return {"error": f"Template listing failed: {e}"}
    
    async def _upsert_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update template"""
        template_id = params.get("template_id")
        body = params.get("body")
        meta = params.get("meta", {})
        
        if not body:
            return {"error": "body is required"}
        
        try:
            result = await self.template_manager.upsert_template(template_id, body, meta)
            return {"template_id": result, "status": "success"}
        except Exception as e:
            return {"error": f"Template upsert failed: {e}"}
    
    async def _generate_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate image from prompt"""
        prompt = params.get("prompt")
        refs = params.get("refs", [])
        size = params.get("size")
        style = params.get("style")
        negative = params.get("negative", [])
        seed = params.get("seed")
        
        if not prompt:
            return {"error": "prompt is required"}
        
        try:
            result = await self.image_gen.generate_image(prompt, refs, size, style, negative, seed)
            return result
        except Exception as e:
            return {"error": f"Image generation failed: {e}"}
    
    async def _edit_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Edit existing image"""
        media_id = params.get("media_id")
        instructions = params.get("instructions")
        mask = params.get("mask")
        size = params.get("size")
        style = params.get("style")
        
        if not media_id or not instructions:
            return {"error": "media_id and instructions are required"}
        
        try:
            result = await self.image_gen.edit_image(media_id, instructions, mask, size, style)
            return result
        except Exception as e:
            return {"error": f"Image editing failed: {e}"}
    
    async def _infographic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate infographic from data"""
        data_spec = params.get("data_spec")
        brand_prefs = params.get("brand_prefs")
        layout_hint = params.get("layout_hint")
        
        if not data_spec:
            return {"error": "data_spec is required"}
        
        try:
            result = await self.infographic_gen.generate_infographic(data_spec, brand_prefs, layout_hint)
            return result
        except Exception as e:
            return {"error": f"Infographic generation failed: {e}"}
    
    # Audio/Video methods
    async def _asr_transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio/video"""
        media_id = params.get("media_id")
        diarization = params.get("diarization", False)
        
        if not media_id:
            return {"error": "media_id is required"}
        
        try:
            result = await self.audio_gen.transcribe_media(media_id, diarization)
            return result
        except Exception as e:
            return {"error": f"Transcription failed: {e}"}
    
    async def _subtitle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate subtitles"""
        media_id = params.get("media_id")
        text = params.get("text")
        style = params.get("style")
        
        if not media_id and not text:
            return {"error": "media_id or text is required"}
        
        try:
            result = await self.audio_gen.generate_subtitles(media_id, text, style)
            return result
        except Exception as e:
            return {"error": f"Subtitle generation failed: {e}"}
    
    async def _video_anonymize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize faces/plates in video"""
        media_id = params.get("media_id")
        faces = params.get("faces", True)
        plates = params.get("plates", True)
        
        if not media_id:
            return {"error": "media_id is required"}
        
        try:
            result = await self.video_gen.anonymize_video(media_id, faces, plates)
            return result
        except Exception as e:
            return {"error": f"Video anonymization failed: {e}"}
    
    async def _generate_video(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate video content"""
        brief = params.get("brief")
        format_spec = params.get("format", "16:9")
        duration_s = params.get("duration_s", 30)
        storyboard = params.get("storyboard")
        voice_id = params.get("voice_id")
        music_id = params.get("music_id")
        subtitles = params.get("subtitles", "auto")
        
        if not brief:
            return {"error": "brief is required"}
        
        if duration_s > 60:
            return {"error": "duration_s must be <= 60 seconds"}
        
        try:
            result = await self.video_gen.generate_video(
                brief, format_spec, duration_s, storyboard, voice_id, music_id, subtitles
            )
            return result
        except Exception as e:
            return {"error": f"Video generation failed: {e}"}
    
    async def _tts_register_voice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Register custom voice for TTS"""
        sample_url = params.get("sample_url")
        consent_token = params.get("consent_token")
        
        if not sample_url or not consent_token:
            return {"error": "sample_url and consent_token are required"}
        
        try:
            result = await self.audio_gen.register_voice(sample_url, consent_token)
            return result
        except Exception as e:
            return {"error": f"Voice registration failed: {e}"}
    
    async def _tts_speak(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert text to speech"""
        text = params.get("text")
        voice_id = params.get("voice_id")
        style = params.get("style")
        speed = params.get("speed")
        
        if not text:
            return {"error": "text is required"}
        
        try:
            result = await self.audio_gen.text_to_speech(text, voice_id, style, speed)
            return result
        except Exception as e:
            return {"error": f"TTS generation failed: {e}"}
    
    async def _music_generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate music"""
        brief = params.get("brief")
        duration_s = params.get("duration_s", 30)
        genre = params.get("genre")
        bpm = params.get("bpm")
        structure = params.get("structure")
        refs = params.get("refs", [])
        
        if not brief:
            return {"error": "brief is required"}
        
        if duration_s > 60:
            return {"error": "duration_s must be <= 60 seconds"}
        
        try:
            result = await self.audio_gen.generate_music(brief, duration_s, genre, bpm, structure, refs)
            return result
        except Exception as e:
            return {"error": f"Music generation failed: {e}"}
    
    # Code/Sites & Connectors
    async def _generate_site(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate website/app"""
        brief = params.get("brief")
        stack = params.get("stack", "nextjs")
        features = params.get("features", [])
        
        if not brief:
            return {"error": "brief is required"}
        
        try:
            result = await self.code_gen.generate_site(brief, stack, features)
            return result
        except Exception as e:
            return {"error": f"Site generation failed: {e}"}
    
    async def _generate_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code components"""
        spec = params.get("spec")
        prog_language = params.get("prog_language")
        tests = params.get("tests", False)
        
        if not spec or not prog_language:
            return {"error": "spec and prog_language are required"}
        
        try:
            result = await self.code_gen.generate_code(spec, prog_language, tests)
            return result
        except Exception as e:
            return {"error": f"Code generation failed: {e}"}
    
    async def _connectors_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available connectors"""
        try:
            result = await self.connector_manager.list_connectors()
            return {"sources": result, "status": "success"}
        except Exception as e:
            return {"error": f"Connector listing failed: {e}"}
    
    async def _connector_link(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Link external data source"""
        source = params.get("source")
        auth = params.get("auth")
        
        if not source or not auth:
            return {"error": "source and auth are required"}
        
        try:
            result = await self.connector_manager.link_connector(source, auth)
            return {"connector_id": result, "status": "success"}
        except Exception as e:
            return {"error": f"Connector linking failed: {e}"}
    
    async def _fetch_assets(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch assets from connected source"""
        connector_id = params.get("connector_id")
        query = params.get("query")
        
        if not connector_id:
            return {"error": "connector_id is required"}
        
        try:
            result = await self.connector_manager.fetch_assets(connector_id, query)
            return {"assets": result, "status": "success"}
        except Exception as e:
            return {"error": f"Asset fetching failed: {e}"}
    
    # Knowledge, SEO, Variants
    async def _rag_ingest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest documents for RAG"""
        docs = params.get("docs", [])
        tags = params.get("tags", [])
        
        if not docs:
            return {"error": "docs are required"}
        
        try:
            result = await self.rag_manager.ingest_documents(docs, tags)
            return {"kb_id": result, "status": "success"}
        except Exception as e:
            return {"error": f"RAG ingestion failed: {e}"}
    
    async def _rag_generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content with RAG citations"""
        brief = params.get("brief")
        cite = params.get("cite", False)
        
        if not brief:
            return {"error": "brief is required"}
        
        try:
            result = await self.rag_manager.generate_with_citations(brief, cite)
            return result
        except Exception as e:
            return {"error": f"RAG generation failed: {e}"}
    
    async def _seo_brief(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SEO brief"""
        url_or_topic = params.get("url_or_topic")
        
        if not url_or_topic:
            return {"error": "url_or_topic is required"}
        
        try:
            result = await self.seo_manager.generate_brief(url_or_topic)
            return result
        except Exception as e:
            return {"error": f"SEO brief generation failed: {e}"}
    
    async def _seo_metadata(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SEO metadata"""
        page_spec = params.get("page_spec")
        
        if not page_spec:
            return {"error": "page_spec is required"}
        
        try:
            result = await self.seo_manager.generate_metadata(page_spec)
            return result
        except Exception as e:
            return {"error": f"SEO metadata generation failed: {e}"}
    
    async def _batch_generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content in batches"""
        task_spec = params.get("task_spec")
        variations = params.get("variations", 1)
        
        if not task_spec:
            return {"error": "task_spec is required"}
        
        try:
            result = await self.service.batch_generate(task_spec, variations)
            return {"variants": result, "status": "success"}
        except Exception as e:
            return {"error": f"Batch generation failed: {e}"}
    
    async def _ab_generate_variants(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate A/B test variants"""
        brief = params.get("brief")
        k = params.get("k", 3)
        
        if not brief:
            return {"error": "brief is required"}
        
        try:
            result = await self.service.generate_ab_variants(brief, k)
            return result
        except Exception as e:
            return {"error": f"A/B variant generation failed: {e}"}
    
    async def _export_bundle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export content bundle"""
        assets = params.get("assets", [])
        format_type = params.get("format", "zip")
        
        if not assets:
            return {"error": "assets are required"}
        
        try:
            result = await self.export_manager.create_bundle(assets, format_type)
            return {"download_url": result, "status": "success"}
        except Exception as e:
            return {"error": f"Bundle export failed: {e}"}
    
    # Brand Voice
    async def _set_brand_voice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set brand voice metadata"""
        meta_json = params.get("meta_json")
        
        if not meta_json:
            return {"error": "meta_json is required"}
        
        try:
            result = await self.brand_voice.set_brand_voice(meta_json)
            return {"status": "success" if result else "failed"}
        except Exception as e:
            return {"error": f"Brand voice setting failed: {e}"}
    
    async def _get_brand_voice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get brand voice metadata"""
        try:
            result = await self.brand_voice.get_brand_voice()
            return result or {}
        except Exception as e:
            return {"error": f"Brand voice retrieval failed: {e}"}

# Module registration
async def get_capabilities() -> Dict[str, Any]:
    """Get creator module capabilities"""
    capabilities = CreatorCapabilities()
    return asdict(capabilities)

async def execute(action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute creator action with context"""
    ai_agent = context.get("ai_agent")
    config = context.get("config")
    r2_client = context.get("r2_client")
    
    if not ai_agent or not config:
        return {"error": "Missing required context (ai_agent, config)"}
    
    module = CreatorModule(ai_agent, config, r2_client)
    return await module.execute(action, params)
