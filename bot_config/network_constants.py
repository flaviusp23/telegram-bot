"""Network and API related constants for the diabetes monitoring system"""

class NetworkSettings:
    """Constants for network operations"""
    # Connection timeouts
    DEFAULT_TIMEOUT = 30  # seconds
    CONNECT_TIMEOUT = 10  # seconds
    READ_TIMEOUT = 30    # seconds
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    RETRY_BACKOFF_FACTOR = 2  # exponential backoff
    
    # Connection pool
    CONNECTION_POOL_SIZE = 10
    CONNECTION_MAX_SIZE = 20
    
    # Keep-alive settings
    KEEPALIVE_TIMEOUT = 5
    KEEPALIVE_INTERVAL = 30
    
    # Request limits
    MAX_REQUEST_SIZE_MB = 10
    MAX_RESPONSE_SIZE_MB = 50
    
    # Chunk sizes
    DOWNLOAD_CHUNK_SIZE = 8192  # 8KB
    UPLOAD_CHUNK_SIZE = 4096    # 4KB


class TelegramSettings:
    """Constants specific to Telegram Bot API"""
    # API limits
    MAX_MESSAGE_LENGTH = 4096
    MAX_CAPTION_LENGTH = 1024
    MAX_INLINE_QUERY_RESULTS = 50
    MAX_CALLBACK_DATA_LENGTH = 64
    
    # File limits
    MAX_FILE_SIZE_MB = 50
    MAX_PHOTO_SIZE_MB = 10
    MAX_DOCUMENT_SIZE_MB = 50
    
    # Rate limits (requests per second)
    GLOBAL_RATE_LIMIT = 30
    GROUP_RATE_LIMIT = 20
    
    # Polling settings
    POLL_TIMEOUT = 60  # Long polling timeout
    POLL_INTERVAL = 0  # No delay between polls
    
    # Webhook settings
    WEBHOOK_MAX_CONNECTIONS = 40
    WEBHOOK_PENDING_UPDATE_LIMIT = 100
    
    # Media group settings
    MAX_MEDIA_GROUP_SIZE = 10
    MEDIA_GROUP_TIMEOUT = 60  # seconds
    
    # Bot command settings
    MAX_COMMAND_LENGTH = 32
    MAX_COMMAND_DESCRIPTION = 256
    
    # Inline keyboard settings
    MAX_INLINE_BUTTONS_PER_ROW = 8
    MAX_INLINE_BUTTON_TEXT_LENGTH = 64


class APIEndpoints:
    """API endpoint constants"""
    # Telegram API
    TELEGRAM_API_BASE = "https://api.telegram.org"
    TELEGRAM_FILE_BASE = "https://api.telegram.org/file"
    
    # Health check endpoints
    HEALTH_CHECK_PATH = "/health"
    API_HEALTH_CHECK_PATH = "/api/v1/health"
    
    # Admin API paths
    ADMIN_API_PREFIX = "/api/v1"
    ADMIN_AUTH_PATH = f"{ADMIN_API_PREFIX}/auth"
    ADMIN_USERS_PATH = f"{ADMIN_API_PREFIX}/users"
    ADMIN_ANALYTICS_PATH = f"{ADMIN_API_PREFIX}/analytics"
    ADMIN_EXPORT_PATH = f"{ADMIN_API_PREFIX}/export"


class HTTPHeaders:
    """Standard HTTP headers"""
    # Common headers
    CONTENT_TYPE = "Content-Type"
    AUTHORIZATION = "Authorization"
    USER_AGENT = "User-Agent"
    ACCEPT = "Accept"
    
    # Security headers
    X_FRAME_OPTIONS = "X-Frame-Options"
    X_CONTENT_TYPE_OPTIONS = "X-Content-Type-Options"
    X_XSS_PROTECTION = "X-XSS-Protection"
    STRICT_TRANSPORT_SECURITY = "Strict-Transport-Security"
    
    # Custom headers
    X_REQUEST_ID = "X-Request-ID"
    X_RATE_LIMIT_REMAINING = "X-RateLimit-Remaining"
    X_RATE_LIMIT_RESET = "X-RateLimit-Reset"
    
    # Default values
    DEFAULT_USER_AGENT = "DiabetesMonitoringBot/1.0"
    DEFAULT_CONTENT_TYPE = "application/json"
    DEFAULT_ACCEPT = "application/json"


class WebhookSettings:
    """Webhook configuration constants"""
    # Webhook paths
    WEBHOOK_PATH = "/webhook"
    WEBHOOK_SECRET_LENGTH = 32
    
    # Webhook verification
    SIGNATURE_HEADER = "X-Telegram-Bot-Api-Secret-Token"
    MAX_SIGNATURE_AGE_SECONDS = 300  # 5 minutes
    
    # Webhook retry settings
    WEBHOOK_MAX_RETRIES = 5
    WEBHOOK_RETRY_DELAY = 60  # seconds
    WEBHOOK_BACKOFF_FACTOR = 2