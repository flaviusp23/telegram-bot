"""
Patient management API endpoints for the admin panel.

This module provides endpoints for:
- Listing patients with pagination and filtering
- Getting patient details
- Updating patient information
- Blocking/unblocking patients
- Viewing patient questionnaire responses
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
async def list_patients(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or telegram ID"),
    status: Optional[str] = Query(None, description="Filter by patient status"),
    registered_from: Optional[datetime] = Query(None, description="Filter by registration date (from)"),
    registered_to: Optional[datetime] = Query(None, description="Filter by registration date (to)"),
    has_responses: Optional[bool] = Query(None, description="Filter by whether patient has responses"),
    admin_user: AdminUser = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """
    List all patients with pagination and filtering.
    
    Required role: Viewer or higher
    """
    # Validate page_size
    if page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size cannot exceed 100"
        )
    
    # Get patients with filters
    try:
        patients, total = UserService.get_patients_with_filters(
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
        logger.error(f"Error fetching patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching patients"
        )
    
    # Get response counts
    patient_ids = [patient.id for patient in patients]
    response_counts = UserService.get_response_counts(db, patient_ids)
    
    # Build response
    items = []
    for patient in patients:
        patient_response = UserResponse(
            id=patient.id,
            first_name=patient.first_name,
            family_name=patient.family_name,
            telegram_id=patient.telegram_id,
            email=patient.email,
            phone_number=patient.phone_number,
            status=patient.status.value,
            registration_date=patient.registration_date,
            last_interaction=patient.last_interaction,
            response_count=response_counts.get(patient.id, 0)
        )
        items.append(patient_response)
    
    # Log the action
    await create_audit_log(
        db=db,
        admin_id=admin_user.id,
        action=AuditAction.LIST_USERS,
        entity_type=EntityType.PATIENT,
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
async def get_patient(
    request: Request,
    user_id: int,
    admin_user: AdminUser = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """
    Get specific patient details including recent responses.
    
    Required role: Viewer or higher
    """
    # Get patient with details
    patient = UserService.get_patient_with_details(db, user_id)
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Get recent responses
    recent_responses = []
    for response in sorted(patient.responses, key=lambda r: r.response_timestamp, reverse=True)[:10]:
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
        entity_type=EntityType.PATIENT,
        entity_id=user_id,
        request=request
    )
    
    return UserDetailResponse(
        id=patient.id,
        first_name=patient.first_name,
        family_name=patient.family_name,
        telegram_id=patient.telegram_id,
        email=patient.email,
        phone_number=patient.phone_number,
        status=patient.status.value,
        registration_date=patient.registration_date,
        last_interaction=patient.last_interaction,
        response_count=len(patient.responses),
        interaction_count=len(patient.interactions),
        recent_responses=recent_responses
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_patient(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    admin_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update patient information.
    
    Required role: Admin or higher
    """
    # Get patient
    patient = db.query(User).filter(User.id == user_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Validate update data
    if user_update.email and not UserService.validate_email(user_update.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Update patient and get changes
    try:
        changes = UserService.update_patient(
            db=db,
            patient=patient,
            first_name=user_update.first_name,
            family_name=user_update.family_name,
            email=user_update.email,
            phone_number=user_update.phone_number,
            status=user_update.status
        )
    except Exception as e:
        logger.error(f"Error updating patient {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating patient"
        )
    
    # Log the action
    await create_audit_log(
        db=db,
        admin_id=admin_user.id,
        action=AuditAction.UPDATE_USER,
        entity_type=EntityType.PATIENT,
        entity_id=user_id,
        changes=changes,
        request=request
    )
    
    # Get response count
    response_count = db.query(Response).filter(Response.user_id == user_id).count()
    
    return UserResponse(
        id=patient.id,
        first_name=patient.first_name,
        family_name=patient.family_name,
        telegram_id=patient.telegram_id,
        email=patient.email,
        phone_number=patient.phone_number,
        status=patient.status.value,
        registration_date=patient.registration_date,
        last_interaction=patient.last_interaction,
        response_count=response_count
    )


@router.post("/{user_id}/block", response_model=UserResponse)
async def block_patient(
    request: Request,
    user_id: int,
    admin_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Block a patient.
    
    Required role: Admin or higher
    """
    # Get patient
    patient = db.query(User).filter(User.id == user_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    if patient.status == UserStatus.blocked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient is already blocked"
        )
    
    # Block patient
    try:
        old_status = UserService.block_patient(db, patient)
    except Exception as e:
        logger.error(f"Error blocking patient {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error blocking patient"
        )
    
    # Log the action
    await create_audit_log(
        db=db,
        admin_id=admin_user.id,
        action=AuditAction.BLOCK_USER,
        entity_type=EntityType.PATIENT,
        entity_id=user_id,
        changes={"status": {"old": old_status, "new": "blocked"}},
        request=request
    )
    
    # Get response count
    response_count = db.query(Response).filter(Response.user_id == user_id).count()
    
    return UserResponse(
        id=patient.id,
        first_name=patient.first_name,
        family_name=patient.family_name,
        telegram_id=patient.telegram_id,
        email=patient.email,
        phone_number=patient.phone_number,
        status=patient.status.value,
        registration_date=patient.registration_date,
        last_interaction=patient.last_interaction,
        response_count=response_count
    )


@router.post("/{user_id}/unblock", response_model=UserResponse)
async def unblock_patient(
    request: Request,
    user_id: int,
    admin_user: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Unblock a patient.
    
    Required role: Admin or higher
    """
    # Get patient
    patient = db.query(User).filter(User.id == user_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    if patient.status != UserStatus.blocked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient is not blocked"
        )
    
    # Unblock patient
    try:
        old_status = UserService.unblock_patient(db, patient)
    except Exception as e:
        logger.error(f"Error unblocking patient {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error unblocking patient"
        )
    
    # Log the action
    await create_audit_log(
        db=db,
        admin_id=admin_user.id,
        action=AuditAction.UNBLOCK_USER,
        entity_type=EntityType.PATIENT,
        entity_id=user_id,
        changes={"status": {"old": old_status, "new": "active"}},
        request=request
    )
    
    # Get response count
    response_count = db.query(Response).filter(Response.user_id == user_id).count()
    
    return UserResponse(
        id=patient.id,
        first_name=patient.first_name,
        family_name=patient.family_name,
        telegram_id=patient.telegram_id,
        email=patient.email,
        phone_number=patient.phone_number,
        status=patient.status.value,
        registration_date=patient.registration_date,
        last_interaction=patient.last_interaction,
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
    Get patient's questionnaire responses.
    
    Required role: Viewer or higher
    """
    # Check if patient exists
    patient = db.query(User).filter(User.id == user_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Validate limit
    if limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 1000"
        )
    
    # Get responses
    try:
        responses = UserService.get_patient_responses(
            db=db,
            user_id=user_id,
            question_type=question_type,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error fetching patient responses for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching patient responses"
        )
    
    # Log the action
    await create_audit_log(
        db=db,
        admin_id=admin_user.id,
        action=AuditAction.VIEW_USER_RESPONSES,
        entity_type=EntityType.PATIENT,
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