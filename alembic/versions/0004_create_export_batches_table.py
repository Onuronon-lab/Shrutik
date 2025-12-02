"""Create export_batches table

Revision ID: 0004
Revises: 0003
Create Date: 2025-11-26 00:01:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create export_batches table
    op.create_table(
        "export_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.String(length=255), nullable=False),
        sa.Column("archive_path", sa.String(length=500), nullable=False),
        sa.Column(
            "storage_type", sa.Enum("local", "r2", name="storagetype"), nullable=False
        ),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("chunk_ids", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "processing", "completed", "failed", name="exportbatchstatus"
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("exported", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("compression_level", sa.Integer(), nullable=True),
        sa.Column(
            "format_version", sa.String(length=10), nullable=False, server_default="1.0"
        ),
        sa.Column("recording_id_range", sa.JSON(), nullable=True),
        sa.Column("language_stats", sa.JSON(), nullable=True),
        sa.Column("total_duration_seconds", sa.Float(), nullable=True),
        sa.Column("filter_criteria", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_export_batches_id"), "export_batches", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_export_batches_batch_id"), "export_batches", ["batch_id"], unique=True
    )
    op.create_index(
        op.f("ix_export_batches_status"), "export_batches", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_export_batches_created_at"),
        "export_batches",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_export_batches_created_at"), table_name="export_batches")
    op.drop_index(op.f("ix_export_batches_status"), table_name="export_batches")
    op.drop_index(op.f("ix_export_batches_batch_id"), table_name="export_batches")
    op.drop_index(op.f("ix_export_batches_id"), table_name="export_batches")

    # Drop table
    op.drop_table("export_batches")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS exportbatchstatus")
    op.execute("DROP TYPE IF EXISTS storagetype")
