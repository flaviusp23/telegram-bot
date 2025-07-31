"""
Request validation middleware for input sanitization and size limits.

Provides protection against:
- Oversized requests
- Malformed JSON
- SQL injection attempts
- XSS attempts
"""

import json
import re

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from admin.core.config import settings

class ValidationError(HTTPException):
    """Exception raised for validation errors"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class RequestValidator:
    """Validates incoming requests for security"""
    
    # Maximum request sizes by content type
    MAX_JSON_SIZE = 1024 * 1024  # 1MB
    MAX_FORM_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE  # From config
    
    # Patterns that might indicate SQL injection
    SQL_PATTERNS = [
        r"(\bunion\b.*\bselect\b|\bselect\b.*\bunion\b)",
        r"(;|\||`|\\x[0-9a-f]+|\\[0-9]+)",
        r"(\bdrop\b.*\btable\b|\bdelete\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b|\bupdate\b.*\bset\b)",
        r"(\bexec\b|\bexecute\b)\s*\(",
        r"<script[^>]*>.*?</script>",
    ]
    
    # Compile patterns for efficiency
    SQL_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in SQL_PATTERNS]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    XSS_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in XSS_PATTERNS]
    
    @classmethod
    def validate_content_length(cls, request: Request) -> None:
        """Check if content length is within limits"""
        content_length = request.headers.get("content-length")
        
        if not content_length:
            return
        
        try:
            size = int(content_length)
        except ValueError:
            raise ValidationError("Invalid content-length header")
        
        content_type = request.headers.get("content-type", "").lower()
        
        if "application/json" in content_type:
            max_size = cls.MAX_JSON_SIZE
        elif "multipart/form-data" in content_type:
            max_size = cls.MAX_FILE_SIZE
        elif "application/x-www-form-urlencoded" in content_type:
            max_size = cls.MAX_FORM_SIZE
        else:
            max_size = cls.MAX_JSON_SIZE
        
        if size > max_size:
            raise ValidationError(f"Request too large. Maximum size: {max_size} bytes")
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Check if string contains potential SQL injection"""
        if not isinstance(value, str):
            return False
        
        # Check against SQL patterns
        for pattern in cls.SQL_REGEX:
            if pattern.search(value):
                return True
        
        return False
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        """Check if string contains potential XSS"""
        if not isinstance(value, str):
            return False
        
        # Check against XSS patterns
        for pattern in cls.XSS_REGEX:
            if pattern.search(value):
                return True
        
        return False
    
    @classmethod
    def validate_json_data(cls, data: Any, path: str = "") -> None:
        """Recursively validate JSON data for security threats"""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check key for injection
                if cls.check_sql_injection(str(key)) or cls.check_xss(str(key)):
                    raise ValidationError(f"Suspicious content in field: {current_path}")
                
                # Validate value
                cls.validate_json_data(value, current_path)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                cls.validate_json_data(item, f"{path}[{i}]")
        
        elif isinstance(data, str):
            # Check string values for injection
            if cls.check_sql_injection(data) or cls.check_xss(data):
                raise ValidationError(f"Suspicious content in field: {path}")
    
    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """Basic string sanitization"""
        if not isinstance(value, str):
            return value
        
        # Remove null bytes
        value = value.replace("\x00", "")
        
        # Trim whitespace
        value = value.strip()
        
        # Limit length to prevent DoS
        max_length = 10000
        if len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @classmethod
    def validate_path_parameter(cls, param: str) -> None:
        """Validate path parameters to prevent directory traversal"""
        if not param:
            return
        
        # Check for directory traversal attempts
        if ".." in param or "/" in param or "\\" in param:
            raise ValidationError("Invalid path parameter")
        
        # Check for null bytes
        if "\x00" in param:
            raise ValidationError("Invalid path parameter")


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation"""
    
    # Paths to skip validation
    SKIP_PATHS = {"/health", "/api/v1/health", "/docs", "/openapi.json", "/redoc"}
    
    async def dispatch(self, request: Request, call_next):
        """Process request with validation"""
        # Skip validation for certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)
        
        try:
            # Validate content length
            RequestValidator.validate_content_length(request)
            
            # For JSON requests, validate the body
            if request.headers.get("content-type", "").startswith("application/json"):
                # Read body
                body = await request.body()
                
                if body:
                    try:
                        # Parse JSON
                        data = json.loads(body)
                        
                        # Validate for security threats
                        RequestValidator.validate_json_data(data)
                        
                    except json.JSONDecodeError:
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": "Invalid JSON in request body"}
                        )
                    except ValidationError as e:
                        return JSONResponse(
                            status_code=e.status_code,
                            content={"detail": e.detail}
                        )
                    
                    # Recreate request with validated body
                    async def receive():
                        return {"type": "http.request", "body": body}
                    
                    request._receive = receive
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            if settings.is_production:
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            return response
            
        except ValidationError as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            # Log error in development
            if settings.is_development:
                print(f"Validation middleware error: {e}")
            
            # Return generic error
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )