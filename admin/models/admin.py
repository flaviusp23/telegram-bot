"""Admin database models for the admin panel"""
from datetime import datetime, timezone
import enum

from sqlalchemy import Column, Integer, String, Enum, Boolean, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.database import Base

# Admin Role Enum
class AdminRole(enum.Enum):
    """Admin role levels"""
    super_admin = "super_admin"
    admin = "admin"
    viewer = "viewer"


# Table names for admin models
class AdminTableNames:
    """Admin panel table names"""
    ADMIN_USERS = "admin_users"
    AUDIT_LOGS = "audit_logs"
    ADMIN_SESSIONS = "admin_sessions"


# Field lengths for admin models
class AdminFieldLengths:
    """Maximum field lengths for admin database columns"""
    USERNAME_LENGTH = 50
    EMAIL_LENGTH = 255
    HASHED_PASSWORD_LENGTH = 255
    ROLE_LENGTH = 20
    ACTION_LENGTH = 100
    ENTITY_TYPE_LENGTH = 50
    IP_ADDRESS_LENGTH = 45  # Support for IPv6
    USER_AGENT_LENGTH = 500
    REFRESH_TOKEN_LENGTH = 255


class AdminUser(Base):
    """Admin user model"""
    __tablename__ = AdminTableNames.ADMIN_USERS
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(AdminFieldLengths.USERNAME_LENGTH), unique=True, nullable=False)
    email = Column(String(AdminFieldLengths.EMAIL_LENGTH), unique=True, nullable=False)
    hashed_password = Column(String(AdminFieldLengths.HASHED_PASSWORD_LENGTH), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(Enum(AdminRole), default=AdminRole.viewer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    
    # Relationships
    audit_logs = relationship("AuditLog", back_populates="admin_user", foreign_keys="AuditLog.admin_user_id")
    sessions = relationship("AdminSession", back_populates="admin_user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AdminUser(id={self.id}, username={self.username}, role={self.role.value})>"


class AuditLog(Base):
    """Audit log model for tracking admin actions"""
    __tablename__ = AdminTableNames.AUDIT_LOGS
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_user_id = Column(Integer, ForeignKey(f"{AdminTableNames.ADMIN_USERS}.id"), nullable=False)
    action = Column(String(AdminFieldLengths.ACTION_LENGTH), nullable=False)
    resource_type = Column(String(AdminFieldLengths.ENTITY_TYPE_LENGTH), nullable=True)
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)  # Store changes as JSON
    ip_address = Column(String(AdminFieldLengths.IP_ADDRESS_LENGTH), nullable=True)
    user_agent = Column(String(AdminFieldLengths.USER_AGENT_LENGTH), nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    
    # Relationships
    admin_user = relationship("AdminUser", back_populates="audit_logs", foreign_keys=[admin_user_id])
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, admin_user_id={self.admin_user_id}, action={self.action}, timestamp={self.timestamp})>"


class AdminSession(Base):
    """Admin session model for managing authentication sessions"""
    __tablename__ = AdminTableNames.ADMIN_SESSIONS
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_user_id = Column(Integer, ForeignKey(f"{AdminTableNames.ADMIN_USERS}.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    last_activity = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    
    # Relationships
    admin_user = relationship("AdminUser", back_populates="sessions")
    
    def __repr__(self):
        return f"<AdminSession(id={self.id}, admin_user_id={self.admin_user_id}, expires_at={self.expires_at})>"
    
    @property
    def is_expired(self):
        """Check if the session has expired"""
        return datetime.now(timezone.utc) > self.expires_at