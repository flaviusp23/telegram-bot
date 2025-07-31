"""
Permission management for admin panel.

This module provides decorators and utilities for role-based access control.
"""

from functools import wraps
from typing import List, Callable

from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from admin.core.security import get_current_active_user, TokenData
from admin.models.admin import AdminUser, AdminRole
from database.database import get_db

class PermissionDenied(HTTPException):
    """Exception raised when user lacks required permissions"""
    def __init__(self, detail: str = "You don't have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


async def get_admin_user(
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> AdminUser:
    """
    Get the admin user from the token data.
    
    Args:
        current_user: Token data from authentication
        db: Database session
        
    Returns:
        AdminUser object
        
    Raises:
        HTTPException: If admin user not found
    """
    admin = db.query(AdminUser).filter(
        AdminUser.id == current_user.user_id
    ).first()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )
    
    return admin


def check_role_hierarchy(user_role: AdminRole, required_role: AdminRole) -> bool:
    """
    Check if user role meets or exceeds required role.
    
    Role hierarchy: super_admin > admin > viewer
    
    Args:
        user_role: User's current role
        required_role: Required role for access
        
    Returns:
        True if user has sufficient permissions
    """
    role_hierarchy = {
        AdminRole.viewer: 0,
        AdminRole.admin: 1,
        AdminRole.super_admin: 2
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 1)
    
    return user_level >= required_level


def require_role(min_role: AdminRole):
    """
    Decorator to require a minimum role for endpoint access.
    
    Usage:
        @router.get("/admin-only")
        @require_role(AdminRole.admin)
        async def admin_endpoint():
            ...
    
    Args:
        min_role: Minimum required role
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if not db or not current_user:
                # If dependencies not in kwargs, this decorator won't work
                # The endpoint should use Depends() properly
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission check failed: missing dependencies"
                )
            
            # Get admin user
            admin = db.query(AdminUser).filter(
                AdminUser.id == current_user.user_id
            ).first()
            
            if not admin:
                raise PermissionDenied("Admin user not found")
            
            if not admin.is_active:
                raise PermissionDenied("Admin account is inactive")
            
            # Check role
            if not check_role_hierarchy(admin.role, min_role):
                raise PermissionDenied(
                    f"This action requires {min_role.value} role or higher"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_role(roles: List[AdminRole]):
    """
    Decorator to require any of the specified roles.
    
    Args:
        roles: List of acceptable roles
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if not db or not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission check failed: missing dependencies"
                )
            
            admin = db.query(AdminUser).filter(
                AdminUser.id == current_user.user_id
            ).first()
            
            if not admin:
                raise PermissionDenied("Admin user not found")
            
            if not admin.is_active:
                raise PermissionDenied("Admin account is inactive")
            
            if admin.role not in roles:
                role_names = [r.value for r in roles]
                raise PermissionDenied(
                    f"This action requires one of these roles: {', '.join(role_names)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class RoleChecker:
    """
    Dependency class for role-based access control.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            admin: AdminUser = Depends(RoleChecker(AdminRole.admin))
        ):
            ...
    """
    def __init__(self, min_role: AdminRole = AdminRole.viewer):
        self.min_role = min_role
    
    async def __call__(
        self,
        current_user: TokenData = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> AdminUser:
        """Check role and return admin user"""
        admin = await get_admin_user(current_user, db)
        
        if not check_role_hierarchy(admin.role, self.min_role):
            raise PermissionDenied(
                f"This action requires {self.min_role.value} role or higher. "
                f"Your role: {admin.role.value}"
            )
        
        return admin


# Convenience instances for common role checks
require_viewer = RoleChecker(AdminRole.viewer)
require_admin = RoleChecker(AdminRole.admin)
require_superadmin = RoleChecker(AdminRole.super_admin)