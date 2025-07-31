"""
Audit log endpoints for admin panel
"""
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from admin.core.permissions import require_viewer, require_admin
from admin.models.admin import AuditLog, AdminUser
from database.database import get_db

router = APIRouter(tags=["audit"])

class AuditLogResponse(BaseModel):
    id: int
    admin_user_id: int
    admin_username: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime

class PaginatedAuditLogs(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

@router.get("/logs", response_model=PaginatedAuditLogs)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    admin_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    days: Optional[int] = Query(None, ge=1, le=365),
    limit: Optional[int] = Query(None, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_viewer)
):
    """
    Get audit logs with filtering and pagination
    """
    # Build query
    query = db.query(AuditLog).join(AdminUser)
    
    # Apply filters
    if admin_id:
        query = query.filter(AuditLog.admin_user_id == admin_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    if days:
        start_date = datetime.now() - timedelta(days=days)
        query = query.filter(AuditLog.timestamp >= start_date)
    
    # Order by timestamp descending
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Get total count
    total = query.count()
    
    # Apply limit if specified (overrides pagination)
    if limit:
        logs = query.limit(limit).all()
        page_size = limit
        page = 1
    else:
        # Apply pagination
        offset = (page - 1) * page_size
        logs = query.offset(offset).limit(page_size).all()
    
    # Format response
    items = []
    for log in logs:
        items.append(AuditLogResponse(
            id=log.id,
            admin_user_id=log.admin_user_id,
            admin_username=log.admin_user.username,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            timestamp=log.timestamp
        ))
    
    return PaginatedAuditLogs(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if not limit else 1
    )

@router.delete("/logs")
async def clear_old_logs(
    days: int = Query(90, description="Delete logs older than this many days", ge=30),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(require_admin)
):
    """
    Clear old audit logs (requires admin role)
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Count logs to be deleted
    count = db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).count()
    
    # Delete old logs
    db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).delete()
    db.commit()
    
    # Log this action
    new_log = AuditLog(
        admin_user_id=current_admin.id,
        action="clear_audit_logs",
        details={"deleted_count": count, "older_than_days": days}
    )
    db.add(new_log)
    db.commit()
    
    return {"message": f"Deleted {count} audit logs older than {days} days"}