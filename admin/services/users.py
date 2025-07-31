"""
Patient service for handling patient-related business logic.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import re

from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from database.models import User, UserStatus, Response

class UserService:
    """Service class for patient-related operations."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def get_patients_with_filters(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        registered_from: Optional[datetime] = None,
        registered_to: Optional[datetime] = None,
        has_responses: Optional[bool] = None
    ) -> Tuple[List[User], int]:
        """
        Get patients with pagination and filters.
        
        Returns:
            Tuple of (patients, total_count)
        """
        query = db.query(User)
        
        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(search_pattern),
                    User.family_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.telegram_id.ilike(search_pattern)
                )
            )
        
        # Apply status filter
        if status:
            try:
                status_enum = UserStatus(status)
                query = query.filter(User.status == status_enum)
            except ValueError:
                # Invalid status, ignore filter
                pass
        
        # Apply date filters
        if registered_from:
            query = query.filter(User.registration_date >= registered_from)
        
        if registered_to:
            query = query.filter(User.registration_date <= registered_to)
        
        # Apply response filter
        if has_responses is not None:
            if has_responses:
                # Patients with at least one response
                query = query.join(Response).distinct()
            else:
                # Patients with no responses
                query = query.outerjoin(Response).filter(Response.id.is_(None))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        patients = query.offset(offset).limit(page_size).all()
        
        return patients, total
    
    @staticmethod
    def get_response_counts(db: Session, user_ids: List[int]) -> Dict[int, int]:
        """
        Get response counts for multiple patients.
        
        Returns:
            Dictionary mapping user_id to response count
        """
        if not user_ids:
            return {}
        
        # Query to get response counts
        counts = db.query(
            Response.user_id,
            func.count(Response.id).label('count')
        ).filter(
            Response.user_id.in_(user_ids)
        ).group_by(Response.user_id).all()
        
        return {user_id: count for user_id, count in counts}
    
    @staticmethod
    def get_patient_with_details(db: Session, patient_id: int) -> Optional[User]:
        """Get patient with related data loaded."""
        return db.query(User).filter(User.id == patient_id).first()
    
    @staticmethod
    def update_patient(
        db: Session,
        patient: User,
        first_name: Optional[str] = None,
        family_name: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update patient information and return changes.
        
        Returns:
            Dictionary of changes made
        """
        changes = {}
        
        if first_name is not None and patient.first_name != first_name:
            changes["first_name"] = {"old": patient.first_name, "new": first_name}
            patient.first_name = first_name
        
        if family_name is not None and patient.family_name != family_name:
            changes["family_name"] = {"old": patient.family_name, "new": family_name}
            patient.family_name = family_name
        
        if email is not None and patient.email != email:
            changes["email"] = {"old": patient.email, "new": email}
            patient.email = email
        
        if phone_number is not None and patient.phone_number != phone_number:
            changes["phone_number"] = {"old": patient.phone_number, "new": phone_number}
            patient.phone_number = phone_number
        
        if status is not None:
            try:
                new_status = UserStatus(status)
                if patient.status != new_status:
                    changes["status"] = {"old": patient.status.value, "new": new_status.value}
                    patient.status = new_status
            except ValueError:
                # Invalid status, ignore
                pass
        
        if changes:
            db.commit()
        
        return changes
    
    @staticmethod
    def block_patient(db: Session, patient: User) -> str:
        """
        Block a patient.
        
        Returns:
            Old status value
        """
        old_status = patient.status.value
        patient.status = UserStatus.blocked
        db.commit()
        return old_status
    
    @staticmethod
    def unblock_patient(db: Session, patient: User) -> str:
        """
        Unblock a patient.
        
        Returns:
            Old status value
        """
        old_status = patient.status.value
        patient.status = UserStatus.active
        db.commit()
        return old_status
    
    @staticmethod
    def get_user_responses(
        db: Session,
        user_id: int,
        question_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Response]:
        """Get patient responses with filters."""
        query = db.query(Response).filter(Response.user_id == user_id)
        
        if question_type:
            query = query.filter(Response.question_type == question_type)
        
        if from_date:
            query = query.filter(Response.response_timestamp >= from_date)
        
        if to_date:
            query = query.filter(Response.response_timestamp <= to_date)
        
        # Order by timestamp descending
        query = query.order_by(Response.response_timestamp.desc())
        
        # Apply limit
        return query.limit(limit).all()
    
    @staticmethod
    def get_patient_responses(
        db: Session,
        user_id: int,
        question_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Response]:
        """Alias for get_user_responses for backward compatibility."""
        return UserService.get_user_responses(
            db=db,
            user_id=user_id,
            question_type=question_type,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )