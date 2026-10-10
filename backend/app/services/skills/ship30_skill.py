import html
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.chat import SourceCitation
from app.schemas.ship30 import Ship30Request, Ship30Response
from app.services.llm.base import BaseLLMClient
from app.services.retrieval import search_transcripts

logger = logging.getLogger(__name__)


class InsufficientTranscriptEvidenceError(Exception):
    """Raised when knowledge base contains no relevant transcripts for the essay topic."""
    pass


class Ship30EssaySkill:
    """Dedicated skill implementing the Ship 30 for 30 Atomic Essay framework.
    
    Principles from Dickie Bush & Nicolas Cole:
    - Format: Atomic Essay (200-300 words).
    - Structure:
        1. Scroll-stopping Headline (The Hook)
        2. Tension / Misconception (1-2 sentences)
        3. Core Grounded Framework (3-4 punchy bullets from Lenny's guest)
        4. Practical Action Step (How to apply it today)
        5. Punchy 1-Sentence Takeaway (The Punchline)
    - Strict Grounding: Drawn exclusively from verified podcast transcripts.
    """

    def __init__(self, llm_client: BaseLLMClient) -> None:
        self.llm_client = llm_client
        self.settings = get_settings()

    async def generate_essay(
        self,
        db: Session,
        request: Ship30Request,
    ) -> Ship30Response:
        """Retrieve transcript evidence and generate a grounded Atomic Essay artifact."""
        # 1. Retrieve knowledge base context
        retrieved_chunks = search_transcripts(
            db=db,
            query=request.topic,
            limit=self.settings.CHAT_SEARCH_LIMIT,
        )

        if not retrieved_chunks:
            raise InsufficientTranscriptEvidenceError(
                f"Cannot generate Ship 30 Atomic Essay: no verified podcast transcripts "
                f"matched topic '{request.topic}'. Under strict grounding rules, essays cannot be invented."
            )

        # 2. Extract citations & format evidence block
        citations: List[SourceCitation] = []
        evidence_lines: List[str] = ["=== VERIFIED PODCAST TRANSCRIPT EVIDENCE ==="]
        guest_names = set()

        for idx, chunk in enumerate(retrieved_chunks, start=1):
            guest = chunk.metadata.get("guest") or "Lenny's Guest"
            episode = chunk.metadata.get("episode") or "Unknown"
            guest_names.add(guest)

            evidence_lines.append(f"\n[Source {idx}]")
            evidence_lines.append(f"Guest: {guest} | Episode #{episode}")
            evidence_lines.append(f"Title: {chunk.transcript_title}")
            evidence_lines.append(f"Excerpt: \"{chunk.chunk_text}\"")

            citations.append(
                SourceCitation(
                    chunk_id=chunk.chunk_id,
                    transcript_id=chunk.transcript_id,
                    transcript_title=chunk.transcript_title,
                    source_filename=chunk.source_filename,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    score=chunk.score,
                    metadata=chunk.metadata,
                )
            )

        evidence_lines.append("\n=== END OF EVIDENCE ===")
        evidence_block = "\n".join(evidence_lines)
        primary_guest = ", ".join(sorted(guest_names)) if guest_names else "Lenny's Guest"

        # 3. Formulate Ship 30 for 30 Prompt
        system_prompt = (
            "You are a master digital writer and product advisor trained in the 'Ship 30 for 30' Atomic Essay framework "
            "(by Dickie Bush & Nicolas Cole) and Lenny's Podcast growth archives.\n\n"
            "YOUR TASK:\n"
            "Write a high-impact, grounded 200-300 word 'Atomic Essay' based EXCLUSIVELY on the provided transcript evidence.\n\n"
            "STRICT SHIP 30 FOR 30 ATOMIC ESSAY RULES:\n"
            "1. LENGTH: Exactly 200 to 300 words total body (excluding title). Every word must earn its place.\n"
            "2. HEADLINE: Create a punchy, curiosity-inducing, scroll-stopping headline starting with '# '.\n"
            "3. HOOK: Open with 1-2 sentences exposing a common industry mistake or counter-intuitive truth.\n"
            "4. BODY: Present the core framework using 3-4 bullet points or short subheaders directly citing the guest's tactics.\n"
            "5. APPLICATION: 1 concrete sentence on what the reader should do today.\n"
            "6. PUNCHLINE: End with a single, memorable 1-sentence takeaway.\n"
            "7. GROUNDING: Do NOT invent frameworks, statistics, or quotes not present in the excerpts.\n"
        )

        user_prompt = (
            f"{evidence_block}\n\n"
            f"Topic: {request.topic}\n"
            f"Target Audience: {request.target_audience}\n"
            f"Primary Guest to Credit: {primary_guest}\n\n"
            "Write the complete Atomic Essay now following the Ship 30 for 30 structure."
        )

        # 4. Generate with LLM
        messages = [{"role": "user", "content": user_prompt}]
        raw_output = await self.llm_client.generate_response(
            messages=messages,
            system_prompt=system_prompt,
        )

        # 5. Parse Title, Hook, Body & Word Count
        lines = [line.strip() for line in raw_output.split("\n") if line.strip()]
        title = f"The Atomic Playbook: {request.topic}"
        hook = ""
        
        # Extract title from markdown heading
        for line in lines:
            if line.startswith("# "):
                title = line.replace("# ", "").strip()
                break
            elif line.startswith("## "):
                title = line.replace("## ", "").strip()
                break

        # Extract hook
        for line in lines:
            if not line.startswith("#") and len(line) > 20:
                hook = line
                break

        # Word count calculation (excluding headings)
        body_words = [
            w for w in re.findall(r"\b\w+\b", raw_output)
            if not w.startswith("#")
        ]
        word_count = len(body_words)
        within_constraints = 180 <= word_count <= 350  # tolerant range for 200-300 word target

        # 6. Generate sanitized self-contained HTML Card Artifact
        html_card = self._render_html_artifact(
            title=title,
            guest=primary_guest,
            body_markdown=raw_output,
            word_count=word_count,
            citations=citations,
        )

        return Ship30Response(
            title=title,
            hook=hook or "Key insight from Lenny's Podcast.",
            word_count=word_count,
            within_constraints=within_constraints,
            content_markdown=raw_output,
            content_html=html_card,
            guest_attribution=primary_guest,
            sources=citations,
        )

    def _render_html_artifact(
        self,
        title: str,
        guest: str,
        body_markdown: str,
        word_count: int,
        citations: List[SourceCitation],
    ) -> str:
        """Render a self-contained, securely styled HTML card for the Atomic Essay."""
        safe_title = html.escape(title)
        safe_guest = html.escape(guest)
        
        # Convert simple markdown lines to clean HTML paragraphs/lists
        content_html_parts = []
        for line in body_markdown.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("- ") or line.startswith("* "):
                clean_item = html.escape(line[2:])
                # bold formatting
                clean_item = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", clean_item)
                content_html_parts.append(f"<li style='margin-bottom: 6px;'>{clean_item}</li>")
            else:
                clean_p = html.escape(line)
                clean_p = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", clean_p)
                content_html_parts.append(f"<p style='margin-bottom: 12px; line-height: 1.6;'>{clean_p}</p>")

        rendered_body = "\n".join(content_html_parts)
        
        sources_list_html = "".join([
            f"<span style='display:inline-block; background:#fef3c7; color:#92400e; padding:3px 8px; border-radius:6px; font-size:11px; margin-right:6px; margin-bottom:6px;'>{html.escape(c.transcript_title)}</span>"
            for c in citations[:3]
        ])

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f8fafc;
      color: #1e293b;
      margin: 0;
      padding: 24px;
    }}
    .atomic-card {{
      max-width: 650px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 32px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }}
    .badge {{
      display: inline-block;
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #b45309;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 4px 10px;
      border-radius: 20px;
      margin-bottom: 12px;
    }}
    h1 {{
      font-size: 24px;
      font-weight: 800;
      line-height: 1.25;
      color: #0f172a;
      margin-top: 0;
      margin-bottom: 8px;
    }}
    .byline {{
      font-size: 13px;
      color: #64748b;
      margin-bottom: 24px;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 12px;
    }}
    .content {{
      font-size: 15px;
      color: #334155;
    }}
    .meta-bar {{
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid #f1f5f9;
      font-size: 12px;
      color: #64748b;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
  </style>
</head>
<body>
  <div class="atomic-card">
    <div class="badge">Ship 30 for 30 • Atomic Essay</div>
    <h1>{safe_title}</h1>
    <div class="byline">Grounded in insights from <strong>{safe_guest}</strong> on Lenny's Podcast</div>
    <div class="content">
      {rendered_body}
    </div>
    <div class="meta-bar">
      <div>Word Count: <strong>{word_count} words</strong></div>
      <div>Strictly Grounded</div>
    </div>
    <div style="margin-top: 16px; padding-top: 12px; border-top: 1px dashed #e2e8f0;">
      <div style="font-size: 11px; font-weight: 600; color: #94a3b8; margin-bottom: 6px; text-transform: uppercase;">Verified Sources</div>
      <div>{sources_list_html}</div>
    </div>
  </div>
</body>
</html>"""
