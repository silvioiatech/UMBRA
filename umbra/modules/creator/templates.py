"""
Template Manager - Manage content templates and template engine
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from string import Template

from ...core.config import UmbraConfig
from .errors import ContentError

logger = logging.getLogger(__name__)

@dataclass
class ContentTemplate:
    """Content template definition"""
    id: str
    name: str
    description: str
    category: str  # "social", "email", "blog", "marketing", "announcement"
    template_type: str  # "text", "html", "markdown"
    body: str
    variables: List[str]  # Required variables
    optional_variables: List[str]  # Optional variables
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    platform: Optional[str] = None  # Target platform if specific

class TemplateManager:
    """Manages content templates and rendering"""
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        self.templates = {}
        
        # Template settings
        self.max_templates = config.get("CREATOR_MAX_TEMPLATES", 100)
        self.max_template_size = config.get("CREATOR_MAX_TEMPLATE_SIZE_KB", 50) * 1024
        
        # Initialize with default templates
        self._load_default_templates()
        
        logger.info(f"Template manager initialized with {len(self.templates)} templates")
    
    def _load_default_templates(self):
        """Load default content templates"""
        
        # Social media templates
        self._add_default_template(
            "social_announcement",
            "Social Media Announcement",
            "General announcement template for social media",
            "social",
            "text",
            """🎉 Exciting news! ${announcement}

${details}

${call_to_action}

${hashtags}""",
            ["announcement", "details", "call_to_action"],
            ["hashtags", "emoji"]
        )
        
        self._add_default_template(
            "social_launch",
            "Product Launch",
            "Product or feature launch announcement",
            "social",
            "text",
            """🚀 Introducing ${product_name}!

${product_description}

Key features:
${features}

${launch_details}

${call_to_action}

${hashtags}""",
            ["product_name", "product_description", "call_to_action"],
            ["features", "launch_details", "hashtags"]
        )
        
        self._add_default_template(
            "blog_howto",
            "How-To Blog Post",
            "Step-by-step guide blog post template",
            "blog",
            "markdown",
            """# How to ${title}

## Introduction
${introduction}

## What You'll Need
${requirements}

## Step-by-Step Guide

${steps}

## Conclusion
${conclusion}

---
*${author_bio}*""",
            ["title", "introduction", "steps"],
            ["requirements", "conclusion", "author_bio"]
        )
        
        # Email templates
        self._add_default_template(
            "email_newsletter",
            "Newsletter Email",
            "Newsletter email template",
            "email",
            "html",
            """<html>
<body>
<h1>${newsletter_title}</h1>

<p>Hi ${subscriber_name},</p>

<p>${opening_message}</p>

<h2>This Week's Highlights</h2>
${highlights}

<h2>${main_section_title}</h2>
${main_content}

<hr>
<p>${closing_message}</p>

<p>Best regards,<br>
${sender_name}</p>

<small>
<a href="${unsubscribe_link}">Unsubscribe</a>
</small>
</body>
</html>""",
            ["newsletter_title", "main_content"],
            ["subscriber_name", "opening_message", "highlights", "main_section_title", "closing_message", "sender_name", "unsubscribe_link"]
        )
        
        # Marketing templates
        self._add_default_template(
            "marketing_promo",
            "Promotional Campaign",
            "Marketing promotional content template",
            "marketing",
            "text",
            """${offer_headline}

${offer_description}

🎯 Benefits:
${benefits}

⏰ ${urgency_message}

${call_to_action}

${terms_conditions}""",
            ["offer_headline", "offer_description", "call_to_action"],
            ["benefits", "urgency_message", "terms_conditions"]
        )
        
        # Event templates
        self._add_default_template(
            "event_invitation",
            "Event Invitation",
            "Event invitation template",
            "event",
            "text",
            """🎪 You're Invited to ${event_name}!

📅 Date: ${event_date}
🕐 Time: ${event_time}
📍 Location: ${event_location}

${event_description}

${event_highlights}

${rsvp_instructions}

${contact_info}""",
            ["event_name", "event_date", "event_time", "event_location"],
            ["event_description", "event_highlights", "rsvp_instructions", "contact_info"]
        )
        
        # Thank you templates
        self._add_default_template(
            "thank_you",
            "Thank You Message",
            "Generic thank you message template",
            "social",
            "text",
            """Thank you ${recipient_name}! 🙏

${thank_you_message}

${what_happens_next}

${additional_message}

${signature}""",
            ["thank_you_message"],
            ["recipient_name", "what_happens_next", "additional_message", "signature"]
        )
        
        # Recap templates
        self._add_default_template(
            "event_recap",
            "Event Recap",
            "Event recap/summary template",
            "social",
            "text",
            """${event_name} Recap 📝

What an amazing ${event_type}! 

Key highlights:
${highlights}

${attendance_stats}

${testimonials}

${thank_you_message}

${next_event_teaser}

${hashtags}""",
            ["event_name", "highlights"],
            ["event_type", "attendance_stats", "testimonials", "thank_you_message", "next_event_teaser", "hashtags"]
        )
    
    def _add_default_template(self, template_id: str, name: str, description: str, 
                            category: str, template_type: str, body: str, 
                            required_vars: List[str], optional_vars: List[str]):
        """Add a default template"""
        template = ContentTemplate(
            id=template_id,
            name=name,
            description=description,
            category=category,
            template_type=template_type,
            body=body,
            variables=required_vars,
            optional_variables=optional_vars,
            metadata={
                "is_default": True,
                "version": "1.0"
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tags=["default", category]
        )
        
        self.templates[template_id] = template
    
    async def render_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Render template with provided variables"""
        try:
            if template_id not in self.templates:
                raise ContentError(f"Template not found: {template_id}", "template")
            
            template = self.templates[template_id]
            
            # Validate required variables
            missing_vars = [var for var in template.variables if var not in variables]
            if missing_vars:
                raise ContentError(f"Missing required variables: {', '.join(missing_vars)}", "template")
            
            # Prepare variables (add defaults for optional ones)
            render_vars = variables.copy()
            for var in template.optional_variables:
                if var not in render_vars:
                    render_vars[var] = ""
            
            # Render template
            if template.template_type == "text":
                return self._render_text_template(template.body, render_vars)
            elif template.template_type == "markdown":
                return self._render_markdown_template(template.body, render_vars)
            elif template.template_type == "html":
                return self._render_html_template(template.body, render_vars)
            else:
                return self._render_text_template(template.body, render_vars)
                
        except Exception as e:
            logger.error(f"Template rendering failed for {template_id}: {e}")
            raise ContentError(f"Template rendering failed: {e}", "template")
    
    def _render_text_template(self, body: str, variables: Dict[str, Any]) -> str:
        """Render text template using Python string.Template"""
        try:
            template = Template(body)
            return template.safe_substitute(variables)
        except Exception as e:
            raise ContentError(f"Text template rendering failed: {e}", "template")
    
    def _render_markdown_template(self, body: str, variables: Dict[str, Any]) -> str:
        """Render markdown template"""
        # For markdown, we use the same logic as text but could add markdown-specific processing
        return self._render_text_template(body, variables)
    
    def _render_html_template(self, body: str, variables: Dict[str, Any]) -> str:
        """Render HTML template"""
        # Basic HTML template rendering - could be enhanced with a proper template engine
        return self._render_text_template(body, variables)
    
    async def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates"""
        template_list = []
        
        for template_id, template in self.templates.items():
            template_list.append({
                "id": template_id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "type": template.template_type,
                "variables": template.variables,
                "optional_variables": template.optional_variables,
                "tags": template.tags,
                "platform": template.platform,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat(),
                "is_default": template.metadata.get("is_default", False)
            })
        
        # Sort by category, then by name
        template_list.sort(key=lambda x: (x["category"], x["name"]))
        return template_list
    
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get specific template details"""
        if template_id not in self.templates:
            return None
        
        template = self.templates[template_id]
        return {
            "id": template_id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "type": template.template_type,
            "body": template.body,
            "variables": template.variables,
            "optional_variables": template.optional_variables,
            "metadata": template.metadata,
            "tags": template.tags,
            "platform": template.platform,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }
    
    async def upsert_template(self, template_id: Optional[str], body: str, 
                            meta: Dict[str, Any]) -> str:
        """Create or update template"""
        try:
            # Validate template size
            if len(body.encode('utf-8')) > self.max_template_size:
                raise ContentError(f"Template too large (max {self.max_template_size} bytes)", "template")
            
            # Check template limit for new templates
            if not template_id and len(self.templates) >= self.max_templates:
                raise ContentError(f"Too many templates (max {self.max_templates})", "template")
            
            # Generate ID if not provided
            if not template_id:
                template_id = self._generate_template_id(meta.get("name", "template"))
            
            # Extract variables from template body
            variables = self._extract_variables(body)
            
            # Create or update template
            now = datetime.utcnow()
            
            if template_id in self.templates:
                # Update existing template
                existing = self.templates[template_id]
                template = ContentTemplate(
                    id=template_id,
                    name=meta.get("name", existing.name),
                    description=meta.get("description", existing.description),
                    category=meta.get("category", existing.category),
                    template_type=meta.get("type", existing.template_type),
                    body=body,
                    variables=variables["required"],
                    optional_variables=variables["optional"],
                    metadata=meta.get("metadata", existing.metadata),
                    created_at=existing.created_at,
                    updated_at=now,
                    tags=meta.get("tags", existing.tags),
                    platform=meta.get("platform", existing.platform)
                )
            else:
                # Create new template
                template = ContentTemplate(
                    id=template_id,
                    name=meta.get("name", f"Template {template_id}"),
                    description=meta.get("description", "Custom template"),
                    category=meta.get("category", "custom"),
                    template_type=meta.get("type", "text"),
                    body=body,
                    variables=variables["required"],
                    optional_variables=variables["optional"],
                    metadata=meta.get("metadata", {}),
                    created_at=now,
                    updated_at=now,
                    tags=meta.get("tags", ["custom"]),
                    platform=meta.get("platform")
                )
            
            self.templates[template_id] = template
            
            logger.info(f"Template {'updated' if template_id in self.templates else 'created'}: {template_id}")
            return template_id
            
        except Exception as e:
            logger.error(f"Template upsert failed: {e}")
            raise ContentError(f"Template upsert failed: {e}", "template")
    
    def _extract_variables(self, template_body: str) -> Dict[str, List[str]]:
        """Extract variables from template body"""
        # Find ${variable} patterns
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, template_body)
        
        # For now, treat all as required variables
        # In the future, could have conventions for optional variables
        required_vars = list(set(matches))  # Remove duplicates
        optional_vars = []
        
        return {
            "required": required_vars,
            "optional": optional_vars
        }
    
    def _generate_template_id(self, name: str) -> str:
        """Generate unique template ID"""
        import hashlib
        
        # Create base ID from name
        base_id = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        base_id = re.sub(r'_{2,}', '_', base_id)  # Replace multiple underscores
        base_id = base_id.strip('_')  # Remove leading/trailing underscores
        
        if not base_id:
            base_id = "template"
        
        # Check if ID already exists
        if base_id not in self.templates:
            return base_id
        
        # Add timestamp/hash suffix for uniqueness
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        hash_part = hashlib.md5(f"{name}_{timestamp}".encode()).hexdigest()[:6]
        
        return f"{base_id}_{timestamp}_{hash_part}"
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete template"""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        
        # Prevent deletion of default templates
        if template.metadata.get("is_default", False):
            raise ContentError("Cannot delete default template", "template")
        
        del self.templates[template_id]
        logger.info(f"Template deleted: {template_id}")
        return True
    
    async def search_templates(self, query: str, category: Optional[str] = None, 
                             platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search templates by query, category, or platform"""
        results = []
        query_lower = query.lower() if query else ""
        
        for template_id, template in self.templates.items():
            # Category filter
            if category and template.category != category:
                continue
            
            # Platform filter
            if platform and template.platform and template.platform != platform:
                continue
            
            # Text search
            if query_lower:
                searchable_text = f"{template.name} {template.description} {' '.join(template.tags)}".lower()
                if query_lower not in searchable_text:
                    continue
            
            results.append({
                "id": template_id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "type": template.template_type,
                "platform": template.platform,
                "tags": template.tags,
                "variables": template.variables,
                "created_at": template.created_at.isoformat()
            })
        
        return results
    
    async def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all templates in a specific category"""
        return await self.search_templates("", category=category)
    
    async def get_templates_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """Get all templates for a specific platform"""
        return await self.search_templates("", platform=platform)
    
    def get_template_categories(self) -> List[str]:
        """Get list of all template categories"""
        categories = set()
        for template in self.templates.values():
            categories.add(template.category)
        return sorted(list(categories))
    
    def get_template_platforms(self) -> List[str]:
        """Get list of all template platforms"""
        platforms = set()
        for template in self.templates.values():
            if template.platform:
                platforms.add(template.platform)
        return sorted(list(platforms))
    
    async def validate_template(self, body: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate template body and variables"""
        issues = []
        warnings = []
        
        try:
            # Extract variables from template
            extracted_vars = self._extract_variables(body)
            
            # Check for undefined variables in render
            try:
                test_vars = {var: f"test_{var}" for var in extracted_vars["required"]}
                self._render_text_template(body, test_vars)
            except Exception as e:
                issues.append(f"Template rendering error: {e}")
            
            # Check variable naming
            for var in extracted_vars["required"]:
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var):
                    warnings.append(f"Variable '{var}' has non-standard naming")
            
            # Check template size
            body_size = len(body.encode('utf-8'))
            if body_size > self.max_template_size:
                issues.append(f"Template too large: {body_size} bytes (max: {self.max_template_size})")
            elif body_size > self.max_template_size * 0.8:
                warnings.append(f"Template size approaching limit: {body_size} bytes")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "variables": extracted_vars,
                "size_bytes": body_size
            }
            
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Validation error: {e}"],
                "warnings": [],
                "variables": {"required": [], "optional": []},
                "size_bytes": len(body.encode('utf-8'))
            }
    
    async def preview_template(self, template_id: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Preview template rendering with provided variables"""
        try:
            if template_id not in self.templates:
                raise ContentError(f"Template not found: {template_id}", "template")
            
            template = self.templates[template_id]
            
            # Use provided variables or generate sample values
            preview_vars = {}
            
            for var in template.variables:
                if var in variables:
                    preview_vars[var] = variables[var]
                else:
                    # Generate sample value
                    preview_vars[var] = f"[Sample {var.replace('_', ' ').title()}]"
            
            for var in template.optional_variables:
                if var in variables:
                    preview_vars[var] = variables[var]
                else:
                    preview_vars[var] = f"[Optional {var.replace('_', ' ').title()}]"
            
            # Render preview
            rendered = await self.render_template(template_id, preview_vars)
            
            return {
                "template_id": template_id,
                "template_name": template.name,
                "rendered_content": rendered,
                "variables_used": preview_vars,
                "character_count": len(rendered),
                "word_count": len(rendered.split())
            }
            
        except Exception as e:
            logger.error(f"Template preview failed for {template_id}: {e}")
            raise ContentError(f"Template preview failed: {e}", "template")
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about templates"""
        total_templates = len(self.templates)
        categories = {}
        platforms = {}
        default_count = 0
        custom_count = 0
        
        for template in self.templates.values():
            # Category stats
            if template.category not in categories:
                categories[template.category] = 0
            categories[template.category] += 1
            
            # Platform stats
            if template.platform:
                if template.platform not in platforms:
                    platforms[template.platform] = 0
                platforms[template.platform] += 1
            
            # Type stats
            if template.metadata.get("is_default", False):
                default_count += 1
            else:
                custom_count += 1
        
        return {
            "total_templates": total_templates,
            "default_templates": default_count,
            "custom_templates": custom_count,
            "categories": categories,
            "platforms": platforms,
            "max_templates": self.max_templates,
            "usage_percentage": (total_templates / self.max_templates) * 100
        }
