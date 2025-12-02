"""Add export audit log table

Revision ID: 0002
Revises: 0001
Create Date: 2024-10-30 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "export_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("export_id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("export_type", sa.String(length=50), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("filters_applied", sa.JSON(), nullable=True),
        sa.Column("records_exported", sa.Integer(), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_export_audit_logs_id"), "export_audit_logs", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_export_audit_logs_export_id"),
        "export_audit_logs",
        ["export_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_export_audit_logs_user_id"),
        "export_audit_logs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_export_audit_logs_export_type"),
        "export_audit_logs",
        ["export_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_export_audit_logs_created_at"),
        "export_audit_logs",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        "ix_export_audit_logs_user_type",
        "export_audit_logs",
        ["user_id", "export_type"],
    )
    op.create_index(
        "ix_export_audit_logs_type_created",
        "export_audit_logs",
        ["export_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_export_audit_logs_type_created", table_name="export_audit_logs")
    op.drop_index("ix_export_audit_logs_user_type", table_name="export_audit_logs")

    op.drop_index(
        op.f("ix_export_audit_logs_created_at"), table_name="export_audit_logs"
    )
    op.drop_index(
        op.f("ix_export_audit_logs_export_type"), table_name="export_audit_logs"
    )
    op.drop_index(op.f("ix_export_audit_logs_user_id"), table_name="export_audit_logs")
    op.drop_index(
        op.f("ix_export_audit_logs_export_id"), table_name="export_audit_logs"
    )
    op.drop_index(op.f("ix_export_audit_logs_id"), table_name="export_audit_logs")

    op.drop_table("export_audit_logs")
