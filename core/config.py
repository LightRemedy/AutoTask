import os

# Test configuration - DO NOT USE IN PRODUCTION
# Replace these with your actual test bot token and chat ID
TELEGRAM_BOT_TOKEN = "7928217263:AAFR60EKzxRE4td2LSkvQK0425Ss9bwOOdU"  # Example test token
TELEGRAM_CHAT_ID = "325917353"  # Example test chat ID

# Validate required environment variables
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Warning: Telegram configuration is incomplete. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file") 