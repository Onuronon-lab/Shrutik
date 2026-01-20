"""add is_verified to users

Revision ID: cd84ef65d459
Revises: 0005
Create Date: 2026-01-20 19:09:51.730690

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "cd84ef65d459"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the 'is_verified' column to users table
    op.add_column(
        "users",
        sa.Column(
            "is_verified", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )


def downgrade() -> None:
    # Remove the 'is_verified' column if we downgrade
    op.drop_column("users", "is_verified")
