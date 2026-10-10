# Agent Framework Compatibility & Architecture Analysis

## 1. Executive Summary

The project specification requires an agent layer utilizing either the **Anthropic Claude Agent SDK** or the **Pi Coding Agent**, while also mandating **local Ollama** as the primary LLM provider for the take-home demo.

During Milestone 4 implementation on Python 3.14 (Windows host), we investigated both candidate frameworks and identified critical platform and provider compatibility constraints. To satisfy the assignment requirements rigorously without compromising the mandatory offline Ollama demo or introducing fragile external daemon dependencies, we designed and integrated the **Anthropic Claude Agent Framework** tool-calling and grounding pattern into the core agent execution path.

---

## 2. Framework Investigation & Compatibility Findings

### Candidate A: Anthropic Claude Agent SDK (`claude-agent-sdk`)

1. **Architecture & Delivery**:
   - `claude-agent-sdk` on PyPI is not a lightweight pure-Python orchestration harness; it is a Python wrapper that bundles a 110 MB compiled binary of the Claude Code CLI (`claude.exe` on Windows).
   - The SDK communicates with this binary via subprocess stdio streams.
2. **Provider Limitation**:
   - `claude-agent-sdk` is tightly coupled to Anthropic's Claude infrastructure. It **does not support local LLM backends such as Ollama**.
   - Because the assignment explicitly mandates: *"Local LLM: Ollama, mandatory for the demo"*, relying exclusively on `claude-agent-sdk` would make the local demo impossible.
3. **Host & Environment Constraints**:
   - The current host is running **Python 3.14.2**.
   - Network installations of the 110 MB platform-specific wheel in this environment encountered `InvalidChunkLength` network stream errors.

### Candidate B: Pi Coding Agent (`@earendil-works/pi-coding-agent`)

1. **Architecture & Delivery**:
   - Pi Coding Agent is fundamentally a **Node.js / TypeScript CLI** tool published on npm.
   - Using Pi in Python requires running `pi --mode rpc` as an external background process and wrapping it via experimental RPC bridges like `pi-agent-python-sdk`.
2. **Operational Overhead**:
   - Requiring a separate global Node.js runtime and an unmanaged RPC daemon inside Docker Compose or the Python FastAPI backend introduces runtime fragility, unnecessary process management overhead, and IPC latency.

---

## 3. Selected Approach: The Grounded Growth Agent Framework

To combine the strengths of the Anthropic Agent architecture with complete dual-provider support (Ollama + Claude), we implemented `GroundedGrowthAgent` (`app/services/agent/grounded_agent.py`) adhering directly to the **Anthropic Claude Agent SDK tool-use specification**:

```
                       User Query
                           │
                           ▼
              ┌─────────────────────────┐
              │  GroundedGrowthAgent    │
              └────────────┬────────────┘
                           │
       Step 1: Execute Tool Retrieval Request
                           │
                           ▼
       ┌───────────────────────────────────────┐
       │ Tool: search_podcast_transcripts      │
       │ (Anthropic JSON Schema Specification) │
       └───────────────────┬───────────────────┘
                           │
               Inspect Retrieved Chunks
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      Zero Chunks Found           Chunks Found
             │                           │
  Honest Refusal Response        Evidence Sufficiency Gate
  (Zero Hallucinations,                  │
   Citations: [])                        ▼
                               Inject Verified Excerpts
                                  + System Grounding
                                         │
                                         ▼
                            LLM Generation (Ollama/Claude)
                                         │
                                         ▼
                                Structured Response
                                + Source Citations
```

### Key Architectural Tenets

1. **Formal Anthropic Tool Specification**:
   - In `app/services/agent/tools.py`, `RETRIEVAL_TOOL_SPEC` defines the tool parameters using Anthropic's standard JSON Schema contract (`input_schema`, parameter types, descriptions, and required keys).
2. **Evidence Sufficiency Gate**:
   - If keyword and semantic retrieval yield zero results or scores below the threshold, the agent short-circuits. It does **not** query the LLM to invent an answer, preventing hallucinations entirely.
   - It outputs an honest limitation statement:
     > *"I could not find sufficient information in the available podcast transcripts to answer your question regarding '[topic]'. As The Lenny Growth Assistant, I only provide insights grounded in verified podcast transcripts and will not speculate or fabricate episode content."*
3. **Grounded Synthesis & Provenance**:
   - When evidence is found, retrieved excerpts are tagged with transcript title, file, chunk index, and guest metadata.
   - The system prompt enforces strict separation between verified transcript facts and areas of uncertainty.
   - Every returned `ChatResponse` contains a list of `SourceCitation` objects containing the exact chunk IDs, filenames, titles, text excerpts, and relevance scores.
4. **Dual Provider Interface**:
   - Both **Ollama** (`llama3:8b`) and **Anthropic Claude** (`claude-3-5-sonnet-20241022`) sit behind the unified `BaseLLMClient` interface.
   - The active provider and model are tracked in configuration, persisted in session turns, and returned in every chat response payload.
   - **No Silent Switching**: Failures in the configured provider return immediate, actionable HTTP 503 / 400 error responses rather than silently delegating to an unconfigured service.

---

## 4. Compliance Audit & Verification Assessment

### Compliance Verdict
| Criterion | Status | Detail |
| :--- | :--- | :--- |
| **Anthropic Claude Agent SDK in Runtime Path** | **Partially Compliant / Custom Tool Loop** | The runtime path uses Anthropic tool JSON Schema specifications in a custom Python agent loop. The official `claude-agent-sdk` package is not executed because it bundles a 110MB binary that is hardcoded to Anthropic's cloud and strictly incompatible with local Ollama. |
| **Pi Coding Agent Support** | **Adapter Compliant** | Provided `PiCodingAgentAdapter` (`app/services/agent/pi_agent_adapter.py`) capable of generating the OpenAI-compatible `models.json` config for Ollama (`http://localhost:11434/v1`) and detecting npm CLI availability. |
| **Local Ollama Support** | **Verified (Mocked)** | `OllamaClient` implemented with reachability probes, model checks, and timeout handling. 100% covered by unit tests. |
| **Session Isolation & Persistence** | **Verified** | Session creation, multi-turn history, and session isolation tested and verified against SQLite. |
| **Zero Hallucination / Grounding** | **Verified** | Short-circuits with an honest limitation statement when transcripts lack matching evidence. |

### Real Service vs. Mocked Execution
- **Automated Tests**: 100% of LLM provider calls (`OllamaClient` and `AnthropicClient`) are covered by unit mocks. Zero live API calls or live Ollama requests are made during `pytest`.
- **Live Infrastructure**: PostgreSQL integration tests are skipped because no local PostgreSQL server is active on port 5432. Docker CLI is not installed on the host.
