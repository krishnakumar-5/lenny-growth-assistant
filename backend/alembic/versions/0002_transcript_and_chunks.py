"""add transcripts and transcript_chunks tables

Revision ID: 0002_transcript_and_chunks
Revises: 0001_initial_tables
Create Date: 2026-10-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_transcript_and_chunks"
down_revision: Union[str, None] = "0001_initial_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transcripts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("meta_info", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transcripts_id"), "transcripts", ["id"], unique=False)
    op.create_index(op.f("ix_transcripts_source_id"), "transcripts", ["source_id"], unique=True)
    op.create_index(op.f("ix_transcripts_title"), "transcripts", ["title"], unique=False)
    op.create_index(op.f("ix_transcripts_content_hash"), "transcripts", ["content_hash"], unique=False)

    op.create_table(
        "transcript_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("transcript_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("meta_info", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["transcript_id"],
            ["transcripts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transcript_chunks_id"), "transcript_chunks", ["id"], unique=False)
    op.create_index(op.f("ix_transcript_chunks_transcript_id"), "transcript_chunks", ["transcript_id"], unique=False)
    op.create_index(op.f("ix_transcript_chunks_chunk_index"), "transcript_chunks", ["chunk_index"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transcript_chunks_chunk_index"), table_name="transcript_chunks")
    op.drop_index(op.f("ix_transcript_chunks_transcript_id"), table_name="transcript_chunks")
    op.drop_index(op.f("ix_transcript_chunks_id"), table_name="transcript_chunks")
    op.drop_table("transcript_chunks")

    op.drop_index(op.f("ix_transcripts_content_hash"), table_name="transcripts")
    op.drop_index(op.f("ix_transcripts_title"), table_name="transcripts")
    op.drop_index(op.f("ix_transcripts_source_id"), table_name="transcripts")
    op.drop_index(op.f("ix_transcripts_id"), table_name="transcripts")
    op.drop_table("transcripts")
