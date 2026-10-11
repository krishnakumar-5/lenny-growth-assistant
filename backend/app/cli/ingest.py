import argparse
import logging
import os
from pathlib import Path
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import get_settings
from app.db.session import SessionLocal, check_db_connection
from app.services.ingestion import ingest_directory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingest_cli")


def main() -> int:
    """CLI entrypoint for transcript directory ingestion."""
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="Ingest podcast transcripts into The Lenny Growth Assistant knowledge base."
    )
    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        default=None,
        help="Custom transcript directory path (defaults to settings.transcripts_path).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Target maximum characters per chunk (default: 1000).",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Character overlap between consecutive chunks (default: 200).",
    )
    parser.add_argument(
        "--init-tables",
        action="store_true",
        help="Automatically initialize database schema if tables do not exist.",
    )
    parser.add_argument(
        "--purge-fixtures",
        action="store_true",
        help="Safely remove all synthetic benchmark and test fixture records from the database without touching authentic podcast episodes.",
    )

    args = parser.parse_args()

    # Verify database connectivity
    if not check_db_connection():
        logger.error("Cannot connect to database. Check DATABASE_URL and server status.")
        print("Error: Database connection check failed. Aborting ingestion.", file=sys.stderr)
        return 2

    # Handle fixture purging if requested
    if args.purge_fixtures:
        from app.models.transcript import Transcript
        from app.services.retrieval import purge_test_fixtures
        with SessionLocal() as db:
            purged = purge_test_fixtures(db)
            remaining = db.query(Transcript).count()
            print("=" * 60)
            print(f"Lenny Growth Assistant - Fixture Management")
            print("=" * 60)
            print(f"Successfully purged {purged} synthetic test fixture records from the database.")
            print(f"Remaining authentic dataset episodes preserved: {remaining}")
        return 0

    # Determine target directory: prefer CLI --dir, then LENNYS_DATASET_DIR, then TRANSCRIPTS_DIR
    if args.dir:
        target_dir = Path(args.dir).resolve()
    elif settings.authentic_dataset_path and settings.authentic_dataset_path.exists():
        target_dir = settings.authentic_dataset_path
    else:
        target_dir = settings.transcripts_path

    print("=" * 60)
    print(f"Lenny Growth Assistant - Transcript Ingestion Pipeline")
    print(f"Target Directory: {target_dir}")
    print(f"Chunk Config: size={args.chunk_size}, overlap={args.chunk_overlap}")
    print("=" * 60)

    if not target_dir.exists():
        logger.error("Target transcript directory does not exist: %s", target_dir)
        print(f"Error: Directory not found: {target_dir}", file=sys.stderr)
        return 1

    # Initialize tables if requested
    if args.init_tables:
        from app.db.init_db import init_db
        from app.db.session import engine
        init_db(engine)

    # Execute ingestion
    with SessionLocal() as db:
        summary = ingest_directory(
            target_dir,
            db,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )

    print("\n--- Ingestion Summary Report ---")
    print(f"Total files discovered: {summary.total_files}")
    print(f"  - Newly created:       {summary.created}")
    print(f"  - Updated (modified):  {summary.updated}")
    print(f"  - Skipped (unchanged): {summary.skipped_unchanged}")
    print(f"  - Skipped (empty):     {summary.skipped_empty}")
    print(f"  - Failed with errors:  {summary.failed}")
    print("--------------------------------")

    # Report individual failures or actions
    for res in summary.results:
        if res.status == "failed":
            print(f"  [FAILED]  {res.filename}: {res.message}", file=sys.stderr)
        elif res.status in ("created", "updated"):
            print(f"  [{res.status.upper()}] {res.filename} -> {res.chunks_count} chunks")

    if summary.has_failures:
        print("\nIngestion finished with errors.", file=sys.stderr)
        return 1

    print("\nIngestion completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
