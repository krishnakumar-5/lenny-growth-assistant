# System Architecture Specification

## 1. System Overview & Component Diagram

**The Lenny Growth Assistant** is engineered as a modular, containerized multi-tier system with both local-first LLM evaluation support and advanced agent orchestration:

```
+-------------------------------------------------------------+
|                      User Browser                           |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                 Frontend (React + Vite)                     |
|  - Interactive Chat Interface & Model Toolbar               |
|  - Knowledge Explorer & Citation Inspector                  |
|  - Ship 30 for 30 Essay Generator & Secure Artifact Viewer  |
+-------------------------------------------------------------+
                               |
                               | REST (HTTP / JSON)
                               v
+-------------------------------------------------------------+
|                 Backend (FastAPI / Python)                  |
|  - API Routers: /health, /sources, /chat, /skills           |
|  - Transcript Ingestion & Keyword Retrieval Service         |
|  - Grounded Growth Agent Orchestrator                       |
+-------------------------------------------------------------+
         |                       |                     |
         v                       v                     v
+------------------+    +------------------+    +------------------+
| LLM Provider     |    | Agent Runtime    |    | Database Layer   |
| Layer:           |    | Layer:           |    |                  |
| - OllamaClient   |    | - Pi Coding      |    | - PostgreSQL     |
|   (Local /v1)    |    |   Agent (CLI)    |    |   (psycopg 3)    |
| - AnthropicClient|    | - Anthropic Tool |    | - SQLite         |
|   (Cloud Claude) |    |   Calling Loop   |    |   (Unit Tests)   |
+------------------+    +------------------+    +------------------+
```

---

## 2. Transcript Ingestion & Knowledge Base Pipeline

```
Raw Transcript (.md/.txt)
         │
         ▼
[Frontmatter Parser] ──> Extracts title, guest, episode, topic, synthetic_test_data
         │
         ▼
[SHA-256 Hash Check] ──> If hash matches existing transcript, skip (Idempotency)
         │
         ▼
[Paragraph-Aware Chunker] ──> Splits text on paragraph boundaries (target 1,000 chars, 200 overlap)
         │
         ▼
[SQLAlchemy Persistence] ──> Inserts Transcript record and associated TranscriptChunk records
```

### Chunking Mechanics
- **Target Size**: 1,000 characters per chunk.
- **Overlap Window**: 200 characters sliding overlap preserving cross-paragraph context.
- **Offsets**: Character offsets (`start_char`, `end_char`) are indexed in chunk metadata for exact provenance tracing.

---

## 3. Retrieval Algorithm & Relevance Scoring

The keyword retrieval engine operates directly in standard SQL without requiring external proprietary vector services, ensuring 100% portability across both SQLite and PostgreSQL.

```
Query Terms = Extract alphanumeric words >= 2 chars (excluding stop words)
Candidate Chunks = WHERE chunk_text ILIKE %term% OR title ILIKE %term%

Score Calculation:
1. Exact Phrase Match:       +10.0 in text, +15.0 in title
2. Term Frequency:           +2.0 per chunk match, +4.0 per title match
3. Query Coverage Ratio:     +5.0 * (matched_terms / total_query_terms)
```

---

## 4. Agent Framework Layer

### A. Official Pi Coding Agent Runtime Adapter
- **Package**: `@earendil-works/pi-coding-agent` (Node.js CLI `pi`).
- **Execution Mode**: Subprocess execution via `asyncio.create_subprocess_exec(exe, "-p", prompt)`.
- **Model Bridge**: Generates `~/.pi/agent/models.json` configuring local Ollama via OpenAI-compatible endpoints:
  ```json
  {
    "providers": {
      "ollama": {
        "baseUrl": "http://localhost:11434/v1",
        "api": "openai-completions",
        "apiKey": "ollama",
        "models": [{"id": "llama3:8b"}]
      }
    }
  }
  ```
- **Error Mapping**:
  - Binary missing on PATH -> **HTTP 503 Service Unavailable**.
  - Process timeout -> **HTTP 504 Gateway Timeout**.
  - Non-zero exit code -> **HTTP 502 Bad Gateway**.

### B. Anthropic Claude Agent Tool-Calling Pattern
- Defines `search_podcast_transcripts` adhering to Anthropic JSON Schema contracts (`RETRIEVAL_TOOL_SPEC`).
- Executes evidence sufficiency check before LLM invocation.
- If zero matching chunks are retrieved, immediately returns an honest disclaimer without calling the LLM.

---

## 5. Database Schema & Models

```sql
-- Conversations & Messages
CREATE TABLE conversation_sessions (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Transcripts & Chunks
CREATE TABLE transcripts (
    id UUID PRIMARY KEY,
    source_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    source_filename VARCHAR(255) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    raw_content TEXT NOT NULL,
    meta_info JSON NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE transcript_chunks (
    id UUID PRIMARY KEY,
    transcript_id UUID NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    meta_info JSON NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```
