# System & UI/UX Design Specification

## 1. Overview & UI/UX Architecture

**The Lenny Growth Assistant** features a responsive web interface designed with React 18, Vite, TypeScript, and Tailwind CSS. The design language emphasizes clarity, readability, and immediate trust through provenance transparency.

### Design Principles
1. **Provenance First**: Every insight provided by an assistant turn must show where it came from via clickable citation badges.
2. **Honest Incompleteness**: If information is absent or insufficient, display explicit, non-accusatory refusal banners rather than fabricating context.
3. **Artifact-Driven Productivity**: Complex outputs (playbooks, Ship 30 essays) are treated as first-class, exportable artifacts with sandboxed visual previews.
4. **Zero-Configuration Switching**: Seamlessly toggle between local Ollama and cloud Anthropic without restarting the application.

---

## 2. Frontend Component Hierarchy

```
frontend/src/
├── App.tsx                     # Top-level coordinator, session lifecycle, message turns
├── components/
│   ├── Navbar.tsx              # Brand header, system health pill, active session reset, tab toggle
│   ├── ModelSelector.tsx       # Provider (Ollama / Anthropic), Model, and Agent Framework toolbar
│   ├── ChatMessage.tsx         # User & assistant bubbles, formatted markdown, and citation pills
│   ├── SuggestedPrompts.tsx    # Curated query starters (PLG, Retention, and Refusal test)
│   ├── KnowledgeExplorer.tsx   # Search and inspect indexed chunks, scores, and provenance
│   ├── Ship30Generator.tsx     # Atomic Essay generator with curated frameworks and custom topic input
│   ├── ArtifactViewer.tsx      # Secure, sandboxed viewer for Atomic Essays (Markdown & HTML iframe)
│   └── CitationInspector.tsx   # Modal for deep inspection of retrieved chunks and synthetic disclaimer
├── services/
│   └── api.ts                  # Type-safe fetch client with ApiError status propagation
└── types/
    └── api.ts                  # TypeScript interfaces matching backend Pydantic models
```

---

## 3. UI/UX Interaction Flows

### Flow 1: Grounded Conversational Turn
1. **User Query**: User submits a question (e.g., *"What is Elena Verna's reverse trial?"*).
2. **Optimistic Turn**: User message immediately appears in the message list with a timestamp.
3. **Loading State**: An amber indicator indicates retrieval and synthesis progress.
4. **Assistant Response**:
   - Parsed with markdown headings, bold accents, and lists.
   - Grounding citation pills appear below the message (e.g. `[Elena Verna on PLG (#1)]`).
   - If ungrounded, an amber refusal badge appears: *"Strict Grounding Active: No transcript evidence found"*.
5. **Citation Inspection**: Clicking any citation pill opens the `CitationInspector` modal showing full chunk text and metadata.

### Flow 2: Ship 30 for 30 Atomic Essay Generation
1. **Navigation**: User clicks the **Ship 30 Essays** tab in the top navigation.
2. **Selection**: User chooses a curated framework (e.g. *"Elena Verna: The 14-Day Reverse Trial"*) or enters a custom topic.
3. **Synthesis**: The backend retrieves authentic transcript evidence and formats an Atomic Essay strictly between 200 and 300 words.
4. **Artifact Viewer Modal**:
   - Opens automatically with three tabs: **Preview** (typography), **HTML Card** (sandboxed iframe), and **Raw Markdown**.
   - Displays a green/amber word count constraint pill: e.g. *"245 words • Ship 30 Compliant (200-300w)"*.
   - One-click buttons to **Copy Markdown** or **Export .md**.

---

## 4. Security Architecture & Artifact Sandbox Isolation

### The Sandboxed iframe Architecture
When rendering HTML/CSS artifacts (such as visual cards for Atomic Essays), injecting untrusted or LLM-generated HTML directly into the host DOM using `dangerouslySetInnerHTML` introduces severe security risks:
- Cross-Site Scripting (XSS) attacks.
- Cookie and LocalStorage exfiltration.
- CSS style leakage affecting the host application layout.

**Our Solution in `ArtifactViewer.tsx`**:
```tsx
<iframe
  title="Sanitized HTML Artifact Preview"
  srcDoc={artifact.content_html}
  sandbox=""
  className="w-full h-[520px] border-0"
/>
```

**Security Guarantees**:
1. **`sandbox=""`**: Treats the iframe content as being from an entirely unique origin.
2. **Zero Script Execution**: Without `allow-scripts`, no JavaScript within the generated HTML can execute.
3. **Zero Storage Access**: The iframe cannot access cookies, session tokens, or `localStorage` of the parent host.
4. **Zero DOM Traversal**: The iframe document is completely decoupled from the parent application DOM tree.
5. **Style Encapsulation**: CSS within the iframe is strictly constrained to its internal bounding box.

---

## 5. API Design & Data Contracts

### 1. `POST /api/v1/chat`
- **Request**:
  ```json
  {
    "message": "What is cohort retention?",
    "session_id": "optional-uuid",
    "provider": "ollama",
    "model": "llama3:8b",
    "agent_framework": "anthropic_tool_agent"
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "message": "Cohort retention measures user engagement over uniform time periods...",
    "role": "assistant",
    "provider": "ollama",
    "model": "llama3:8b",
    "agent_framework": "anthropic_tool_agent",
    "sources": [
      {
        "chunk_id": "c1",
        "transcript_title": "Elena Verna on PLG",
        "score": 35.0,
        "metadata": { "guest": "Elena Verna" }
      }
    ],
    "insufficient_evidence": false
  }
  ```

### 2. `POST /api/v1/skills/ship30-essay`
- **Request**:
  ```json
  {
    "topic": "The 14-day reverse trial in B2B SaaS",
    "target_audience": "Founders and Growth PMs",
    "provider": "ollama",
    "model": "llama3:8b"
  }
  ```
- **Response**:
  ```json
  {
    "title": "The Death of the 30-Day Free Trial",
    "hook": "Most B2B SaaS companies kick users out after 14 days...",
    "word_count": 245,
    "within_constraints": true,
    "content_markdown": "# The Death of the 30-Day Free Trial...",
    "content_html": "<!DOCTYPE html>...",
    "guest_attribution": "Elena Verna",
    "sources": [...]
  }
  ```

---

## 6. Error Handling & Resilience

| Scenario | HTTP Status | User-Facing Presentation |
| :--- | :---: | :--- |
| **Ollama Daemon Offline** | 503 | Displays actionable guidance: *"Local Ollama service is unavailable at http://localhost:11434. Verify 'ollama serve' or switch Provider to Anthropic."* |
| **Anthropic Key Missing** | 400 | Informs user that `ANTHROPIC_API_KEY` is not set in `.env`. |
| **Zero Transcripts Match** | 422 / 200 (flagged) | Refusal notification: *"Grounding Safeguard Notice: No verified podcast transcripts matched topic."* |
| **Pi CLI Missing** | 503 | Notifies user that `pi` CLI executable is not on PATH and explains how to install it. |
