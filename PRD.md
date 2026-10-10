# Product Requirements Document (PRD)

## Project: The Lenny Growth Assistant
**Role:** Forward Deployed Engineer (FDE) Take-Home Assignment  
**Target Completion:** 12 October 2026  
**Status:** Approved & Implemented  

---

## 1. Executive Summary & Vision

*Lenny's Podcast* is the definitive archive of real-world product craft, containing hundreds of hours of tactical advice from world-class operators (e.g., Elena Verna, Shreyas Doshi, Brian Balfour, Casey Winters). However, this knowledge is locked in lengthy audio recordings and sprawling text transcripts. 

**The Lenny Growth Assistant** is an intelligent full-stack AI system designed to synthesize and operationalize these insights. Unlike generic chatbots, the system operates under **Strict Grounding Guardrails**: it answers questions using *only* verified transcript evidence, refuses speculation when evidence is absent, cites exact guest quotes and chunk provenance, generates 200–300 word **Ship 30 for 30 Atomic Essays**, and renders safe visual cards in a **Secure Artifact Viewer**.

---

## 2. Target Personas

| Persona | Core Job to be Done | Critical Needs |
| :--- | :--- | :--- |
| **Product Manager (PM)** | Designing onboarding, pricing, or product strategy. | Tactical frameworks, concrete trade-offs, and pre-mortems directly from proven leaders. |
| **Growth Engineer / Lead** | Optimizing loops, activation milestones, and reverse trials. | Technical specifics, metrics definitions (PQLs, cohort retention), and avoidance of vanity metrics. |
| **Early-Stage Founder** | Finding Product-Market Fit and setting up the growth engine. | Distinguishing between linear funnels and compounding loops; knowing when to invest in sales vs. self-serve. |
| **Product Writer / Marketer** | Publishing clear thought leadership and growth playbooks. | Converting podcast takeaways into 200–300 word Atomic Essays using the Ship 30 for 30 framework. |

---

## 3. Goals & Non-Goals

### Goals
1. **Zero Hallucination / Strict Grounding**: Answers must be backed by indexed transcript excerpts. If evidence does not exist in the knowledge base, the system must trigger an honest refusal rather than fabricating advice.
2. **Deterministic Citation Integrity**: Every claim is linked to an inspectable source citation (title, guest, episode number, filename, chunk offset, and score).
3. **Dual Provider Support with Local-First Demo**: Support local Ollama (`llama3:8b`, `qwen2.5:3b`) for offline evaluation, and cloud Anthropic Claude (`claude-3-5-sonnet-20241022`).
4. **Agent Framework Compliance**: Integrate the required **Pi Coding Agent** runtime adapter and Anthropic Claude tool-calling pattern.
5. **Ship 30 for 30 Essay Skill**: Generate constrained 200–300 word Atomic Essays following Dickie Bush & Nicolas Cole's framework.
6. **Secure Artifact Viewing**: Provide a sandboxed environment (`<iframe>` sandbox) for rendering HTML/CSS cards and formatted Markdown without XSS risks.

### Non-Goals
1. Serving general world knowledge (e.g., questions about astrophysics or cryptocurrency are rejected by the grounding gate).
2. Transcribing raw MP3 audio on the fly (transcripts are ingested from Markdown/text files).
3. Unrestricted web browsing or external search tool use.

---

## 4. Functional Requirements

### FR-1: Transcript Ingestion & Knowledge Base
- **FR-1.1**: Support ingestion from local directories (`data/transcripts/`) in `.md` and `.txt` formats.
- **FR-1.2**: Extract YAML frontmatter (`title`, `guest`, `episode`, `topic`, `synthetic_test_data`). Fallback to first H1 heading if frontmatter is absent.
- **FR-1.3**: Chunk documents using paragraph-aware windowing (1,000 characters target, 200 character sliding overlap).
- **FR-1.4**: Calculate SHA-256 content hashes to ensure idempotent ingestion (preventing duplicate chunks on re-runs).
- **FR-1.5**: Tag synthetic benchmark fixtures explicitly (`synthetic_test_data: true`) so they are never misrepresented as authentic recordings.

### FR-2: Search & Retrieval Engine
- **FR-2.1**: Expose `POST /api/v1/sources/search` with keyword and phrase relevance scoring.
- **FR-2.2**: Include phrase match boosts (+10.0 text, +15.0 title), term frequency boosts, query coverage ratio boosts, and stop-word filtering.
- **FR-2.3**: Return ranked results with chunk text, score, and parent metadata.

### FR-3: Grounded Conversational Assistant
- **FR-3.1**: Expose `POST /api/v1/chat` accepting user messages, optional `session_id`, provider, model, and `agent_framework`.
- **FR-3.2**: Persist conversational sessions and messages in PostgreSQL / SQLite with strict session isolation and timestamps.
- **FR-3.3**: Evidence Sufficiency Gate: If zero chunks match the user query, immediately return an honest limitation message without calling the LLM.
- **FR-3.4**: Citation Association: Attach `SourceCitation` objects to assistant responses.

### FR-4: Dual LLM Provider & Agent Layer
- **FR-4.1**: Local Ollama client (`OllamaClient`) with daemon reachability probes and model validation.
- **FR-4.2**: Cloud Anthropic Claude client (`AnthropicClient`) with API key validation.
- **FR-4.3**: Pi Coding Agent adapter (`PiCodingAgentAdapter`) executing the `@earendil-works/pi-coding-agent` CLI (`pi -p <prompt>`) with `~/.pi/agent/models.json` Ollama OpenAI-compatible bridge.
- **FR-4.4**: Documented non-silent fallback policy: return clear HTTP 503/400 errors instead of masking outages.

### FR-5: Ship 30 for 30 Atomic Essay Skill
- **FR-5.1**: Expose `POST /api/v1/skills/ship30-essay` taking topic, target audience, and provider.
- **FR-5.2**: Generate an Atomic Essay strictly between 200 and 300 words adhering to the Dickie Bush & Nicolas Cole framework.
- **FR-5.3**: Structure: Scroll-stopping headline, 1-2 sentence hook, 3-4 bullet framework from Lenny's guest, 1 actionable application, and 1-sentence punchline.
- **FR-5.4**: Return both Markdown output and a self-contained, sanitized HTML card artifact.

### FR-6: React + Vite Frontend & Secure Artifact Viewer
- **FR-6.1**: Interactive Chat UI with message history, provider/model/framework selectors, and suggestion chips.
- **FR-6.2**: Expandable Citation Inspector modal displaying chunk text, score, and guest details.
- **FR-6.3**: Knowledge Base Explorer tab to search and browse indexed chunks directly.
- **FR-6.4**: Secure Artifact Viewer featuring:
  - Rendered Markdown preview.
  - HTML Card view rendered inside a sandboxed `<iframe>` with `sandbox=""` to guarantee security isolation.
  - Raw Markdown view.
  - Word count constraint verification badge (200-300 words).
  - Export (.md file download and copy to clipboard).
- **FR-6.5**: Live system health pill tracking backend and database connectivity.

---

## 5. Non-Functional Requirements

- **Security**: No hardcoded API keys or secrets in Git. Sandboxed iframe rendering prevents cross-site scripting (XSS) and style contamination. Strict TLS certificate verification is enforced.
- **Reliability & Portability**: Runs seamlessly on local SQLite for testing/offline use, or on PostgreSQL via Docker Compose.
- **Testing**: Complete zero-external-dependency automated test coverage (Pytest for backend, Vitest for frontend).

---

## 6. Success Metrics & Verification

1. **Test Coverage**: 100% of core backend and frontend components covered by unit tests.
2. **Idempotency**: Re-running transcript ingestion produces 0 duplicate records.
3. **Zero Hallucination Rate**: Ungrounded queries trigger 100% refusal rate without calling external LLMs.
4. **Word Count Compliance**: Ship 30 essays meet the 200–300 word target.
