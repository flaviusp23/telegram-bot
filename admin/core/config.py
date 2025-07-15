"""
Admin configuration module using pydantic-settings.

This module provides:
- Environment variable loading with proper validation
- Configuration management for the admin panel
- Settings for database, JWT, CORS, and server configuration
- Singleton settings instance
"""

import os
from typing import List, Optional
from datetime import timedelta

from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses pydantic-settings for automatic validation and type conversion.
    """
    
    # Environment settings
    ENVIRONMENT: str = Field(default="DEV", description="Application environment (DEV/PROD)")
    
    # Server settings
    ADMIN_HOST: str = Field(default="127.0.0.1", description="Admin server host")
    ADMIN_PORT: int = Field(default=8000, description="Admin server port")
    
    # Database settings
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_USER: str = Field(default="root", description="Database username")
    DB_PASSWORD: str = Field(default="", description="Database password")
    DB_NAME: str = Field(default="diabetes_monitoring", description="Database name")
    DB_PORT: int = Field(default=3306, description="Database port")
    
    # Security settings
    SECRET_KEY: str = Field(alias="ADMIN_SECRET_KEY", description="Secret key for JWT encoding")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"], description="Allowed HTTP methods")
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], description="Allowed HTTP headers")
    
    # Admin settings
    ADMIN_TELEGRAM_IDS: List[str] = Field(default=[], description="Telegram IDs with admin access")
    ADMIN_DEFAULT_USERNAME: str = Field(default="admin", description="Default admin username")
    ADMIN_DEFAULT_EMAIL: str = Field(default="admin@localhost", description="Default admin email")
    
    # API settings
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 route prefix")
    API_TITLE: str = Field(default="Diabetes Monitor Admin API", description="API title")
    API_VERSION: str = Field(default="1.0.0", description="API version")
    
    # Encryption settings (from main app)
    ENCRYPTION_KEY: Optional[str] = Field(default=None, description="Encryption key for sensitive data")
    
    # Pagination settings
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="Default page size for pagination")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum page size for pagination")
    
    # File upload settings
    MAX_UPLOAD_SIZE: int = Field(default=10485760, description="Maximum file upload size in bytes (10MB)")
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = Field(
        default=["jpg", "jpeg", "png", "pdf", "xlsx", "xls", "csv"],
        description="Allowed file upload extensions"
    )
    
    # Session settings
    SESSION_COOKIE_NAME: str = Field(default="admin_session", description="Session cookie name")
    SESSION_COOKIE_SECURE: bool = Field(default=False, description="Require HTTPS for session cookie")
    SESSION_COOKIE_HTTPONLY: bool = Field(default=True, description="HTTP only session cookie")
    SESSION_COOKIE_SAMESITE: str = Field(default="lax", description="SameSite cookie policy")
    
    # Rate limiting settings
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_LOGIN_PER_MINUTE: int = Field(default=5, description="Login attempts per minute")
    RATE_LIMIT_API_PER_MINUTE: int = Field(default=120, description="API requests per minute")
    RATE_LIMIT_GLOBAL_PER_MINUTE: int = Field(default=300, description="Global requests per minute per IP")
    
    # Request validation settings
    MAX_REQUEST_SIZE: int = Field(default=1048576, description="Maximum request size in bytes (1MB)")
    REQUEST_VALIDATION_ENABLED: bool = Field(default=True, description="Enable request validation")
    
    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate that SECRET_KEY is set and secure."""
        if not v or v == "your-secret-key-here":
            raise ValueError(
                "SECRET_KEY must be set in environment variables. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long for security")
        return v
    
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate and normalize environment setting."""
        v = v.upper()
        if v not in ['DEV', 'PROD']:
            raise ValueError("ENVIRONMENT must be either 'DEV' or 'PROD'")
        return v
    
    @field_validator('ADMIN_TELEGRAM_IDS', mode='before')
    @classmethod
    def parse_admin_telegram_ids(cls, v: any) -> List[str]:
        """Parse comma-separated admin telegram IDs."""
        if isinstance(v, str):
            return [id.strip() for id in v.split(',') if id.strip()]
        elif isinstance(v, list):
            return v
        return []
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: any) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        elif isinstance(v, list):
            return v
        return []
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == 'PROD'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == 'DEV'
    
    @property
    def database_url(self) -> str:
        """Build database connection URL."""
        return f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def access_token_expire_timedelta(self) -> timedelta:
        """Get access token expiration as timedelta."""
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    @property
    def refresh_token_expire_timedelta(self) -> timedelta:
        """Get refresh token expiration as timedelta."""
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
    
    def get_cors_origins(self) -> List[str]:
        """
        Get CORS origins based on environment.
        
        In production, uses configured origins.
        In development, includes additional localhost ports.
        """
        origins = self.CORS_ORIGINS.copy()
        
        if self.is_development:
            # Add common development ports
            dev_origins = [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000",
                "http://127.0.0.1:8080",
            ]
            for origin in dev_origins:
                if origin not in origins:
                    origins.append(origin)
        
        return origins
    
    def validate_file_extension(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in self.ALLOWED_UPLOAD_EXTENSIONS
    
    def validate_file_size(self, size: int) -> bool:
        """Check if file size is within limits."""
        return 0 < size <= self.MAX_UPLOAD_SIZE
    
    def get_rate_limit_rules(self) -> dict:
        """Get rate limit rules configuration."""
        return {
            "/api/v1/auth/login": (self.RATE_LIMIT_LOGIN_PER_MINUTE, 60),
            "/api/v1/auth/refresh": (self.RATE_LIMIT_LOGIN_PER_MINUTE * 2, 60),
            "/api/v1/auth/change-password": (3, 60),
            "default": (self.RATE_LIMIT_API_PER_MINUTE, 60)
        }


# Create singleton settings instance
settings = Settings()


# Export commonly used settings for convenience
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
DATABASE_URL = settings.database_url


# Validation function to ensure critical settings are properly configured
def validate_settings():
    """
    Validate critical settings on application startup.
    
    Raises:
        ValueError: If any critical setting is missing or invalid
    """
    critical_settings = {
        'SECRET_KEY': settings.SECRET_KEY,
        'DB_HOST': settings.DB_HOST,
        'DB_USER': settings.DB_USER,
        'DB_NAME': settings.DB_NAME,
    }
    
    for name, value in critical_settings.items():
        if not value:
            raise ValueError(f"{name} must be set in environment variables")
    
    # Additional validation for production
    if settings.is_production:
        if not settings.DB_PASSWORD:
            raise ValueError("DB_PASSWORD must be set in production environment")
        
        if settings.SESSION_COOKIE_SECURE is False:
            print("WARNING: SESSION_COOKIE_SECURE should be True in production")
        
        if "localhost" in settings.CORS_ORIGINS or "127.0.0.1" in settings.CORS_ORIGINS:
            print("WARNING: localhost/127.0.0.1 in CORS_ORIGINS in production environment")
    
    print(f"Settings validated successfully for {settings.ENVIRONMENT} environment")


# Run validation when module is imported
if __name__ != "__main__":
    try:
        validate_settings()
    except ValueError as e:
        print(f"Configuration error: {e}")
        raise