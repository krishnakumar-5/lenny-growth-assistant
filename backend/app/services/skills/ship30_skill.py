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
    """Dedicated skill implementing the Ship 30 for 30 growth essay framework.

    Principles adapted from Dickie Bush & Nicolas Cole for long-form synthesis:
    - Target Length: ~1,250 words (strictly targeting 1,150–1,350 words for the body, excluding title and sources).
    - Structure:
        1. Scroll-stopping Headline (The Hook)
        2. Tension / Misconception & Introduction (Exposing common mistakes, setting stakes)
        3. Descriptive Markdown Headings (##, ###) with skimmable bullet points and bold emphasis
        4. Practical Examples & Applications supported directly by retrieved evidence
        5. Concluding Takeaway & Memorable Punchline
    - Strict Grounding: Drawn exclusively from verified podcast transcripts (no invented facts or quotes).
    """

    MIN_BODY_WORDS: int = 1150
    MAX_BODY_WORDS: int = 1350
    TARGET_BODY_WORDS: int = 1250
    MAX_RETRIES: int = 1

    def __init__(self, llm_client: BaseLLMClient) -> None:
        self.llm_client = llm_client
        self.settings = get_settings()

    async def generate_essay(
        self,
        db: Session,
        request: Ship30Request,
    ) -> Ship30Response:
        """Retrieve transcript evidence and generate a grounded long-form essay artifact."""
        # 1. Retrieve knowledge base context (excluding synthetic fixtures)
        retrieved_chunks = search_transcripts(
            db=db,
            query=request.topic,
            limit=max(self.settings.CHAT_SEARCH_LIMIT, 6),
            exclude_synthetic=True,
        )

        if not retrieved_chunks:
            raise InsufficientTranscriptEvidenceError(
                f"Cannot generate Ship 30 Essay: no verified podcast transcripts "
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
            post_url = chunk.metadata.get("post_url") or chunk.metadata.get("source_url")
            if post_url:
                evidence_lines.append(f"Source URL: {post_url}")
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

        # 3. Formulate System Prompt & User Prompt
        system_prompt = (
            "You are a master digital writer and executive growth advisor trained in the 'Ship 30 for 30' writing architecture "
            "(by Dickie Bush & Nicolas Cole) and Lenny's Podcast growth archives.\n\n"
            "YOUR TASK:\n"
            "Write a comprehensive, deeply grounded long-form growth essay of approximately 1,250 words "
            "(strictly targeting 1,150 to 1,350 words for the essay body, excluding the title and references), "
            "synthesizing verified podcast transcript evidence from Lenny's Podcast into an actionable masterclass.\n\n"
            "ESSAY STRUCTURE & SHIP 30 PRINCIPLES:\n"
            "1. SCROLL-STOPPING HEADLINE: Open with a compelling '# [Headline]' that delivers a sharp, provocative hook.\n"
            "2. THE HOOK & INTRODUCTION: Open with 1-2 punchy sentences exposing a common startup mistake or mental trap. "
            "Follow with a clear introduction establishing the stakes, why conventional wisdom fails, and what the framework achieves.\n"
            "3. DESCRIPTIVE MARKDOWN HEADINGS: Structure the essay using descriptive ## and ### headings:\n"
            "   - Section 1: The Core Problem & Conventional Myth (Why the standard playbook fails)\n"
            "   - Section 2: The Grounded Framework & Operating Mechanics (Deconstruct the guest's model using skimmable bullet points and bold key terms)\n"
            "   - Section 3: Real-World Applications & Edge Cases (Practical nuances, trade-offs, and metrics derived from the transcript excerpts)\n"
            "   - Section 4: The Tactical Implementation Playbook (Step-by-step actions product teams can execute today)\n"
            "   - Section 5: The Concluding Takeaway (A definitive summary and memorable 1-sentence punchline)\n"
            "4. SKIMMABILITY & FORMATTING: Use descriptive headings (##, ###), concise paragraphs, formatted bullet lists (- or *), "
            "and selective bold emphasis (**bold**) for core insights.\n"
            "5. STRICT GROUNDING & ACCURACY: Base all mechanics, frameworks, guest perspectives, and examples strictly on the provided transcript evidence. "
            "Do NOT invent facts, statistics, guest opinions, or external frameworks. Never label generated content as a direct quote unless the exact quote appears in the excerpts.\n"
            "6. LENGTH & DENSITY: Target 1,150 to 1,350 words in the body. Do NOT pad with generic fluff or repeated platitudes; "
            "instead, thoroughly explore the operational mechanisms, trade-offs, and implementation details substantiated by the evidence.\n"
        )

        user_prompt = (
            f"{evidence_block}\n\n"
            f"Topic: {request.topic}\n"
            f"Target Audience: {request.target_audience}\n"
            f"Primary Guest(s) to Credit: {primary_guest}\n\n"
            "Write the complete ~1,250-word grounded essay now following the Ship 30 for 30 architecture (target: 1,150–1,350 words in the body). "
            "Start directly with '# [Headline]'."
        )

        # 4. Generate with LLM
        messages = [{"role": "user", "content": user_prompt}]
        raw_output = await self.llm_client.generate_response(
            messages=messages,
            system_prompt=system_prompt,
        )

        # 5. Extract Title, Hook, Body & Word Count
        title, hook, body = self._extract_title_hook_and_body(raw_output, request.topic)
        word_count = self._count_body_words(body)

        # 6. Bounded Retry if outside target range (max 1 retry)
        current_output = raw_output
        if not (self.MIN_BODY_WORDS <= word_count <= self.MAX_BODY_WORDS) and self.MAX_RETRIES > 0:
            logger.info(
                "Ship30 essay body word count (%d) outside target range [%d, %d]. Initiating bounded retry.",
                word_count,
                self.MIN_BODY_WORDS,
                self.MAX_BODY_WORDS,
            )
            if word_count < self.MIN_BODY_WORDS:
                retry_prompt = (
                    f"Your previous draft had {word_count} words in the body, which is below the target range of "
                    f"{self.MIN_BODY_WORDS} to {self.MAX_BODY_WORDS} words (~1,250 words).\n\n"
                    f"Please expand the essay to reach between {self.MIN_BODY_WORDS} and {self.MAX_BODY_WORDS} words for the body.\n"
                    f"Elaborate on the practical mechanisms, operational implementation steps, and concrete growth trade-offs "
                    f"explained by {primary_guest} in the verified transcript excerpts.\n\n"
                    f"CRITICAL GROUNDING RULES:\n"
                    f"- Do NOT invent statistics, metrics, or frameworks not found in the excerpts.\n"
                    f"- Do NOT use repetitive filler or generic fluff.\n"
                    f"- Expand on the specific implementation details, organizational challenges, and metrics substantiated by the evidence.\n\n"
                    f"Return the complete revised essay now starting with '# [Headline]'."
                )
            else:
                retry_prompt = (
                    f"Your previous draft had {word_count} words in the body, which exceeds the target range of "
                    f"{self.MIN_BODY_WORDS} to {self.MAX_BODY_WORDS} words (~1,250 words).\n\n"
                    f"Please edit and tighten the essay so the body is strictly between {self.MIN_BODY_WORDS} and {self.MAX_BODY_WORDS} words.\n"
                    f"Keep all descriptive headings, core framework mechanics, evidence attribution, and the concluding punchline.\n\n"
                    f"Return the complete revised essay now starting with '# [Headline]'."
                )

            retry_messages = [
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": current_output},
                {"role": "user", "content": retry_prompt},
            ]

            try:
                revised_output = await self.llm_client.generate_response(
                    messages=retry_messages,
                    system_prompt=system_prompt,
                )
                revised_title, revised_hook, revised_body = self._extract_title_hook_and_body(
                    revised_output, request.topic
                )
                revised_word_count = self._count_body_words(revised_body)
                current_output = revised_output
                title, hook, body = revised_title, revised_hook, revised_body
                word_count = revised_word_count
            except Exception as exc:
                logger.warning("Bounded retry failed (%s). Retaining original draft.", exc)

        within_constraints = (self.MIN_BODY_WORDS <= word_count <= self.MAX_BODY_WORDS)

        # 7. Render Sanitized Self-Contained HTML Artifact
        html_card = self._render_html_artifact(
            title=title,
            guest=primary_guest,
            body_markdown=body,
            word_count=word_count,
            within_constraints=within_constraints,
            citations=citations,
        )

        return Ship30Response(
            title=title,
            hook=hook,
            word_count=word_count,
            within_constraints=within_constraints,
            content_markdown=current_output,
            content_html=html_card,
            guest_attribution=primary_guest,
            sources=citations,
        )

    def _extract_title_hook_and_body(self, raw_output: str, default_topic: str) -> Tuple[str, str, str]:
        """Extract headline title, hook, and isolated essay body excluding title and trailing sources."""
        lines = raw_output.split("\n")
        title = f"The Growth Playbook: {default_topic}"
        title_line_idx = -1

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                title_line_idx = idx
                break
            elif stripped.startswith("## ") and title_line_idx == -1:
                title = stripped[3:].strip()
                title_line_idx = idx
                break

        # Extract hook (first substantive non-header paragraph)
        hook = ""
        for idx, line in enumerate(lines):
            if idx == title_line_idx:
                continue
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and len(stripped) > 20:
                hook = stripped
                break

        # Body: remove title line if present
        body_lines = [line for idx, line in enumerate(lines) if idx != title_line_idx]
        body_raw = "\n".join(body_lines).strip()

        # Strip any trailing sources/references/citations section
        split_sections = re.split(
            r"\n#{1,3}\s*(?:Sources|References|Citations|Verified Sources)\b",
            body_raw,
            flags=re.IGNORECASE,
        )
        body = split_sections[0].strip()

        return title, hook or "Key framework from Lenny's Podcast.", body

    def _count_body_words(self, body: str) -> int:
        """Accurately counts words in the essay body, ignoring markdown formatting tokens."""
        # Remove markdown header syntax e.g. ##, ###
        cleaned = re.sub(r"^#{1,6}\s+", "", body, flags=re.MULTILINE)
        # Remove bullet markers e.g. - or *
        cleaned = re.sub(r"^[\*\-]\s+", "", cleaned, flags=re.MULTILINE)
        # Match alphanumeric words, preserving internal apostrophes
        words = re.findall(r"\b[a-zA-Z0-9]+(?:['’][a-zA-Z0-9]+)?\b", cleaned)
        return len(words)

    def _render_markdown_body_to_html(self, body_markdown: str, skip_title: Optional[str] = None) -> str:
        """Safely converts Markdown body to sanitized HTML.

        Renders headings (h2, h3, h4), lists (ul/li, ol/li), paragraphs (p), and bold text (strong).
        All content is strictly escaped with html.escape() to prevent HTML injection.
        """
        blocks = [b.strip() for b in re.split(r"\n\s*\n+", body_markdown) if b.strip()]
        html_parts: List[str] = []

        for block in blocks:
            # Check if block is a heading
            if block.startswith("#"):
                lines = block.split("\n")
                first_line = lines[0].strip()
                rest = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

                if first_line.startswith("# "):
                    heading_text = first_line[2:].strip()
                    if not (skip_title and heading_text.lower() == skip_title.lower()):
                        safe_h = html.escape(heading_text)
                        safe_h = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe_h)
                        html_parts.append(
                            f"<h2 style='font-size: 20px; font-weight: 800; color: #0f172a; margin-top: 28px; margin-bottom: 12px; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px;'>{safe_h}</h2>"
                        )
                elif first_line.startswith("## "):
                    safe_h = html.escape(first_line[3:].strip())
                    safe_h = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe_h)
                    html_parts.append(
                        f"<h2 style='font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 24px; margin-bottom: 10px;'>{safe_h}</h2>"
                    )
                elif first_line.startswith("### "):
                    safe_h = html.escape(first_line[4:].strip())
                    safe_h = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe_h)
                    html_parts.append(
                        f"<h3 style='font-size: 16px; font-weight: 600; color: #1e293b; margin-top: 20px; margin-bottom: 8px;'>{safe_h}</h3>"
                    )
                elif first_line.startswith("#### "):
                    safe_h = html.escape(first_line[5:].strip())
                    safe_h = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe_h)
                    html_parts.append(
                        f"<h4 style='font-size: 14px; font-weight: 600; color: #334155; margin-top: 16px; margin-bottom: 6px;'>{safe_h}</h4>"
                    )

                if rest:
                    safe_rest = html.escape(rest)
                    safe_rest = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe_rest)
                    html_parts.append(f"<p style='margin-bottom: 16px; line-height: 1.7; color: #334155;'>{safe_rest}</p>")
                continue

            # Check if block is an unordered list
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if all(re.match(r"^[-*]\s+", l) for l in lines):
                items = []
                for l in lines:
                    item_text = re.sub(r"^[-*]\s+", "", l)
                    safe_item = html.escape(item_text)
                    safe_item = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe_item)
                    items.append(f"<li style='margin-bottom: 8px; line-height: 1.6; color: #334155;'>{safe_item}</li>")
                items_str = "\n".join(items)
                html_parts.append(f"<ul style='margin-top: 8px; margin-bottom: 16px; padding-left: 24px;'>\n{items_str}\n</ul>")
                continue

            # Check if block is an ordered list
            if all(re.match(r"^\d+\.\s+", l) for l in lines):
                items = []
                for l in lines:
                    item_text = re.sub(r"^\d+\.\s+", "", l)
                    safe_item = html.escape(item_text)
                    safe_item = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe_item)
                    items.append(f"<li style='margin-bottom: 8px; line-height: 1.6; color: #334155;'>{safe_item}</li>")
                items_str = "\n".join(items)
                html_parts.append(f"<ol style='margin-top: 8px; margin-bottom: 16px; padding-left: 24px;'>\n{items_str}\n</ol>")
                continue

            # Standard paragraph block
            joined_text = " ".join(lines)
            safe_p = html.escape(joined_text)
            safe_p = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", safe_p)
            html_parts.append(f"<p style='margin-bottom: 16px; line-height: 1.7; color: #334155;'>{safe_p}</p>")

        return "\n".join(html_parts)

    def _render_html_artifact(
        self,
        title: str,
        guest: str,
        body_markdown: str,
        word_count: int,
        within_constraints: bool,
        citations: List[SourceCitation],
    ) -> str:
        """Render a self-contained, securely styled HTML card for the essay."""
        safe_title = html.escape(title)
        safe_guest = html.escape(guest)

        rendered_body = self._render_markdown_body_to_html(body_markdown, skip_title=title)

        source_badges: List[str] = []
        for c in citations[:6]:
            safe_c_title = html.escape(c.transcript_title)
            safe_c_guest = html.escape(c.metadata.get("guest") or "Podcast Guest")
            url = c.metadata.get("post_url") or c.metadata.get("source_url") or c.metadata.get("youtube_url")

            if url and (url.startswith("http://") or url.startswith("https://")):
                safe_url = html.escape(url, quote=True)
                source_badges.append(
                    f"<a href='{safe_url}' target='_blank' rel='noopener noreferrer' "
                    f"style='display:inline-block; background:#fef3c7; color:#92400e; padding:4px 10px; border-radius:6px; "
                    f"font-size:12px; margin-right:8px; margin-bottom:8px; text-decoration:none; font-weight:500; border:1px solid #fde68a;'>"
                    f"{safe_c_title} <span style='color:#b45309; font-size:11px;'>({safe_c_guest})</span></a>"
                )
            else:
                source_badges.append(
                    f"<span style='display:inline-block; background:#fef3c7; color:#92400e; padding:4px 10px; border-radius:6px; "
                    f"font-size:12px; margin-right:8px; margin-bottom:8px; font-weight:500; border:1px solid #fde68a;'>"
                    f"{safe_c_title} <span style='color:#b45309; font-size:11px;'>({safe_c_guest})</span></span>"
                )

        sources_list_html = "".join(source_badges)

        status_badge_html = (
            f"<span style='background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0; padding:4px 10px; border-radius:12px; font-size:11px; font-weight:600;'>"
            f"&#10003; Target Compliant ({word_count} words)</span>"
            if within_constraints
            else
            f"<span style='background:#fff1f2; color:#9f1239; border:1px solid #fecdd3; padding:4px 10px; border-radius:12px; font-size:11px; font-weight:600;'>"
            f"&#9888; {word_count} words (Outside 1,150&ndash;1,350w target)</span>"
        )

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
    .essay-card {{
      max-width: 740px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 36px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
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
      padding: 4px 12px;
      border-radius: 20px;
      margin-bottom: 14px;
    }}
    h1 {{
      font-size: 26px;
      font-weight: 800;
      line-height: 1.3;
      color: #0f172a;
      margin-top: 0;
      margin-bottom: 8px;
    }}
    .byline {{
      font-size: 13px;
      color: #64748b;
      margin-bottom: 24px;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 14px;
    }}
    .content {{
      font-size: 15px;
      color: #334155;
    }}
    .meta-bar {{
      margin-top: 32px;
      padding-top: 18px;
      border-top: 1px solid #f1f5f9;
      font-size: 12px;
      color: #64748b;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
  </style>
</head>
<body>
  <div class="essay-card">
    <div class="badge">Ship 30 for 30 &bull; Growth Essay</div>
    <h1>{safe_title}</h1>
    <div class="byline">Grounded in insights from <strong>{safe_guest}</strong> on Lenny's Podcast</div>
    <div class="content">
      {rendered_body}
    </div>
    <div class="meta-bar">
      <div>Word Count: <strong>{word_count} words</strong> (Target: 1,150&ndash;1,350 words)</div>
      <div>{status_badge_html}</div>
    </div>
    <div style="margin-top: 20px; padding-top: 16px; border-top: 1px dashed #e2e8f0;">
      <div style="font-size: 11px; font-weight: 700; color: #64748b; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em;">Verified Sources</div>
      <div>{sources_list_html}</div>
    </div>
  </div>
</body>
</html>"""
