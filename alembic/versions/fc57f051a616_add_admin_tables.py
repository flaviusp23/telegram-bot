"""add admin tables

Revision ID: fc57f051a616
Revises: 015023907239
Create Date: 2025-01-15 13:22:26.958942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc57f051a616'
down_revision: Union[str, Sequence[str], None] = '015023907239'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create admin tables with proper indexes."""
    
    # Create admin_users table
    op.create_table('admin_users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('role', sa.Enum('super_admin', 'admin', 'viewer', name='adminrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('last_login', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    # Create indexes for admin_users
    op.create_index('ix_admin_users_username', 'admin_users', ['username'])
    op.create_index('ix_admin_users_email', 'admin_users', ['email'])
    op.create_index('ix_admin_users_is_active', 'admin_users', ['is_active'])
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('admin_user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['admin_user_id'], ['admin_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for audit_logs
    op.create_index('ix_audit_logs_admin_user_id', 'audit_logs', ['admin_user_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type_id', 'audit_logs', ['resource_type', 'resource_id'])
    
    # Create admin_sessions table
    op.create_table('admin_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('admin_user_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_activity', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['admin_user_id'], ['admin_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token')
    )
    
    # Create indexes for admin_sessions
    op.create_index('ix_admin_sessions_session_token', 'admin_sessions', ['session_token'])
    op.create_index('ix_admin_sessions_admin_user_id', 'admin_sessions', ['admin_user_id'])
    op.create_index('ix_admin_sessions_expires_at', 'admin_sessions', ['expires_at'])
    
    # Create trigger for updated_at column on admin_users (MySQL syntax)
    op.execute("""
        CREATE TRIGGER update_admin_users_updated_at 
        BEFORE UPDATE ON admin_users 
        FOR EACH ROW 
        SET NEW.updated_at = CURRENT_TIMESTAMP;
    """)


def downgrade() -> None:
    """Drop admin tables and related objects."""
    
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_admin_users_updated_at")
    
    # Drop indexes for admin_sessions
    op.drop_index('ix_admin_sessions_expires_at', table_name='admin_sessions')
    op.drop_index('ix_admin_sessions_admin_user_id', table_name='admin_sessions')
    op.drop_index('ix_admin_sessions_session_token', table_name='admin_sessions')
    
    # Drop admin_sessions table
    op.drop_table('admin_sessions')
    
    # Drop indexes for audit_logs
    op.drop_index('ix_audit_logs_resource_type_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_admin_user_id', table_name='audit_logs')
    
    # Drop audit_logs table
    op.drop_table('audit_logs')
    
    # Drop indexes for admin_users
    op.drop_index('ix_admin_users_is_active', table_name='admin_users')
    op.drop_index('ix_admin_users_email', table_name='admin_users')
    op.drop_index('ix_admin_users_username', table_name='admin_users')
    
    # Drop admin_users table
    op.drop_table('admin_users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS adminrole")