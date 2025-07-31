"""add_language_preference_to_users

Revision ID: 35e61d65ed37
Revises: 78d03c8c9027
Create Date: 2025-07-31 19:46:03.440574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35e61d65ed37'
down_revision: Union[str, Sequence[str], None] = '78d03c8c9027'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add language column to users table
    op.add_column('users', sa.Column('language', sa.String(5), nullable=True))
    
    # Set default language to 'en' for existing users
    op.execute("UPDATE users SET language = 'en' WHERE language IS NULL")
    
    # Make the column non-nullable after setting defaults
    op.alter_column('users', 'language',
                    existing_type=sa.String(5),
                    nullable=False,
                    server_default='en')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'language')
