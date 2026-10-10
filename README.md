# The Lenny Growth Assistant

**Forward Deployed Engineer (FDE) Take-Home Assignment**  
**Due Date:** 12 October 2026

---

## 1. Project Overview

**The Lenny Growth Assistant** is an intelligent assistant designed to extract, synthesize, and operationalize high-leverage product and growth insights from *Lenny's Podcast* and newsletter transcripts. Built for product managers, growth engineers, and founders, the assistant provides grounded answers, actionable playbooks, and strategic frameworks backed by real-world operator experience.

---

## 2. Planned Architecture

The application is engineered as a modular, containerized multi-tier system with both local-first LLM evaluation support and advanced agent orchestration:

```
+-------------------------------------------------------------+
|                      User Browser                           |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                 Frontend (React + Vite)                     |
|  - Interactive Chat Interface & Growth Playbook Explorer    |
|  - Real-time Streaming & Citation Inspector                 |
+-------------------------------------------------------------+
                              |
                              | HTTP / WebSocket
                              v
+-------------------------------------------------------------+
|                 Backend (FastAPI / Python)                  |
|  - Asynchronous API endpoints & Session Management          |
|  - Query Routing, Context Ingestion, & Verification         |
+-------------------------------------------------------------+
         |                                         |
         v                                         v
+--------------------+                   +--------------------+
|    Agent Layer     |                   |     Database       |
|  - Claude Agent    |                   |  - PostgreSQL      |
|    SDK / Pi Agent  |                   |  - Metadata, Chats |
|  - Multi-step      |                   |    & Vector Store  |
|    Reasoning       |                   +--------------------+
+--------------------+
         |
         v
+-------------------------------------------------------------+
|                 Local LLM (Ollama Service)                  |
|  - Offline / Local model execution (Mandatory for Demo)     |
+-------------------------------------------------------------+
```

### Key Components

- **Frontend (`frontend/`)**: React with Vite providing a fast, modern conversational interface, source citation viewing, and structured output rendering.
- **Backend (`backend/`)**: FastAPI Python backend handling request validation, conversation history, document retrieval, and tool orchestration.
- **Database**: PostgreSQL for persistent conversation history, user sessions, structured metadata, and vectorized transcript chunk storage.
- **Local LLM**: Ollama running locally in Docker/host for zero-cost, reproducible offline demonstrations.
- **Agent Layer**: Anthropic Claude Agent SDK / Pi Coding Agent providing reflective reasoning, retrieval tool-calling, and structured answer synthesis.
- **Deployment**: Docker Compose orchestrating all microservices with unified networking and environment configuration.

---

## 3. Directory Structure

```
lenny-growth-assistant/
├── backend/            # FastAPI backend application, routers, services, models
│   ├── alembic/        # Alembic database migration scripts & revisions
│   ├── app/            # Application core, API routes, DB session, models, schemas
│   │   ├── api/        # Route endpoints (health, root, etc.)
│   │   ├── core/       # Pydantic Settings and configurations
│   │   ├── db/         # SQLAlchemy engine, session maker, base, and health check
│   │   ├── models/     # SQLAlchemy 2.x models (ConversationSession, Message)
│   │   └── schemas/    # Pydantic response/request validation schemas
│   ├── tests/          # Pytest suite covering endpoints, DB models & relationships
│   ├── Dockerfile      # Production backend container definition
│   ├── alembic.ini     # Database migration configuration
│   └── requirements.txt# Backend Python dependencies
├── frontend/           # React + Vite user interface and components
├── data/               # Knowledge base, transcript datasets, and fixtures
├── docs/               # System architecture documentation and design specs
├── agent_logs/         # Agent execution traces, logs, and evaluation outputs
├── tests/              # End-to-end, integration, and unit tests
├── .env.example        # Environment variable definitions template
├── .gitignore          # Git exclusion rules for secrets, virtualenvs, dependencies
├── docker-compose.yml  # Multi-container orchestration (DB, Ollama, Backend, Frontend)
└── README.md           # Project overview, architecture, and setup instructions
```

---

## 4. Backend Setup & Run Instructions (Windows PowerShell)

Follow these exact steps from the project root in Windows PowerShell to set up the backend virtual environment, install dependencies, run tests, and start the FastAPI development server:

### 1. Create Virtual Environment
```powershell
python -m venv backend\.venv
```

### 2. Activate Virtual Environment
```powershell
.\backend\.venv\Scripts\Activate.ps1
```
*(If execution policies prevent script activation, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` or use the direct python path `backend\.venv\Scripts\python.exe`)*

### 3. Install Dependencies
```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### 4. Run Pytest Test Suite

The test suite clearly distinguishes between fast unit tests (in-memory SQLite) and integration tests (live PostgreSQL):

- **Run all unit tests (SQLite in-memory, ~1s execution):**
  ```powershell
  .\backend\.venv\Scripts\python.exe -m pytest backend\tests -v -m unit
  ```

- **Run the full test suite (auto-skips PostgreSQL integration tests if no live DB is reachable):**
  ```powershell
  .\backend\.venv\Scripts\python.exe -m pytest backend\tests -v
  ```

- **Run PostgreSQL integration tests (requires a running PostgreSQL instance):**
  ```powershell
  $env:TEST_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/lenny_growth"
  .\backend\.venv\Scripts\python.exe -m pytest backend\tests -v -m integration
  ```

### 5. Run Database Migrations (Alembic)
To inspect migration heads or preview generated PostgreSQL DDL offline:
```powershell
.\backend\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini heads
.\backend\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head --sql
```
To apply migrations against a running PostgreSQL database:
```powershell
.\backend\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
```

### 6. Start the FastAPI Development Server
```powershell
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Run Transcript Ingestion Pipeline (CLI)
To ingest transcripts from the configured `data/transcripts/` directory into the database:
```powershell
.\backend\.venv\Scripts\python.exe backend\app\cli\ingest.py --init-tables
```
Options:
- `--dir <path>`: Custom transcript folder (defaults to `data/transcripts`).
- `--chunk-size <int>`: Max characters per chunk (default: 1000).
- `--chunk-overlap <int>`: Overlap between consecutive chunks (default: 200).
- `--init-tables`: Auto-creates tables if not already present.

---

## 5. Knowledge Base & Retrieval (RAG Foundation)

### Adding Transcript Files
Place podcast transcripts into `data/transcripts/` in either Markdown (`.md`) or plain text (`.txt`) format:
- **Markdown with Frontmatter**:
  ```markdown
  ---
  title: "The Hierarchy of Growth and Retention Accounting"
  guest: "Elena Verna"
  episode: 42
  topic: "Product-Led Growth"
  ---
  # The Hierarchy of Growth and Retention Accounting
  [Episode transcript text...]
  ```
- **Plain Text**: Files without frontmatter automatically derive the title from the first header or filename stem. No fake metadata or episode details are fabricated.

### How Chunking Works
- Transcripts are parsed and split using paragraph-aware windowing (`split_text_into_chunks`).
- If a paragraph is exceptionally long, it splits cleanly on sentence boundaries.
- Preserves a sliding overlap (`chunk_overlap=200`) so critical context spanning chunk boundaries is never lost.
- Tracks `start_char` and `end_char` character offsets in chunk metadata.
- Trailing text fragments smaller than `min_chunk_size=100` are merged into previous chunks to avoid tiny context slivers.

### How Retrieval Works
- **Endpoint**: `POST /api/v1/sources/search`
- **Algorithm**: Portable keyword-based relevance matching:
  - Exact phrase match bonus (+10.0 in text, +15.0 in title).
  - Per-term occurrences boost (+2.0 text, +4.0 title).
  - Query term coverage ratio boost (+5.0 * ratio).
- **Architecture Trade-off**: Operates directly in standard SQL without requiring external vector databases or remote embedding APIs. 100% portable across both SQLite unit tests and PostgreSQL deployments.

### Example Retrieval API Request
```bash
curl -X POST http://localhost:8000/api/v1/sources/search \
  -H "Content-Type: application/json" \
  -d '{"query": "cohort retention", "limit": 3}'
```
**Example Response**:
```json
{
  "query": "cohort retention",
  "total_results": 1,
  "results": [
    {
      "chunk_id": "12b57a6d-016f-44d6-b1a9-d415a3584b32",
      "transcript_id": "09c6eee0-ae11-4773-afa0-05f9061519bf",
      "transcript_title": "The Hierarchy of Growth and Retention Accounting",
      "source_filename": "sample_growth_accounting.md",
      "chunk_index": 0,
      "chunk_text": "Welcome to this session on growth strategy...",
      "score": 35.0,
      "metadata": {
        "guest": "Elena Verna",
        "topic": "Product-Led Growth",
        "start_char": 0,
        "end_char": 932
      }
    }
  ]
}
```

---

## 6. LLM Providers & Grounded Chat (Milestone 4)

### Dual LLM Provider Architecture
The assistant supports both local-first offline execution (mandatory for the demo) and cloud inference via a unified provider abstraction (`app.services.llm.base.BaseLLMClient`):

1. **Local LLM (Ollama)**:
   - Default provider (`LLM_PROVIDER=ollama`).
   - Standard model: `llama3:8b` (configurable via `OLLAMA_MODEL`).
   - Base URL: `http://localhost:11434` (configurable via `OLLAMA_BASE_URL`).
   - Probing: Automatic `/api/tags` reachability and model-existence validation.
   - Setup instructions:
     ```powershell
     # 1. Start Ollama daemon
     ollama serve
     
     # 2. Pull the required model
     ollama pull llama3:8b
     ```
2. **Cloud LLM (Anthropic Claude)**:
   - Secondary provider (`LLM_PROVIDER=anthropic`).
   - Standard model: `claude-3-5-sonnet-20241022` (configurable via `ANTHROPIC_MODEL`).
   - Requires explicit API key (`ANTHROPIC_API_KEY`).
   - Clear validation: Returns HTTP 400 with actionable messages if key is missing or invalid.
3. **Documented Fallback & Reliability Policy**:
   - The application does **not** silently fall back between providers. If the requested or configured provider fails (e.g. Ollama daemon not running), the API returns an explicit HTTP 503 or 400 with actionable troubleshooting guidance rather than masking runtime failures.

---

### The Grounded Growth Agent Layer
The agent layer (`app.services.agent.grounded_agent.GroundedGrowthAgent`) conforms to the **Anthropic Claude Agent Framework** tool-calling pattern:
- **Retrieval Tool Schema**: Defines `search_podcast_transcripts` using standard Anthropic JSON Schema contracts (`RETRIEVAL_TOOL_SPEC`).
- **Evidence Sufficiency Gate**: If the knowledge base contains no matching transcript chunks, the agent short-circuits and returns an honest disclaimer without calling the LLM, eliminating hallucination risks:
  > *"I could not find sufficient information in the available podcast transcripts to answer your question regarding '[topic]'. As The Lenny Growth Assistant, I only provide insights grounded in verified podcast transcripts and will not speculate or fabricate episode content."*
- **Strict Grounding Guardrails**: When evidence is found, retrieved chunks are injected into the prompt with instructions to strictly separate verified facts from uncertainty.
- **Citation Integrity**: Returns structured `SourceCitation` objects containing chunk IDs, transcript titles, source filenames, chunk indices, and relevance scores only for chunks actually retrieved.
- **Synthetic Benchmark Transparency**: Any benchmark fixtures (e.g., `data/transcripts/sample_growth_accounting.md`) are explicitly marked as synthetic test data and not presented as authentic podcast recordings.

---

### Chat API (`POST /api/v1/chat`)

#### Request Payload
```json
{
  "message": "What is cohort retention?",
  "session_id": "optional-uuid-for-multi-turn-history",
  "provider": "ollama",
  "model": "llama3:8b"
}
```

#### Response Structure
```json
{
  "session_id": "b182cb86-c567-46f4-b25b-cb81cf941a37",
  "message": "Cohort retention measures user engagement over uniform time periods...",
  "role": "assistant",
  "provider": "ollama",
  "model": "llama3:8b",
  "sources": [
    {
      "chunk_id": "12b57a6d-016f-44d6-b1a9-d415a3584b32",
      "transcript_id": "09c6eee0-ae11-4773-afa0-05f9061519bf",
      "transcript_title": "The Hierarchy of Growth and Retention Accounting",
      "source_filename": "sample_growth_accounting.md",
      "chunk_index": 0,
      "chunk_text": "Cohort retention measures user engagement over uniform time periods.",
      "score": 35.0,
      "metadata": {
        "guest": "Elena Verna",
        "synthetic_test_data": true
      }
    }
  ],
  "insufficient_evidence": false,
  "created_at": "2026-10-09T13:54:00Z"
}
```

#### Windows PowerShell Invocation Example
```powershell
$body = @{
    message = "What are the key retention metrics?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Method Post -ContentType "application/json" -Body $body
```

---

## 7. Docker & Container Deployment (Docker-Enabled Systems)

Multi-container orchestration is defined in `docker-compose.yml`:
- **db**: PostgreSQL 16 Alpine with persistent volume `postgres_data` and healthcheck (`pg_isready`).
- **backend**: FastAPI service built via `backend/Dockerfile`, waiting for `db` to be healthy before starting.

### Commands for Docker Environments
```bash
# 1. Build backend container image
docker build -t lenny-growth-backend:latest ./backend

# 2. Start PostgreSQL and FastAPI backend
docker compose up -d db backend

# 3. Apply database migrations inside the backend container
docker compose exec backend alembic upgrade head

# 4. Ingest transcripts inside the backend container
docker compose exec backend python app/cli/ingest.py

# 5. Run tests inside the running container (including live Postgres integration tests)
docker compose exec backend pytest -v

# 6. Check container logs
docker compose logs -f backend
```

---

## 8. Verification Status Matrix

| Component | Status | Details |
| :--- | :--- | :--- |
| **FastAPI Root (`GET /`)** | Verified | Responds 200 OK with app name, version, status, and docs URL. |
| **API Health (`GET /api/v1/health`)** | Verified | Accurately returns status, timestamp, version, and `"database": "unavailable"` when DB is offline. |
| **Interactive Docs (`GET /docs`)** | Verified | Swagger UI served properly at `/docs`. |
| **SQLAlchemy 2.x Models** | Verified | `ConversationSession`, `Message`, `Transcript`, `TranscriptChunk` models with cascading deletes & timestamps. |
| **Transcript Ingestion CLI** | Verified | Idempotent ingestion pipeline, SHA-256 hash checks, duplicate avoidance verified. |
| **Search & Retrieval API** | Verified | `POST /api/v1/sources/search` with relevance ranking and provenance metadata verified. |
| **LLM Provider Clients** | Verified | Dual provider clients (`OllamaClient` and `AnthropicClient`) with reachability probes and timeouts. |
| **Grounded Growth Agent** | Verified | Anthropic tool-calling pattern, evidence sufficiency gate, and anti-hallucination guardrails. |
| **Grounded Chat Endpoint (`POST /api/v1/chat`)** | Verified | Session persistence, multi-turn history, session isolation, and structured source citations. |
| **Ship 30 for 30 Essay Skill** | **Verified** | Dedicated `POST /api/v1/skills/ship30-essay` endpoint generating 200-300 word Atomic Essays with HTML cards. |
| **Secure Artifact Viewer** | **Verified** | Sandboxed `<iframe>` (`sandbox=""`), rendered Markdown, raw Markdown, and one-click `.md` export. |
| **Authentic Podcast Transcripts** | **Verified** | Authentic episodes for Elena Verna, Shreyas Doshi, and Brian Balfour indexed with full metadata. |
| **Automated Backend Pytest Suite** | **Verified** | **68 passed**, **1 skipped** (PostgreSQL integration test skipped gracefully when server absent). |
| **React + Vite Frontend** | **Verified** | Interactive chat, Citation Inspector modal, Knowledge Explorer, Ship 30 Generator, and Artifact Viewer. |
| **Frontend Test Suite (Vitest)** | **Verified** | **17 passed** covering Navbar, ModelSelector, ChatMessage, CitationInspector, ArtifactViewer, and API service. |
| **Frontend Production Build** | **Verified** | Clean Vite + TypeScript production build (`dist/`) in 13.5s. |
| **PRD & Design Specifications** | **Verified** | `PRD.md`, `docs/design.md`, `docs/architecture.md`, `docs/manual_test_plan.md`, `docs/demo_video_script.md`. |
| **Agent Execution Traces** | **Verified** | Structured JSON execution traces in `agent_logs/` (Ollama, refusal gate, Ship 30, and Pi CLI). |
| **Docker Build & Runtime** | **Unverified (Host Limitation)** | `docker` CLI not installed on current Windows evaluation host. `Dockerfile` & `docker-compose.yml` authored to production specifications. |
| **Live PostgreSQL Server** | **Unverified (Host Limitation)** | No native PostgreSQL server active on localhost:5432; live integration test marked to skip gracefully. |

---

## 7. Ship 30 for 30: Atomic Essay Skill & Artifact Viewer

The assistant includes a dedicated skill implementing the **Ship 30 for 30** digital writing framework by Dickie Bush & Nicolas Cole:

### The Framework Constraints
- **Word Count**: Exactly **200–300 words** per Atomic Essay.
- **Structure**:
  1. Scroll-stopping headline (`# Title`).
  2. 1-2 sentence hook exposing a status-quo mistake.
  3. 3-4 bullet framework directly grounded in transcript evidence.
  4. 1 actionable application step.
  5. 1 punchy ending takeaway.

### API Endpoint (`POST /api/v1/skills/ship30-essay`)
```json
{
  "topic": "Elena Verna on why retention precedes acquisition",
  "target_audience": "Founders and Growth Leaders",
  "provider": "ollama",
  "model": "llama3:8b"
}
```

### Secure Artifact Viewer Architecture
When rendering visual HTML cards, the application isolates generated content inside a sandboxed `<iframe>`:
```tsx
<iframe
  title="Sanitized HTML Artifact Preview"
  srcDoc={artifact.content_html}
  sandbox=""
  className="w-full h-[520px] border-0"
/>
```
- **`sandbox=""`**: Enforces strict origin separation, disallowing scripts, cookies, `localStorage`, and DOM traversal.
- **Tabs**: Rendered Markdown preview, Sandboxed HTML Card view, and Raw Markdown.
- **Export**: One-click **Copy Markdown** and **Export .md** file download.

---

## 8. Frontend Setup & Run Instructions

The frontend is built with React 18, Vite, TypeScript, and Tailwind CSS in `frontend/`.

### 1. Install Dependencies
```powershell
cd frontend
npm install
```

### 2. Run Automated Unit Tests (Vitest)
```powershell
npm test
```
Executes 17 component and API service tests in jsdom.

### 3. Build for Production
```powershell
npm run build
```
Executes TypeScript type checking (`tsc`) followed by Vite production bundling to `frontend/dist/`.

### 4. Start Development Server
```powershell
npm run dev
```
Serves the web application at `http://localhost:5173`.

---

## 9. Development Roadmap & Milestones

- [x] Initial project repository scaffold created.
- [x] Environment configuration templates and container orchestration scaffolded.
- [x] Modular FastAPI backend scaffolded with root `/`, health `/api/v1/health`, and `/docs`.
- [x] Pytest suite covering root and health endpoints.
- [x] PostgreSQL persistence layer with SQLAlchemy 2.x and psycopg 3.
- [x] ConversationSession and Message relational models with cascading delete and timestamps.
- [x] Alembic migration framework and initial revision (`0001_initial_tables`).
- [x] Backend Dockerfile containerizing the FastAPI application.
- [x] Clear separation of fast SQLite unit tests and conditional PostgreSQL integration tests.
- [x] Transcript ingestion pipeline supporting `.md` and `.txt`, metadata parsing, and idempotency.
- [x] Authentic podcast transcripts for Elena Verna, Shreyas Doshi, and Brian Balfour.
- [x] Transcript chunking with paragraph-aware overlap and boundary preservation.
- [x] Portable keyword-based retrieval service and `POST /api/v1/sources/search` endpoint.
- [x] Alembic migration `0002_transcript_and_chunks`.
- [x] Local LLM integration (Ollama client with reachability probe & timeout handling).
- [x] Cloud LLM integration (Anthropic Claude client with key validation & error handling).
- [x] Official Pi Coding Agent runtime integration (`@earendil-works/pi-coding-agent`) with Ollama bridge.
- [x] Grounded Growth Agent layer conforming to Anthropic tool-use patterns.
- [x] Grounded Chat endpoint (`POST /api/v1/chat`) with session persistence & citations.
- [x] Dedicated Ship 30 for 30 Atomic Essay generation skill (`POST /api/v1/skills/ship30-essay`).
- [x] React & Vite frontend UI implementation (Chat, Knowledge Explorer, Citation Inspector, Health Monitor).
- [x] Dedicated Ship 30 Essay Generator and Secure Sandboxed Artifact Viewer.
- [x] Complete PRD, system design, technical architecture, manual UI test plan, and video script.
- [x] Full automated test suites: **68 backend tests** + **17 frontend tests** passing.
- [ ] End-to-end containerized deployment verification with Docker Compose on Docker-enabled host.



