# 🚂 Railway Deployment Guide

## Quick Deploy to Railway

1. **Fork this repository** to your GitHub account

2. **Connect to Railway**:
   - Go to [Railway](https://railway.app)
   - Click "New Project" 
   - Select "Deploy from GitHub repo"
   - Choose your forked UMBRA repository

3. **Configure Environment Variables**:
   In Railway dashboard, add these variables:

   **Required:**
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ALLOWED_USER_IDS=123456789,987654321  
   ALLOWED_ADMIN_IDS=123456789
   ```

   **Optional (for enhanced features):**
   ```
   OPENROUTER_API_KEY=your_api_key
   R2_ACCOUNT_ID=your_cloudflare_account
   R2_ACCESS_KEY_ID=your_access_key
   R2_SECRET_ACCESS_KEY=your_secret_key
   R2_BUCKET=your_bucket_name
   ```

4. **Deploy**: Railway will automatically build and deploy your bot

5. **Verify**: Check the logs to ensure successful deployment

## Getting Your Tokens

### Telegram Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Type `/newbot`
3. Follow instructions to create your bot
4. Copy the token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### User IDs  
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your user ID
3. Add your user ID to both `ALLOWED_USER_IDS` and `ALLOWED_ADMIN_IDS`

## Health Check

Once deployed, your bot will be available at:
- **Health endpoint**: `https://your-app.railway.app/health`
- **Bot**: Start a chat with your bot on Telegram

## Features Available

- ✅ **Core Bot**: `/start`, `/help`, `/status`
- ✅ **Financial Assistant**: Expense tracking and Swiss tax features
- ✅ **Business Operations**: Client and project management
- ✅ **AI Integration**: (with OPENROUTER_API_KEY)
- ✅ **Cloud Storage**: (with R2 credentials)

## Troubleshooting

**Bot not responding?**
- Check Railway logs for errors
- Verify TELEGRAM_BOT_TOKEN is correct
- Ensure your user ID is in ALLOWED_USER_IDS

**Features missing?**
- Add optional environment variables for full functionality
- Check bot permissions if commands don't work

---

**Your bot is now production-ready on Railway!** 🎉