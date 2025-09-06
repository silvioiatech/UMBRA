# 🤖 UMBRA - Production MCP Bot

A production-ready Telegram bot framework with modular MCP (Model Control Protocol) architecture, designed for Railway deployment.

## 🚀 Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/UMBRA)

### 1. Clone & Deploy
```bash
git clone https://github.com/silvioiatech/UMBRA.git
cd UMBRA
# Deploy to Railway or build Docker image
```

### 2. Configure Environment Variables

Set these **required** variables in Railway:

```bash
# 🤖 Telegram Bot Setup  
TELEGRAM_BOT_TOKEN=your_bot_token_here    # Get from @BotFather
ALLOWED_USER_IDS=123456789,987654321      # Get from @userinfobot  
ALLOWED_ADMIN_IDS=123456789               # Admin user IDs
```

**Optional** features:
```bash
# 🧠 AI Integration
OPENROUTER_API_KEY=your_api_key           # For AI features

# ☁️ Cloud Storage  
R2_ACCOUNT_ID=your_cloudflare_account     # For file storage
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key  
R2_BUCKET=your_bucket_name
```

### 3. Deploy
Railway will automatically build and deploy your bot with the included `Dockerfile` and `railway.yaml` configuration.

## ✨ Features

- 🤖 **Telegram Bot Framework** - Complete bot infrastructure
- 🧠 **AI Integration** - OpenRouter AI support  
- 💰 **Financial Assistant** - Swiss accounting and finance tools
- 🏢 **Business Operations** - Client and project management
- 🎨 **Content Creation** - AI-powered content generation
- ☁️ **Cloud Storage** - Cloudflare R2 integration
- 🔒 **Security** - Built-in permissions and rate limiting

## 🔧 Local Development

```bash
# Clone repository
git clone https://github.com/silvioiatech/UMBRA.git
cd UMBRA

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your tokens

# Run locally
python main.py
```

## 📖 Documentation

- **Health Check**: `/health` endpoint for monitoring
- **Production Logging**: Structured JSON logging
- **Auto-scaling**: Supports Railway's auto-scaling
- **Zero Downtime**: Health checks ensure smooth deployments

## 🐳 Docker

```bash
# Build image
docker build -t umbra .

# Run container  
docker run -d --env-file .env -p 8000:8000 umbra
```

## 🛠️ Architecture

- **Modular Design**: MCP-based module system
- **Production Ready**: Health checks, logging, error handling
- **Scalable**: Stateless design for horizontal scaling
- **Secure**: Permission system and rate limiting

## 📝 License

[MIT License](LICENSE)

---

**Ready for production deployment on Railway in minutes!** 🚂