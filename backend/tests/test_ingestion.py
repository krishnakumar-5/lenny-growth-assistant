import json
from pathlib import Path
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.transcript import Transcript, TranscriptChunk
from app.services.chunking import split_text_into_chunks
from app.services.ingestion import ingest_directory, ingest_transcript_file, load_dataset_index
from app.services.parser import parse_frontmatter, parse_transcript_file, repair_mojibake
from app.services.retrieval import search_transcripts


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


@pytest.mark.unit
def test_mojibake_repair_diagnostics():
    """Verify that repair_mojibake fixes known CP1252/UTF-8 double-encoding artifacts without mutating clean text."""
    # CP1252 mojibake artifacts
    dirty = "Itâ€™s an â€œauthenticâ€ episode â€” with cafÃ© and jalapeÃ±o."
    fixed = repair_mojibake(dirty)
    assert fixed == "It's an \"authentic\" episode — with café and jalapeño."

    # Clean text should remain strictly unaltered
    clean = "Elena Verna discusses PLG, freemium, and reverse trials."
    assert repair_mojibake(clean) == clean

    # Empty text
    assert repair_mojibake("") == ""


@pytest.mark.unit
def test_parse_authentic_dataset_yaml_frontmatter(tmp_path: Path):
    """Verify parsing rich YAML frontmatter matching Lenny's Data starter dataset."""
    sample_content = """---
title: "Adam Mosseri: AI is a tailwind for authenticity"
date: "2026-07-09"
type: "podcast"
guest: "Adam Mosseri"
channel: "Lenny's Podcast"
post_url: "https://www.lennysnewsletter.com/p/adam-mosseri-ai-is-a-tailwind-for"
description: "AI is a tailwind for authenticity, covering product design and leadership."
word_count: 12640
youtube_url: "https://www.youtube.com/watch?v=sample123"
video_id: "sample123"
---

**Adam Mosseri** (00:00:00):
No, I think taste matters a ton. In a world where it's easier to build things, it's more important to make sure that your time is spent figuring out what you should be building in the first place.

**Lenny Rachitsky** (00:00:23):
What's something that the Instagram algorithm knows about human behavior that people may not realize?
"""
    file_path = tmp_path / "adam-mosseri.md"
    file_path.write_text(sample_content, encoding="utf-8")

    title, raw_content, metadata, content_hash = parse_transcript_file(file_path)

    assert title == "Adam Mosseri: AI is a tailwind for authenticity"
    assert metadata["guest"] == "Adam Mosseri"
    assert metadata["date"] == "2026-07-09"
    assert metadata["post_url"] == "https://www.lennysnewsletter.com/p/adam-mosseri-ai-is-a-tailwind-for"
    assert metadata["source_url"] == "https://www.lennysnewsletter.com/p/adam-mosseri-ai-is-a-tailwind-for"
    assert metadata["youtube_url"] == "https://www.youtube.com/watch?v=sample123"
    assert metadata["video_id"] == "sample123"
    assert metadata["word_count"] == 12640
    assert metadata["speaker_timestamps_present"] is True
    assert metadata["source_filename"] == "adam-mosseri.md"
    assert len(content_hash) == 64


@pytest.mark.unit
def test_load_dataset_index_catalog(tmp_path: Path):
    """Verify loading and resolving index.json catalog metadata."""
    index_data = {
        "schema_version": "2.0",
        "podcasts": [
            {
                "title": "Molly Graham on Burnout",
                "filename": "podcasts/molly-graham-2.md",
                "word_count": 18220,
                "date": "2026-09-27",
                "guest": "Molly Graham",
                "post_url": "https://www.lennysnewsletter.com/p/the-grief-loneliness-and-burnout",
            }
        ]
    }
    index_file = tmp_path / "index.json"
    index_file.write_text(json.dumps(index_data), encoding="utf-8")

    lookup = load_dataset_index(tmp_path)
    assert "podcasts/molly-graham-2.md" in lookup
    assert "molly-graham-2.md" in lookup
    assert "molly-graham-2" in lookup

    entry = lookup["molly-graham-2.md"]
    assert entry["guest"] == "Molly Graham"
    assert entry["post_url"] == "https://www.lennysnewsletter.com/p/the-grief-loneliness-and-burnout"


@pytest.mark.unit
def test_ingest_directory_with_podcasts_subdirectory_and_idempotency(test_db, tmp_path: Path):
    """Verify auto-discovery of podcasts/ subdirectory, index metadata merging, and idempotency."""
    # Create directory structure matching external dataset
    podcasts_dir = tmp_path / "podcasts"
    podcasts_dir.mkdir()

    index_data = {
        "podcasts": [
            {
                "title": "Brian Balfour Strategy",
                "filename": "podcasts/brian.md",
                "guest": "Brian Balfour",
                "post_url": "https://www.lennysnewsletter.com/p/brian-balfour",
            }
        ]
    }
    (tmp_path / "index.json").write_text(json.dumps(index_data), encoding="utf-8")

    sample_md = """---
title: "Brian Balfour Strategy"
date: "2026-08-01"
type: "podcast"
guest: "Brian Balfour"
word_count: 500
---

**Brian Balfour** (00:00:10):
Loops compound while linear funnels hit diminishing returns over time.
"""
    (podcasts_dir / "brian.md").write_text(sample_md, encoding="utf-8")

    # First ingestion run
    summary1 = ingest_directory(tmp_path, test_db)
    assert summary1.total_files == 1
    assert summary1.created == 1
    assert summary1.skipped_unchanged == 0

    # Verify metadata merged post_url from index.json
    transcript = test_db.execute(select(Transcript).where(Transcript.source_id == "brian")).scalar_one()
    assert transcript.meta_info.get("post_url") == "https://www.lennysnewsletter.com/p/brian-balfour"
    assert transcript.meta_info.get("source_url") == "https://www.lennysnewsletter.com/p/brian-balfour"
    assert transcript.meta_info.get("synthetic_test_data") is False
    assert transcript.meta_info.get("is_test_fixture") is False

    # Second ingestion run (idempotency check)
    summary2 = ingest_directory(tmp_path, test_db)
    assert summary2.total_files == 1
    assert summary2.created == 0
    assert summary2.skipped_unchanged == 1

    # Verify no duplicate records
    all_transcripts = test_db.execute(select(Transcript)).scalars().all()
    assert len(all_transcripts) == 1


@pytest.mark.unit
def test_retrieval_preserves_authentic_citations(test_db, tmp_path: Path):
    """Verify that search_transcripts returns SearchResultItem with authentic post_url and metadata."""
    sample_md = """---
title: "Adam Mosseri: AI and Authenticity"
guest: "Adam Mosseri"
date: "2026-07-09"
post_url: "https://www.lennysnewsletter.com/p/adam-mosseri-ai"
---

**Adam Mosseri** (00:00:00):
In a world where there is an abundance of synthetic content, authenticity becomes paramount.
"""
    file_path = tmp_path / "adam-mosseri.md"
    file_path.write_text(sample_md, encoding="utf-8")

    ingest_transcript_file(file_path, test_db)

    results = search_transcripts(test_db, "authenticity synthetic", limit=5)
    assert len(results) >= 1
    top_result = results[0]
    assert top_result.transcript_title == "Adam Mosseri: AI and Authenticity"
    assert top_result.metadata.get("post_url") == "https://www.lennysnewsletter.com/p/adam-mosseri-ai"
    assert top_result.metadata.get("source_url") == "https://www.lennysnewsletter.com/p/adam-mosseri-ai"
    assert top_result.metadata.get("guest") == "Adam Mosseri"
    assert top_result.metadata.get("synthetic_test_data") is False
