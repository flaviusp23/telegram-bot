"""Environment variable validators for the diabetes monitoring system.

This module provides validation functions to ensure all required environment
variables are properly set before the application starts.
"""
import os
import sys
from typing import List, Tuple


class EnvironmentValidationError(Exception):
    """Raised when environment validation fails"""
    pass


def validate_environment() -> None:
    """Validate all required environment variables.
    
    Checks that all required environment variables are set and valid.
    Raises EnvironmentValidationError with detailed messages if validation fails.
    """
    errors: List[str] = []
    
    # Check BOT_TOKEN
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        errors.append("BOT_TOKEN is not set. This is required for Telegram bot authentication.")
    elif len(bot_token.strip()) == 0:
        errors.append("BOT_TOKEN is set but empty. Please provide a valid Telegram bot token.")
    elif not ':' in bot_token:
        errors.append("BOT_TOKEN appears to be invalid. It should contain a colon (:) character.")
    
    # Check ENCRYPTION_KEY
    encryption_key = os.getenv('ENCRYPTION_KEY')
    if not encryption_key:
        errors.append("ENCRYPTION_KEY is not set. This is required for encrypting sensitive data.")
    elif len(encryption_key.strip()) == 0:
        errors.append("ENCRYPTION_KEY is set but empty. Please provide a valid encryption key.")
    elif len(encryption_key) < 32:
        errors.append("ENCRYPTION_KEY is too short. It should be at least 32 characters for security.")
    
    # Check database credentials
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    
    if not db_host:
        errors.append("DB_HOST is not set. This is required for database connection.")
    elif len(db_host.strip()) == 0:
        errors.append("DB_HOST is set but empty. Please provide a valid database host.")
    
    if not db_user:
        errors.append("DB_USER is not set. This is required for database authentication.")
    elif len(db_user.strip()) == 0:
        errors.append("DB_USER is set but empty. Please provide a valid database username.")
    
    if db_password is None:  # Allow empty password for some databases
        errors.append("DB_PASSWORD is not set. This is required for database authentication.")
    
    if not db_name:
        errors.append("DB_NAME is not set. This is required to specify which database to use.")
    elif len(db_name.strip()) == 0:
        errors.append("DB_NAME is set but empty. Please provide a valid database name.")
    
    # Check optional but recommended variables
    warnings: List[str] = []
    
    environment = os.getenv('ENVIRONMENT')
    if not environment:
        warnings.append("ENVIRONMENT is not set. Defaulting to 'DEV' mode.")
    elif environment.upper() not in ['DEV', 'PROD']:
        warnings.append(f"ENVIRONMENT is set to '{environment}' which is not recognized. Use 'DEV' or 'PROD'.")
    
    # Check if .env file exists (helpful hint)
    if errors and not os.path.exists('.env'):
        errors.append("\nHint: No .env file found. Create one with the required variables or set them in your environment.")
    
    # Print warnings
    if warnings:
        print("\n⚠️  Environment Variable Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    # Raise error if any validation failed
    if errors:
        error_message = "\n❌ Environment Validation Failed!\n\n"
        error_message += "The following required environment variables are missing or invalid:\n\n"
        for error in errors:
            error_message += f"  - {error}\n"
        
        error_message += "\n📝 Required Environment Variables:\n"
        error_message += "  - BOT_TOKEN: Your Telegram bot token\n"
        error_message += "  - ENCRYPTION_KEY: A secure key for data encryption (min 32 chars)\n"
        error_message += "  - DB_HOST: Database server hostname\n"
        error_message += "  - DB_USER: Database username\n"
        error_message += "  - DB_PASSWORD: Database password\n"
        error_message += "  - DB_NAME: Database name\n"
        error_message += "\n📝 Optional Environment Variables:\n"
        error_message += "  - ENVIRONMENT: 'DEV' or 'PROD' (defaults to 'DEV')\n"
        error_message += "  - OPENAI_API_KEY: For AI features (optional)\n"
        error_message += "  - ADMIN_TELEGRAM_IDS: Comma-separated admin Telegram IDs\n"
        
        raise EnvironmentValidationError(error_message)
    
    print("✅ Environment validation passed!")


def validate_database_url() -> str:
    """Construct and validate database URL.
    
    Returns:
        str: The constructed database URL
        
    Raises:
        EnvironmentValidationError: If database URL cannot be constructed
    """
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'diabetes_monitoring')
    
    # Construct the database URL
    if db_password:
        db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
    else:
        db_url = f"mysql+pymysql://{db_user}@{db_host}/{db_name}"
    
    return db_url


if __name__ == "__main__":
    """Allow running this module directly for testing"""
    try:
        validate_environment()
        print("\n🔗 Database URL:", validate_database_url())
    except EnvironmentValidationError as e:
        print(e)
        sys.exit(1)