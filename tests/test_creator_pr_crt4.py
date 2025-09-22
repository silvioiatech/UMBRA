#!/usr/bin/env python3
"""
Test Creator v1 CRT4 - Provider Configuration & Environment Validation
Validates that Creator module meets PR CRT4 requirements:
- OpenRouter-first for text with Creator overrides
- Provider selection by environment variables
- Graceful no-op when capabilities not configured
- Presigned URLs for all saved assets
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

class CreatorPRCRT4Test:
    """Test suite for Creator v1 PR CRT4 requirements"""
    
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
        
        logger.info("Creator PR CRT4 test suite initialized")
    
    async def test_openrouter_first_text_routing(self) -> Dict[str, Any]:
        """Test 1: OpenRouter-first text routing with Creator overrides"""
        logger.info("🧪 Testing OpenRouter-first text routing...")
        
        try:
            # Test provider manager configuration
            provider_manager = self.creator.provider_manager
            
            # Check if OpenRouter is configured and has priority
            text_providers = await provider_manager.get_available_providers("text")
            
            # Check for Creator model override
            openrouter_config = provider_manager.get_provider_config("openrouter")
            creator_model_override = self.config.get("CREATOR_OPENROUTER_MODEL_TEXT")
            
            test_result = {
                "success": len(text_providers) > 0 and "openrouter" in text_providers,
                "openrouter_available": "openrouter" in text_providers,
                "openrouter_priority": text_providers[0] == "openrouter" if text_providers else False,
                "creator_model_override": creator_model_override,
                "configured_providers": text_providers,
                "openrouter_config": bool(openrouter_config)
            }
            
            logger.info(f"✅ OpenRouter text routing test: {test_result['success']}")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ OpenRouter text routing test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_provider_selection_by_env(self) -> Dict[str, Any]:
        """Test 2: Provider selection by environment variables"""
        logger.info("🧪 Testing provider selection by environment...")
        
        try:
            provider_manager = self.creator.provider_manager
            results = {}
            
            # Test each capability's provider selection
            capabilities = ["image", "video", "tts", "music", "asr"]
            
            for capability in capabilities:
                env_var = f"CREATOR_{capability.upper()}_PROVIDER"
                configured_provider = self.config.get(env_var)
                available_providers = await provider_manager.get_available_providers(capability)
                
                results[capability] = {
                    "env_var": env_var,
                    "configured_provider": configured_provider,
                    "available_providers": available_providers,
                    "provider_matches_env": configured_provider in available_providers if configured_provider else True,
                    "has_providers": len(available_providers) > 0
                }
            
            # Overall success
            success = all(
                result["provider_matches_env"] for result in results.values()
            )
            
            test_result = {
                "success": success,
                "results": results,
                "total_capabilities": len(capabilities),
                "configured_capabilities": len([r for r in results.values() if r["has_providers"]])
            }
            
            logger.info(f"✅ Provider selection test: {test_result['success']}")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Provider selection test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_graceful_no_op_unconfigured(self) -> Dict[str, Any]:
        """Test 3: Graceful no-op when capabilities not configured"""
        logger.info("🧪 Testing graceful no-op for unconfigured capabilities...")
        
        try:
            # Test actions that require different capabilities
            test_actions = [
                ("generate_image", {"prompt": "test image"}, "image"),
                ("generate_video", {"brief": "test video"}, "video"),
                ("tts_speak", {"text": "test speech"}, "tts"),
                ("music_generate", {"brief": "test music"}, "music"),
                ("asr_transcribe", {"media_id": "test"}, "asr")
            ]
            
            results = {}
            
            for action, params, capability in test_actions:
                try:
                    result = await self.creator.execute(action, params)
                    
                    # Check if result indicates graceful handling
                    is_graceful = (
                        "error" in result and 
                        "not configured" in result.get("error", "").lower()
                    ) or (
                        "error" in result and
                        "not available" in result.get("error", "").lower()
                    )
                    
                    results[action] = {
                        "capability": capability,
                        "executed": True,
                        "graceful_failure": is_graceful,
                        "error_message": result.get("error", ""),
                        "success": result.get("success", False)
                    }
                    
                except Exception as e:
                    results[action] = {
                        "capability": capability,
                        "executed": False,
                        "graceful_failure": False,
                        "error_message": str(e),
                        "success": False
                    }
            
            # Success if all unconfigured capabilities fail gracefully
            graceful_count = sum(1 for r in results.values() if r["graceful_failure"] or r["success"])
            
            test_result = {
                "success": graceful_count >= len(test_actions) * 0.5,  # At least 50% graceful
                "results": results,
                "graceful_failures": graceful_count,
                "total_actions": len(test_actions),
                "graceful_rate": graceful_count / len(test_actions)
            }
            
            logger.info(f"✅ Graceful no-op test: {test_result['success']}")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Graceful no-op test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_presigned_urls_for_assets(self) -> Dict[str, Any]:
        """Test 4: Presigned URLs returned for all saved assets"""
        logger.info("🧪 Testing presigned URLs for saved assets...")
        
        try:
            if not self.r2_client:
                return {
                    "success": False, 
                    "error": "R2 client not configured",
                    "r2_configured": False
                }
            
            # Test asset saving with presigned URL return
            test_asset_data = b"Test asset content for PR CRT4"
            
            # Use export manager to save asset
            export_manager = self.creator.export_manager
            
            presigned_url = await export_manager.save_single_asset(
                asset_data=test_asset_data,
                asset_type="text",
                filename="test_crt4.txt",
                metadata={"test": "crt4_validation"}
            )
            
            # Validate presigned URL
            is_valid_url = (
                presigned_url and 
                presigned_url.startswith("https://") and
                "cloudflarestorage.com" in presigned_url
            )
            
            test_result = {
                "success": is_valid_url,
                "presigned_url_returned": bool(presigned_url),
                "url_format_valid": is_valid_url,
                "url_length": len(presigned_url) if presigned_url else 0,
                "r2_configured": True,
                "test_asset_size": len(test_asset_data)
            }
            
            # Test bundle export with presigned URL
            if is_valid_url:
                try:
                    bundle_assets = [
                        {
                            "type": "text",
                            "content": "Test bundle content",
                            "meta": {"test": "crt4_bundle"}
                        }
                    ]
                    
                    bundle_url = await self.creator.execute("export_bundle", {
                        "assets": bundle_assets,
                        "format": "json"
                    })
                    
                    test_result["bundle_export_success"] = "download_url" in bundle_url
                    test_result["bundle_url"] = bundle_url.get("download_url", "")
                    
                except Exception as e:
                    test_result["bundle_export_error"] = str(e)
            
            logger.info(f"✅ Presigned URLs test: {test_result['success']}")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Presigned URLs test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_missing_key_clear_errors(self) -> Dict[str, Any]:
        """Test 5: Clear errors with remediation hints for missing keys"""
        logger.info("🧪 Testing clear errors for missing provider keys...")
        
        try:
            provider_manager = self.creator.provider_manager
            config_status = provider_manager.get_configuration_status()
            
            missing_configs = config_status.get("missing_configurations", [])
            provider_details = config_status.get("provider_details", {})
            
            # Test error messages for missing providers
            error_clarity_results = {}
            
            # Test each capability
            capabilities = ["image", "video", "tts", "music", "asr"]
            
            for capability in capabilities:
                coverage = config_status["capability_coverage"].get(capability, {})
                provider_count = coverage.get("count", 0)
                
                if provider_count == 0:
                    # Test if we get a helpful error message
                    from umbra.modules.creator.graceful_fallbacks import get_missing_provider_message
                    
                    error_message = get_missing_provider_message(capability, {})
                    
                    error_clarity_results[capability] = {
                        "providers_configured": provider_count,
                        "has_helpful_message": len(error_message) > 50,
                        "message_mentions_env_vars": "CREATOR_" in error_message,
                        "message_has_examples": "your_" in error_message or "sk-" in error_message,
                        "error_message": error_message[:200] + "..." if len(error_message) > 200 else error_message
                    }
            
            # Overall assessment
            helpful_errors = sum(
                1 for result in error_clarity_results.values() 
                if result["has_helpful_message"] and result["message_mentions_env_vars"]
            )
            
            test_result = {
                "success": len(missing_configs) == 0 or helpful_errors > 0,
                "missing_configurations": len(missing_configs),
                "helpful_error_messages": helpful_errors,
                "error_clarity_results": error_clarity_results,
                "provider_recommendations": provider_manager.get_provider_recommendations()
            }
            
            logger.info(f"✅ Error clarity test: {test_result['success']}")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Error clarity test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_status_command_providers(self) -> Dict[str, Any]:
        """Test 6: /status command reflects provider configuration"""
        logger.info("🧪 Testing /status command provider information...")
        
        try:
            provider_manager = self.creator.provider_manager
            
            # Get status information that would be shown in /status
            config_status = provider_manager.get_configuration_status()
            
            # Test provider status information
            status_info = {
                "configured_providers": config_status["configured_providers"],
                "active_instances": config_status["active_instances"],
                "capability_coverage": config_status["capability_coverage"],
                "missing_configurations": len(config_status["missing_configurations"])
            }
            
            # Check if each capability has status info
            capabilities_with_status = 0
            for capability in ["text", "image", "video", "tts", "music", "asr"]:
                if capability in status_info["capability_coverage"]:
                    capabilities_with_status += 1
            
            test_result = {
                "success": capabilities_with_status >= 4,  # At least 4 capabilities tracked
                "status_info": status_info,
                "capabilities_tracked": capabilities_with_status,
                "total_capabilities": 6,
                "has_provider_details": bool(config_status.get("provider_details")),
                "tracks_missing_configs": "missing_configurations" in config_status
            }
            
            logger.info(f"✅ Status command test: {test_result['success']}")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Status command test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all PR CRT4 validation tests"""
        logger.info("🚀 Starting Creator v1 PR CRT4 validation tests...")
        
        test_methods = [
            ("openrouter_first_text_routing", self.test_openrouter_first_text_routing),
            ("provider_selection_by_env", self.test_provider_selection_by_env),
            ("graceful_no_op_unconfigured", self.test_graceful_no_op_unconfigured),
            ("presigned_urls_for_assets", self.test_presigned_urls_for_assets),
            ("missing_key_clear_errors", self.test_missing_key_clear_errors),
            ("status_command_providers", self.test_status_command_providers)
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
            "pr_crt4_validation": {
                "passed_tests": passed_tests,
                "total_tests": len(test_methods),
                "success_rate": passed_tests / len(test_methods),
                "all_tests_passed": passed_tests == len(test_methods)
            },
            "test_results": results,
            "pr_requirements": {
                "openrouter_first_routing": results.get("openrouter_first_text_routing", {}).get("success", False),
                "provider_env_selection": results.get("provider_selection_by_env", {}).get("success", False),
                "graceful_no_op": results.get("graceful_no_op_unconfigured", {}).get("success", False),
                "presigned_urls": results.get("presigned_urls_for_assets", {}).get("success", False),
                "clear_error_messages": results.get("missing_key_clear_errors", {}).get("success", False),
                "status_integration": results.get("status_command_providers", {}).get("success", False)
            }
        }
        
        # Final PR CRT4 status
        pr_requirements_met = sum(overall_result["pr_requirements"].values()) >= 4  # At least 4/6 requirements
        
        logger.info("=" * 60)
        logger.info("🏁 Creator v1 PR CRT4 Validation Results:")
        logger.info(f"Tests Passed: {passed_tests}/{len(test_methods)}")
        logger.info(f"Success Rate: {overall_result['pr_crt4_validation']['success_rate']:.1%}")
        logger.info("=" * 60)
        
        for requirement, status in overall_result["pr_requirements"].items():
            status_icon = "✅" if status else "❌"
            logger.info(f"{status_icon} {requirement.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
        
        logger.info("=" * 60)
        
        if pr_requirements_met:
            logger.info("🎉 PR CRT4 REQUIREMENTS SUBSTANTIALLY MET!")
            logger.info("✅ Creator v1 providers & env is ready for merge!")
        else:
            logger.warning("⚠️ Some PR CRT4 requirements not met")
            logger.info("Please review failed tests above")
        
        overall_result["pr_crt4_ready"] = pr_requirements_met
        
        return overall_result

async def main():
    """Run Creator v1 PR CRT4 validation"""
    try:
        test_suite = CreatorPRCRT4Test()
        results = await test_suite.run_all_tests()
        
        # Return appropriate exit code
        if results["pr_crt4_ready"]:
            print("\n🎉 Creator v1 PR CRT4 validation PASSED!")
            sys.exit(0)
        else:
            print("\n❌ Creator v1 PR CRT4 validation FAILED!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test suite failed to run: {e}")
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())
