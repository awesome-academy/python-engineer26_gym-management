"""rename sold_by to updated_by

Revision ID: 6a6df0e5db58
Revises: 2a0cb1c9eff2, 53f35ad06c3e
Create Date: 2026-06-28 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "6a6df0e5db58"
down_revision: Union[str, Sequence[str], None] = "1c19775a7574"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "subscriptions",
        "sold_by",
        new_column_name="updated_by",
        existing_type=sa.String(),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "subscriptions",
        "updated_by",
        new_column_name="sold_by",
        existing_type=sa.String(),
        existing_nullable=True,
    )
