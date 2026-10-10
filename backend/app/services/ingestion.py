from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transcript import Transcript, TranscriptChunk
from app.services.chunking import split_text_into_chunks
from app.services.parser import parse_transcript_file

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Outcome of processing an individual transcript file."""

    filename: str
    status: str  # "created", "updated", "skipped_unchanged", "skipped_empty", "failed"
    transcript_id: Optional[uuid.UUID] = None
    chunks_count: int = 0
    message: Optional[str] = None


@dataclass
class IngestionSummary:
    """Aggregate report across a directory ingestion run."""

    total_files: int = 0
    created: int = 0
    updated: int = 0
    skipped_unchanged: int = 0
    skipped_empty: int = 0
    failed: int = 0
    results: List[IngestionResult] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return self.failed > 0


def ingest_transcript_file(
    file_path: Path,
    db: Session,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> IngestionResult:
    """Ingest or update a single transcript file idempotently.
    
    If the file content is unchanged (matched by SHA-256 hash), ingestion is skipped.
    If the file content is modified, chunks are regenerated and updated.
    """
    filename = file_path.name

    # 1. Parse file safely
    try:
        title, content, metadata, content_hash = parse_transcript_file(file_path)
    except ValueError as ve:
        # File is empty or whitespace
        logger.warning("Skipping empty transcript file: %s", filename)
        return IngestionResult(
            filename=filename,
            status="skipped_empty",
            message=str(ve),
        )
    except Exception as exc:
        logger.error("Failed to parse transcript file %s: %s", filename, exc)
        return IngestionResult(
            filename=filename,
            status="failed",
            message=f"Parse error: {exc}",
        )

    # Use file stem as unique source identifier
    source_id = file_path.stem.lower().strip()

    try:
        # 2. Check for existing transcript by source_id
        existing = db.execute(
            select(Transcript).where(Transcript.source_id == source_id)
        ).scalar_one_or_none()

        if existing:
            # Idempotency check: if hash matches, do not recreate or duplicate
            if existing.content_hash == content_hash:
                logger.info("Transcript '%s' unchanged. Skipping.", filename)
                return IngestionResult(
                    filename=filename,
                    status="skipped_unchanged",
                    transcript_id=existing.id,
                    chunks_count=len(existing.chunks),
                    message="Content hash matches existing record",
                )

            # Content has changed -> update existing record and replace chunks
            logger.info("Updating existing transcript '%s' with new content.", filename)
            existing.title = title
            existing.source_filename = filename
            existing.raw_content = content
            existing.content_hash = content_hash
            existing.meta_info = metadata

            # Clear existing chunks (cascade handles deletion)
            existing.chunks.clear()
            db.flush()

            # Split into chunks
            chunks_data = split_text_into_chunks(content, chunk_size, chunk_overlap)
            for c in chunks_data:
                chunk = TranscriptChunk(
                    transcript_id=existing.id,
                    chunk_index=c.index,
                    chunk_text=c.text,
                    char_count=c.char_count,
                    meta_info=c.metadata,
                )
                existing.chunks.append(chunk)

            db.commit()
            db.refresh(existing)

            return IngestionResult(
                filename=filename,
                status="updated",
                transcript_id=existing.id,
                chunks_count=len(existing.chunks),
                message="Updated existing record and regenerated chunks",
            )

        # 3. Create brand new transcript
        new_transcript = Transcript(
            source_id=source_id,
            title=title,
            source_filename=filename,
            content_hash=content_hash,
            raw_content=content,
            meta_info=metadata,
        )
        db.add(new_transcript)
        db.flush()

        # Split into chunks and attach
        chunks_data = split_text_into_chunks(content, chunk_size, chunk_overlap)
        for c in chunks_data:
            chunk = TranscriptChunk(
                transcript_id=new_transcript.id,
                chunk_index=c.index,
                chunk_text=c.text,
                char_count=c.char_count,
                meta_info=c.metadata,
            )
            new_transcript.chunks.append(chunk)

        db.commit()
        db.refresh(new_transcript)

        return IngestionResult(
            filename=filename,
            status="created",
            transcript_id=new_transcript.id,
            chunks_count=len(new_transcript.chunks),
            message="Successfully ingested and chunked",
        )

    except Exception as exc:
        db.rollback()
        logger.exception("Database error while ingesting %s: %s", filename, exc)
        return IngestionResult(
            filename=filename,
            status="failed",
            message=f"Database error: {exc}",
        )


def ingest_directory(
    directory_path: Path,
    db: Session,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> IngestionSummary:
    """Ingest all supported (.md, .txt) transcript files in a target directory."""
    summary = IngestionSummary()

    if not directory_path.exists() or not directory_path.is_dir():
        logger.warning("Directory does not exist: %s", directory_path)
        return summary

    files = [
        f for f in sorted(directory_path.iterdir())
        if f.is_file() and f.suffix.lower() in [".md", ".txt"]
    ]

    summary.total_files = len(files)

    for file_path in files:
        result = ingest_transcript_file(
            file_path,
            db,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        summary.results.append(result)

        if result.status == "created":
            summary.created += 1
        elif result.status == "updated":
            summary.updated += 1
        elif result.status == "skipped_unchanged":
            summary.skipped_unchanged += 1
        elif result.status == "skipped_empty":
            summary.skipped_empty += 1
        elif result.status == "failed":
            summary.failed += 1

    return summary
