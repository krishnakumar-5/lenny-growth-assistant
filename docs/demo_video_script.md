# 2–3 Minute Camera-On Demo Video Script & Guide

**Project:** The Lenny Growth Assistant  
**Role:** Forward Deployed Engineer (FDE) Take-Home Assignment  
**Target Duration:** 2 minutes 30 seconds  
**Format:** Camera-On (Picture-in-Picture or Split-Screen with Screen Recording)  

---

## Timing Cue Sheet & Walkthrough

```
[0:00 - 0:25] ── Introduction & System Architecture
[0:25 - 0:55] ── Grounded RAG Chat & Provenance Citation Inspection
[0:55 - 1:20] ── The Anti-Hallucination Refusal Gate
[1:20 - 1:55] ── Ship 30 for 30 Atomic Essay Skill & Sandboxed Artifact Viewer
[1:55 - 2:15] ── Knowledge Base Explorer & Dual Provider Setup (Ollama / Claude)
[2:15 - 2:30] ── Verification Summary & Conclusion
```

---

## Detailed Script & Actions

### 1. Introduction & Architecture (0:00 - 0:25)
- **Visual**: Camera on speaker (intro), then transition to browser view showing `http://localhost:5173`.
- **Spoken Script**:
  > *"Hi everyone, welcome to the demonstration of The Lenny Growth Assistant. Built as a Forward Deployed Engineer take-home project, this application extracts, synthesizes, and operationalizes high-leverage product and growth insights from Lenny's Podcast archives. The system is engineered as a containerized multi-tier application: FastAPI backend with SQLAlchemy and Alembic, a React 18 and Vite frontend, and a dual-provider inference layer supporting both local offline Ollama and cloud Anthropic Claude."*

### 2. Grounded Chat & Citation Inspection (0:25 - 0:55)
- **Visual**: Browser on Chat tab. Click suggested prompt or type: *"What is Elena Verna's reverse trial framework?"*.
- **Spoken Script**:
  > *"First, let's explore grounded conversational retrieval. Unlike standard LLM chatbots that make up plausible-sounding advice, our assistant operates under strict grounding rules. I'll ask about Elena Verna's reverse trial framework. Notice the response: it explains the 14-day enterprise trial with automatic downgrade to freemium. Below the answer, you can see the citation pill. When I click it, the Citation Inspector modal opens, displaying the exact transcript excerpt from Episode 78, relevance score, and source metadata."*

### 3. Anti-Hallucination Refusal Gate (0:55 - 1:20)
- **Visual**: Type in chat: *"Explain quantum entanglement and quantum computing architecture."*
- **Spoken Script**:
  > *"Now let's test our anti-hallucination safeguards. If I ask a question completely absent from the podcast knowledge base—such as quantum entanglement—the retrieval engine returns zero matching chunks. Instead of allowing the LLM to hallucinate or pretend Lenny discussed quantum physics, the evidence sufficiency gate short-circuits and delivers an honest refusal banner. Zero hallucination, zero wasted tokens."*

### 4. Ship 30 for 30 Essay Skill & Sandboxed Artifact Viewer (1:20 - 1:55)
- **Visual**: Click top navigation tab **"Ship 30 Essays"**. Select curated template **"Elena Verna: The 14-Day Reverse Trial"**. Click **Generate Atomic Essay Artifact**. The Artifact Viewer modal opens.
- **Spoken Script**:
  > *"Next, let's look at our dedicated skill: the Ship 30 for 30 Atomic Essay Generator. Based on Dickie Bush and Nicolas Cole's framework, this skill transforms podcast insights into a punchy, 200 to 300 word Atomic Essay with a scroll-stopping headline, a 1-sentence hook, and tactical bullet points. 
  > Notice our Secure Artifact Viewer: it confirms the word count constraint is satisfied. It provides a rendered Markdown view, and in the 'HTML Card' tab, it renders the card inside an isolated, sandboxed iframe without script execution privileges to eliminate XSS risks. Users can copy the Markdown or download a clean .md file with one click."*

### 5. Knowledge Explorer & Inference Toolbar (1:55 - 2:15)
- **Visual**: Click **"Transcripts"** tab. Search for *"pre-mortem"*. Show Shreyas Doshi chunks. Then point to the **Inference Settings** toolbar.
- **Spoken Script**:
  > *"Under the Transcripts tab, operators can browse and search indexed chunks directly to inspect relevance rankings. In our Inference Settings toolbar, users can seamlessly switch between local Ollama for zero-cost offline evaluation and cloud Anthropic Claude, as well as toggle the agent runtime between Anthropic tool calling and the Pi Coding Agent CLI adapter."*

### 6. Verification Summary & Conclusion (2:15 - 2:30)
- **Visual**: Switch back to terminal or display test summary.
- **Spoken Script**:
  > *"To ensure enterprise-grade reliability, our test suite boasts 68 backend tests in Pytest and 17 frontend tests in Vitest—all passing offline with zero external network dependencies. Thank you for watching, and all instructions to run the application locally are documented in the README!"*
