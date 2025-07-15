"""
User management API endpoints for the admin panel.

This module provides endpoints for:
- Listing users with pagination and filtering
- Getting user details
- Updating user information
- Blocking/unblocking users
- Viewing user questionnaire responses
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User, UserStatus, Response
from admin.core.permissions import require_admin, require_viewer, AdminUser
from admin.utils.audit import create_audit_log, AuditAction, EntityType
from admin.schemas.users import (
    UserResponse, UserDetailResponse, UserUpdate,
    PaginatedUsers, ResponseModel
)
from admin.services.users import UserService
import logging

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/", response_model=PaginatedUsers)
async def list_users(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or telegram ID"),
    status: Optional[str] = Query(None, description="Filter by user status"),
    registered_from: Optional[datetime] = Query(None, description="Filter by registration date (from)"),
    registered_to: Optional[datetime] = Query(None, description="Filter by registration date (to)"),
    has_responses: Optional[bool] = Query(None, description="Filter by whether user has responses"),
    admin_user: AdminUser = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """
    List all users with pagination and filtering.
    
    Required role: Viewer or higher
    """
    # Validate page_size
    if page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size cannot exceed 100"
        )
    
    # Get users with filters
    try:
        users, total = UserService.get_users_with_filters(
            db=db,
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            registered_from=registered_from,
            registered_to=registered_to,
            has_responses=has_responses
        )
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching users"
        )
    
    # Get response counts
    user_ids = [user.id for user in users]
    response_counts = UserService.get_response_counts(db, user_ids)
    
    # Build response
    items = []
    for user in users:
        user_response = UserResponse(
            id=user.id,
            first_name=user.first_name,
            family_name=user.family_name,
            telegram_id=user.telegram_id,
            email=user.email,
            phone_number=user.phone_number,
            status=user.status.value,
            registration_date=user.registration_date,
            last_interaction=user.last_interaction,
            response_count=response_counts.get(user.id, 0)
        )
        items.append(user_response)
    
    # Log the action
    await create_audit_log(
        db=db,
        admin_id=admin_user.id,
        action=AuditAction.LIST_USERS,
        entity_type=EntityType.USER,
        changes={"filters": {
            "search": search,
            "status": status,
            "registered_from": registered_from.isoformat() if registered_from else None,
            "registered_to": registered_to.isoformat() if registered_to else None,
            "has_responses": has_responses,
            "page": page,
            "page_size": page_size
        }},
        request=request
    )
    
    return PaginatedUsers(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    request: Request,
    user_id: int,
    admin_user: AdminUser = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """
    Get specific user details including recent responses.
    
    Required role: Viewer or higher
    """
    # Get user with details
    user = UserService.get_user_with_details(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get recent responses
    recent_responses = []
    for response in sorted(user.responses, key=lambda r: r.response_timestamp, reverse=True)[:10]:
        recent_responses.append({
            "id": response.id,
            "question_type": response.question_type,
            "response_value": response.response_value,
            "response_timestamp": response.response_timestamp
        })
    
    # Log the action
    await create_audit_log(
        db=db,
        admin_id=admin_user.id,
        action=AuditAction.VIEW_USER,
        entity_type=EntityType.USER,
        entity_id=user_id,
        request=request
    )
    
    return UserDetailResponse(
        id=user.id,
        first_name=user.first_name,
        family_name=user.family_name,
        telegram_id=user.telegram_id,
        email=user.email,
        phone_number=user.phone_number,
        status=user.status.value,
        registration_date=user.registration_date,
        last_interaction=user.last_interaction,
        response_count=len(user.responses),
        interaction_count=len(user.interactions),
        recent_responses=recent_responses
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    admin_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update user information.
    
    Required role: Admin or higher
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate update data
    if user_update.email and not UserService.validate_email(user_update.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Update user and get changes
    try:
        changes = UserService.update_user(
            db=db,
            user=user,
            first_name=user_update.first_name,
            family_name=user_update.family_name,
            email=user_update.email,
            phone_number=user_update.phone_number,
            status=user_update.status
        )
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )
    
    # Log the action
    await create_audit_log(
        db=db,
        admin_id=admin_user.id,
        action=AuditAction.UPDATE_USER,
        entity_type=EntityType.USER,
        entity_id=user_id,
        changes=changes,
        request=request
    )
    
    # Get response count
    response_count = db.query(Response).filter(Response.user_id == user_id).count()
    
    return UserResponse(
        id=user.id,
        first_name=user.first_name,
        family_name=user.family_name,
        telegram_id=user.telegram_id,
        email=user.email,
        phone_number=user.phone_number,
        status=user.status.value,
        registration_date=user.registration_date,
        last_interaction=user.last_interaction,
        response_count=response_count
    )


@router.post("/{user_id}/block", response_model=UserResponse)
async def block_user(
    request: Request,
    user_id: int,
    admin_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Block a user.
    
    Required role: Admin or higher
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.status == UserStatus.blocked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already blocked"
        )
    
    # Block user
    try:
        old_status = UserService.block_user(db, user)
    except Exception as e:
        logger.error(f"Error blocking user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error blocking user"
        )
    
    # Log the action
    await create_audit_log(
        db=db,
        admin_id=admin_user.id,
        action=AuditAction.BLOCK_USER,
        entity_type=EntityType.USER,
        entity_id=user_id,
        changes={"status": {"old": old_status, "new": "blocked"}},
        request=request
    )
    
    # Get response count
    response_count = db.query(Response).filter(Response.user_id == user_id).count()
    
    return UserResponse(
        id=user.id,
        first_name=user.first_name,
        family_name=user.family_name,
        telegram_id=user.telegram_id,
        email=user.email,
        phone_number=user.phone_number,
        status=user.status.value,
        registration_date=user.registration_date,
        last_interaction=user.last_interaction,
        response_count=response_count
    )


@router.post("/{user_id}/unblock", response_model=UserResponse)
async def unblock_user(
    request: Request,
    user_id: int,
    admin_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Unblock a user.
    
    Required role: Admin or higher
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.status != UserStatus.blocked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not blocked"
        )
    
    # Unblock user
    try:
        old_status = UserService.unblock_user(db, user)
    except Exception as e:
        logger.error(f"Error unblocking user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error unblocking user"
        )
    
    # Log the action
    await create_audit_log(
        db=db,
        admin_id=admin_user.id,
        action=AuditAction.UNBLOCK_USER,
        entity_type=EntityType.USER,
        entity_id=user_id,
        changes={"status": {"old": old_status, "new": "active"}},
        request=request
    )
    
    # Get response count
    response_count = db.query(Response).filter(Response.user_id == user_id).count()
    
    return UserResponse(
        id=user.id,
        first_name=user.first_name,
        family_name=user.family_name,
        telegram_id=user.telegram_id,
        email=user.email,
        phone_number=user.phone_number,
        status=user.status.value,
        registration_date=user.registration_date,
        last_interaction=user.last_interaction,
        response_count=response_count
    )


@router.get("/{user_id}/responses", response_model=List[ResponseModel])
async def get_user_responses(
    request: Request,
    user_id: int,
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    from_date: Optional[datetime] = Query(None, description="Filter responses from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter responses to this date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of responses to return"),
    admin_user: AdminUser = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """
    Get user's questionnaire responses.
    
    Required role: Viewer or higher
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate limit
    if limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 1000"
        )
    
    # Get responses
    try:
        responses = UserService.get_user_responses(
            db=db,
            user_id=user_id,
            question_type=question_type,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error fetching user responses for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching user responses"
        )
    
    # Log the action
    await create_audit_log(
        db=db,
        admin_id=admin_user.id,
        action=AuditAction.VIEW_USER_RESPONSES,
        entity_type=EntityType.USER,
        entity_id=user_id,
        changes={"filters": {
            "question_type": question_type,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "limit": limit
        }},
        request=request
    )
    
    return [ResponseModel(
        id=response.id,
        question_type=response.question_type,
        response_value=response.response_value,
        response_timestamp=response.response_timestamp
    ) for response in responses]