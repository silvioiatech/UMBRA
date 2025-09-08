"""
Code Generation - Generate websites, apps, components, and code scaffolds
"""

import logging
import json
import zipfile
import tempfile
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path

from ...ai.agent import UmbraAIAgent
from ...core.config import UmbraConfig
from .model_provider_enhanced import EnhancedModelProviderManager
from .errors import ContentError

logger = logging.getLogger(__name__)

@dataclass
class CodeGenerationRequest:
    """Code generation request"""
    brief: str
    stack: str  # "nextjs", "nuxt", "express", "flask", "react", "vue", "python", "js"
    features: List[str]
    tests: bool = False
    docs: bool = True

@dataclass
class CodeResult:
    """Code generation result"""
    files: Dict[str, str]  # filename -> content
    zip_url: Optional[str] = None
    readme_url: Optional[str] = None
    meta: Dict[str, Any] = None

class CodeGenerator:
    """AI-powered code and site generation"""
    
    def __init__(self, ai_agent: UmbraAIAgent, config: UmbraConfig):
        self.ai_agent = ai_agent
        self.config = config
        self.provider_manager = EnhancedModelProviderManager(config)
        
        # Code generation settings
        self.max_files = config.get("CREATOR_MAX_FILES_PER_PROJECT", 50)
        self.max_file_size = config.get("CREATOR_MAX_FILE_SIZE_KB", 100) * 1024
        
        # Supported stacks and their templates
        self.stack_templates = {
            "nextjs": self._get_nextjs_template,
            "nuxt": self._get_nuxt_template,
            "express": self._get_express_template,
            "flask": self._get_flask_template,
            "react": self._get_react_template,
            "vue": self._get_vue_template,
            "python": self._get_python_template,
            "fastapi": self._get_fastapi_template,
            "django": self._get_django_template
        }
        
        logger.info("Code generator initialized")
    
    async def generate_site(self, brief: str, stack: str = "nextjs", 
                          features: List[str] = None) -> Dict[str, Any]:
        """Generate complete website/app"""
        try:
            if stack not in self.stack_templates:
                raise ContentError(f"Unsupported stack: {stack}", "code")
            
            features = features or []
            request = CodeGenerationRequest(
                brief=brief,
                stack=stack,
                features=features,
                tests=True,
                docs=True
            )
            
            # Get text provider for code generation
            provider = await self.provider_manager.get_text_provider()
            if not provider:
                raise ContentError("No text provider available for code generation", "code")
            
            # Generate project structure
            project_files = await self._generate_project_files(request, provider)
            
            # Create ZIP bundle
            zip_url = await self._create_project_zip(project_files, f"{stack}_project")
            
            # Generate README
            readme_content = await self._generate_readme(request, project_files, provider)
            project_files["README.md"] = readme_content
            
            return {
                "zip_url": zip_url,
                "readme_url": zip_url,  # README is included in ZIP
                "meta": {
                    "stack": stack,
                    "features": features,
                    "file_count": len(project_files),
                    "brief": brief
                }
            }
            
        except Exception as e:
            logger.error(f"Site generation failed: {e}")
            raise ContentError(f"Site generation failed: {e}", "code")
    
    async def generate_code(self, spec: str, prog_language: str, 
                          tests: bool = False) -> Dict[str, Any]:
        """Generate code components"""
        try:
            # Get text provider
            provider = await self.provider_manager.get_text_provider()
            if not provider:
                raise ContentError("No text provider available for code generation", "code")
            
            # Generate code
            code_content = await self._generate_single_file_code(spec, prog_language, provider)
            
            files = {f"main.{self._get_file_extension(prog_language)}": code_content}
            
            # Generate tests if requested
            if tests:
                test_content = await self._generate_tests(spec, prog_language, code_content, provider)
                files[f"test_main.{self._get_file_extension(prog_language)}"] = test_content
            
            # Create ZIP if multiple files
            if len(files) > 1:
                zip_url = await self._create_project_zip(files, f"{prog_language}_code")
                return {
                    "zip_url": zip_url,
                    "gist_url": None,
                    "meta": {
                        "language": prog_language,
                        "has_tests": tests,
                        "file_count": len(files)
                    }
                }
            else:
                # Single file - could create gist
                return {
                    "zip_url": None,
                    "gist_url": await self._create_gist(files, spec),
                    "code": code_content,
                    "meta": {
                        "language": prog_language,
                        "has_tests": tests,
                        "file_count": len(files)
                    }
                }
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise ContentError(f"Code generation failed: {e}", "code")
    
    async def generate_component(self, spec: str, framework: str = "react") -> Dict[str, Any]:
        """Generate UI component"""
        try:
            provider = await self.provider_manager.get_text_provider()
            if not provider:
                raise ContentError("No text provider available", "code")
            
            component_code = await self._generate_component_code(spec, framework, provider)
            
            # Generate component files
            files = {}
            
            if framework == "react":
                component_name = self._extract_component_name(spec)
                files[f"{component_name}.jsx"] = component_code
                files[f"{component_name}.css"] = await self._generate_component_styles(spec, provider)
                
                # Generate stories for Storybook
                files[f"{component_name}.stories.js"] = await self._generate_component_stories(spec, component_name, provider)
            
            elif framework == "vue":
                component_name = self._extract_component_name(spec)
                files[f"{component_name}.vue"] = component_code
            
            zip_url = await self._create_project_zip(files, f"{framework}_component")
            
            return {
                "zip_url": zip_url,
                "meta": {
                    "framework": framework,
                    "component_name": self._extract_component_name(spec),
                    "file_count": len(files)
                }
            }
            
        except Exception as e:
            logger.error(f"Component generation failed: {e}")
            raise ContentError(f"Component generation failed: {e}", "code")
    
    async def _generate_project_files(self, request: CodeGenerationRequest, provider) -> Dict[str, str]:
        """Generate all project files"""
        files = {}
        
        # Get base template
        template_generator = self.stack_templates[request.stack]
        base_files = template_generator(request)
        files.update(base_files)
        
        # Generate main application logic
        main_code = await self._generate_main_application(request, provider)
        
        # Update main files with generated code
        if request.stack == "nextjs":
            files["pages/index.js"] = main_code
            if "api" in request.features:
                files["pages/api/hello.js"] = await self._generate_api_endpoint(request, provider)
        elif request.stack == "express":
            files["app.js"] = main_code
        elif request.stack == "flask":
            files["app.py"] = main_code
        
        # Generate feature-specific files
        for feature in request.features:
            feature_files = await self._generate_feature_files(feature, request, provider)
            files.update(feature_files)
        
        # Generate tests if requested
        if request.tests:
            test_files = await self._generate_test_files(request, provider)
            files.update(test_files)
        
        return files
    
    async def _generate_main_application(self, request: CodeGenerationRequest, provider) -> str:
        """Generate main application code"""
        prompt = f"""Generate the main application code for a {request.stack} project.

Brief: {request.brief}
Features: {', '.join(request.features)}

Requirements:
- Clean, production-ready code
- Follow {request.stack} best practices
- Include error handling
- Add helpful comments
- Implement the core functionality described in the brief

Generate only the code, no explanations:"""

        result = await provider.generate_text(prompt, max_tokens=2000, temperature=0.3)
        if not result.success:
            raise ContentError(f"Failed to generate main application: {result.error}", "code")
        
        return result.data
    
    async def _generate_api_endpoint(self, request: CodeGenerationRequest, provider) -> str:
        """Generate API endpoint code"""
        prompt = f"""Generate an API endpoint for a {request.stack} project.

Brief: {request.brief}

Create a RESTful API endpoint that supports the main functionality.
Include proper error handling and response formatting.

Generate only the code:"""

        result = await provider.generate_text(prompt, max_tokens=1000, temperature=0.3)
        if not result.success:
            raise ContentError(f"Failed to generate API endpoint: {result.error}", "code")
        
        return result.data
    
    async def _generate_feature_files(self, feature: str, request: CodeGenerationRequest, provider) -> Dict[str, str]:
        """Generate files for a specific feature"""
        files = {}
        
        if feature == "auth":
            files.update(await self._generate_auth_files(request, provider))
        elif feature == "database":
            files.update(await self._generate_database_files(request, provider))
        elif feature == "api":
            files.update(await self._generate_api_files(request, provider))
        elif feature == "ui":
            files.update(await self._generate_ui_files(request, provider))
        
        return files
    
    async def _generate_auth_files(self, request: CodeGenerationRequest, provider) -> Dict[str, str]:
        """Generate authentication-related files"""
        prompt = f"""Generate authentication code for a {request.stack} project.

Include:
- User login/logout functionality
- Session management
- Route protection
- Password hashing (if applicable)

Brief: {request.brief}

Generate the auth module code:"""

        result = await provider.generate_text(prompt, max_tokens=1500, temperature=0.3)
        if not result.success:
            return {}
        
        if request.stack in ["express", "flask"]:
            return {"auth.py" if request.stack == "flask" else "auth.js": result.data}
        elif request.stack == "nextjs":
            return {"lib/auth.js": result.data}
        
        return {}
    
    async def _generate_database_files(self, request: CodeGenerationRequest, provider) -> Dict[str, str]:
        """Generate database-related files"""
        prompt = f"""Generate database configuration and models for a {request.stack} project.

Include:
- Database connection setup
- Data models/schemas
- Basic CRUD operations
- Database initialization

Brief: {request.brief}

Generate the database code:"""

        result = await provider.generate_text(prompt, max_tokens=1500, temperature=0.3)
        if not result.success:
            return {}
        
        if request.stack == "flask":
            return {"models.py": result.data, "database.py": "# Database configuration"}
        elif request.stack == "express":
            return {"models.js": result.data, "database.js": "# Database configuration"}
        
        return {}
    
    async def _generate_api_files(self, request: CodeGenerationRequest, provider) -> Dict[str, str]:
        """Generate API-related files"""
        files = {}
        
        # Generate main API routes
        prompt = f"""Generate RESTful API routes for a {request.stack} project.

Brief: {request.brief}

Create comprehensive API endpoints including:
- GET, POST, PUT, DELETE operations
- Input validation
- Error handling
- Response formatting

Generate the API routes code:"""

        result = await provider.generate_text(prompt, max_tokens=2000, temperature=0.3)
        if result.success:
            if request.stack == "flask":
                files["routes.py"] = result.data
            elif request.stack == "express":
                files["routes.js"] = result.data
            elif request.stack == "nextjs":
                files["pages/api/index.js"] = result.data
        
        return files
    
    async def _generate_ui_files(self, request: CodeGenerationRequest, provider) -> Dict[str, str]:
        """Generate UI component files"""
        files = {}
        
        if request.stack in ["nextjs", "react", "vue", "nuxt"]:
            # Generate main components
            components = ["Header", "Footer", "Navigation", "Layout"]
            
            for component in components:
                prompt = f"""Generate a {component} component for a {request.stack} project.

Brief: {request.brief}

Create a modern, responsive {component} component with:
- Clean design
- Accessibility features
- Proper styling
- Component props

Generate only the component code:"""

                result = await provider.generate_text(prompt, max_tokens=800, temperature=0.4)
                if result.success:
                    if request.stack in ["nextjs", "react"]:
                        files[f"components/{component}.jsx"] = result.data
                    elif request.stack in ["vue", "nuxt"]:
                        files[f"components/{component}.vue"] = result.data
        
        return files
    
    async def _generate_test_files(self, request: CodeGenerationRequest, provider) -> Dict[str, str]:
        """Generate test files"""
        prompt = f"""Generate comprehensive tests for a {request.stack} project.

Brief: {request.brief}
Features: {', '.join(request.features)}

Include:
- Unit tests for main functionality
- Integration tests (if applicable)
- API endpoint tests (if applicable)
- Component tests (if UI framework)

Use appropriate testing framework for {request.stack}.

Generate the test code:"""

        result = await provider.generate_text(prompt, max_tokens=1500, temperature=0.3)
        if not result.success:
            return {}
        
        test_files = {}
        if request.stack == "flask":
            test_files["test_app.py"] = result.data
        elif request.stack == "express":
            test_files["test/app.test.js"] = result.data
        elif request.stack in ["nextjs", "react"]:
            test_files["__tests__/index.test.js"] = result.data
        
        return test_files
    
    async def _generate_readme(self, request: CodeGenerationRequest, files: Dict[str, str], provider) -> str:
        """Generate README documentation"""
        prompt = f"""Generate a comprehensive README.md for a {request.stack} project.

Brief: {request.brief}
Features: {', '.join(request.features)}
Files included: {', '.join(list(files.keys())[:10])}

Include:
- Project description
- Installation instructions
- Usage examples
- API documentation (if applicable)
- Development setup
- Contributing guidelines
- License information

Generate a well-structured README:"""

        result = await provider.generate_text(prompt, max_tokens=2000, temperature=0.4)
        if not result.success:
            return f"# {request.stack.title()} Project\n\n{request.brief}\n\n## Installation\n\nTODO: Add installation instructions"
        
        return result.data
    
    async def _generate_single_file_code(self, spec: str, language: str, provider) -> str:
        """Generate single file code"""
        prompt = f"""Generate {language} code based on the following specification:

{spec}

Requirements:
- Clean, readable code
- Follow {language} best practices
- Include proper error handling
- Add helpful comments
- Make it production-ready

Generate only the code:"""

        result = await provider.generate_text(prompt, max_tokens=1500, temperature=0.3)
        if not result.success:
            raise ContentError(f"Failed to generate {language} code: {result.error}", "code")
        
        return result.data
    
    async def _generate_tests(self, spec: str, language: str, code: str, provider) -> str:
        """Generate tests for code"""
        prompt = f"""Generate comprehensive tests for the following {language} code:

Original specification: {spec}

Code to test:
{code[:1000]}...

Create tests that:
- Cover main functionality
- Test edge cases
- Include error handling tests
- Follow {language} testing best practices

Generate only the test code:"""

        result = await provider.generate_text(prompt, max_tokens=1000, temperature=0.3)
        if not result.success:
            return f"# TODO: Add tests for {language} code"
        
        return result.data
    
    async def _generate_component_code(self, spec: str, framework: str, provider) -> str:
        """Generate UI component code"""
        prompt = f"""Generate a {framework} component based on this specification:

{spec}

Requirements:
- Modern {framework} best practices
- Responsive design
- Accessibility features
- Proper prop types/interfaces
- Clean, maintainable code

Generate only the component code:"""

        result = await provider.generate_text(prompt, max_tokens=1000, temperature=0.4)
        if not result.success:
            raise ContentError(f"Failed to generate {framework} component: {result.error}", "code")
        
        return result.data
    
    async def _generate_component_styles(self, spec: str, provider) -> str:
        """Generate CSS styles for component"""
        prompt = f"""Generate CSS styles for a component with this specification:

{spec}

Create:
- Modern, responsive styles
- Clean design
- Proper hover/focus states
- Mobile-friendly layout

Generate only the CSS:"""

        result = await provider.generate_text(prompt, max_tokens=500, temperature=0.4)
        if not result.success:
            return "/* TODO: Add component styles */"
        
        return result.data
    
    async def _generate_component_stories(self, spec: str, component_name: str, provider) -> str:
        """Generate Storybook stories for component"""
        prompt = f"""Generate Storybook stories for a React component.

Component: {component_name}
Specification: {spec}

Create stories that showcase:
- Default state
- Different prop variations
- Interactive states
- Edge cases

Generate only the stories code:"""

        result = await provider.generate_text(prompt, max_tokens=600, temperature=0.4)
        if not result.success:
            return f"// TODO: Add Storybook stories for {component_name}"
        
        return result.data
    
    def _get_file_extension(self, language: str) -> str:
        """Get file extension for programming language"""
        extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "cpp": "cpp",
            "c": "c",
            "go": "go",
            "rust": "rs",
            "php": "php",
            "ruby": "rb",
            "swift": "swift",
            "kotlin": "kt"
        }
        return extensions.get(language.lower(), "txt")
    
    def _extract_component_name(self, spec: str) -> str:
        """Extract component name from specification"""
        # Simple extraction - look for capitalized words
        words = spec.split()
        for word in words:
            if word[0].isupper() and len(word) > 2:
                return word
        return "Component"
    
    async def _create_project_zip(self, files: Dict[str, str], project_name: str) -> str:
        """Create ZIP file from project files"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
                with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, content in files.items():
                        # Create directory structure
                        zip_file.writestr(f"{project_name}/{filename}", content.encode('utf-8'))
                
                # In a real implementation, upload to R2 and return presigned URL
                zip_path = tmp_file.name
                return f"https://storage.example.com/projects/{project_name}.zip"
        
        except Exception as e:
            logger.error(f"Failed to create project ZIP: {e}")
            raise ContentError(f"Failed to create project ZIP: {e}", "code")
    
    async def _create_gist(self, files: Dict[str, str], description: str) -> str:
        """Create GitHub Gist (placeholder)"""
        # Placeholder implementation
        # In a real implementation, this would create a GitHub Gist
        return f"https://gist.github.com/placeholder/{hash(description)}"
    
    # Stack templates
    
    def _get_nextjs_template(self, request: CodeGenerationRequest) -> Dict[str, str]:
        """Get Next.js project template"""
        return {
            "package.json": json.dumps({
                "name": "nextjs-project",
                "version": "1.0.0",
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start"
                },
                "dependencies": {
                    "next": "^13.0.0",
                    "react": "^18.0.0",
                    "react-dom": "^18.0.0"
                }
            }, indent=2),
            "next.config.js": "module.exports = { reactStrictMode: true };",
            "pages/_app.js": "export default function App({ Component, pageProps }) { return <Component {...pageProps} />; }",
            ".gitignore": "node_modules/\n.next/\nout/\n.env.local"
        }
    
    def _get_express_template(self, request: CodeGenerationRequest) -> Dict[str, str]:
        """Get Express.js project template"""
        return {
            "package.json": json.dumps({
                "name": "express-project",
                "version": "1.0.0",
                "main": "app.js",
                "scripts": {
                    "start": "node app.js",
                    "dev": "nodemon app.js"
                },
                "dependencies": {
                    "express": "^4.18.0",
                    "cors": "^2.8.5",
                    "helmet": "^6.0.0"
                }
            }, indent=2),
            ".gitignore": "node_modules/\n.env\nlogs/"
        }
    
    def _get_flask_template(self, request: CodeGenerationRequest) -> Dict[str, str]:
        """Get Flask project template"""
        return {
            "requirements.txt": "Flask==2.3.0\nFlask-CORS==4.0.0\ngunicorn==20.1.0",
            "config.py": "import os\n\nclass Config:\n    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key'",
            ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/"
        }
    
    def _get_react_template(self, request: CodeGenerationRequest) -> Dict[str, str]:
        """Get React project template"""
        return {
            "package.json": json.dumps({
                "name": "react-project",
                "version": "1.0.0",
                "dependencies": {
                    "react": "^18.0.0",
                    "react-dom": "^18.0.0",
                    "react-scripts": "5.0.0"
                },
                "scripts": {
                    "start": "react-scripts start",
                    "build": "react-scripts build",
                    "test": "react-scripts test"
                }
            }, indent=2),
            "public/index.html": "<!DOCTYPE html><html><head><title>React App</title></head><body><div id=\"root\"></div></body></html>",
            "src/index.js": "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\n\nconst root = ReactDOM.createRoot(document.getElementById('root'));\nroot.render(<App />);",
            ".gitignore": "node_modules/\nbuild/\n.env.local"
        }
    
    def _get_nuxt_template(self, request: CodeGenerationRequest) -> Dict[str, str]:
        """Get Nuxt.js project template"""
        return {
            "package.json": json.dumps({
                "name": "nuxt-project",
                "version": "1.0.0",
                "scripts": {
                    "dev": "nuxt",
                    "build": "nuxt build",
                    "start": "nuxt start"
                },
                "dependencies": {
                    "nuxt": "^3.0.0"
                }
            }, indent=2),
            "nuxt.config.js": "export default { ssr: true };",
            ".gitignore": "node_modules/\n.nuxt/\ndist/"
        }
    
    def _get_vue_template(self, request: CodeGenerationRequest) -> Dict[str, str]:
        """Get Vue.js project template"""
        return {
            "package.json": json.dumps({
                "name": "vue-project",
                "version": "1.0.0",
                "dependencies": {
                    "vue": "^3.0.0"
                },
                "scripts": {
                    "dev": "vite",
                    "build": "vite build"
                }
            }, indent=2),
            "index.html": "<!DOCTYPE html><html><head><title>Vue App</title></head><body><div id=\"app\"></div></body></html>",
            ".gitignore": "node_modules/\ndist/"
        }
    
    def _get_python_template(self, request: CodeGenerationRequest) -> Dict[str, str]:
        """Get Python project template"""
        return {
            "requirements.txt": "# Add your dependencies here",
            "main.py": "# Main application entry point",
            ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/"
        }
    
    def _get_fastapi_template(self, request: CodeGenerationRequest) -> Dict[str, str]:
        """Get FastAPI project template"""
        return {
            "requirements.txt": "fastapi==0.104.0\nuvicorn==0.24.0\npydantic==2.5.0",
            "main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}",
            ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/"
        }
    
    def _get_django_template(self, request: CodeGenerationRequest) -> Dict[str, str]:
        """Get Django project template"""
        return {
            "requirements.txt": "Django==4.2.0\npsycopg2-binary==2.9.5",
            "manage.py": "#!/usr/bin/env python\nimport os\nimport sys\n\nif __name__ == '__main__':\n    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')\n    from django.core.management import execute_from_command_line\n    execute_from_command_line(sys.argv)",
            ".gitignore": "__pycache__/\n*.pyc\n.env\ndb.sqlite3"
        }
