import os
from dotenv import load_dotenv
from bot_config.validators import validate_environment

load_dotenv()

# Validate environment variables before proceeding
validate_environment()

# Environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'DEV').upper()  # DEV or PROD
IS_PRODUCTION = ENVIRONMENT == 'PROD'
IS_DEVELOPMENT = ENVIRONMENT == 'DEV'

# Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Database
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'diabetes_monitoring')

# Encryption
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# LLM (optional for now)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Admin settings
# Comma-separated list of telegram IDs that have admin access
ADMIN_TELEGRAM_IDS = os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if os.getenv('ADMIN_TELEGRAM_IDS') else []