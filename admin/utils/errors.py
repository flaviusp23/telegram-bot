"""
Error handling utilities for consistent API error responses.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class APIError(HTTPException):
    """Base API error with consistent format."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        error_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.error_type = error_type or self.__class__.__name__
        self.details = details
        
        super().__init__(
            status_code=status_code,
            detail=message,
            headers=headers
        )
    
    def to_response(self) -> JSONResponse:
        """Convert to JSON response with consistent format."""
        content = {
            "error": {
                "code": self.status_code,
                "message": self.detail,
                "type": self.error_type
            }
        }
        
        if self.details:
            content["error"]["details"] = self.details
        
        return JSONResponse(
            status_code=self.status_code,
            content=content,
            headers=self.headers
        )


class ValidationError(APIError):
    """Validation error (400)."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = {"field": field} if field else None
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_type="ValidationError",
            details=details,
            **kwargs
        )


class AuthenticationError(APIError):
    """Authentication error (401)."""
    
    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_type="AuthenticationError",
            headers={"WWW-Authenticate": "Bearer"},
            **kwargs
        )


class PermissionError(APIError):
    """Permission error (403)."""
    
    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_type="PermissionError",
            **kwargs
        )


class NotFoundError(APIError):
    """Not found error (404)."""
    
    def __init__(self, resource: str, resource_id: Optional[Any] = None, **kwargs):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with ID {resource_id} not found"
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_type="NotFoundError",
            details={"resource": resource, "id": resource_id} if resource_id else {"resource": resource},
            **kwargs
        )


class ConflictError(APIError):
    """Conflict error (409)."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_type="ConflictError",
            **kwargs
        )


class RateLimitError(APIError):
    """Rate limit error (429)."""
    
    def __init__(self, retry_after: int, **kwargs):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message="Rate limit exceeded. Please try again later.",
            error_type="RateLimitError",
            headers={"Retry-After": str(retry_after)},
            **kwargs
        )


class InternalError(APIError):
    """Internal server error (500)."""
    
    def __init__(self, message: str = "Internal server error", **kwargs):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_type="InternalServerError",
            **kwargs
        )


def create_error_response(
    status_code: int,
    message: str,
    error_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """Create a consistent error response."""
    content = {
        "error": {
            "code": status_code,
            "message": message,
            "type": error_type or "Error"
        }
    }
    
    if details:
        content["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers
    )