from dataclasses import dataclass
import re
from typing import Any, Dict, List


@dataclass
class ChunkResult:
    """Represents an individual text chunk ready for persistence."""

    index: int
    text: str
    char_count: int
    metadata: Dict[str, Any]


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    min_chunk_size: int = 100,
) -> List[ChunkResult]:
    """Split text into overlapping chunks respecting natural paragraph boundaries.
    
    Args:
        text: Raw document text to partition.
        chunk_size: Target maximum characters per chunk.
        chunk_overlap: Approximate characters of overlap between consecutive chunks.
        min_chunk_size: Threshold below which trailing fragments are merged rather
            than kept as isolated fragments.
            
    Returns:
        List of ChunkResult items containing sequence index, text, and offsets.
    """
    clean_text = text.strip()
    if not clean_text:
        return []

    # If document is small enough, return as a single chunk
    if len(clean_text) <= chunk_size:
        return [
            ChunkResult(
                index=0,
                text=clean_text,
                char_count=len(clean_text),
                metadata={"start_char": 0, "end_char": len(clean_text)},
            )
        ]

    # Split on double line breaks (paragraphs)
    raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", clean_text) if p.strip()]

    # If any paragraph is individually longer than chunk_size, split by sentences
    units: List[str] = []
    for para in raw_paragraphs:
        if len(para) <= chunk_size:
            units.append(para)
        else:
            # Sentence split
            sentences = re.split(r"(?<=[.!?])\s+", para)
            for s in sentences:
                s = s.strip()
                if s:
                    units.append(s)

    chunks: List[ChunkResult] = []
    current_units: List[str] = []
    current_len = 0
    start_offset = 0

    for unit in units:
        unit_len = len(unit) + 2  # account for separator

        if current_units and (current_len + unit_len > chunk_size):
            # Form chunk from current units
            chunk_body = "\n\n".join(current_units)
            end_offset = start_offset + len(chunk_body)
            chunks.append(
                ChunkResult(
                    index=len(chunks),
                    text=chunk_body,
                    char_count=len(chunk_body),
                    metadata={"start_char": start_offset, "end_char": end_offset},
                )
            )

            # Calculate overlap: keep recent units up to chunk_overlap chars
            overlap_units: List[str] = []
            overlap_len = 0
            for prev_unit in reversed(current_units):
                if overlap_len + len(prev_unit) <= chunk_overlap:
                    overlap_units.insert(0, prev_unit)
                    overlap_len += len(prev_unit) + 2
                else:
                    break

            current_units = overlap_units + [unit]
            current_len = sum(len(u) + 2 for u in current_units)
            start_offset = max(0, end_offset - overlap_len)
        else:
            current_units.append(unit)
            current_len += unit_len

    # Add remaining units
    if current_units:
        final_body = "\n\n".join(current_units)
        # If final chunk is too tiny and we already have prior chunks, append to previous
        if len(final_body) < min_chunk_size and chunks:
            prev = chunks[-1]
            merged_body = prev.text + "\n\n" + final_body
            chunks[-1] = ChunkResult(
                index=prev.index,
                text=merged_body,
                char_count=len(merged_body),
                metadata={
                    "start_char": prev.metadata["start_char"],
                    "end_char": prev.metadata["start_char"] + len(merged_body),
                },
            )
        else:
            chunks.append(
                ChunkResult(
                    index=len(chunks),
                    text=final_body,
                    char_count=len(final_body),
                    metadata={
                        "start_char": start_offset,
                        "end_char": start_offset + len(final_body),
                    },
                )
            )

    return chunks
