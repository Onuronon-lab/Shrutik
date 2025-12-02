"""Initial database schema

Revision ID: 0001
Revises:
Create Date: 2024-10-27 00:23:19.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "languages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_languages_code"), "languages", ["code"], unique=True)
    op.create_index(op.f("ix_languages_id"), "languages", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("CONTRIBUTOR", "ADMIN", "SWORIK_DEVELOPER", name="userrole"),
            nullable=False,
        ),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "scripts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "duration_category",
            sa.Enum("SHORT", "MEDIUM", "LONG", name="durationcategory"),
            nullable=False,
        ),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["language_id"],
            ["languages.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_scripts_duration_category"),
        "scripts",
        ["duration_category"],
        unique=False,
    )
    op.create_index(op.f("ix_scripts_id"), "scripts", ["id"], unique=False)
    op.create_index(
        op.f("ix_scripts_language_id"), "scripts", ["language_id"], unique=False
    )

    op.create_table(
        "voice_recordings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "UPLOADED", "PROCESSING", "CHUNKED", "FAILED", name="recordingstatus"
            ),
            nullable=False,
        ),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["language_id"],
            ["languages.id"],
        ),
        sa.ForeignKeyConstraint(
            ["script_id"],
            ["scripts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_voice_recordings_id"), "voice_recordings", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_voice_recordings_language_id"),
        "voice_recordings",
        ["language_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_voice_recordings_script_id"),
        "voice_recordings",
        ["script_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_voice_recordings_status"), "voice_recordings", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_voice_recordings_user_id"),
        "voice_recordings",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "audio_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recording_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False),
        sa.Column("sentence_hint", sa.Text(), nullable=True),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["recording_id"],
            ["voice_recordings.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audio_chunks_id"), "audio_chunks", ["id"], unique=False)
    op.create_index(
        op.f("ix_audio_chunks_recording_id"),
        "audio_chunks",
        ["recording_id"],
        unique=False,
    )

    op.create_table(
        "transcriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("quality", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("is_consensus", sa.Boolean(), nullable=True),
        sa.Column("is_validated", sa.Boolean(), nullable=True),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["audio_chunks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["language_id"],
            ["languages.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transcriptions_chunk_id"), "transcriptions", ["chunk_id"], unique=False
    )
    op.create_index(
        op.f("ix_transcriptions_id"), "transcriptions", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_transcriptions_is_consensus"),
        "transcriptions",
        ["is_consensus"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transcriptions_is_validated"),
        "transcriptions",
        ["is_validated"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transcriptions_language_id"),
        "transcriptions",
        ["language_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transcriptions_user_id"), "transcriptions", ["user_id"], unique=False
    )

    op.create_table(
        "quality_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transcription_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), nullable=False),
        sa.Column(
            "decision",
            sa.Enum(
                "APPROVED",
                "REJECTED",
                "NEEDS_REVISION",
                "FLAGGED",
                name="reviewdecision",
            ),
            nullable=False,
        ),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["transcription_id"],
            ["transcriptions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_quality_reviews_decision"),
        "quality_reviews",
        ["decision"],
        unique=False,
    )
    op.create_index(
        op.f("ix_quality_reviews_id"), "quality_reviews", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_quality_reviews_reviewer_id"),
        "quality_reviews",
        ["reviewer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_quality_reviews_transcription_id"),
        "quality_reviews",
        ["transcription_id"],
        unique=False,
    )

    op.create_index(
        "ix_voice_recordings_user_status", "voice_recordings", ["user_id", "status"]
    )
    op.create_index(
        "ix_audio_chunks_recording_index",
        "audio_chunks",
        ["recording_id", "chunk_index"],
    )
    op.create_index(
        "ix_transcriptions_chunk_consensus",
        "transcriptions",
        ["chunk_id", "is_consensus"],
    )
    op.create_index(
        "ix_transcriptions_user_created", "transcriptions", ["user_id", "created_at"]
    )
    op.create_index(
        "ix_quality_reviews_transcription_decision",
        "quality_reviews",
        ["transcription_id", "decision"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_quality_reviews_transcription_decision", table_name="quality_reviews"
    )
    op.drop_index("ix_transcriptions_user_created", table_name="transcriptions")
    op.drop_index("ix_transcriptions_chunk_consensus", table_name="transcriptions")
    op.drop_index("ix_audio_chunks_recording_index", table_name="audio_chunks")
    op.drop_index("ix_voice_recordings_user_status", table_name="voice_recordings")

    op.drop_table("quality_reviews")
    op.drop_table("transcriptions")
    op.drop_table("audio_chunks")
    op.drop_table("voice_recordings")
    op.drop_table("scripts")
    op.drop_table("users")
    op.drop_table("languages")

    op.execute("DROP TYPE IF EXISTS reviewdecision")
    op.execute("DROP TYPE IF EXISTS recordingstatus")
    op.execute("DROP TYPE IF EXISTS durationcategory")
    op.execute("DROP TYPE IF EXISTS userrole")
