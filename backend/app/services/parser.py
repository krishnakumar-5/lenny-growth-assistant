import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def compute_content_hash(text: str) -> str:
    """Compute deterministic SHA-256 hex digest of file text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def repair_mojibake(text: str) -> str:
    """Diagnose and fix identifiable Windows-1252 / UTF-8 encoding mismatch sequences.

    Only applies repairs when specific known mojibake artifacts are present (e.g. 'itâ€™s' -> \"it's\").
    Does not alter valid text.
    """
    if not text:
        return text

    # Common Windows-1252 to UTF-8 double-encoding artifacts
    replacements = [
        ("â€™", "'"),
        ("â€˜", "'"),
        ("â€œ", '"'),
        ("â€\x9d", '"'),
        ("â€”", "—"),
        ("â€“", "–"),
        ("â€¦", "…"),
        ("Â ", " "),
        ("Ã©", "é"),
        ("Ã¨", "è"),
        ("Ã¡", "á"),
        ("Ã±", "ñ"),
    ]

    has_mojibake = any(bad in text for bad, _ in replacements) or "â€" in text
    if not has_mojibake:
        return text

    cleaned = text
    for bad, good in replacements:
        if bad in cleaned:
            cleaned = cleaned.replace(bad, good)

    # Handle trailing double-quote artifact where \x9d was dropped
    cleaned = re.sub(r"â€(?=[\s\.,;!?\)\n\r])", '"', cleaned)
    return cleaned


def read_file_text(file_path: Path) -> str:
    """Read file content strictly as UTF-8 with mojibake repair, falling back safely."""
    raw_bytes = file_path.read_bytes()
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content = raw_bytes.decode("utf-8", errors="replace")
        except Exception:
            content = file_path.read_text(encoding="latin-1")
    return repair_mojibake(content)


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

            try:
                import yaml
                loaded = yaml.safe_load(raw_meta)
                if isinstance(loaded, dict):
                    for k, v in loaded.items():
                        norm_key = str(k).strip().lower()
                        if isinstance(v, str):
                            metadata[norm_key] = v.strip()
                        else:
                            metadata[norm_key] = v
                    return metadata, body
            except Exception:
                pass

            # Fallback line-by-line parsing if YAML module fails
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
    if "title" in metadata and str(metadata["title"]).strip():
        return str(metadata["title"]).strip()

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

    content = read_file_text(file_path)

    if not content.strip():
        raise ValueError(f"Transcript file is empty: {file_path.name}")

    content_hash = compute_content_hash(content)
    metadata, body = parse_frontmatter(content)
    title = extract_title(content, file_path.name, metadata)

    # Detect presence of timestamped speaker dialogues in transcript body
    has_timestamps = bool(re.search(r"\*\*[^*]+\*\*\s*\(\d{1,2}:\d{2}(?::\d{2})?\):", body))
    metadata["speaker_timestamps_present"] = has_timestamps

    # Harmonize post_url and source_url
    if "post_url" in metadata and "source_url" not in metadata:
        metadata["source_url"] = metadata["post_url"]
    elif "source_url" in metadata and "post_url" not in metadata:
        metadata["post_url"] = metadata["source_url"]

    # Attach baseline provenance metadata safely
    metadata["source_filename"] = file_path.name
    metadata["extension"] = file_path.suffix.lower()
    metadata["char_count"] = len(content)

    return title, content, metadata, content_hash
