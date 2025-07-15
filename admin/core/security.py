"""
Security module for authentication and authorization.

This module provides:
- Password hashing and verification using bcrypt
- JWT token creation and verification
- OAuth2 password bearer authentication
- User authentication from tokens
- Password strength validation
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Dict, Any
import re

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# Import configuration from config module
from .config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class TokenData(BaseModel):
    """Token data model for JWT payload."""
    username: Optional[str] = None
    user_id: Optional[int] = None
    exp: Optional[datetime] = None


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Password hashing functions
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# JWT token functions
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Dictionary containing data to encode in the token
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def create_tokens(user_id: int, username: str) -> Token:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: User's ID
        username: User's username
        
    Returns:
        Token object containing access_token, refresh_token, and token_type
    """
    token_data = {
        "sub": str(user_id),
        "username": username,
        "user_id": user_id
    }
    
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


def verify_token(token: str, credentials_exception: HTTPException) -> TokenData:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        credentials_exception: Exception to raise if verification fails
        
    Returns:
        TokenData object containing decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        user_id: int = payload.get("user_id")
        
        if username is None or user_id is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, user_id=user_id)
        return token_data
        
    except JWTError:
        raise credentials_exception


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Get current user from JWT token.
    
    This function is used as a dependency in FastAPI routes to authenticate users.
    
    Args:
        token: JWT token from OAuth2 bearer authentication
        
    Returns:
        TokenData object containing user information
        
    Raises:
        HTTPException: If token is invalid or user cannot be authenticated
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    return verify_token(token, credentials_exception)


async def get_current_active_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    Verify that the current user is active.
    
    This can be extended to check if user is active in database.
    
    Args:
        current_user: Current user data from token
        
    Returns:
        TokenData object if user is active
        
    Raises:
        HTTPException: If user is inactive
    """
    # Here you would typically check if user is active in database
    # For now, we'll assume all authenticated users are active
    return current_user


# Password validation functions
def validate_password_strength(password: str) -> Dict[str, Union[bool, str]]:
    """
    Validate password strength based on security requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password string to validate
        
    Returns:
        Dictionary with 'valid' boolean and 'message' string
    """
    if len(password) < 8:
        return {
            "valid": False,
            "message": "Password must be at least 8 characters long"
        }
    
    if not re.search(r"[A-Z]", password):
        return {
            "valid": False,
            "message": "Password must contain at least one uppercase letter"
        }
    
    if not re.search(r"[a-z]", password):
        return {
            "valid": False,
            "message": "Password must contain at least one lowercase letter"
        }
    
    if not re.search(r"\d", password):
        return {
            "valid": False,
            "message": "Password must contain at least one digit"
        }
    
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return {
            "valid": False,
            "message": "Password must contain at least one special character"
        }
    
    return {
        "valid": True,
        "message": "Password meets all security requirements"
    }


def get_password_strength_score(password: str) -> int:
    """
    Calculate password strength score from 0-100.
    
    Args:
        password: Password to evaluate
        
    Returns:
        Integer score from 0 (weakest) to 100 (strongest)
    """
    score = 0
    
    # Length score (max 30 points)
    length_score = min(len(password) * 2, 30)
    score += length_score
    
    # Character variety score (max 40 points)
    if re.search(r"[a-z]", password):
        score += 10
    if re.search(r"[A-Z]", password):
        score += 10
    if re.search(r"\d", password):
        score += 10
    if re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        score += 10
    
    # Pattern avoidance score (max 30 points)
    # Check for common patterns
    common_patterns = [
        r"(.)\1{2,}",  # Repeated characters
        r"(012|123|234|345|456|567|678|789|890)",  # Sequential numbers
        r"(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)",  # Sequential letters
    ]
    
    pattern_penalty = 0
    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            pattern_penalty += 10
    
    score += max(30 - pattern_penalty, 0)
    
    return min(score, 100)


# Utility functions for token refresh
async def refresh_access_token(refresh_token: str) -> Token:
    """
    Generate a new access token using a refresh token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        New Token object with fresh access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        user_id: int = payload.get("user_id")
        
        if username is None or user_id is None:
            raise credentials_exception
            
        # Create new tokens
        return create_tokens(user_id=user_id, username=username)
        
    except JWTError:
        raise credentials_exception