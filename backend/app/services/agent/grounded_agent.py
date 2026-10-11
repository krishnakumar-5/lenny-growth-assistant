from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.chat import SourceCitation
from app.schemas.sources import SearchResultItem
from app.services.agent.pi_agent_adapter import PiCodingAgentAdapter
from app.services.agent.tools import RETRIEVAL_TOOL_SPEC, execute_retrieval_tool
from app.services.llm.base import BaseLLMClient

logger = logging.getLogger(__name__)


@dataclass
class AgentExecutionResult:
    """Encapsulates the final synthesized response and supporting evidence."""

    response_text: str
    citations: List[SourceCitation]
    insufficient_evidence: bool
    provider: str
    model: str
    agent_framework: str = "anthropic_tool_agent"


class GroundedGrowthAgent:
    """Agent orchestrator implementing tool-calling retrieval and grounded synthesis.
    
    Supports dual execution frameworks:
    1. Pi Coding Agent (@earendil-works/pi-coding-agent) CLI runtime adapter
    2. Anthropic Tool-Use Agent orchestration loop
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        agent_framework: Optional[str] = None,
    ) -> None:
        self.llm_client = llm_client
        self.settings = get_settings()
        self.agent_framework = (agent_framework or self.settings.AGENT_FRAMEWORK).strip().lower()
        self.tools = [RETRIEVAL_TOOL_SPEC]
        if self.agent_framework == "pi_coding_agent":
            self.pi_adapter = PiCodingAgentAdapter(
                ollama_base_url=self.settings.OLLAMA_BASE_URL,
                ollama_model=self.llm_client.model_name,
            )
        else:
            self.pi_adapter = None

    async def run(
        self,
        db: Session,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        search_limit: Optional[int] = None,
    ) -> AgentExecutionResult:
        """Execute the agentic flow: tool retrieval -> verification -> grounded generation."""
        limit = search_limit or self.settings.CHAT_SEARCH_LIMIT

        # Step 1: Formulate tool parameters and execute retrieval tool (excluding synthetic fixtures)
        retrieved_chunks = execute_retrieval_tool(
            db=db,
            query=user_message,
            limit=limit,
            exclude_synthetic=True,
        )

        # Step 2: Evidence Sufficiency Verification
        if not retrieved_chunks:
            logger.info("Knowledge base returned 0 matching chunks for query: %s", user_message)
            clean_query = user_message.strip()
            topic_summary = f"'{clean_query}'" if len(clean_query) < 80 else f"'{clean_query[:77]}...'"
            fallback_message = (
                f"I could not find sufficient information in the available podcast transcripts to answer your question regarding {topic_summary}. "
                "As The Lenny Growth Assistant, I only provide insights grounded in verified podcast transcripts and will not speculate, "
                "assume unmentioned episodes, or fabricate guest advice."
            )
            return AgentExecutionResult(
                response_text=fallback_message,
                citations=[],
                insufficient_evidence=True,
                provider=self.llm_client.provider_name,
                model=self.llm_client.model_name,
                agent_framework=self.agent_framework,
            )

        # Step 3: Format Evidence Context Block
        evidence_lines: List[str] = ["=== RETRIEVED TRANSCRIPT EVIDENCE ==="]
        citations: List[SourceCitation] = []

        for idx, chunk in enumerate(retrieved_chunks, start=1):
            guest_str = chunk.metadata.get("guest") or "Not specified"
            episode_str = chunk.metadata.get("episode") or chunk.metadata.get("date") or "Not specified"
            post_url_str = chunk.metadata.get("post_url") or chunk.metadata.get("source_url")
            synthetic_flag = chunk.metadata.get("synthetic_test_data", False) or chunk.metadata.get("is_test_fixture", False)
            disclaimer = " [BENCHMARK TEST DATA - NOT AUTHENTIC EPISODE]" if synthetic_flag else ""

            evidence_lines.append(f"\n[Source {idx}]")
            evidence_lines.append(f"Title: {chunk.transcript_title}{disclaimer}")
            evidence_lines.append(f"File: {chunk.source_filename} (Chunk #{chunk.chunk_index})")
            evidence_lines.append(f"Guest: {guest_str} | Date/Episode: {episode_str}")
            if post_url_str:
                evidence_lines.append(f"Source URL: {post_url_str}")
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

        # Step 4: Strict System Prompt Enforcing Grounding and Distinguishing Facts
        system_prompt = (
            "You are The Lenny Growth Assistant, an AI growth advisor operationalizing tactical frameworks "
            "and insights from Lenny's Podcast.\n\n"
            "STRICT GROUNDING & FACTUAL INTEGRITY RULES:\n"
            "1. Answer the user's question using ONLY facts and frameworks directly supported by the retrieved "
            "transcript excerpts provided in the context.\n"
            "2. Clearly distinguish between source-supported facts and areas of uncertainty or missing context.\n"
            "3. NEVER invent, assume, or fabricate quotes, guest names, companies, metrics, or episode numbers "
            "not present in the excerpts.\n"
            "4. When stating facts or tactics, explicitly reference the source transcript or guest mentioned in the excerpts.\n"
            "5. If the excerpts only partially address the question, provide the supported facts and explicitly identify "
            "what remains unanswered.\n"
            "6. Note: Any test or sample transcript labeled as synthetic test data must not be cited as an authentic podcast interview."
        )

        # Step 5: Build Conversation Context with History
        messages: List[Dict[str, str]] = []

        # Add recent conversation turns
        if conversation_history:
            for turn in conversation_history[-self.settings.MAX_HISTORY_TURNS:]:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        # Inject evidence into current user query
        augmented_user_message = (
            f"{evidence_block}\n\n"
            f"User Question: {user_message}\n\n"
            "Please provide a well-structured, actionable response grounded exclusively in the evidence above."
        )
        messages.append({"role": "user", "content": augmented_user_message})

        # Step 6: Generate Grounded Response via Selected Agent Framework
        if self.agent_framework == "pi_coding_agent" and self.pi_adapter:
            full_prompt = (
                f"{system_prompt}\n\n"
                f"{augmented_user_message}"
            )
            response_text = await self.pi_adapter.execute_query(
                prompt=full_prompt,
                model=self.llm_client.model_name,
                provider=self.llm_client.provider_name,
            )
        else:
            response_text = await self.llm_client.generate_response(
                messages=messages,
                system_prompt=system_prompt,
            )

        return AgentExecutionResult(
            response_text=response_text,
            citations=citations,
            insufficient_evidence=False,
            provider=self.llm_client.provider_name,
            model=self.llm_client.model_name,
            agent_framework=self.agent_framework,
        )
