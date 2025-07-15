"""
Audit logging utilities for tracking admin actions.

This module provides utilities for creating audit logs for all admin actions.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request

from admin.models.admin import AuditLog


class AuditAction:
    """Standard audit action types"""
    # User management actions
    LIST_USERS = "list_users"
    VIEW_USER = "view_user"
    UPDATE_USER = "update_user"
    BLOCK_USER = "block_user"
    UNBLOCK_USER = "unblock_user"
    VIEW_USER_RESPONSES = "view_user_responses"
    
    # Auth actions
    LOGIN = "login"
    LOGOUT = "logout"
    REFRESH_TOKEN = "refresh_token"
    CHANGE_PASSWORD = "change_password"
    
    # Admin management actions
    CREATE_ADMIN = "create_admin"
    UPDATE_ADMIN = "update_admin"
    DELETE_ADMIN = "delete_admin"
    VIEW_ADMIN = "view_admin"
    LIST_ADMINS = "list_admins"
    
    # Data export actions
    EXPORT_USER_DATA = "export_user_data"
    EXPORT_RESPONSES = "export_responses"
    EXPORT_ANALYTICS = "export_analytics"


class EntityType:
    """Standard entity types for audit logs"""
    USER = "user"
    ADMIN = "admin"
    RESPONSE = "response"
    SESSION = "session"
    EXPORT = "export"


async def create_audit_log(
    db: Session,
    admin_id: int,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    changes: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """
    Create an audit log entry.
    
    Args:
        db: Database session
        admin_id: ID of the admin performing the action
        action: Action being performed (use AuditAction constants)
        entity_type: Type of entity being acted upon (use EntityType constants)
        entity_id: ID of the entity being acted upon
        changes: Dictionary of changes made (will be stored as JSON)
        request: FastAPI request object for IP and user agent
        
    Returns:
        Created AuditLog instance
    """
    audit_log = AuditLog(
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes_json=changes,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    return audit_log


def format_changes(old_values: Dict[str, Any], new_values: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Format changes for audit log in a consistent way.
    
    Args:
        old_values: Dictionary of old values
        new_values: Dictionary of new values
        
    Returns:
        Formatted changes dictionary with old/new pairs
    """
    changes = {}
    
    # Find all keys that changed
    all_keys = set(old_values.keys()) | set(new_values.keys())
    
    for key in all_keys:
        old_val = old_values.get(key)
        new_val = new_values.get(key)
        
        # Only include if value actually changed
        if old_val != new_val:
            changes[key] = {
                "old": old_val,
                "new": new_val
            }
    
    return changes


def sanitize_changes(changes: Dict[str, Any], sensitive_fields: Optional[list] = None) -> Dict[str, Any]:
    """
    Sanitize sensitive information from audit log changes.
    
    Args:
        changes: Dictionary of changes
        sensitive_fields: List of field names to sanitize (default: password fields)
        
    Returns:
        Sanitized changes dictionary
    """
    if sensitive_fields is None:
        sensitive_fields = ["password", "hashed_password", "token", "refresh_token", "access_token"]
    
    sanitized = changes.copy()
    
    for field in sensitive_fields:
        if field in sanitized:
            # Replace with placeholder
            if isinstance(sanitized[field], dict):
                # Handle old/new format
                if "old" in sanitized[field]:
                    sanitized[field]["old"] = "***REDACTED***"
                if "new" in sanitized[field]:
                    sanitized[field]["new"] = "***REDACTED***"
            else:
                sanitized[field] = "***REDACTED***"
    
    return sanitized