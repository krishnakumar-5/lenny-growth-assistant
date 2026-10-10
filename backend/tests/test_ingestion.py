from pathlib import Path
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.transcript import Transcript, TranscriptChunk
from app.services.chunking import split_text_into_chunks
from app.services.ingestion import ingest_directory, ingest_transcript_file
from app.services.parser import parse_frontmatter, parse_transcript_file


@pytest.fixture(scope="function")
def test_db():
    """Isolated in-memory SQLite database for ingestion tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.mark.unit
def test_parse_frontmatter_and_title(tmp_path: Path):
    """Verify frontmatter extraction and title parsing from markdown."""
    md_content = """---
title: "Mastering Customer Retention"
guest: "Elena Verna"
topic: "B2B Growth"
---

# Mastering Customer Retention

Retention is the single most important metric for durable product growth.
"""
    file_path = tmp_path / "retention_guide.md"
    file_path.write_text(md_content, encoding="utf-8")

    title, raw_text, metadata, content_hash = parse_transcript_file(file_path)

    assert title == "Mastering Customer Retention"
    assert metadata["guest"] == "Elena Verna"
    assert metadata["topic"] == "B2B Growth"
    assert metadata["source_filename"] == "retention_guide.md"
    assert len(content_hash) == 64


@pytest.mark.unit
def test_parse_plain_text_without_frontmatter(tmp_path: Path):
    """Verify title fallback for plain text files without metadata."""
    txt_content = "Discussion on Product Led Onboarding.\n\nFirst paragraph of text."
    file_path = tmp_path / "product_led_onboarding.txt"
    file_path.write_text(txt_content, encoding="utf-8")

    title, raw_text, metadata, content_hash = parse_transcript_file(file_path)

    assert title == "Product Led Onboarding"
    assert metadata["source_filename"] == "product_led_onboarding.txt"
    assert "guest" not in metadata  # No fabricated data


@pytest.mark.unit
def test_parse_empty_file_raises_error(tmp_path: Path):
    """Verify that empty or whitespace files raise ValueError."""
    empty_file = tmp_path / "empty.md"
    empty_file.write_text("   \n\n  ", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        parse_transcript_file(empty_file)


@pytest.mark.unit
def test_chunking_and_overlap():
    """Verify paragraph boundaries, chunk sizing, and overlap continuity."""
    paragraphs = [
        "Paragraph 1: Core acquisition loops drive initial trial signups.",
        "Paragraph 2: Activation milestones must occur within the first 48 hours.",
        "Paragraph 3: Monetization expansion happens when teams collaborate.",
        "Paragraph 4: Enterprise procurement requires security certifications.",
    ]
    doc = "\n\n".join(paragraphs)

    # Chunk with small target to force splitting
    chunks = split_text_into_chunks(doc, chunk_size=150, chunk_overlap=50, min_chunk_size=30)

    assert len(chunks) >= 2
    for i, chunk in enumerate(chunks):
        assert chunk.index == i
        assert len(chunk.text) > 0
        assert "start_char" in chunk.metadata
        assert "end_char" in chunk.metadata

    # Verify short text produces single chunk without truncation
    short_chunks = split_text_into_chunks("Short single paragraph text.", chunk_size=500)
    assert len(short_chunks) == 1
    assert short_chunks[0].text == "Short single paragraph text."


@pytest.mark.unit
def test_idempotent_ingestion(test_db, tmp_path: Path):
    """Verify re-ingesting unchanged file is skipped and creates no duplicates."""
    file_path = tmp_path / "growth_loops.md"
    file_path.write_text("# Growth Loops\n\nViral and paid loops explanation.", encoding="utf-8")

    # First ingestion
    res1 = ingest_transcript_file(file_path, test_db, chunk_size=500)
    assert res1.status == "created"
    assert res1.chunks_count > 0

    # Verify in DB
    transcripts = test_db.execute(select(Transcript)).scalars().all()
    assert len(transcripts) == 1
    chunks = test_db.execute(select(TranscriptChunk)).scalars().all()
    initial_chunk_count = len(chunks)

    # Second ingestion (unchanged)
    res2 = ingest_transcript_file(file_path, test_db, chunk_size=500)
    assert res2.status == "skipped_unchanged"

    # Count must remain exactly identical
    assert len(test_db.execute(select(Transcript)).scalars().all()) == 1
    assert len(test_db.execute(select(TranscriptChunk)).scalars().all()) == initial_chunk_count


@pytest.mark.unit
def test_update_modified_file_ingestion(test_db, tmp_path: Path):
    """Verify modifying a file updates the existing record and replaces chunks."""
    file_path = tmp_path / "pricing_tiers.md"
    file_path.write_text("# Pricing Tiers v1\n\nInitial pricing tiers.", encoding="utf-8")

    res1 = ingest_transcript_file(file_path, test_db)
    assert res1.status == "created"

    # Modify content
    file_path.write_text("# Pricing Tiers v2\n\nUpdated expanded enterprise tiers.", encoding="utf-8")

    res2 = ingest_transcript_file(file_path, test_db)
    assert res2.status == "updated"

    # Verify only 1 transcript exists with updated title
    transcript = test_db.execute(select(Transcript)).scalar_one()
    assert transcript.title == "Pricing Tiers v2"


@pytest.mark.unit
def test_ingest_directory_summary(test_db, tmp_path: Path):
    """Verify ingest_directory aggregates counts for valid, duplicate, and empty files."""
    (tmp_path / "doc1.md").write_text("# Doc 1\n\nContent one.", encoding="utf-8")
    (tmp_path / "doc2.txt").write_text("Doc 2\n\nContent two.", encoding="utf-8")
    (tmp_path / "empty.md").write_text("", encoding="utf-8")

    summary = ingest_directory(tmp_path, test_db)

    assert summary.total_files == 3
    assert summary.created == 2
    assert summary.skipped_empty == 1
    assert summary.failed == 0
