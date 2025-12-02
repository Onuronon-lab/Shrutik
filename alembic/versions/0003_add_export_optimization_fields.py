"""Add export optimization fields to audio_chunks

Revision ID: 0003
Revises: 0002
Create Date: 2025-11-26 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to audio_chunks table
    op.add_column(
        "audio_chunks",
        sa.Column("transcript_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "audio_chunks",
        sa.Column(
            "ready_for_export", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "audio_chunks",
        sa.Column(
            "consensus_quality", sa.Float(), nullable=False, server_default="0.0"
        ),
    )
    op.add_column(
        "audio_chunks",
        sa.Column("consensus_transcript_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "audio_chunks",
        sa.Column(
            "consensus_failed_count", sa.Integer(), nullable=False, server_default="0"
        ),
    )

    # Add foreign key constraint for consensus_transcript_id
    op.create_foreign_key(
        "fk_audio_chunks_consensus_transcript_id",
        "audio_chunks",
        "transcriptions",
        ["consensus_transcript_id"],
        ["id"],
    )

    # Create indexes for optimization
    op.create_index(
        op.f("ix_audio_chunks_transcript_count"),
        "audio_chunks",
        ["transcript_count"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audio_chunks_ready_for_export"),
        "audio_chunks",
        ["ready_for_export"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_audio_chunks_ready_for_export"), table_name="audio_chunks")
    op.drop_index(op.f("ix_audio_chunks_transcript_count"), table_name="audio_chunks")

    # Drop foreign key constraint
    op.drop_constraint(
        "fk_audio_chunks_consensus_transcript_id", "audio_chunks", type_="foreignkey"
    )

    # Drop columns
    op.drop_column("audio_chunks", "consensus_failed_count")
    op.drop_column("audio_chunks", "consensus_transcript_id")
    op.drop_column("audio_chunks", "consensus_quality")
    op.drop_column("audio_chunks", "ready_for_export")
    op.drop_column("audio_chunks", "transcript_count")
