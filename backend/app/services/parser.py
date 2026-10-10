import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def compute_content_hash(text: str) -> str:
    """Compute deterministic SHA-256 hex digest of file text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Extract YAML-style frontmatter from markdown text if present.
    
    Returns (metadata_dict, remaining_body_text).
    """
    metadata: Dict[str, Any] = {}
    stripped = text.strip()

    if stripped.startswith("---"):
        parts = stripped.split("---", 2)
        if len(parts) >= 3:
            raw_meta = parts[1].strip()
            body = parts[2].strip()

            # Parse simple key-value pairs without requiring external YAML libraries
            for line in raw_meta.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower()
                    val = val.strip().strip('"').strip("'")
                    if val:
                        metadata[key] = val
            return metadata, body

    return metadata, text


def extract_title(raw_text: str, filename: str, metadata: Dict[str, Any]) -> str:
    """Determine document title from metadata, markdown headers, or filename."""
    # 1. From frontmatter metadata
    if "title" in metadata and metadata["title"].strip():
        return metadata["title"].strip()

    # 2. From first Markdown H1 or H2 header (# Title or ## Title)
    for line in raw_text.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("# ") or trimmed.startswith("## "):
            header_title = trimmed.lstrip("#").strip()
            if header_title:
                return header_title

    # 3. Fallback: humanize filename without extension
    stem = Path(filename).stem
    clean_stem = re.sub(r"[_\-]+", " ", stem).strip()
    return clean_stem.title() if clean_stem else "Untitled Transcript"


def parse_transcript_file(file_path: Path) -> Tuple[str, str, Dict[str, Any], str]:
    """Parse transcript file and return (title, raw_content, metadata, content_hash).
    
    Raises:
        ValueError: If file is empty or cannot be decoded.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Transcript file not found: {file_path}")

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = file_path.read_text(encoding="latin-1")

    if not content.strip():
        raise ValueError(f"Transcript file is empty: {file_path.name}")

    content_hash = compute_content_hash(content)
    metadata, body = parse_frontmatter(content)
    title = extract_title(content, file_path.name, metadata)

    # Attach baseline provenance metadata safely
    metadata["source_filename"] = file_path.name
    metadata["extension"] = file_path.suffix.lower()
    metadata["char_count"] = len(content)

    return title, content, metadata, content_hash
