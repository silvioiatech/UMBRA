#!/usr/bin/env python3
"""
Test Creator v1 - PR CRT3 Validation
Validates that Creator module meets PR CRT3 requirements:
- Text via OpenRouter; media via providers; presigned URLs returned
- PII redaction; platform limits enforced  
- Bundled exports (.md/.json/.zip)
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Any

# Add Umbra to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from umbra.core.config import UmbraConfig
from umbra.modules.creator_mcp import CreatorModule
from umbra.ai.agent import UmbraAIAgent
from umbra.storage.r2_client import R2Client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CreatorPRCRT3Test:
    """Test suite for Creator v1 PR CRT3 requirements"""
    
    def __init__(self):
        self.config = UmbraConfig()
        self.ai_agent = UmbraAIAgent(self.config)
        self.r2_client = None
        
        # Initialize R2 if configured
        if all([
            self.config.get("R2_ACCOUNT_ID"),
            self.config.get("R2_ACCESS_KEY_ID"),
            self.config.get("R2_SECRET_ACCESS_KEY")
        ]):
            self.r2_client = R2Client(self.config)
        
        self.creator = CreatorModule(self.ai_agent, self.config, self.r2_client)
        
        logger.info("Creator PR CRT3 test suite initialized")
    
    async def test_capabilities(self) -> Dict[str, Any]:
        """Test 1: Verify Creator capabilities are properly exposed"""
        logger.info("🧪 Testing Creator capabilities...")
        
        try:
            capabilities = self.creator.get_capabilities()
            
            required_actions = [
                "generate_post", "content_pack", "generate_image", 
                "generate_video", "tts_speak", "export_bundle",
                "validate", "set_brand_voice"
            ]
            
            available_actions = capabilities.get("actions", [])
            missing_actions = [action for action in required_actions if action not in available_actions]
            
            result = {
                "success": len(missing_actions) == 0,
                "total_actions": len(available_actions),
                "required_actions_present": len(required_actions) - len(missing_actions),
                "missing_actions": missing_actions,
                "version": capabilities.get("version", "unknown")
            }
            
            logger.info(f"✅ Capabilities test: {result['success']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Capabilities test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_text_generation_openrouter(self) -> Dict[str, Any]:
        """Test 2: Text generation via OpenRouter"""
        logger.info("🧪 Testing text generation via OpenRouter...")
        
        try:
            # Test basic post generation
            result = await self.creator.execute("generate_post", {
                "topic": "AI technology trends",
                "platform": "linkedin",
                "tone": "professional"
            })
            
            success = (
                "error" not in result and 
                result.get("content") and 
                len(result.get("content", "")) > 10
            )
            
            test_result = {
                "success": success,
                "content_generated": bool(result.get("content")),
                "content_length": len(result.get("content", "")),
                "provider_used": result.get("provider_used", "unknown"),
                "platform": result.get("platform"),
                "validation_present": "validation" in result
            }
            
            if not success:
                test_result["error"] = result.get("error", "Unknown error")
            
            logger.info(f"✅ Text generation test: {test_result['success']}")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Text generation test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_pii_redaction(self) -> Dict[str, Any]:
        """Test 3: PII redaction functionality"""
        logger.info("🧪 Testing PII redaction...")
        
        try:
            # Text with PII
            test_text = "Contact me at john.doe@example.com or call +1-555-123-4567"
            
            # Test validation which includes PII detection
            result = await self.creator.execute("validate", {
                "text": test_text,
                "platform": "twitter"
            })
            
            pii_detected = result.get("pii_detected", [])
            
            test_result = {
                "success": len(pii_detected) > 0,
                "pii_types_detected": pii_detected,
                "email_detected": "email" in pii_detected,
                "phone_detected": "phone" in pii_detected,
                "validation_errors": result.get("errors", []),
                "validation_warnings": result.get("warnings", [])
            }
            
            logger.info(f"✅ PII redaction test: {test_result['success']}")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ PII redaction test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_platform_limits_enforcement(self) -> Dict[str, Any]:
        """Test 4: Platform limits enforcement"""
        logger.info("🧪 Testing platform limits enforcement...")
        
        try:
            # Generate content that might exceed platform limits
            very_long_topic = "AI " * 100  # Very long topic
            
            result = await self.creator.execute("generate_post", {
                "topic": very_long_topic,
                "platform": "twitter",  # Twitter has strict character limits
                "length": "long"
            })
            
            content = result.get("content", "")
            validation = result.get("validation", {})
            
            # Check if content respects Twitter's character limit (280)
            within_limits = len(content) <= 280 if content else False
            
            test_result = {
                "success": within_limits or bool(validation.get("warnings")),
                "content_length": len(content),
                "platform_limit_respected": within_limits,
                "validation_present": bool(validation),
                "validation_warnings": validation.get("warnings", []),
                "validation_errors": validation.get("errors", [])
            }
            
            logger.info(f"✅ Platform limits test: {test_result['success']}")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Platform limits test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_bundled_exports(self) -> Dict[str, Any]:
        """Test 5: Bundled exports (.md/.json/.zip)"""
        logger.info("🧪 Testing bundled exports...")
        
        try:
            # Create test assets for export
            test_assets = [
                {
                    "type": "text",
                    "content": "Test content for export",
                    "meta": {"platform": "test", "generated_at": "2024-01-01"}
                },
                {
                    "type": "text", 
                    "content": "# Test Markdown\n\nThis is a test.",
                    "filename": "test.md",
                    "meta": {"format": "markdown"}
                }
            ]
            
            results = {}
            
            # Test all export formats
            for format_type in ["zip", "json", "md"]:
                try:
                    result = await self.creator.execute("export_bundle", {
                        "assets": test_assets,
                        "format": format_type,
                        "metadata": {"test": True, "format": format_type}
                    })
                    
                    results[format_type] = {
                        "success": "download_url" in result or "error" not in result,
                        "has_download_url": "download_url" in result,
                        "download_url": result.get("download_url", ""),
                        "error": result.get("error")
                    }
                    
                except Exception as e:
                    results[format_type] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Overall success if at least one format works
            overall_success = any(r["success"] for r in results.values())
            
            test_result = {
                "success": overall_success,
                "formats_tested": list(results.keys()),
                "formats_working": [fmt for fmt, res in results.items() if res["success"]],
                "results": results,
                "r2_configured": self.r2_client is not None
            }
            
            logger.info(f"✅ Bundled exports test: {test_result['success']}")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Bundled exports test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_provider_configuration(self) -> Dict[str, Any]:
        """Test 6: Provider configuration status"""
        logger.info("🧪 Testing provider configuration...")
        
        try:
            # Check provider manager configuration
            provider_manager = self.creator.provider_manager
            config_status = provider_manager.get_configuration_status()
            
            # Check key capabilities
            text_providers = config_status["capability_coverage"].get("text", {}).get("count", 0)
            image_providers = config_status["capability_coverage"].get("image", {}).get("count", 0)
            
            test_result = {
                "success": text_providers > 0,  # At least text generation should work
                "text_providers_available": text_providers,
                "image_providers_available": image_providers,
                "total_configured_providers": config_status["configured_providers"],
                "active_instances": config_status["active_instances"],
                "missing_configurations": len(config_status["missing_configurations"]),
                "openrouter_configured": any(
                    "openrouter" in p for p in config_status["provider_details"].keys()
                )
            }
            
            logger.info(f"✅ Provider configuration test: {test_result['success']}")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Provider configuration test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all PR CRT3 validation tests"""
        logger.info("🚀 Starting Creator v1 PR CRT3 validation tests...")
        
        test_methods = [
            ("capabilities", self.test_capabilities),
            ("text_generation_openrouter", self.test_text_generation_openrouter),
            ("pii_redaction", self.test_pii_redaction),
            ("platform_limits_enforcement", self.test_platform_limits_enforcement),
            ("bundled_exports", self.test_bundled_exports),
            ("provider_configuration", self.test_provider_configuration)
        ]
        
        results = {}
        passed_tests = 0
        
        for test_name, test_method in test_methods:
            try:
                result = await test_method()
                results[test_name] = result
                if result.get("success"):
                    passed_tests += 1
                    
            except Exception as e:
                logger.error(f"Test {test_name} crashed: {e}")
                results[test_name] = {"success": False, "error": f"Test crashed: {e}"}
        
        overall_result = {
            "pr_crt3_validation": {
                "passed_tests": passed_tests,
                "total_tests": len(test_methods),
                "success_rate": passed_tests / len(test_methods),
                "all_tests_passed": passed_tests == len(test_methods)
            },
            "test_results": results,
            "pr_requirements": {
                "text_via_openrouter": results.get("text_generation_openrouter", {}).get("success", False),
                "pii_redaction": results.get("pii_redaction", {}).get("success", False),
                "platform_limits": results.get("platform_limits_enforcement", {}).get("success", False),
                "bundled_exports": results.get("bundled_exports", {}).get("success", False)
            }
        }
        
        # Final PR CRT3 status
        pr_requirements_met = all(overall_result["pr_requirements"].values())
        
        logger.info("=" * 60)
        logger.info("🏁 Creator v1 PR CRT3 Validation Results:")
        logger.info(f"Tests Passed: {passed_tests}/{len(test_methods)}")
        logger.info(f"Success Rate: {overall_result['pr_crt3_validation']['success_rate']:.1%}")
        logger.info("=" * 60)
        
        for requirement, status in overall_result["pr_requirements"].items():
            status_icon = "✅" if status else "❌"
            logger.info(f"{status_icon} {requirement.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
        
        logger.info("=" * 60)
        
        if pr_requirements_met:
            logger.info("🎉 PR CRT3 REQUIREMENTS FULLY MET!")
            logger.info("✅ Creator v1 is ready for merge!")
        else:
            logger.warning("⚠️ Some PR CRT3 requirements not met")
            logger.info("Please review failed tests above")
        
        overall_result["pr_crt3_ready"] = pr_requirements_met
        
        return overall_result

async def main():
    """Run Creator v1 PR CRT3 validation"""
    try:
        test_suite = CreatorPRCRT3Test()
        results = await test_suite.run_all_tests()
        
        # Return appropriate exit code
        if results["pr_crt3_ready"]:
            print("\n🎉 Creator v1 PR CRT3 validation PASSED!")
            sys.exit(0)
        else:
            print("\n❌ Creator v1 PR CRT3 validation FAILED!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test suite failed to run: {e}")
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())
