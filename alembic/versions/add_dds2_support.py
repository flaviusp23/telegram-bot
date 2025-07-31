"""Add DDS-2 support

Revision ID: add_dds2_support
Revises: fc57f051a616
Create Date: 2025-01-31

This migration doesn't require schema changes since the existing Response table
can handle DDS-2 data. The question_type field can store the new DDS-2 types,
and response_value can store the 1-6 scale values.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_dds2_support'
down_revision = 'fc57f051a616'
branch_labels = None
depends_on = None


def upgrade():
    """
    No schema changes needed for DDS-2 support.
    The existing tables can handle the new question types and response values.
    
    Existing schema supports:
    - question_type: VARCHAR(20) - Can store 'dds2_q1_overwhelmed', 'dds2_q2_failing'
    - response_value: VARCHAR(10) - Can store '1' through '6'
    
    If you want to add a language preference field to users table in the future:
    op.add_column('users', sa.Column('language', sa.String(5), nullable=False, server_default='en'))
    op.create_index('idx_language', 'users', ['language'])
    """
    pass


def downgrade():
    """
    No changes to revert.
    
    If language column was added:
    op.drop_index('idx_language', 'users')
    op.drop_column('users', 'language')
    """
    pass