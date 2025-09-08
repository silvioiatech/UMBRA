"""
SEO Manager - Generate SEO briefs, metadata, and structured data
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import re

from ...ai.agent import UmbraAIAgent
from ...core.config import UmbraConfig
from .model_provider_enhanced import EnhancedModelProviderManager
from .errors import ContentError

logger = logging.getLogger(__name__)

@dataclass
class SEOKeyword:
    """SEO keyword with metrics"""
    keyword: str
    search_volume: Optional[int] = None
    difficulty: Optional[str] = None  # "low", "medium", "high"
    intent: Optional[str] = None  # "informational", "navigational", "transactional"
    competition: Optional[str] = None

@dataclass
class SEOBrief:
    """SEO content brief"""
    primary_keyword: str
    secondary_keywords: List[str]
    target_audience: str
    content_structure: List[str]
    questions_to_answer: List[str]
    competitor_analysis: List[Dict[str, Any]]
    recommended_length: int
    meta_description: str
    title_suggestions: List[str]

@dataclass
class StructuredData:
    """Structured data markup"""
    type: str  # "Article", "Product", "FAQ", etc.
    data: Dict[str, Any]
    json_ld: str

class SEOManager:
    """SEO briefs, metadata, and structured data generator"""
    
    def __init__(self, ai_agent: UmbraAIAgent, config: UmbraConfig):
        self.ai_agent = ai_agent
        self.config = config
        self.provider_manager = EnhancedModelProviderManager(config)
        
        # SEO settings
        self.default_title_length = config.get("CREATOR_SEO_TITLE_LENGTH", 60)
        self.default_description_length = config.get("CREATOR_SEO_DESCRIPTION_LENGTH", 160)
        self.default_content_length = config.get("CREATOR_SEO_CONTENT_LENGTH", 1500)
        
        # Schema.org types
        self.schema_types = {
            "article": "Article",
            "blog": "BlogPosting",
            "news": "NewsArticle",
            "product": "Product",
            "service": "Service",
            "organization": "Organization",
            "person": "Person",
            "faq": "FAQPage",
            "how_to": "HowTo",
            "recipe": "Recipe",
            "event": "Event",
            "local_business": "LocalBusiness"
        }
        
        logger.info("SEO manager initialized")
    
    async def generate_brief(self, url_or_topic: str) -> Dict[str, Any]:
        """Generate comprehensive SEO brief"""
        try:
            # Get text provider
            provider = await self.provider_manager.get_text_provider()
            if not provider:
                raise ContentError("No text provider available for SEO brief", "seo")
            
            # Determine if input is URL or topic
            is_url = url_or_topic.startswith(("http://", "https://"))
            
            if is_url:
                # Analyze existing page
                page_data = await self._analyze_existing_page(url_or_topic)
                topic = page_data.get("topic", url_or_topic)
            else:
                topic = url_or_topic
                page_data = {}
            
            # Generate keyword research
            keywords = await self._generate_keyword_research(topic, provider)
            
            # Generate content structure
            structure = await self._generate_content_structure(topic, keywords, provider)
            
            # Generate questions to answer
            questions = await self._generate_content_questions(topic, keywords, provider)
            
            # Generate competitor insights
            competitors = await self._generate_competitor_analysis(topic, provider)
            
            # Generate meta elements
            meta_elements = await self._generate_meta_elements(topic, keywords, provider)
            
            brief = SEOBrief(
                primary_keyword=keywords[0] if keywords else topic,
                secondary_keywords=keywords[1:6] if len(keywords) > 1 else [],
                target_audience=await self._identify_target_audience(topic, provider),
                content_structure=structure,
                questions_to_answer=questions,
                competitor_analysis=competitors,
                recommended_length=self.default_content_length,
                meta_description=meta_elements["description"],
                title_suggestions=meta_elements["titles"]
            )
            
            return {
                "brief": {
                    "primary_keyword": brief.primary_keyword,
                    "secondary_keywords": brief.secondary_keywords,
                    "target_audience": brief.target_audience,
                    "content_structure": brief.content_structure,
                    "questions_to_answer": brief.questions_to_answer,
                    "competitor_analysis": brief.competitor_analysis,
                    "recommended_length": brief.recommended_length,
                    "meta_description": brief.meta_description,
                    "title_suggestions": brief.title_suggestions
                },
                "keywords": {
                    "primary": brief.primary_keyword,
                    "secondary": brief.secondary_keywords,
                    "all_keywords": keywords
                },
                "structure": brief.content_structure,
                "questions": brief.questions_to_answer,
                "meta": {
                    "title_suggestions": brief.title_suggestions,
                    "description": brief.meta_description,
                    "recommended_length": brief.recommended_length
                }
            }
            
        except Exception as e:
            logger.error(f"SEO brief generation failed: {e}")
            raise ContentError(f"SEO brief generation failed: {e}", "seo")
    
    async def generate_metadata(self, page_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive SEO metadata"""
        try:
            provider = await self.provider_manager.get_text_provider()
            if not provider:
                raise ContentError("No text provider available for metadata generation", "seo")
            
            title = page_spec.get("title", "")
            description = page_spec.get("description", "")
            content = page_spec.get("content", "")
            url = page_spec.get("url", "")
            type_hint = page_spec.get("type", "article")
            
            # Generate meta tags
            meta_tags = await self._generate_meta_tags(title, description, content, provider)
            
            # Generate Open Graph tags
            og_tags = await self._generate_og_tags(page_spec, provider)
            
            # Generate Twitter Card tags
            twitter_tags = await self._generate_twitter_tags(page_spec, provider)
            
            # Generate JSON-LD structured data
            json_ld = await self._generate_json_ld(page_spec, type_hint, provider)
            
            # Generate robots meta
            robots_meta = self._generate_robots_meta(page_spec)
            
            # Generate canonical URL
            canonical = page_spec.get("canonical_url", url)
            
            return {
                "json_ld": json_ld,
                "meta_tags": meta_tags,
                "og_card": og_tags,
                "twitter_card": twitter_tags,
                "robots": robots_meta,
                "canonical": canonical,
                "structured_data": {
                    "type": type_hint,
                    "json_ld": json_ld
                }
            }
            
        except Exception as e:
            logger.error(f"Metadata generation failed: {e}")
            raise ContentError(f"Metadata generation failed: {e}", "seo")
    
    async def _analyze_existing_page(self, url: str) -> Dict[str, Any]:
        """Analyze existing page for SEO"""
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract existing SEO elements
                    title = soup.title.string if soup.title else ""
                    
                    meta_desc = ""
                    meta_description = soup.find("meta", attrs={"name": "description"})
                    if meta_description:
                        meta_desc = meta_description.get("content", "")
                    
                    # Extract headings
                    headings = []
                    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                        headings.append({
                            "level": h.name,
                            "text": h.get_text().strip()
                        })
                    
                    # Extract content
                    content = soup.get_text()
                    
                    return {
                        "url": url,
                        "title": title,
                        "meta_description": meta_desc,
                        "headings": headings,
                        "content_length": len(content.split()),
                        "topic": title or "Website Analysis"
                    }
                else:
                    return {"url": url, "topic": url}
                    
        except Exception as e:
            logger.warning(f"Failed to analyze page {url}: {e}")
            return {"url": url, "topic": url}
    
    async def _generate_keyword_research(self, topic: str, provider) -> List[str]:
        """Generate keyword research"""
        prompt = f"""Generate a comprehensive list of SEO keywords for the topic: {topic}

Include:
- 1 primary keyword (most important)
- 5-10 secondary keywords (related terms)
- 5-10 long-tail keywords (specific phrases)
- LSI keywords (semantically related)

Focus on keywords that have good search potential and are relevant to the topic.
Return only the keywords, one per line, in order of importance:"""

        result = await provider.generate_text(prompt, max_tokens=500, temperature=0.4)
        if not result.success:
            return [topic]
        
        # Parse keywords from response
        keywords = []
        for line in result.data.strip().split('\n'):
            keyword = line.strip()
            if keyword and not keyword.startswith(('#', '-', '*')):
                # Clean up keyword
                keyword = re.sub(r'^[\d\.\-\*\s]+', '', keyword).strip()
                if keyword:
                    keywords.append(keyword)
        
        return keywords[:20]  # Limit to top 20 keywords
    
    async def _generate_content_structure(self, topic: str, keywords: List[str], provider) -> List[str]:
        """Generate content structure outline"""
        keywords_text = ", ".join(keywords[:5])
        
        prompt = f"""Create a detailed content structure outline for a comprehensive article about: {topic}

Target keywords: {keywords_text}

Generate a hierarchical outline with:
- Introduction
- 4-6 main sections (H2 level)
- 2-3 subsections for each main section (H3 level)
- Conclusion

Focus on covering the topic thoroughly while naturally incorporating the target keywords.
Format as a structured list:"""

        result = await provider.generate_text(prompt, max_tokens=800, temperature=0.3)
        if not result.success:
            return [f"Introduction to {topic}", f"Main aspects of {topic}", f"Conclusion"]
        
        # Parse structure from response
        structure = []
        for line in result.data.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith(('#', 'Note:', 'Remember:')):
                structure.append(line)
        
        return structure
    
    async def _generate_content_questions(self, topic: str, keywords: List[str], provider) -> List[str]:
        """Generate questions the content should answer"""
        keywords_text = ", ".join(keywords[:5])
        
        prompt = f"""Generate 8-12 important questions that an article about "{topic}" should answer.

Target keywords: {keywords_text}

Focus on:
- Questions your target audience would ask
- Common search queries related to the topic
- Questions that naturally incorporate the keywords
- A mix of basic and advanced questions

Return only the questions, one per line:"""

        result = await provider.generate_text(prompt, max_tokens=600, temperature=0.4)
        if not result.success:
            return [f"What is {topic}?", f"How does {topic} work?", f"Why is {topic} important?"]
        
        # Parse questions from response
        questions = []
        for line in result.data.strip().split('\n'):
            line = line.strip()
            if line and line.endswith('?'):
                # Clean up question
                question = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()
                if question:
                    questions.append(question)
        
        return questions
    
    async def _generate_competitor_analysis(self, topic: str, provider) -> List[Dict[str, Any]]:
        """Generate competitor analysis insights"""
        prompt = f"""Analyze the competitive landscape for content about: {topic}

Provide insights about:
- 3-5 types of content that typically rank well for this topic
- Common content gaps in existing articles
- Unique angles to differentiate your content
- Content formats that perform well (lists, how-tos, etc.)

Format as actionable insights:"""

        result = await provider.generate_text(prompt, max_tokens=600, temperature=0.4)
        if not result.success:
            return []
        
        # Parse insights into structured format
        insights = []
        current_insight = {}
        
        for line in result.data.strip().split('\n'):
            line = line.strip()
            if line:
                if ':' in line and not current_insight:
                    # New insight category
                    category, content = line.split(':', 1)
                    current_insight = {
                        "category": category.strip(),
                        "insight": content.strip(),
                        "type": "competitive_insight"
                    }
                    insights.append(current_insight)
                    current_insight = {}
                elif line.startswith(('-', '*', '•')):
                    # Bullet point
                    if insights:
                        if "details" not in insights[-1]:
                            insights[-1]["details"] = []
                        insights[-1]["details"].append(line[1:].strip())
        
        return insights[:5]  # Limit to top 5 insights
    
    async def _identify_target_audience(self, topic: str, provider) -> str:
        """Identify target audience for the topic"""
        prompt = f"""Describe the primary target audience for content about: {topic}

Include:
- Demographics (age, profession, interests)
- Knowledge level (beginner, intermediate, expert)
- Search intent (what they're looking for)
- Pain points and needs

Provide a concise audience description:"""

        result = await provider.generate_text(prompt, max_tokens=200, temperature=0.3)
        if result.success:
            return result.data.strip()
        else:
            return f"People interested in learning about {topic}"
    
    async def _generate_meta_elements(self, topic: str, keywords: List[str], provider) -> Dict[str, Any]:
        """Generate meta title and description"""
        primary_keyword = keywords[0] if keywords else topic
        
        # Generate title suggestions
        title_prompt = f"""Generate 5 compelling SEO titles for content about: {topic}

Primary keyword: {primary_keyword}

Requirements:
- Include the primary keyword naturally
- 50-60 characters optimal length
- Engaging and click-worthy
- Clear value proposition

Return only the titles, one per line:"""

        title_result = await provider.generate_text(title_prompt, max_tokens=300, temperature=0.5)
        
        if title_result.success:
            titles = [line.strip() for line in title_result.data.strip().split('\n') if line.strip()]
        else:
            titles = [f"{primary_keyword}: Complete Guide", f"Everything About {primary_keyword}"]
        
        # Generate meta description
        desc_prompt = f"""Write a compelling meta description for content about: {topic}

Primary keyword: {primary_keyword}

Requirements:
- 150-160 characters
- Include primary keyword naturally
- Clear value proposition
- Call to action
- Engaging and informative

Return only the meta description:"""

        desc_result = await provider.generate_text(desc_prompt, max_tokens=150, temperature=0.4)
        
        if desc_result.success:
            description = desc_result.data.strip()
        else:
            description = f"Learn everything about {primary_keyword}. Comprehensive guide covering key aspects, benefits, and practical tips."
        
        # Ensure proper length
        if len(description) > 160:
            description = description[:157] + "..."
        
        return {
            "titles": titles[:5],
            "description": description
        }
    
    async def _generate_meta_tags(self, title: str, description: str, content: str, provider) -> Dict[str, str]:
        """Generate HTML meta tags"""
        # Ensure title length
        if len(title) > self.default_title_length:
            title = title[:self.default_title_length-3] + "..."
        
        # Ensure description length
        if len(description) > self.default_description_length:
            description = description[:self.default_description_length-3] + "..."
        
        meta_tags = {
            "title": title,
            "description": description,
            "viewport": "width=device-width, initial-scale=1",
            "charset": "utf-8"
        }
        
        # Generate keywords from content if available
        if content:
            keyword_prompt = f"""Extract 5-8 relevant keywords from this content for meta keywords tag:

{content[:500]}...

Return only keywords separated by commas:"""
            
            keyword_result = await provider.generate_text(keyword_prompt, max_tokens=100, temperature=0.3)
            if keyword_result.success:
                meta_tags["keywords"] = keyword_result.data.strip()
        
        return meta_tags
    
    async def _generate_og_tags(self, page_spec: Dict[str, Any], provider) -> Dict[str, str]:
        """Generate Open Graph tags"""
        title = page_spec.get("title", "")
        description = page_spec.get("description", "")
        url = page_spec.get("url", "")
        image = page_spec.get("image", "")
        type_hint = page_spec.get("type", "article")
        
        og_tags = {
            "og:title": title,
            "og:description": description,
            "og:type": type_hint,
            "og:url": url
        }
        
        if image:
            og_tags.update({
                "og:image": image,
                "og:image:alt": f"Image for {title}"
            })
        
        # Site-specific tags
        site_name = page_spec.get("site_name")
        if site_name:
            og_tags["og:site_name"] = site_name
        
        return og_tags
    
    async def _generate_twitter_tags(self, page_spec: Dict[str, Any], provider) -> Dict[str, str]:
        """Generate Twitter Card tags"""
        title = page_spec.get("title", "")
        description = page_spec.get("description", "")
        image = page_spec.get("image", "")
        
        twitter_tags = {
            "twitter:card": "summary_large_image" if image else "summary",
            "twitter:title": title,
            "twitter:description": description
        }
        
        if image:
            twitter_tags["twitter:image"] = image
        
        # Creator/site info
        twitter_handle = page_spec.get("twitter_handle")
        if twitter_handle:
            twitter_tags["twitter:creator"] = twitter_handle
            twitter_tags["twitter:site"] = twitter_handle
        
        return twitter_tags
    
    async def _generate_json_ld(self, page_spec: Dict[str, Any], schema_type: str, provider) -> str:
        """Generate JSON-LD structured data"""
        try:
            # Base schema data
            schema_data = {
                "@context": "https://schema.org",
                "@type": self.schema_types.get(schema_type, "Article")
            }
            
            # Common properties
            if page_spec.get("title"):
                schema_data["headline"] = page_spec["title"]
            
            if page_spec.get("description"):
                schema_data["description"] = page_spec["description"]
            
            if page_spec.get("url"):
                schema_data["url"] = page_spec["url"]
            
            if page_spec.get("image"):
                schema_data["image"] = page_spec["image"]
            
            # Date properties
            now = datetime.utcnow().isoformat() + "Z"
            schema_data["datePublished"] = page_spec.get("published_date", now)
            schema_data["dateModified"] = page_spec.get("modified_date", now)
            
            # Author
            author = page_spec.get("author")
            if author:
                if isinstance(author, str):
                    schema_data["author"] = {
                        "@type": "Person",
                        "name": author
                    }
                else:
                    schema_data["author"] = author
            
            # Publisher
            publisher = page_spec.get("publisher")
            if publisher:
                schema_data["publisher"] = publisher
            
            # Schema-specific properties
            if schema_type == "article" or schema_type == "blog":
                schema_data["@type"] = "BlogPosting"
                if page_spec.get("word_count"):
                    schema_data["wordCount"] = page_spec["word_count"]
            
            elif schema_type == "product":
                schema_data["@type"] = "Product"
                if page_spec.get("price"):
                    schema_data["offers"] = {
                        "@type": "Offer",
                        "price": page_spec["price"],
                        "priceCurrency": page_spec.get("currency", "USD")
                    }
            
            elif schema_type == "faq":
                schema_data["@type"] = "FAQPage"
                faqs = page_spec.get("faqs", [])
                if faqs:
                    schema_data["mainEntity"] = [
                        {
                            "@type": "Question",
                            "name": faq.get("question", ""),
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": faq.get("answer", "")
                            }
                        }
                        for faq in faqs
                    ]
            
            return json.dumps(schema_data, indent=2)
            
        except Exception as e:
            logger.error(f"JSON-LD generation failed: {e}")
            return "{}"
    
    def _generate_robots_meta(self, page_spec: Dict[str, Any]) -> str:
        """Generate robots meta tag"""
        robots_directives = []
        
        # Default directives
        if page_spec.get("index", True):
            robots_directives.append("index")
        else:
            robots_directives.append("noindex")
        
        if page_spec.get("follow", True):
            robots_directives.append("follow")
        else:
            robots_directives.append("nofollow")
        
        # Additional directives
        if page_spec.get("archive", True):
            robots_directives.append("archive")
        
        if page_spec.get("snippet", True):
            robots_directives.append("snippet")
        
        return ", ".join(robots_directives)
    
    async def generate_sitemap_entry(self, page_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sitemap entry for page"""
        return {
            "loc": page_spec.get("url", ""),
            "lastmod": page_spec.get("modified_date", datetime.utcnow().isoformat()),
            "changefreq": page_spec.get("change_frequency", "weekly"),
            "priority": page_spec.get("priority", 0.8)
        }
    
    async def generate_faq_schema(self, questions: List[Dict[str, str]]) -> str:
        """Generate FAQ schema markup"""
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": qa.get("question", ""),
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": qa.get("answer", "")
                    }
                }
                for qa in questions
            ]
        }
        
        return json.dumps(faq_schema, indent=2)
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SEO metadata"""
        issues = []
        warnings = []
        
        # Title validation
        title = metadata.get("meta_tags", {}).get("title", "")
        if not title:
            issues.append("Missing title tag")
        elif len(title) > 60:
            warnings.append(f"Title too long ({len(title)} chars, recommended: 50-60)")
        elif len(title) < 30:
            warnings.append(f"Title too short ({len(title)} chars, recommended: 50-60)")
        
        # Description validation
        description = metadata.get("meta_tags", {}).get("description", "")
        if not description:
            issues.append("Missing meta description")
        elif len(description) > 160:
            warnings.append(f"Description too long ({len(description)} chars, recommended: 150-160)")
        elif len(description) < 120:
            warnings.append(f"Description too short ({len(description)} chars, recommended: 150-160)")
        
        # Open Graph validation
        og_tags = metadata.get("og_card", {})
        if not og_tags.get("og:title"):
            warnings.append("Missing Open Graph title")
        if not og_tags.get("og:description"):
            warnings.append("Missing Open Graph description")
        if not og_tags.get("og:image"):
            warnings.append("Missing Open Graph image")
        
        # JSON-LD validation
        json_ld = metadata.get("json_ld", "")
        if json_ld:
            try:
                json.loads(json_ld)
            except json.JSONDecodeError:
                issues.append("Invalid JSON-LD structured data")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "score": max(0, 100 - len(issues) * 20 - len(warnings) * 5)
        }
