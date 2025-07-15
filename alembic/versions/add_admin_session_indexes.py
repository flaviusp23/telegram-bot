"""add admin session indexes

Revision ID: add_admin_session_indexes
Revises: fc57f051a616
Create Date: 2025-01-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_admin_session_indexes'
down_revision: Union[str, Sequence[str], None] = 'fc57f051a616'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add additional indexes for admin session queries."""
    
    # Add composite index for session lookups by admin_user_id and token
    op.create_index(
        'ix_admin_sessions_admin_token',
        'admin_sessions',
        ['admin_user_id', 'session_token']
    )
    
    # Add index for active sessions query (not expired)
    op.create_index(
        'ix_admin_sessions_active',
        'admin_sessions',
        ['expires_at', 'admin_user_id']
    )
    
    # Add indexes for audit logs filtering
    op.create_index(
        'ix_audit_logs_admin_action_timestamp',
        'audit_logs',
        ['admin_user_id', 'action', 'timestamp']
    )
    
    # Add index for IP-based queries (for security monitoring)
    op.create_index(
        'ix_audit_logs_ip_timestamp',
        'audit_logs',
        ['ip_address', 'timestamp']
    )
    
    # Add index for admin_users role-based queries
    op.create_index(
        'ix_admin_users_role_active',
        'admin_users',
        ['role', 'is_active']
    )


def downgrade() -> None:
    """Remove the additional indexes."""
    
    op.drop_index('ix_admin_users_role_active', table_name='admin_users')
    op.drop_index('ix_audit_logs_ip_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_admin_action_timestamp', table_name='audit_logs')
    op.drop_index('ix_admin_sessions_active', table_name='admin_sessions')
    op.drop_index('ix_admin_sessions_admin_token', table_name='admin_sessions')