"""Create export_downloads table

Revision ID: 0005
Revises: 0004
Create Date: 2025-11-26 00:02:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create export_downloads table
    op.create_table(
        "export_downloads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "downloaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["export_batches.batch_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_export_downloads_id"), "export_downloads", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_export_downloads_batch_id"),
        "export_downloads",
        ["batch_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_export_downloads_user_id"),
        "export_downloads",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_export_downloads_downloaded_at"),
        "export_downloads",
        ["downloaded_at"],
        unique=False,
    )

    # Create composite index for daily download counting
    op.create_index(
        "ix_export_downloads_user_download_date",
        "export_downloads",
        ["user_id", "downloaded_at"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        "ix_export_downloads_user_download_date", table_name="export_downloads"
    )
    op.drop_index(
        op.f("ix_export_downloads_downloaded_at"), table_name="export_downloads"
    )
    op.drop_index(op.f("ix_export_downloads_user_id"), table_name="export_downloads")
    op.drop_index(op.f("ix_export_downloads_batch_id"), table_name="export_downloads")
    op.drop_index(op.f("ix_export_downloads_id"), table_name="export_downloads")

    # Drop table
    op.drop_table("export_downloads")
