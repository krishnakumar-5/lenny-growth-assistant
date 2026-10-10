# Manual UI Test Plan: The Lenny Growth Assistant

**Application URL:** `http://localhost:5173`  
**Backend API URL:** `http://localhost:8000`  
**Target Browser:** Chrome, Edge, Safari, Firefox  

---

## Test Suite Overview

| Test Case | Feature Under Test | Expected Outcome |
| :--- | :--- | :--- |
| **TC-01** | System Health Badge | Displays "API v1.0" with green status indicator. |
| **TC-02** | Starter Prompt Chips | Clicking a starter chip populates and sends the query. |
| **TC-03** | Grounded Conversational Turn | Generates an answer with citations directly from transcripts. |
| **TC-04** | Citation Inspector Modal | Displays full chunk excerpt, guest name, episode, and score. |
| **TC-05** | Synthetic Benchmark Notice | Displays yellow warning banner for synthetic fixtures. |
| **TC-06** | Anti-Hallucination Refusal Gate | Refuses to answer queries absent from transcripts without hallucinating. |
| **TC-07** | Multi-Turn Conversation | Maintains conversational context across turns within a session. |
| **TC-08** | Reset Conversation Session | Clears chat history and creates a fresh session ID. |
| **TC-09** | Knowledge Base Explorer | Searches indexed transcript chunks directly with relevance scoring. |
| **TC-10** | Ship 30 Essay Generation | Synthesizes an Atomic Essay between 200 and 300 words. |
| **TC-11** | Artifact Viewer: Preview Tab | Displays typography, word count constraint badge, and citations. |
| **TC-12** | Artifact Viewer: HTML Card | Renders visual card safely inside a sandboxed `<iframe>`. |
| **TC-13** | Artifact Viewer: Export Actions | Successfully copies markdown to clipboard and downloads `.md`. |
| **TC-14** | Provider & Model Switching | Toggles between Ollama and Anthropic Claude models seamlessly. |
| **TC-15** | Graceful Error Recovery | Displays actionable troubleshooting guidance when a provider fails. |

---

## Detailed Test Procedures

### TC-01: System Health Badge
1. Open `http://localhost:5173` in your browser.
2. Observe the top-right corner of the navigation bar.
3. **Pass Criteria**: A badge displays `"API v1.0 (Postgres Online)"` or `"(SQLite/Offline DB)"` with a green shield icon.

### TC-02: Suggested Prompts Execution
1. On an empty chat screen, view the suggested prompts section.
2. Click **"Elena Verna on Growth Accounting"**.
3. **Pass Criteria**: The question is sent automatically, an amber loading indicator appears, and a response is rendered.

### TC-03: Grounded Conversational Turn
1. Enter query: *"What is Elena Verna's definition of a reverse trial?"*
2. Press **Enter** or click the send button.
3. **Pass Criteria**: The response outlines the 14-day full enterprise trial followed by graceful downgrade to freemium. Below the response, a citation badge appears (`[Elena Verna on Product-Led Growth (#1)]`).

### TC-04: Citation Inspector Modal
1. Click the citation pill attached to the assistant response in TC-03.
2. **Pass Criteria**: A modal opens displaying:
   - Transcript Title: *"The Ultimate Guide to Product-Led Growth (PLG) and Product-Led Sales"*
   - Guest: **Elena Verna** | Episode: **78**
   - Exact verbatim excerpt mentioning reverse trials.
   - Relevance score badge (e.g. `Score: 35.0`).

### TC-05: Synthetic Benchmark Notice
1. In the chat, ask: *"Explain the cohort retention accounting formulas from the benchmark sample."*
2. Click on the resulting citation for `sample_growth_accounting.md`.
3. **Pass Criteria**: The modal displays a yellow warning box: *"Synthetic Benchmark Test Data: This chunk is derived from test fixtures and is not an authentic recording from Lenny's Podcast."*

### TC-06: Anti-Hallucination Refusal Gate
1. Enter query: *"Explain quantum computing, quantum entanglement, and semiconductor lithography."*
2. Press **Enter**.
3. **Pass Criteria**: The assistant returns an honest refusal stating: *"I could not find sufficient information in the available podcast transcripts..."*. A refusal banner appears, and no external LLM hallucination is returned.

### TC-07: Multi-Turn Conversation Continuity
1. In the same conversation, ask: *"Who was the guest that explained that framework?"*
2. **Pass Criteria**: The assistant recalls the previous context and identifies the guest without losing the conversational thread.

### TC-08: Reset Conversation Session
1. Click the **"New Session"** button in the top navigation bar.
2. **Pass Criteria**: Chat messages are cleared, and the session ID resets.

### TC-09: Knowledge Base Explorer
1. Click the **"Transcripts"** tab in the top navigation bar.
2. Enter search term: *"pre-mortem"*, select **Top 5**, and click **Search**.
3. **Pass Criteria**: Results display chunks from Shreyas Doshi's episode explaining pre-mortems, along with relevance scores and file paths.

### TC-10: Ship 30 for 30 Atomic Essay Generation
1. Click the **"Ship 30 Essays"** tab in the top navigation bar.
2. Under curated frameworks, click **"Elena Verna: The 14-Day Reverse Trial"**.
3. **Pass Criteria**: The system triggers synthesis and automatically opens the **Artifact Viewer** with an Atomic Essay artifact.

### TC-11: Artifact Viewer: Preview Tab
1. In the Artifact Viewer, observe the Preview tab.
2. **Pass Criteria**:
   - Scroll-stopping headline starting with an H1 heading.
   - Word count constraint badge indicates: `245 words • Ship 30 Compliant (200-300w)`.
   - Core framework is broken into 3–4 bullet points.
   - Cites Elena Verna and lists verified transcript sources at the bottom.

### TC-12: Artifact Viewer: Sandboxed HTML Card
1. In the Artifact Viewer, click the **"HTML Card (Isolated)"** tab.
2. Inspect the iframe in browser DevTools (`F12`).
3. **Pass Criteria**: The card is rendered inside an `<iframe>` with attribute `sandbox=""`. The visual design is encapsulated and isolated from host styles.

### TC-13: Artifact Viewer: Export Actions
1. Click **"Copy"**. Verify notification changes to `"Copied"`. Paste into a text editor to confirm Markdown is copied.
2. Click **"Export .md"**.
3. **Pass Criteria**: The browser downloads a clean markdown file (e.g. `the-atomic-playbook-reverse-trial.md`).

### TC-14: Provider & Model Switching
1. In the top toolbar, switch Provider from **Ollama (Local Offline)** to **Anthropic (Cloud API)**.
2. Observe model updates to `claude-3-5-sonnet-20241022`.
3. Switch Framework to **Pi Coding Agent (CLI)**.
4. **Pass Criteria**: Toolbar reflects the active inference configurations.

### TC-15: Graceful Error Recovery
1. Select **Ollama** when the daemon is not running. Send a message.
2. **Pass Criteria**: The assistant returns an actionable error message explaining that Ollama is offline at `http://localhost:11434` with instructions on how to start it, without leaking stack traces.
