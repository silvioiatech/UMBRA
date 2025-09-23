# UMBRA 🎭

**Universal Multi-Bot Reasoning Assistant**

A comprehensive AI-powered platform combining Swiss-focused financial assistance, content creation, VPS management, and business orchestration with privacy-first architecture and Railway deployment.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

## 🎯 What is UMBRA?

UMBRA is a modular AI assistant platform that provides:

- **🇨🇭 Swiss Accountant**: OCR-powered expense tracking, QR-bill processing, and tax compliance
- **🎨 Creator**: Multi-modal content generation (text, images, video, audio, music)
- **🛠️ Concierge**: VPS management with Docker operations and system monitoring
- **💼 Business**: Client lifecycle management and instance orchestration
- **🏭 Production**: n8n workflow automation and orchestration
- **💬 General Chat**: AI-powered conversations with OpenRouter integration

All modules feature comprehensive security (RBAC), observability (Prometheus metrics), and audit compliance.

## 🚀 Quick Start

### 1-Click Railway Deployment

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

### Manual Deployment

1. **Clone & Setup**
   ```bash
   git clone https://github.com/silvioiatech/UMBRA.git
   cd UMBRA
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Configure Environment**
   ```bash
   # Required: Telegram Bot
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ALLOWED_USER_IDS=["user_id_1", "user_id_2"]
   ALLOWED_ADMIN_IDS=["admin_user_id"]

   # Required: OpenRouter AI
   OPENROUTER_API_KEY=your_openrouter_api_key
   OPENROUTER_DEFAULT_MODEL=anthropic/claude-3.5-sonnet:beta

   # Required: R2 Storage
   R2_ACCOUNT_ID=your_cloudflare_account_id
   R2_ACCESS_KEY_ID=your_r2_access_key
   R2_SECRET_ACCESS_KEY=your_r2_secret_key
   R2_BUCKET=your_bucket_name
   R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
   ```

3. **Deploy to Railway**
   ```bash
   # Connect your GitHub repo to Railway
   # Railway will auto-deploy using the Dockerfile
   # Set environment variables in Railway dashboard
   ```

4. **Verify Deployment**
   ```bash
   # Check health endpoint
   curl https://your-app.railway.app/health

   # Test in Telegram
   /start
   /status
   ```

## 🏗️ Architecture

### Core Components

```
UMBRA/
├── umbra/                   # Main application package
│   ├── core/                # F1-F4R2: Core runtime, AI, storage
│   │   ├── config.py        # Configuration management
│   │   ├── rbac.py          # Role-based access control
│   │   ├── metrics.py       # Prometheus metrics
│   │   ├── audit.py         # Audit trail system
│   │   └── logging_mw.py    # Structured logging
│   ├── modules/             # Business modules
│   │   ├── swiss_accountant/# Swiss tax & finance assistant
│   │   ├── creator/         # Multi-modal content generation
│   │   ├── concierge/       # VPS management & Docker ops
│   │   ├── business/        # Client lifecycle management
│   │   └── production/      # n8n workflow orchestration
│   ├── storage/             # F4R2: R2-first storage
│   ├── ai/                  # F3R1: OpenRouter integration
│   └── bot.py              # F2: Telegram bot interface
├── tests/                   # All test files
├── demos/                   # Demo and example files
├── scripts/                 # Setup and utility scripts
├── docs/                    # Documentation files
├── Dockerfile              # Railway deployment
├── main.py                 # Application entry point
└── quickstart.py           # Quick start script
```

### Technology Stack

- **Runtime**: Python 3.11+ with FastAPI
- **AI**: OpenRouter (Claude, GPT, Gemini)
- **Storage**: Cloudflare R2 (S3-compatible)
- **Database**: SQLite with F4R2 architecture
- **Deployment**: Railway with Docker
- **Monitoring**: Prometheus metrics + structured logging
- **Security**: RBAC + audit trail + data redaction

## 📋 Module Overview

| Module | Status | Description | Key Features |
|--------|--------|-------------|--------------|
| **F1-F4R2** | ✅ | Core runtime + AI + storage | Railway deployment, OpenRouter, R2 storage |
| **Swiss Accountant** | ✅ | Financial assistance | OCR receipts, QR-bills, tax reports, VAT compliance |
| **Creator** | ✅ | Content generation | Text, images, video, audio, music, transcription |
| **Concierge** | ✅ | VPS management | Docker ops, system monitoring, file management |
| **Business** | ✅ | Client management | Instance gateway, lifecycle management |
| **Production** | ✅ | Workflow automation | n8n integration, workflow orchestration |
| **Security (SEC1)** | ✅ | Security & observability | RBAC, metrics, audit, redaction |

## ⚙️ Configuration

### Required Environment Variables

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
ALLOWED_USER_IDS=["123456789", "987654321"]
ALLOWED_ADMIN_IDS=["123456789"]

# OpenRouter AI Configuration
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_DEFAULT_MODEL=anthropic/claude-3.5-sonnet:beta

# R2 Storage Configuration
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET=umbra-storage
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com

# System Configuration
LOCALE_TZ=Europe/Zurich
PRIVACY_MODE=strict
RATE_LIMIT_PER_MIN=20
```

### Optional: Creator Providers

```bash
# Image Generation
CREATOR_IMAGE_PROVIDER=stability  # stability|openai|replicate
CREATOR_STABILITY_API_KEY=sk-...
CREATOR_OPENAI_API_KEY=sk-...
CREATOR_REPLICATE_API_TOKEN=r8_...

# Video Generation
CREATOR_VIDEO_PROVIDER=pika      # pika|runway|replicate
CREATOR_PIKA_API_KEY=pika_...
CREATOR_RUNWAY_API_KEY=rw_...

# Audio & Music
CREATOR_TTS_PROVIDER=elevenlabs  # elevenlabs|openai
CREATOR_ELEVENLABS_API_KEY=...
CREATOR_MUSIC_PROVIDER=suno      # suno|replicate
CREATOR_SUNO_API_KEY=...

# Speech Recognition
CREATOR_ASR_PROVIDER=deepgram    # deepgram|openai
CREATOR_DEEPGRAM_API_KEY=...
```

### Optional: Production Module

```bash
# n8n MCP Server (Railway-hosted) - RECOMMENDED
N8N_MCP_SERVER_URL=https://your-n8n-mcp.railway.app
N8N_MCP_API_KEY=your_mcp_api_key

# Legacy n8n Direct Connection (optional fallback)
MAIN_N8N_URL=https://your-n8n.railway.app
```

## 🔧 Usage Examples

### Telegram Commands

```bash
# General
/start                    # Welcome message
/help                     # Command overview
/status                   # System status

# Swiss Accountant
"Upload receipt"          # OCR processing
"Monthly report"          # Financial summary
"Tax export 2024"         # Tax authority export

# Creator
"Generate image: sunset"  # Image creation
"Create video script"     # Text generation
"Transcribe audio"        # Speech-to-text

# Concierge (Admin only)
"System status"           # VPS monitoring
"Docker containers"       # Container management
"File backup"             # File operations
```

### API Usage

```python
from umbra.modules.swiss_accountant_mcp import SwissAccountantMCP

# Initialize module
accountant = SwissAccountantMCP()

# Process receipt
result = await accountant.execute('ingest_document', {
    'user_id': 'user123',
    'file_path': '/uploads/receipt.pdf'
})

# Generate monthly report
report = await accountant.execute('monthly_report', {
    'user_id': 'user123',
    'year': 2024,
    'month': 9
})
```

## 📊 Monitoring

### Health Checks

```bash
# Main application
GET /health              # General health
GET /health/ready        # Readiness check
GET /health/live         # Liveness check

# Metrics server (port 9090)
GET /metrics             # Prometheus metrics
GET /metrics?format=json # JSON format
GET /metrics/summary     # Human-readable summary
```

### Key Metrics

- `umbra_requests_total` - Request counts by module
- `umbra_request_duration_seconds` - Performance metrics
- `umbra_module_health` - Module availability
- `umbra_creator_costs_usd` - AI operation costs
- `umbra_rbac_checks_total` - Security metrics

### Logs

UMBRA uses structured JSON logging with automatic request tracking:

```json
{
  "timestamp": "2024-09-08T10:30:00Z",
  "level": "INFO",
  "request_id": "req_abc123",
  "user_id": "123456789",
  "module": "swiss_accountant",
  "action": "ingest_document",
  "message": "Document processed successfully"
}
```

## 🔐 Security

### Role-Based Access Control

- **User Role**: Access to general functionality
- **Admin Role**: Full access including management operations
- **Module-specific permissions**: Fine-grained access control

### Data Protection

- **PII Redaction**: Automatic masking of sensitive data
- **Audit Trail**: Immutable activity logging
- **Encrypted Storage**: Secure R2 storage with access controls
- **Request Isolation**: User-scoped data access

### Compliance

- **GDPR Compatible**: Data portability and deletion rights
- **Swiss Banking Secrecy**: Financial data protection
- **Audit Compliance**: Comprehensive event logging

## 🧪 Development

### Local Setup

```bash
# Clone repository
git clone https://github.com/silvioiatech/UMBRA.git
cd UMBRA

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Run locally
python main.py

# Or with Docker
docker build -t umbra .
docker run --env-file .env -p 8000:8000 umbra
```

### Testing

```bash
# Run all tests
python -m pytest tests/

# Test specific modules
python tests/test_swiss_accountant.py
python tests/test_creator_pr_crt3.py
python tests/f4r2_integration_test.py

# System integration test
python tests/system_test.py
```

### Module Development

```python
from umbra.core.module import BaseModule

class MyModule(BaseModule):
    def __init__(self):
        super().__init__("my_module")
    
    async def handle_command(self, update, context):
        # Your module logic here
        pass
```

## 📚 Documentation

### Main Documentation
- [Architecture Overview](./docs/ARCHITECTURE.md)
- [Project Map](./docs/PROJECT_MAP.md)
- [Action Plan](./docs/ACTION_PLAN.md)

### Module Documentation
- [F3R1 AI Integration](./docs/F3R1_README.md)
- [F4R2 Storage](./docs/F4R2_README.md)
- [Swiss Accountant](./umbra/modules/swiss_accountant/README.md)
- [Creator Module](./docs/CREATOR_README.md)
- [Production Module & N8n MCP Integration](./docs/N8N_MCP_INTEGRATION.md)
- [Security Documentation](./docs/PR_SEC1_COMPLETION_REPORT.md)

### Directory Structure
- [`/tests`](./tests/README.md) - All test files and testing documentation
- [`/demos`](./demos/README.md) - Demo and example files
- [`/scripts`](./scripts/README.md) - Setup and utility scripts
- [`/docs`](./docs/README.md) - Complete project documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the docs/ directory
- **Issues**: Create a GitHub issue
- **Community**: Join our discussions

## 🚀 Railway Deployment

### One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

### Manual Railway Setup

1. **Connect Repository**
   - Fork this repository
   - Connect to Railway dashboard
   - Select your forked repository

2. **Configure Environment**
   - Add all required environment variables
   - Ensure Telegram bot token is set
   - Configure OpenRouter and R2 credentials

3. **Deploy**
   - Railway automatically builds using Dockerfile
   - Monitor deployment logs
   - Test `/health` endpoint

4. **Verify**
   ```bash
   # Check deployment
   curl https://your-app.railway.app/health
   
   # Test Telegram bot
   /start
   /status verbose
   ```

### Environment Setup

Copy `.env.example` to set up your environment variables. All major providers are supported with graceful fallbacks.

---

**Built with ❤️ for the Swiss community and beyond**

*UMBRA: Where AI meets Swiss precision in financial management, content creation, and system administration.*