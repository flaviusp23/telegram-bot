import os
from dotenv import load_dotenv

load_dotenv()

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