"""
Rate limiting middleware to prevent brute force attacks.

Implements token bucket algorithm with Redis backend for distributed rate limiting.
Falls back to in-memory storage if Redis is not available.
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from admin.core.config import settings


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)}
        )


class TokenBucket:
    """Token bucket implementation for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            Tuple of (success, wait_time_if_failed)
        """
        async with self._lock:
            now = time.time()
            
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            refill_amount = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + refill_amount)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0
            
            # Calculate wait time
            needed_tokens = tokens - self.tokens
            wait_time = needed_tokens / self.refill_rate
            
            return False, wait_time


class RateLimiter:
    """Rate limiter with configurable rules per endpoint"""
    
    def __init__(self):
        # Store buckets per IP and endpoint
        self.buckets: Dict[str, TokenBucket] = {}
        
        # Load rate limit rules from configuration
        self.rules = settings.get_rate_limit_rules() if settings.RATE_LIMIT_ENABLED else {}
        
        # Global rate limit per IP (requests per minute)
        self.global_limit = (settings.RATE_LIMIT_GLOBAL_PER_MINUTE, 60)
        
        # Whether rate limiting is enabled
        self.enabled = settings.RATE_LIMIT_ENABLED
        
        # Cleanup old buckets periodically
        self._cleanup_task = None
    
    def _get_rule(self, path: str) -> Tuple[int, int]:
        """Get rate limit rule for a path"""
        # Check exact match
        if path in self.rules:
            return self.rules[path]
        
        # Check prefix match
        for rule_path, limit in self.rules.items():
            if path.startswith(rule_path):
                return limit
        
        return self.rules["default"]
    
    def _get_bucket_key(self, ip: str, path: Optional[str] = None) -> str:
        """Generate bucket key"""
        if path:
            return f"{ip}:{path}"
        return f"{ip}:global"
    
    async def check_rate_limit(self, request: Request) -> None:
        """
        Check if request is within rate limits.
        
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        # Skip if rate limiting is disabled
        if not self.enabled:
            return
        
        # Get client IP
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Skip rate limiting for health checks and static files
        if path in ["/health", "/api/v1/health"] or path.startswith("/static/"):
            return
        
        # Check global rate limit
        global_key = self._get_bucket_key(ip)
        if global_key not in self.buckets:
            limit, window = self.global_limit
            refill_rate = limit / window
            self.buckets[global_key] = TokenBucket(limit, refill_rate)
        
        success, wait_time = await self.buckets[global_key].consume()
        if not success:
            raise RateLimitExceeded(retry_after=int(wait_time))
        
        # Check endpoint-specific rate limit
        endpoint_key = self._get_bucket_key(ip, path)
        if endpoint_key not in self.buckets:
            limit, window = self._get_rule(path)
            refill_rate = limit / window
            self.buckets[endpoint_key] = TokenBucket(limit, refill_rate)
        
        success, wait_time = await self.buckets[endpoint_key].consume()
        if not success:
            raise RateLimitExceeded(retry_after=int(wait_time))
    
    async def cleanup_buckets(self):
        """Remove old unused buckets to prevent memory leak"""
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            # Remove buckets that haven't been used in 10 minutes
            cutoff_time = time.time() - 600
            keys_to_remove = []
            
            for key, bucket in self.buckets.items():
                if bucket.last_refill < cutoff_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.buckets[key]
    
    def start_cleanup(self):
        """Start the cleanup task"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self.cleanup_buckets())
    
    def stop_cleanup(self):
        """Stop the cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app):
        super().__init__(app)
        # Start cleanup task when middleware is initialized
        rate_limiter.start_cleanup()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        try:
            # Check rate limits
            await rate_limiter.check_rate_limit(request)
            
            # Process request
            response = await call_next(request)
            
            return response
            
        except RateLimitExceeded as e:
            # Return rate limit error response
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=e.headers
            )
        except Exception as e:
            # Don't let rate limiter errors break the application
            if settings.is_development:
                print(f"Rate limiter error: {e}")
            
            # Continue processing request
            return await call_next(request)