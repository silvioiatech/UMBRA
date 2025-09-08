#!/bin/bash
# Creator v1 Setup Script - PR CRT3
# Configures environment for Creator module

set -e

echo "🎨 Setting up Creator v1 (PR CRT3)..."

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -d "umbra" ]; then
    echo "❌ Please run this script from the Umbra project root directory"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version OK: $python_version"

# Install dependencies
echo "📦 Installing Creator dependencies..."

# Core AI dependencies
pip install -q openai anthropic replicate elevenlabs-python stability-sdk

# Media processing
pip install -q pillow opencv-python-headless moviepy pydub

# Export and storage
pip install -q boto3 httpx zipfile36

# Data processing
pip install -q pandas numpy

echo "✅ Dependencies installed"

# Check environment variables
echo "🔧 Checking environment configuration..."

# Essential variables
essential_vars=(
    "TELEGRAM_BOT_TOKEN"
    "OPENROUTER_API_KEY"
    "R2_ACCOUNT_ID"
    "R2_ACCESS_KEY_ID"
    "R2_SECRET_ACCESS_KEY"
    "R2_BUCKET"
)

missing_essential=()

for var in "${essential_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_essential+=("$var")
    fi
done

if [ ${#missing_essential[@]} -gt 0 ]; then
    echo "❌ Missing essential environment variables:"
    for var in "${missing_essential[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please set these in your .env file or environment"
    exit 1
fi

echo "✅ Essential configuration OK"

# Optional Creator providers
echo "🤖 Checking Creator AI providers..."

optional_vars=(
    "CREATOR_STABILITY_API_KEY"
    "CREATOR_ELEVENLABS_API_KEY"
    "CREATOR_OPENAI_API_KEY"
    "CREATOR_REPLICATE_API_TOKEN"
    "CREATOR_DEEPGRAM_API_KEY"
)

configured_providers=0
total_providers=${#optional_vars[@]}

for var in "${optional_vars[@]}"; do
    if [ ! -z "${!var}" ]; then
        ((configured_providers++))
        echo "✅ $var configured"
    else
        echo "⚪ $var not configured"
    fi
done

echo "📊 Creator Providers: $configured_providers/$total_providers configured"

if [ $configured_providers -eq 0 ]; then
    echo "⚠️  No Creator AI providers configured"
    echo "   Text generation will work via OpenRouter, but media generation will be limited"
fi

# Test basic module import
echo "🧪 Testing Creator module import..."

python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from umbra.modules.creator_mcp import CreatorModule
    print('✅ Creator module import successful')
except ImportError as e:
    print(f'❌ Creator module import failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'⚠️  Creator module import warning: {e}')
"

if [ $? -ne 0 ]; then
    echo "❌ Creator module test failed"
    exit 1
fi

# Test configuration
echo "🔧 Testing Creator configuration..."

python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from umbra.core.config import UmbraConfig
    from umbra.ai.agent import UmbraAIAgent
    from umbra.modules.creator_mcp import CreatorModule
    
    config = UmbraConfig()
    ai_agent = UmbraAIAgent(config)
    creator = CreatorModule(ai_agent, config)
    
    # Test capabilities
    capabilities = creator.get_capabilities()
    actions = capabilities.get('actions', [])
    
    print(f'✅ Creator initialized with {len(actions)} actions')
    
    # Test provider manager
    provider_status = creator.provider_manager.get_configuration_status()
    configured = provider_status['configured_providers']
    active = provider_status['active_instances']
    
    print(f'✅ Provider manager: {configured} configured, {active} active')
    
except Exception as e:
    print(f'❌ Creator configuration test failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Creator configuration test failed"
    exit 1
fi

# Run PR CRT3 validation if test file exists
if [ -f "test_creator_pr_crt3.py" ]; then
    echo "🧪 Running PR CRT3 validation tests..."
    
    python3 test_creator_pr_crt3.py
    
    if [ $? -eq 0 ]; then
        echo "🎉 PR CRT3 validation PASSED!"
    else
        echo "⚠️  PR CRT3 validation had issues (check logs above)"
    fi
else
    echo "⚪ PR CRT3 test file not found (skipping validation)"
fi

# Summary
echo ""
echo "🎉 Creator v1 Setup Complete!"
echo ""
echo "📋 Summary:"
echo "   ✅ Creator module installed and configured"
echo "   ✅ Essential environment variables set"
echo "   📊 $configured_providers/$total_providers AI providers configured"
echo "   🤖 Creator ready for use"
echo ""
echo "🚀 Next steps:"
echo "   1. Start the bot: python3 main.py"
echo "   2. Test Creator: /status in Telegram"
echo "   3. Try Creator commands: send a message to generate content"
echo ""
echo "📚 Documentation:"
echo "   - PR CRT3 completion report: PR_CRT3_COMPLETION_REPORT.md"
echo "   - Creator API docs: umbra/modules/creator/API_DOCUMENTATION.md"
echo ""

# Optional provider setup hints
if [ $configured_providers -lt $total_providers ]; then
    echo "💡 To configure additional AI providers:"
    echo "   - Stability AI (images): CREATOR_STABILITY_API_KEY"
    echo "   - ElevenLabs (TTS): CREATOR_ELEVENLABS_API_KEY" 
    echo "   - OpenAI (multi): CREATOR_OPENAI_API_KEY"
    echo "   - Replicate (multi): CREATOR_REPLICATE_API_TOKEN"
    echo ""
fi

echo "✨ Creator v1 is ready for production! 🎨"
