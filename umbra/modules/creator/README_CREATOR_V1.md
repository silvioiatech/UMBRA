# 🎨 Creator v1 - Omnimedia Content Generator

**PR CRT3 Complete** | **Production Ready** | **42 Actions Available**

Creator v1 is Umbra's comprehensive content generation system that combines advanced AI capabilities with robust infrastructure to deliver scalable, secure, and intelligent content creation.

## 🚀 Quick Start

### Setup
```bash
# Run automated setup
./setup_creator.sh

# Or manual setup
pip install openai anthropic replicate elevenlabs-python stability-sdk
```

### Basic Usage
```python
# Generate social media post
await creator.execute("generate_post", {
    "topic": "AI technology trends", 
    "platform": "linkedin",
    "tone": "professional"
})

# Create complete content pack
await creator.execute("content_pack", {
    "topic": "Product launch",
    "platform": "instagram"
})

# Export bundle
await creator.execute("export_bundle", {
    "assets": [...],
    "format": "zip"  # or "json", "md"
})
```

## ✨ Features

### 🧠 **AI Integration**
- **OpenRouter First** - Primary text generation via OpenRouter
- **Multi-Provider Support** - Stability, ElevenLabs, Replicate, OpenAI
- **Smart Routing** - Automatic provider selection and fallbacks
- **Cost Optimization** - Provider selection based on cost/quality preferences

### 🎯 **Content Generation**
- **Text** - Posts, captions, titles, hashtags, summaries
- **Images** - Generation, editing, infographics, SVG/logos
- **Video** - Short-form generation, editing, anonymization
- **Audio** - TTS, music, transcription, subtitles
- **Code** - Sites, apps, components, documentation

### 🛡️ **Security & Compliance**
- **PII Redaction** - Automatic detection and masking of sensitive data
- **Platform Limits** - Enforcement of character/hashtag/emoji limits
- **Brand Voice** - Consistent voice across all content
- **Content Validation** - Quality scoring and compliance checks

### 📦 **Export & Storage**
- **Multi-Format** - ZIP, JSON, Markdown bundles
- **R2 Integration** - Automatic cloud storage with presigned URLs
- **Asset Management** - Organized storage with metadata
- **Expiration Handling** - Automatic cleanup of expired exports

## 🔧 Configuration

### Essential Variables
```bash
# Core System
TELEGRAM_BOT_TOKEN=your_bot_token
OPENROUTER_API_KEY=your_openrouter_key

# Storage (R2)
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET=umbra
```

### AI Providers (Optional)
```bash
# Image Generation
CREATOR_IMAGE_PROVIDER=stability
CREATOR_STABILITY_API_KEY=your_stability_key

# Text-to-Speech
CREATOR_TTS_PROVIDER=elevenlabs
CREATOR_ELEVENLABS_API_KEY=your_elevenlabs_key

# Multi-Modal
CREATOR_REPLICATE_API_TOKEN=your_replicate_token
CREATOR_OPENAI_API_KEY=your_openai_key

# Speech Recognition
CREATOR_ASR_PROVIDER=deepgram
CREATOR_DEEPGRAM_API_KEY=your_deepgram_key
```

## 📚 API Reference

### Core Actions

#### Text Generation
```python
# Basic post generation
"generate_post" - Generate social media posts
"content_pack" - Complete content packages
"rewrite" - Rewrite with tone/length adjustments
"summarize" - Text summarization
"hashtags" - Generate relevant hashtags
"title_variations" - Create title alternatives
```

#### Media Generation
```python
# Images
"generate_image" - AI image generation
"edit_image" - Image editing and manipulation
"infographic" - Data visualization

# Video & Audio
"generate_video" - Short-form video creation
"video_anonymize" - Face/license plate blurring
"tts_speak" - Text-to-speech conversion
"music_generate" - Music and jingle creation
"asr_transcribe" - Audio transcription
```

#### Validation & Export
```python
# Content Validation
"validate" - Platform compliance checking
"estimate" - Resource estimation

# Export & Storage
"export_bundle" - Multi-format bundle creation
"save_asset" - Individual asset storage
```

#### Brand & SEO
```python
# Brand Management
"set_brand_voice" - Configure brand voice
"get_brand_voice" - Retrieve brand settings

# SEO Optimization
"seo_brief" - SEO strategy generation
"seo_metadata" - Meta tags and schema
```

### Platform Support

**Social Media:**
- Twitter/X - Character limits, hashtag optimization
- Instagram - Story formats, image ratios
- LinkedIn - Professional tone, article format
- TikTok - Short-form video, trending hashtags
- Facebook - Multi-format posts
- Telegram - Message formatting, file handling

**Professional:**
- Email campaigns
- Blog posts
- Documentation
- Presentations

## 🧪 Testing

### Validation Suite
```bash
# Run comprehensive PR CRT3 tests
python3 test_creator_pr_crt3.py

# Check specific components
python3 -c "from umbra.modules.creator_mcp import CreatorModule; print('✅ Import OK')"
```

### Test Coverage
- ✅ **Capabilities** - All 42 actions exposed
- ✅ **Text Generation** - OpenRouter integration
- ✅ **PII Redaction** - Email/phone detection
- ✅ **Platform Limits** - Character/hashtag enforcement
- ✅ **Bundled Exports** - ZIP/JSON/MD formats
- ✅ **Provider Config** - Multi-provider status

## 📊 Monitoring

### Health Checks
```bash
# Bot status with Creator info
/status

# Detailed diagnostics (admin)
/status verbose
```

### Analytics
- **Usage Tracking** - Operations and costs
- **Performance Metrics** - Response times, success rates
- **Provider Health** - Availability and performance
- **Error Monitoring** - Failure tracking and alerting

## 🔒 Security

### PII Protection
- **Automatic Detection** - Emails, phones, credit cards, SSNs
- **Smart Redaction** - Preserves @handles and legitimate URLs
- **Configurable Policies** - Customizable redaction rules

### Content Safety
- **Banned Phrases** - Configurable content filtering
- **Platform Compliance** - Automatic rule enforcement
- **Quality Scoring** - Readability and engagement metrics

## 🛠️ Architecture

### Core Components
```
creator_mcp.py              # Main MCP interface
service.py                  # Orchestration engine
model_provider_enhanced.py  # AI provider management
validate.py                 # Content validation
export.py                   # Bundle creation
voice.py                    # Brand voice management
presets.py                  # Platform configurations
```

### Integration Points
- **Bot Integration** - Automatic discovery and routing
- **Module Registry** - Standard MCP interface
- **R2 Storage** - Cloud asset management
- **Analytics System** - Comprehensive tracking

## 📈 Performance

### Optimization Features
- **Intelligent Caching** - 5-minute TTL for frequent requests
- **Rate Limiting** - Configurable request throttling
- **Batch Processing** - Efficient multi-variant generation
- **Provider Fallbacks** - Automatic failover on errors

### Scalability
- **Async Operations** - Non-blocking I/O throughout
- **Resource Management** - Memory and token optimization
- **Error Recovery** - Graceful degradation on failures

## 🎯 Use Cases

### Content Marketing
- Social media campaigns
- Blog post generation
- Email marketing
- SEO content creation

### Brand Management
- Consistent voice across platforms
- Template-based content
- Brand guideline enforcement
- Asset library management

### Media Production
- Image generation for posts
- Video content creation
- Audio content (podcasts, ads)
- Multi-format adaptation

### Development
- Documentation generation
- Code scaffolding
- API documentation
- README creation

## 🚀 Production Deployment

### Railway Setup
1. **Environment** - Configure all required variables
2. **Storage** - Set up R2 bucket and permissions
3. **Monitoring** - Enable health checks and logging
4. **Scaling** - Configure resource limits

### Best Practices
- **API Keys** - Rotate regularly, use Railway secrets
- **Rate Limits** - Monitor usage and adjust limits
- **Storage** - Regular cleanup of expired exports
- **Monitoring** - Set up alerts for failures

## 📝 License & Support

**License:** MIT  
**Support:** GitHub Issues  
**Documentation:** `/umbra/modules/creator/API_DOCUMENTATION.md`

---

## 🎉 Status: PR CRT3 Complete!

Creator v1 is **production-ready** with all PR CRT3 requirements met:

✅ **Text via OpenRouter; media via providers; presigned URLs returned**  
✅ **PII redaction; platform limits enforced**  
✅ **Bundled exports (.md/.json/.zip)**  

**Ready for deployment! 🚀**
