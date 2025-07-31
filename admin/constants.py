"""Constants for the admin panel"""

class WebSocketSettings:
    """Constants for WebSocket connections"""
    # Channels
    CHANNELS = ["dashboard", "patients", "logs"]
    
    # Timeouts
    PING_TIMEOUT = 5.0  # Timeout for ping/pong messages in seconds
    UPDATE_INTERVAL = 5.0  # Interval for sending updates in seconds
    CONNECTION_TIMEOUT = 30.0  # Maximum time to wait for initial connection
    
    # Error codes
    ERROR_UNAUTHORIZED = 4001
    ERROR_GENERAL = 4000
    
    # Message types
    MSG_CONNECTED = "connected"
    MSG_STATS_UPDATE = "stats_update"
    MSG_PING = "ping"
    MSG_PONG = "pong"
    MSG_ERROR = "error"
    MSG_DISCONNECT = "disconnect"


class RateLimitSettings:
    """Constants for rate limiting"""
    # Default limits
    DEFAULT_REQUESTS_PER_MINUTE = 60
    DEFAULT_REQUESTS_PER_HOUR = 1000
    
    # Endpoint-specific limits
    AUTH_REQUESTS_PER_MINUTE = 5
    AUTH_REQUESTS_PER_HOUR = 20
    
    # WebSocket limits
    WS_CONNECTIONS_PER_USER = 5
    WS_MESSAGES_PER_MINUTE = 100
    
    # Cache settings
    CACHE_TTL = 60  # Cache time-to-live in seconds
    CACHE_MAX_SIZE = 1000  # Maximum number of cached items


class AuthSettings:
    """Constants for authentication"""
    # Token settings
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True
    
    # Login attempts
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    
    # Session settings
    SESSION_TIMEOUT_MINUTES = 60
    MAX_SESSIONS_PER_USER = 3


class APISettings:
    """Constants for API configuration"""
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    MIN_PAGE_SIZE = 1
    
    # Response limits
    MAX_RESPONSE_SIZE_MB = 10
    MAX_UPLOAD_SIZE_MB = 50
    
    # Timeouts
    REQUEST_TIMEOUT_SECONDS = 30
    DATABASE_TIMEOUT_SECONDS = 10
    
    # Cache headers
    CACHE_CONTROL_PUBLIC = "public, max-age=3600"
    CACHE_CONTROL_PRIVATE = "private, max-age=0"
    CACHE_CONTROL_NO_STORE = "no-store"


class ValidationSettings:
    """Constants for input validation"""
    # Field lengths
    MAX_NAME_LENGTH = 100
    MAX_EMAIL_LENGTH = 255
    MAX_PHONE_LENGTH = 20
    MAX_NOTE_LENGTH = 5000
    MAX_SEARCH_LENGTH = 100
    
    # Patterns
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^\+?[1-9]\d{1,14}$'  # E.164 format
    
    # Date/Time
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    TIMEZONE = "UTC"


class NotificationSettings:
    """Constants for notifications"""
    # Email settings
    EMAIL_BATCH_SIZE = 100
    EMAIL_RETRY_ATTEMPTS = 3
    EMAIL_RETRY_DELAY_SECONDS = 60
    
    # Push notification settings
    PUSH_BATCH_SIZE = 500
    PUSH_RETRY_ATTEMPTS = 2
    PUSH_TIMEOUT_SECONDS = 10
    
    # Queue settings
    NOTIFICATION_QUEUE_SIZE = 10000
    QUEUE_PROCESS_INTERVAL_SECONDS = 5


class AnalyticsSettings:
    """Constants for analytics and reporting"""
    # Time windows
    REALTIME_WINDOW_MINUTES = 5
    HOURLY_AGGREGATION_HOURS = 24
    DAILY_AGGREGATION_DAYS = 30
    MONTHLY_AGGREGATION_MONTHS = 12
    
    # Data retention
    REALTIME_RETENTION_HOURS = 1
    HOURLY_RETENTION_DAYS = 7
    DAILY_RETENTION_DAYS = 90
    MONTHLY_RETENTION_YEARS = 2
    
    # Chart settings
    MAX_CHART_POINTS = 1000
    DEFAULT_CHART_POINTS = 100
    CHART_COLOR_PALETTE = [
        '#3498db',  # Blue
        '#2ecc71',  # Green
        '#f1c40f',  # Yellow
        '#e74c3c',  # Red
        '#9b59b6',  # Purple
        '#1abc9c',  # Turquoise
        '#e67e22',  # Orange
        '#34495e',  # Dark Gray
    ]


class LoggingSettings:
    """Constants for logging configuration"""
    # Log levels
    DEFAULT_LOG_LEVEL = "INFO"
    DEBUG_LOG_LEVEL = "DEBUG"
    PRODUCTION_LOG_LEVEL = "WARNING"
    
    # Log formats
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    JSON_LOG_FORMAT = {
        "timestamp": "%(asctime)s",
        "level": "%(levelname)s",
        "logger": "%(name)s",
        "message": "%(message)s",
        "module": "%(module)s",
        "function": "%(funcName)s",
        "line": "%(lineno)d"
    }
    
    # Log rotation
    MAX_LOG_SIZE_MB = 100
    LOG_BACKUP_COUNT = 10
    LOG_ROTATION_INTERVAL_DAYS = 7


class ErrorMessages:
    """Standard error messages for the admin panel"""
    # Authentication errors
    INVALID_CREDENTIALS = "Invalid username or password"
    ACCOUNT_LOCKED = "Account temporarily locked due to too many failed attempts"
    SESSION_EXPIRED = "Your session has expired. Please log in again"
    UNAUTHORIZED_ACCESS = "You don't have permission to access this resource"
    
    # Validation errors
    INVALID_EMAIL_FORMAT = "Please enter a valid email address"
    INVALID_PHONE_FORMAT = "Please enter a valid phone number"
    REQUIRED_FIELD = "This field is required"
    FIELD_TOO_LONG = "This field exceeds the maximum allowed length"
    
    # Database errors
    DATABASE_CONNECTION_ERROR = "Unable to connect to the database"
    RECORD_NOT_FOUND = "The requested record was not found"
    DUPLICATE_ENTRY = "A record with this value already exists"
    
    # API errors
    RATE_LIMIT_EXCEEDED = "Too many requests. Please try again later"
    INVALID_REQUEST = "Invalid request format"
    INTERNAL_SERVER_ERROR = "An unexpected error occurred. Please try again later"
    SERVICE_UNAVAILABLE = "Service temporarily unavailable"


class SuccessMessages:
    """Standard success messages for the admin panel"""
    # CRUD operations
    CREATED_SUCCESSFULLY = "Record created successfully"
    UPDATED_SUCCESSFULLY = "Record updated successfully"
    DELETED_SUCCESSFULLY = "Record deleted successfully"
    
    # Authentication
    LOGIN_SUCCESSFUL = "Login successful"
    LOGOUT_SUCCESSFUL = "Logout successful"
    PASSWORD_CHANGED = "Password changed successfully"
    
    # Data operations
    EXPORT_COMPLETE = "Data export completed successfully"
    IMPORT_COMPLETE = "Data import completed successfully"
    SYNC_COMPLETE = "Synchronization completed successfully"