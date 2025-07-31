"""
Authentication API endpoints for the admin panel.

This module provides endpoints for:
- User login with JWT tokens
- Token refresh
- User logout
- Getting current user info
- Changing password
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from admin.core.security import (
    verify_password,
    hash_password,
    create_tokens,
    refresh_access_token,
    get_current_active_user,
    TokenData,
    validate_password_strength
)
from admin.models.admin import AdminUser, AdminSession, AuditLog
from database.database import get_db

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)


# Pydantic schemas for request/response models
class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User information response schema"""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    """Generic message response schema"""
    message: str


# Helper functions
def get_user_by_username(db: Session, username: str) -> Optional[AdminUser]:
    """Get user by username from database"""
    return db.query(AdminUser).filter(AdminUser.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[AdminUser]:
    """Get user by ID from database"""
    return db.query(AdminUser).filter(AdminUser.id == user_id).first()


def create_audit_log(
    db: Session,
    admin_user_id: int,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Create an audit log entry"""
    try:
        audit_log = AuditLog(
            admin_user_id=admin_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating audit log: {e}")
        # Don't raise - audit logging failure shouldn't break the main operation


def save_refresh_token(db: Session, user_id: int, refresh_token: str, ip_address: Optional[str] = None):
    """Save refresh token to database"""
    try:
        # Calculate expiration time (7 days from now)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Create session record
        session = AdminSession(
            admin_user_id=user_id,
            session_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address
        )
        db.add(session)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating session"
        )


def invalidate_refresh_token(db: Session, refresh_token: str):
    """Invalidate a refresh token by removing it from database"""
    try:
        db.query(AdminSession).filter(AdminSession.session_token == refresh_token).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error invalidating refresh token: {e}")
        # Don't raise - token invalidation failure shouldn't break logout


def check_account_lockout(user: AdminUser) -> bool:
    """Check if user account is locked due to failed login attempts"""
    # Account lockout feature not implemented in current schema
    return False


# API Endpoints
@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login endpoint that returns access and refresh tokens.
    
    - **username**: User's username
    - **password**: User's password
    
    Returns JWT access and refresh tokens along with user information.
    """
    # Get user from database
    user = get_user_by_username(db, login_data.username)
    
    if not user:
        # Log failed login attempt
        client_ip = request.client.host if request.client else None
        logger.warning(f"Failed login attempt for username: {login_data.username} from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if account is locked
    if check_account_lockout(user):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to multiple failed login attempts"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        # Update failed login attempts
        update_failed_login_attempts(db, user, reset=False)
        
        # Log failed login attempt
        client_ip = request.client.host if request.client else None
        logger.warning(f"Failed password for user: {user.username} from IP: {client_ip}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Reset failed login attempts on successful login
    update_failed_login_attempts(db, user, reset=True)
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    tokens = create_tokens(user_id=user.id, username=user.username)
    
    # Save refresh token
    client_ip = request.client.host if request.client else None
    save_refresh_token(db, user.id, tokens.refresh_token, ip_address=client_ip)
    
    # Create audit log
    user_agent = request.headers.get("User-Agent", "Unknown")
    create_audit_log(
        db=db,
        admin_user_id=user.id,
        action="login",
        resource_type="AdminUser",
        resource_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # Return tokens and user info
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active
        }
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access and refresh tokens.
    """
    # Check if refresh token exists in database
    session = db.query(AdminSession).filter(
        AdminSession.session_token == refresh_data.refresh_token
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if session is expired
    if session.is_expired:
        # Remove expired session
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    
    # Get new tokens
    try:
        new_tokens = await refresh_access_token(refresh_data.refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token"
        )
    
    # Invalidate old refresh token
    invalidate_refresh_token(db, refresh_data.refresh_token)
    
    # Save new refresh token
    save_refresh_token(db, session.admin_user_id, new_tokens.refresh_token, ip_address=session.ip_address)
    
    return RefreshTokenResponse(
        access_token=new_tokens.access_token,
        refresh_token=new_tokens.refresh_token,
        token_type=new_tokens.token_type
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    refresh_data: RefreshTokenRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout user and invalidate refresh token.
    
    - **refresh_token**: Refresh token to invalidate
    
    Requires authentication.
    """
    # Verify refresh token belongs to current user
    session = db.query(AdminSession).filter(
        AdminSession.session_token == refresh_data.refresh_token,
        AdminSession.admin_user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )
    
    # Invalidate refresh token
    invalidate_refresh_token(db, refresh_data.refresh_token)
    
    # Create audit log
    create_audit_log(
        db=db,
        admin_user_id=current_user.user_id,
        action="logout",
        resource_type="AdminUser",
        resource_id=current_user.user_id
    )
    
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user information.
    
    Requires authentication.
    """
    # Get user from database
    user = get_user_by_id(db, current_user.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change password for current user.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (must meet security requirements)
    
    Requires authentication.
    """
    # Get user from database
    user = get_user_by_id(db, current_user.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    password_validation = validate_password_strength(password_data.new_password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_validation["message"]
        )
    
    # Check if new password is same as current
    if verify_password(password_data.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Hash new password and update
    user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    
    # Create audit log
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "Unknown")
    create_audit_log(
        db=db,
        admin_user_id=user.id,
        action="change_password",
        resource_type="AdminUser",
        resource_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # Invalidate all refresh tokens for this user (forcing re-login)
    db.query(AdminSession).filter(AdminSession.admin_user_id == user.id).delete()
    db.commit()
    
    return MessageResponse(message="Password changed successfully. Please login again with your new password.")