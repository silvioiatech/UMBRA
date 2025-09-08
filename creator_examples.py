"""
Creator v1 (CRT4) - Complete Usage Examples
Demonstrates all capabilities of the omnimedia content generator
"""

import asyncio
import json
from typing import Dict, Any, List

# These would be your actual imports
from umbra.modules.creator_mcp import CreatorModule
from umbra.ai.agent import UmbraAIAgent
from umbra.core.config import UmbraConfig
from umbra.storage.r2_client import R2Client

async def setup_creator() -> CreatorModule:
    """Setup Creator module with configuration"""
    config = UmbraConfig()
    ai_agent = UmbraAIAgent(config)
    r2_client = R2Client(
        account_id=config.get("R2_ACCOUNT_ID"),
        access_key_id=config.get("R2_ACCESS_KEY_ID"),
        secret_access_key=config.get("R2_SECRET_ACCESS_KEY")
    )
    
    creator = CreatorModule(ai_agent, config, r2_client)
    return creator

# =============================================================================
# 1. BASIC TEXT GENERATION
# =============================================================================

async def example_basic_text_generation():
    """Basic text generation examples"""
    creator = await setup_creator()
    
    print("=== BASIC TEXT GENERATION ===")
    
    # Simple social media post
    post_result = await creator.execute("generate_post", {
        "topic": "AI advancements in 2025",
        "platform": "linkedin",
        "tone": "professional",
        "audience": "tech professionals"
    })
    print(f"LinkedIn Post: {post_result['post']['content']}")
    
    # Generate hashtags
    hashtags_result = await creator.execute("hashtags", {
        "topic": "sustainable technology",
        "platform": "instagram",
        "count": 15
    })
    print(f"Hashtags: {hashtags_result['hashtags']}")
    
    # Title variations
    titles_result = await creator.execute("title_variations", {
        "topic": "Remote work productivity tips",
        "count": 5,
        "platform": "blog"
    })
    print(f"Title Options: {titles_result['titles']}")

# =============================================================================
# 2. CONTENT PACK GENERATION
# =============================================================================

async def example_content_pack_generation():
    """Generate complete content packs"""
    creator = await setup_creator()
    
    print("\n=== CONTENT PACK GENERATION ===")
    
    # Complete Instagram content pack
    pack_result = await creator.execute("content_pack", {
        "topic": "Healthy morning routines for busy professionals",
        "platform": "instagram",
        "tone": "inspiring",
        "audience": "working professionals aged 25-40"
    })
    
    pack = pack_result["pack"]
    print(f"Main Caption: {pack['caption']}")
    print(f"Story Captions: {pack['stories']}")
    print(f"Hashtags: {pack['hashtags']}")
    print(f"Call to Action: {pack['cta']}")

# =============================================================================
# 3. BRAND VOICE MANAGEMENT
# =============================================================================

async def example_brand_voice_management():
    """Brand voice configuration and usage"""
    creator = await setup_creator()
    
    print("\n=== BRAND VOICE MANAGEMENT ===")
    
    # Set brand voice
    brand_voice = {
        "brand_name": "TechFlow",
        "bio": "AI-powered productivity platform for modern teams",
        "audience": "Tech-savvy professionals and entrepreneurs",
        "tone_default": "friendly",
        "voice_personality": "innovative",
        "do": [
            "Be authentic and transparent",
            "Provide actionable insights", 
            "Engage with genuine enthusiasm",
            "Use inclusive language"
        ],
        "dont": [
            "Use technical jargon without explanation",
            "Make unrealistic promises",
            "Ignore user feedback",
            "Be overly promotional"
        ],
        "required_phrases": ["Let's build something amazing"],
        "discouraged_words": ["obviously", "just", "simply"],
        "reading_level": "intermediate",
        "emoji_policy": "moderate",
        "cta_style": "engaging"
    }
    
    await creator.execute("set_brand_voice", {"meta_json": brand_voice})
    print("Brand voice configured successfully!")
    
    # Generate content with brand voice
    branded_post = await creator.execute("generate_post", {
        "topic": "New AI automation features",
        "platform": "linkedin"
    })
    print(f"Branded Content: {branded_post['post']['content']}")

# =============================================================================
# 4. TEMPLATE SYSTEM
# =============================================================================

async def example_template_system():
    """Template creation and usage"""
    creator = await setup_creator()
    
    print("\n=== TEMPLATE SYSTEM ===")
    
    # Create custom template
    template_result = await creator.execute("upsert_template", {
        "template_id": "product_update",
        "body": """🚀 Exciting ${update_type}!

We've just ${action} ${feature_name}!

${feature_description}

Key benefits:
${benefits}

${call_to_action}

${hashtags}""",
        "meta": {
            "name": "Product Update Announcement",
            "description": "Template for product updates and releases",
            "category": "social",
            "type": "text",
            "tags": ["product", "announcement", "update"]
        }
    })
    print(f"Template created: {template_result['template_id']}")
    
    # Use template
    rendered_result = await creator.execute("render_template", {
        "template_id": "product_update",
        "variables": {
            "update_type": "Update",
            "action": "launched",
            "feature_name": "Smart Automation Dashboard",
            "feature_description": "A revolutionary way to manage your automated workflows with AI-powered insights.",
            "benefits": "• 50% faster workflow setup\n• Real-time performance analytics\n• Intelligent error detection",
            "call_to_action": "Try it now with our free 14-day trial!",
            "hashtags": "#AI #Automation #Productivity #TechFlow"
        }
    })
    print(f"Rendered Content:\n{rendered_result['rendered_text']}")

# =============================================================================
# 5. IMAGE GENERATION
# =============================================================================

async def example_image_generation():
    """Image generation and editing"""
    creator = await setup_creator()
    
    print("\n=== IMAGE GENERATION ===")
    
    # Generate image
    image_result = await creator.execute("generate_image", {
        "prompt": "Modern office workspace with AI holographic displays, futuristic but professional, soft lighting",
        "size": "1024x1024",
        "style": "photorealistic",
        "negative": ["cluttered", "dark", "outdated technology"]
    })
    print(f"Generated Image: {image_result['image_url']}")
    
    # Create infographic
    infographic_result = await creator.execute("infographic", {
        "data_spec": {
            "type": "bar_chart",
            "title": "AI Adoption in Remote Work",
            "data": [
                {"label": "Task Automation", "value": 78},
                {"label": "Meeting Scheduling", "value": 65},
                {"label": "Email Management", "value": 52},
                {"label": "Document Analysis", "value": 43},
                {"label": "Time Tracking", "value": 38}
            ]
        },
        "brand_prefs": {
            "color_scheme": "blue",
            "style": "modern",
            "include_logo": True
        }
    })
    print(f"Infographic Created: {infographic_result['image_url']}")

# =============================================================================
# 6. VIDEO GENERATION
# =============================================================================

async def example_video_generation():
    """Video generation and processing"""
    creator = await setup_creator()
    
    print("\n=== VIDEO GENERATION ===")
    
    # Generate short video
    video_result = await creator.execute("generate_video", {
        "brief": "Professional introduction to AI automation tools, modern office setting, presenter explaining benefits",
        "format": "16:9",
        "duration_s": 30,
        "style": "commercial",
        "motion_intensity": "medium",
        "subtitles": "auto"
    })
    print(f"Generated Video: {video_result['video_url']}")
    
    # Convert image to video
    image_to_video_result = await creator.execute("image_to_video", {
        "media_id": "sample_image_123",
        "prompt": "Gentle zoom and parallax effect, professional presentation style",
        "duration": 10
    })
    print(f"Image to Video: {image_to_video_result.get('video_url', 'Failed')}")

# =============================================================================
# 7. AUDIO AND TTS
# =============================================================================

async def example_audio_generation():
    """Audio and text-to-speech examples"""
    creator = await setup_creator()
    
    print("\n=== AUDIO GENERATION ===")
    
    # Text-to-speech
    tts_result = await creator.execute("tts_speak", {
        "text": "Welcome to TechFlow, where AI meets productivity. Let's build something amazing together!",
        "voice_id": "professional_female",
        "style": "friendly",
        "speed": 1.0
    })
    print(f"Generated Audio: {tts_result.get('audio_url', 'Failed')}")
    
    # Generate background music
    music_result = await creator.execute("music_generate", {
        "brief": "Upbeat corporate background music, inspiring and motivational",
        "duration_s": 30,
        "genre": "corporate",
        "bpm": 120,
        "structure": "intro-main-outro"
    })
    print(f"Generated Music: {music_result.get('audio_url', 'Failed')}")

# =============================================================================
# 8. CODE GENERATION
# =============================================================================

async def example_code_generation():
    """Code and website generation"""
    creator = await setup_creator()
    
    print("\n=== CODE GENERATION ===")
    
    # Generate React component
    code_result = await creator.execute("generate_code", {
        "spec": "Create a responsive product card component with image, title, description, price, and add to cart button",
        "prog_language": "react",
        "tests": True
    })
    print(f"Generated Component: {code_result.get('component_code', 'Failed')[:200]}...")
    
    # Generate full website
    site_result = await creator.execute("generate_site", {
        "brief": "Landing page for AI productivity tool, modern design, hero section, features, pricing, testimonials",
        "stack": "nextjs",
        "features": ["responsive", "dark_mode", "animations", "contact_form"]
    })
    print(f"Generated Site: {site_result.get('site_url', 'Failed')}")

# =============================================================================
# 9. EXTERNAL CONNECTORS
# =============================================================================

async def example_external_connectors():
    """Connect to external data sources"""
    creator = await setup_creator()
    
    print("\n=== EXTERNAL CONNECTORS ===")
    
    # List available connectors
    connectors_result = await creator.execute("connectors_list", {})
    print(f"Available Connectors: {connectors_result['sources']}")
    
    # Link Notion workspace (if configured)
    if "notion" in connectors_result['sources']:
        link_result = await creator.execute("connector_link", {
            "source": "notion",
            "auth": {"token": "your_notion_token"}
        })
        
        if "connector_id" in link_result:
            # Fetch assets from Notion
            assets_result = await creator.execute("fetch_assets", {
                "connector_id": link_result["connector_id"],
                "query": "product roadmap"
            })
            print(f"Notion Assets Found: {len(assets_result.get('assets', []))}")

# =============================================================================
# 10. RAG AND KNOWLEDGE
# =============================================================================

async def example_rag_knowledge():
    """RAG-based content generation with citations"""
    creator = await setup_creator()
    
    print("\n=== RAG AND KNOWLEDGE ===")
    
    # Ingest documents
    documents = [
        {
            "content": "AI automation tools have increased remote work productivity by 40% according to recent studies.",
            "source": "Remote Work Report 2024",
            "url": "https://example.com/report"
        },
        {
            "content": "The most effective AI tools for teams include task automation, meeting scheduling, and document analysis.",
            "source": "AI in Business Whitepaper",
            "url": "https://example.com/whitepaper"
        }
    ]
    
    rag_ingest_result = await creator.execute("rag_ingest", {
        "docs": documents,
        "tags": ["ai", "productivity", "remote_work"]
    })
    print(f"Knowledge Base Created: {rag_ingest_result['kb_id']}")
    
    # Generate content with citations
    rag_generate_result = await creator.execute("rag_generate", {
        "brief": "Write an article about AI tools improving remote work productivity",
        "cite": True
    })
    print(f"Generated with Citations: {rag_generate_result.get('content', 'Failed')[:200]}...")

# =============================================================================
# 11. SEO OPTIMIZATION
# =============================================================================

async def example_seo_optimization():
    """SEO content optimization"""
    creator = await setup_creator()
    
    print("\n=== SEO OPTIMIZATION ===")
    
    # Generate SEO brief
    seo_brief_result = await creator.execute("seo_brief", {
        "url_or_topic": "AI productivity tools for remote teams"
    })
    print(f"SEO Keywords: {seo_brief_result.get('keywords', {}).get('primary', 'N/A')}")
    print(f"Content Structure: {seo_brief_result.get('structure', 'N/A')}")
    
    # Generate SEO metadata
    seo_metadata_result = await creator.execute("seo_metadata", {
        "page_spec": {
            "title": "AI Productivity Tools - Transform Your Remote Team",
            "description": "Discover powerful AI tools that boost remote team productivity by 40%. Features automation, scheduling, and analytics.",
            "type": "article",
            "url": "https://techflow.ai/productivity-tools",
            "image": "https://techflow.ai/images/productivity-hero.jpg"
        }
    })
    print(f"Generated Meta Tags: {len(seo_metadata_result.get('meta_tags', []))} tags")
    print(f"Schema.org JSON-LD: {bool(seo_metadata_result.get('json_ld'))}")

# =============================================================================
# 12. A/B TESTING AND VARIANTS
# =============================================================================

async def example_ab_testing():
    """A/B testing and content variants"""
    creator = await setup_creator()
    
    print("\n=== A/B TESTING AND VARIANTS ===")
    
    # Generate A/B test variants
    ab_result = await creator.execute("ab_generate_variants", {
        "brief": "Email subject line for new AI feature launch announcement",
        "k": 5
    })
    
    print("A/B Test Variants:")
    for i, variant in enumerate(ab_result.get('variants', []), 1):
        print(f"  {i}. {variant.get('content', 'N/A')} (Score: {variant.get('scores', {}).get('combined', 0)})")

# =============================================================================
# 13. BATCH GENERATION
# =============================================================================

async def example_batch_generation():
    """Batch content generation"""
    creator = await setup_creator()
    
    print("\n=== BATCH GENERATION ===")
    
    # Batch generate social media posts
    batch_task = {
        "action": "generate_post",
        "base_params": {
            "platform": "linkedin",
            "tone": "professional"
        },
        "variants": [
            {"topic": "AI in healthcare"},
            {"topic": "Machine learning trends"},
            {"topic": "Automation in finance"},
            {"topic": "Future of remote work"},
            {"topic": "Sustainable technology"}
        ]
    }
    
    batch_result = await creator.execute("batch_generate", {
        "task_spec": batch_task,
        "variations": 1
    })
    
    print(f"Batch Generated: {len(batch_result.get('variants', []))} posts")
    for i, variant in enumerate(batch_result.get('variants', [])[:3], 1):
        print(f"  {i}. {variant.get('content', 'N/A')[:100]}...")

# =============================================================================
# 14. EXPORT AND DISTRIBUTION
# =============================================================================

async def example_export_distribution():
    """Export content bundles"""
    creator = await setup_creator()
    
    print("\n=== EXPORT AND DISTRIBUTION ===")
    
    # Create export bundle
    assets = [
        {
            "type": "text",
            "name": "LinkedIn Post",
            "content": "Excited to share our latest AI productivity insights! 🚀",
            "metadata": {"platform": "linkedin", "tone": "professional"}
        },
        {
            "type": "image",
            "name": "Hero Image",
            "url": "https://example.com/hero.jpg",
            "metadata": {"size": "1200x630", "format": "jpg"}
        },
        {
            "type": "template",
            "name": "Product Update Template",
            "content": "Template content here...",
            "metadata": {"category": "social", "variables": ["product_name", "features"]}
        }
    ]
    
    export_result = await creator.execute("export_bundle", {
        "assets": assets,
        "format": "zip"
    })
    print(f"Export Bundle: {export_result.get('download_url', 'Failed')}")

# =============================================================================
# 15. CONTENT VALIDATION
# =============================================================================

async def example_content_validation():
    """Content validation and compliance"""
    creator = await setup_creator()
    
    print("\n=== CONTENT VALIDATION ===")
    
    # Validate social media content
    content_to_validate = "Check out our amazing new product! Contact john.doe@company.com or call +1-555-123-4567 for more info! 🔥🔥🔥"
    
    validation_result = await creator.execute("validate", {
        "text": content_to_validate,
        "platform": "linkedin"
    })
    
    print(f"Content Valid: {validation_result.get('valid', False)}")
    print(f"PII Detected: {validation_result.get('pii_detected', [])}")
    print(f"Platform Issues: {validation_result.get('platform_issues', [])}")
    print(f"Brand Voice Score: {validation_result.get('brand_voice_score', 0)}")

# =============================================================================
# 16. AUTO-ORCHESTRATION
# =============================================================================

async def example_auto_orchestration():
    """Auto-orchestrate content creation from input"""
    creator = await setup_creator()
    
    print("\n=== AUTO-ORCHESTRATION ===")
    
    # Auto-create content from simple input
    auto_result = await creator.execute("auto", {
        "input": "We just launched a new AI feature that helps schedule meetings automatically",
        "goal": "social_media_campaign",
        "platform": "linkedin",
        "tone": "professional"
    })
    
    print("Auto-Generated Campaign:")
    campaign = auto_result.get('result', {})
    print(f"  Main Post: {campaign.get('main_post', 'N/A')[:100]}...")
    print(f"  Images: {len(campaign.get('images', []))} generated")
    print(f"  Hashtags: {campaign.get('hashtags', 'N/A')}")

# =============================================================================
# 17. COST ESTIMATION
# =============================================================================

async def example_cost_estimation():
    """Estimate costs for operations"""
    creator = await setup_creator()
    
    print("\n=== COST ESTIMATION ===")
    
    # Estimate content creation costs
    estimate_result = await creator.execute("estimate", {
        "brief": "Complete social media campaign with images and video",
        "platform": "instagram"
    })
    
    print(f"Estimated Cost: ${estimate_result.get('cost_estimate_usd', 0):.2f}")
    print(f"Estimated Time: {estimate_result.get('time_estimate_seconds', 0)} seconds")
    print(f"Resources Needed: {estimate_result.get('resources_needed', [])}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def run_all_examples():
    """Run all examples"""
    examples = [
        ("Basic Text Generation", example_basic_text_generation),
        ("Content Pack Generation", example_content_pack_generation),
        ("Brand Voice Management", example_brand_voice_management),
        ("Template System", example_template_system),
        ("Image Generation", example_image_generation),
        ("Video Generation", example_video_generation),
        ("Audio Generation", example_audio_generation),
        ("Code Generation", example_code_generation),
        ("External Connectors", example_external_connectors),
        ("RAG Knowledge", example_rag_knowledge),
        ("SEO Optimization", example_seo_optimization),
        ("A/B Testing", example_ab_testing),
        ("Batch Generation", example_batch_generation),
        ("Export Distribution", example_export_distribution),
        ("Content Validation", example_content_validation),
        ("Auto-Orchestration", example_auto_orchestration),
        ("Cost Estimation", example_cost_estimation)
    ]
    
    for name, example_func in examples:
        try:
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            print(f"{'='*60}")
            await example_func()
        except Exception as e:
            print(f"Error in {name}: {e}")
        
        # Small delay between examples
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    # Run specific example
    # asyncio.run(example_basic_text_generation())
    
    # Or run all examples
    asyncio.run(run_all_examples())

# =============================================================================
# QUICK REFERENCE
# =============================================================================

"""
QUICK REFERENCE FOR CREATOR V1 ACTIONS:

TEXT:
- generate_post(topic, platform?, tone?, audience?, length?)
- content_pack(topic, platform?, tone?, audience?)
- rewrite(text, tone?, length?)
- summarize(text, target_length?)
- hashtags(topic, platform?, count=10)
- title_variations(topic, count=3, platform?)

MEDIA:
- generate_image(prompt, refs?, size?, style?, negative?, seed?)
- edit_image(media_id, instructions, mask?, size?, style?)
- infographic(data_spec, brand_prefs?, layout_hint?)
- generate_video(brief, format?, duration_s?, storyboard?, voice_id?, music_id?, subtitles?)
- tts_speak(text, voice_id?, style?, speed?)
- music_generate(brief, duration_s?, genre?, bpm?, structure?, refs?)

CODE:
- generate_site(brief, stack?, features?)
- generate_code(spec, prog_language, tests?)

TEMPLATES:
- list_templates()
- render_template(template_id, variables)
- upsert_template(template_id?, body, meta)

KNOWLEDGE:
- rag_ingest(docs, tags?)
- rag_generate(brief, cite?)
- seo_brief(url_or_topic)
- seo_metadata(page_spec)

CONNECTORS:
- connectors_list()
- connector_link(source, auth)
- fetch_assets(connector_id, query?)

UTILITIES:
- auto(input, goal?, platform?, tone?)
- validate(text|asset, platform)
- estimate(brief, media?, text?, platform?)
- batch_generate(task_spec, variations)
- ab_generate_variants(brief, k=3)
- export_bundle(assets, format?)

BRAND:
- set_brand_voice(meta_json)
- get_brand_voice()

Supported platforms: instagram, linkedin, twitter, telegram, youtube, tiktok, facebook
Supported formats: Images (1024x1024, 1920x1080, etc.), Videos (9:16, 1:1, 16:9), Audio (mp3, wav)
Supported providers: OpenAI, Stability, ElevenLabs, Replicate, Notion, Google Drive, GitHub, Slack
"""
