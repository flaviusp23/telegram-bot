"""merge_heads_for_language_support

Revision ID: 78d03c8c9027
Revises: add_admin_session_indexes, add_dds2_support
Create Date: 2025-07-31 19:45:54.115217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78d03c8c9027'
down_revision: Union[str, Sequence[str], None] = ('add_admin_session_indexes', 'add_dds2_support')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
