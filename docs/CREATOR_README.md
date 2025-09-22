# Creator v1 - Omnimedia Content Generator

Brand-aware omnimedia generator supporting text, images, video, audio/voice, music, code/sites, and 3D/AR assets with agent orchestration and platform guardrails.

## 🚀 Features

### Content Generation
- **Text**: Social media posts, content packs, rewrites, summaries, hashtags, titles
- **Images**: AI-generated images, editing, infographics, variations
- **Video**: Short video generation (≤60s), editing, anonymization, multi-format
- **Audio**: Text-to-speech, music generation, transcription, subtitles
- **Code**: Websites, apps, components with multiple framework support
- **SEO**: Content briefs, metadata generation, structured data

### Platform Integration
- **Multi-platform optimization**: Instagram, LinkedIn, Twitter/X, Telegram, YouTube, TikTok
- **Brand voice consistency**: Centralized brand guidelines and tone management
- **Template system**: Reusable content templates with variables
- **Export capabilities**: ZIP bundles, JSON exports, presigned URLs

### Data & Knowledge
- **RAG system**: Document ingestion with citation-based content generation
- **External connectors**: Notion, Google Drive, GitHub, Slack, Dropbox
- **Content validation**: PII detection, platform compliance, brand guidelines
- **A/B testing**: Generate multiple variants with engagement scoring

## 📋 Requirements

### Essential Providers
- **OpenRouter API key**: Primary text generation
- **R2/S3 Storage**: Asset storage and exports

### Optional Providers
- **Stability AI**: High-quality image generation
- **ElevenLabs**: Premium text-to-speech
- **Replicate**: Cost-effective multi-modal AI
- **OpenAI**: DALL-E, Whisper, GPT models
- **Deepgram**: Advanced speech recognition

## 🛠 Installation

### 1. Environment Setup

Copy the example configuration:
```bash
cp .env.example.crt4 .env
```

### 2. Essential Configuration

Minimum required variables:
```bash
# Text generation
OPENROUTER_API_KEY=your_openrouter_api_key

# Storage
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET=umbra
R2_ENDPOINT=https://your_account.r2.cloudflarestorage.com
```

### 3. Provider Configuration

Add providers based on your needs:

**For Images:**
```bash
CREATOR_IMAGE_PROVIDER=stability
CREATOR_STABILITY_API_KEY=your_stability_key
```

**For Audio:**
```bash
CREATOR_TTS_PROVIDER=elevenlabs
CREATOR_ELEVENLABS_API_KEY=your_elevenlabs_key
```

**For Video:**
```bash
CREATOR_VIDEO_PROVIDER=replicate
CREATOR_REPLICATE_API_TOKEN=your_replicate_token
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 🎯 Quick Start

### Basic Text Generation

```python
from umbra.modules.creator_mcp import CreatorModule
from umbra.ai.agent import UmbraAIAgent
from umbra.core.config import UmbraConfig

# Initialize
config = UmbraConfig()
ai_agent = UmbraAIAgent(config)
creator = CreatorModule(ai_agent, config)

# Generate a social media post
result = await creator.execute("generate_post", {
    "topic": "AI innovation in 2025",
    "platform": "linkedin",
    "tone": "professional"
})

print(result["post"]["content"])
```

### Content Pack Generation

```python
# Generate complete content pack
result = await creator.execute("content_pack", {
    "topic": "sustainable technology",
    "platform": "instagram", 
    "tone": "engaging"
})

print(f"Caption: {result['pack']['caption']}")
print(f"Hashtags: {result['pack']['hashtags']}")
print(f"Titles: {result['pack']['titles']}")
```

### Image Generation

```python
# Generate image
result = await creator.execute("generate_image", {
    "prompt": "futuristic cityscape with green technology",
    "size": "1024x1024",
    "style": "photorealistic"
})

print(f"Image URL: {result['image_url']}")
```

### Template Usage

```python
# Render template
result = await creator.execute("render_template", {
    "template_id": "social_announcement",
    "variables": {
        "announcement": "New product launch",
        "details": "Revolutionary AI-powered features",
        "call_to_action": "Learn more at our website",
        "hashtags": "#AI #Innovation #TechNews"
    }
})

print(result["rendered_text"])
```

## 📚 API Reference

### Core Actions

#### Text Generation
- `generate_post(topic, platform?, tone?, audience?, length?)` - Generate social media post
- `content_pack(topic, platform?, tone?, audience?)` - Generate complete content pack
- `rewrite(text, tone?, length?)` - Rewrite text with style adjustments
- `summarize(text, target_length?)` - Summarize content
- `hashtags(topic, platform?, count=10)` - Generate hashtags
- `title_variations(topic, count=3, platform?)` - Generate title options

#### Media Generation
- `generate_image(prompt, refs?, size?, style?, negative?, seed?)` - Generate images
- `edit_image(media_id, instructions, mask?, size?, style?)` - Edit existing images
- `generate_video(brief, format?, duration_s?, storyboard?, voice_id?, music_id?, subtitles?)` - Generate short videos
- `tts_speak(text, voice_id?, style?, speed?)` - Text-to-speech
- `music_generate(brief, duration_s?, genre?, bpm?, structure?, refs?)` - Generate music

#### Code Generation
- `generate_site(brief, stack?, features?)` - Generate websites/apps
- `generate_code(spec, prog_language, tests?)` - Generate code components

#### Data & Knowledge
- `rag_ingest(docs, tags?)` - Ingest documents for RAG
- `rag_generate(brief, cite?)` - Generate with citations
- `seo_brief(url_or_topic)` - Generate SEO content brief
- `seo_metadata(page_spec)` - Generate SEO metadata

#### Templates
- `list_templates()` - List available templates
- `render_template(template_id, variables)` - Render template
- `upsert_template(template_id?, body, meta)` - Create/update template

#### Brand Voice
- `set_brand_voice(meta_json)` - Set brand voice guidelines
- `get_brand_voice()` - Get current brand voice

#### Utilities
- `validate(text|asset, platform)` - Validate content
- `export_bundle(assets, format?)` - Export content bundle
- `connectors_list()` - List available connectors
- `batch_generate(task_spec, variations)` - Batch generation
- `ab_generate_variants(brief, k=3)` - A/B test variants

### Platform Support

Supported platforms with specific optimizations:
- **Instagram**: 2200 chars, 30 hashtags, visual focus
- **LinkedIn**: 3000 chars, 5 hashtags, professional tone
- **Twitter/X**: 280 chars, 3 hashtags, concise format
- **Telegram**: 4096 chars, inline formatting
- **YouTube**: 5000 chars, video descriptions
- **TikTok**: 2200 chars, trending hashtags
- **Facebook**: 63K chars, engagement focus

### Brand Voice Configuration

```json
{
  "brand_name": "TechCorp",
  "bio": "Leading AI innovation company",
  "audience": "Tech professionals and enthusiasts",
  "tone_default": "professional",
  "do": ["be authentic", "provide value", "engage audience"],
  "dont": ["use jargon", "be overly promotional"],
  "cta_style": "engaging",
  "emoji_policy": "moderate",
  "reading_level": "intermediate"
}
```

## 🔧 Advanced Configuration

### Provider Selection

Set preferred providers for each capability:

```bash
# Image generation priority
CREATOR_IMAGE_PROVIDER=stability  # Primary
CREATOR_REPLICATE_API_TOKEN=...   # Fallback

# Audio generation
CREATOR_TTS_PROVIDER=elevenlabs   # Premium quality
CREATOR_OPENAI_API_KEY=...        # Fallback

# Video generation  
CREATOR_VIDEO_PROVIDER=runway     # High quality
CREATOR_REPLICATE_API_TOKEN=...   # Cost effective
```

### Content Limits

```bash
CREATOR_MAX_OUTPUT_TOKENS=2000
CREATOR_MAX_VIDEO_DURATION=60
CREATOR_MAX_TTS_LENGTH=4000
CREATOR_MAX_BUNDLE_SIZE_MB=100
```

### Security Settings

```bash
CREATOR_PII_DEFAULT=true
CREATOR_CONTENT_FILTER_ENABLED=true
CREATOR_VOICE_CONSENT_REQUIRED=true
```

## 🧩 External Connectors

### Notion Integration

```bash
CREATOR_NOTION_TOKEN=secret_xyz...

# Usage
result = await creator.execute("connector_link", {
    "source": "notion",
    "auth": {"token": "secret_xyz..."}
})

assets = await creator.execute("fetch_assets", {
    "connector_id": result["connector_id"],
    "query": "meeting notes"
})
```

### Google Drive Integration

```bash
CREATOR_GOOGLE_DRIVE_CREDENTIALS='{"type":"service_account",...}'

# Usage  
result = await creator.execute("fetch_assets", {
    "connector_id": "drive_123",
    "query": "quarterly reports"
})
```

### Supported Connectors
- **Notion**: Pages, databases, content extraction
- **Google Drive**: Files, folders, document content  
- **GitHub**: Repositories, files, code analysis
- **Slack**: Messages, files, workspace content
- **Dropbox**: Files, folders, content access
- **S3/R2**: Object storage, file management

## 📊 Template System

### Built-in Templates

- `social_announcement` - General announcements
- `social_launch` - Product/feature launches  
- `blog_howto` - Step-by-step guides
- `email_newsletter` - Newsletter format
- `marketing_promo` - Promotional campaigns
- `event_invitation` - Event invitations
- `thank_you` - Thank you messages
- `event_recap` - Event summaries

### Custom Templates

Create custom templates with variables:

```python
await creator.execute("upsert_template", {
    "template_id": "my_template",
    "body": "Hello ${name}! Welcome to ${company}. ${message}",
    "meta": {
        "name": "Custom Welcome",
        "category": "email",
        "description": "Welcome email template"
    }
})
```

## 🎨 Infographics & Data Visualization

Generate infographics from data:

```python
result = await creator.execute("infographic", {
    "data_spec": {
        "type": "chart",
        "data": [
            {"category": "Q1", "value": 100},
            {"category": "Q2", "value": 150},
            {"category": "Q3", "value": 120}
        ],
        "title": "Quarterly Growth"
    },
    "layout_hint": "vertical"
})
```

### Supported Chart Types
- Bar, Column, Pie, Donut
- Line, Area, Scatter, Bubble  
- Timeline, Funnel, Gauge
- Treemap, Network diagrams

## 🔍 SEO Optimization

### Content Briefs

```python
brief = await creator.execute("seo_brief", {
    "url_or_topic": "AI automation tools"
})

print(f"Primary keyword: {brief['keywords']['primary']}")
print(f"Structure: {brief['structure']}")
print(f"Questions: {brief['questions']}")
```

### Metadata Generation

```python
metadata = await creator.execute("seo_metadata", {
    "page_spec": {
        "title": "AI Tools Guide",
        "description": "Complete guide to AI automation tools",
        "type": "article",
        "url": "https://example.com/ai-tools"
    }
})

print(metadata["json_ld"])  # Structured data
print(metadata["og_card"])  # Open Graph tags
```

## 🔄 A/B Testing & Variants

Generate multiple content variants:

```python
variants = await creator.execute("ab_generate_variants", {
    "brief": "Promote our new AI feature",
    "k": 5
})

for variant in variants["variants"]:
    print(f"Score: {variant['scores']['combined']}")
    print(f"Content: {variant['content']}")
```

## 📦 Export & Distribution

Export content in multiple formats:

```python
bundle = await creator.execute("export_bundle", {
    "assets": [
        {"type": "text", "content": "Social media post"},
        {"type": "image", "url": "https://..."},
        {"type": "video", "url": "https://..."}
    ],
    "format": "zip"
})

print(f"Download: {bundle['download_url']}")
```

### Export Formats
- **ZIP**: Complete bundle with metadata
- **JSON**: Structured data export
- **Markdown**: Documentation format

## 🚨 Error Handling

```python
try:
    result = await creator.execute("generate_post", params)
    if "error" in result:
        print(f"Error: {result['error']}")
        print(f"Type: {result['error_type']}")
    else:
        print(f"Success: {result}")
except Exception as e:
    print(f"Exception: {e}")
```

### Common Error Types
- `creator_error` - Module-specific errors
- `validation_error` - Content validation failed
- `provider_error` - External API issues
- `consent_error` - Voice consent required
- `token_limit_error` - Content too long

## 🔧 Troubleshooting

### Provider Issues

Check provider status:
```python
from umbra.modules.creator.model_provider_enhanced import EnhancedModelProviderManager

manager = EnhancedModelProviderManager(config)
status = manager.get_configuration_status()
print(status["capability_coverage"])
```

### Missing Configuration

The system will provide helpful error messages:
```
Error: Stability AI API key not configured
Hint: Set CREATOR_STABILITY_API_KEY in your environment
```

### Rate Limits

Monitor usage and implement backoff:
```python
if "rate_limit" in result.get("error", ""):
    await asyncio.sleep(60)  # Wait before retry
```

## 📈 Performance & Monitoring

### Cost Estimation

```python
estimate = await creator.execute("estimate", {
    "brief": "Generate social media campaign",
    "platform": "instagram"
})

print(f"Estimated cost: ${estimate['cost_estimate_usd']}")
print(f"Processing time: {estimate['time_estimate_seconds']}s")
```

### Analytics

Track usage and performance:
- Request counts by action type
- Provider response times
- Cost breakdown by provider
- Error rates and types

## 🤝 Contributing

1. Follow the provider interface standards in `providers.py`
2. Add comprehensive error handling
3. Include unit tests for new features
4. Update documentation and examples
5. Test with multiple providers

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Support

- GitHub Issues: Report bugs and feature requests
- Documentation: Comprehensive API reference
- Examples: Sample implementations and use cases

---

**Creator v1** - Transforming content creation with AI-powered omnimedia generation! 🚀✨
