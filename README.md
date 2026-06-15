# 🎙️ Voice Agent with Dual RAG Tools

<p align="center">
  <strong>Voice-enabled AI agent for healthcare benefit document QA — powered by LangGraph, dual RAG pipelines, Whisper STT, and Piper TTS.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Agent-LangGraph-orange"/>
  <img src="https://img.shields.io/badge/STT-faster--whisper-green"/>
  <img src="https://img.shields.io/badge/TTS-Piper-purple"/>
  <img src="https://img.shields.io/badge/LLM-Groq%20%7C%20Gemini-blueviolet"/>
  <img src="https://img.shields.io/badge/License-MIT-lightgrey"/>
</p>

---

> A voice-enabled AI agent that answers questions about healthcare benefit documents. The system integrates two independent RAG retrieval pipelines — one for **SBC** (Summary of Benefits and Coverage) documents and one for **SPD** (Summary Plan Description) documents — wired into a **LangGraph** agent that routes queries to the right tool, and wraps everything in a full **voice loop** (speech-to-text → agent → text-to-speech). Text mode is also supported for fast testing without a microphone.

---

## 🧠 What This Project Does

Healthcare benefit documents come in two forms that serve very different purposes:

- **SBC** — short summary covering deductibles, copays, out-of-pocket limits, and what is or isn't covered
- **SPD** — the full legal plan document covering eligibility, exclusions, definitions, COBRA, HIPAA, appeals, and more

This agent lets users **speak or type a question**, routes it to the correct document pipeline, retrieves a grounded answer, and **speaks or prints it back** — all locally, with no cloud dependency for voice or retrieval.

---

## ✨ Features

- 🎤 **Voice Input** — `faster-whisper` transcribes microphone audio to text locally
- ⌨️ **Text Input** — type questions directly in the terminal without a microphone
- 🔊 **Voice Output** — Piper TTS converts the agent's answer back to spoken audio
- 📝 **Text Output** — answer always printed to the terminal regardless of mode
- 🤖 **LangGraph Agent** — ReAct agent with two registered RAG tools; routes each query to the right document
- 📄 **Dual RAG Pipelines** — separate retrieval backends for SBC and SPD; data is never mixed
- 🧭 **Smart Tool Routing** — agent decides whether to call `search_sbc`, `search_spd`, both, or neither based on the query
- 🌐 **Dual LLM Support** — switch between Groq (Llama 3.3 70B) and Gemini (2.5 Flash) at runtime
- 💰 **Per-query Cost Tracking** — token counts, USD cost, and latency logged per LLM step
- 🧾 **Trace Logging** — every query logged to `process.log` with a unique Query ID

---

## 🏗️ Architecture Overview

```
 🎤 Microphone Input          ⌨️  Text Input
        │                              │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │   STT — faster-whisper   │   Transcribes spoken audio → text
        │   recorder.py            │   Captures audio via sounddevice
        │   transcriber.py         │   (skipped in text mode)
        └─────────────┬────────────┘
                      │
                      ▼
        ┌─────────────────────────────────────────┐
        │         LangGraph ReAct Agent           │
        │         agent.py                        │
        │                                         │
        │  Step 1 — Relevance Check               │
        │    Is this about SBC, SPD, or neither?  │
        │                                         │
        │  Step 2 — Tool Routing                  │
        │   ┌─────────────┐   ┌──────────────┐   │
        │   │ @search_sbc │   │ @search_spd  │   │
        │   │ SBC Pipeline│   │ SPD Pipeline │   │
        │   └──────┬──────┘   └──────┬───────┘   │
        │          └────────┬─────────┘           │
        │                   │                     │
        │  Step 3 — Final Answer                  │
        │    Grounded response from retrieved     │
        │    context — no hallucination           │
        └──────────────────┬──────────────────────┘
                           │
                           ▼
        ┌──────────────────────────┐
        │   TTS — Piper            │   Converts answer text → speech
        │   tts.py                 │   Plays audio via aplay
        └──────────────────────────┘   (skipped in text mode)
                           │
                           ▼
          🔊 Spoken Answer  +  📝 Printed Answer
```

---

## 🖥️ Demo

### Voice Mode — General Knowledge Query (not benefit-related)

```
════════════════════════════════════════════════════════════════════════
  AGENT QUERY RESULT
════════════════════════════════════════════════════════════════════════

  Step 1  ◈ Relevance Check
  ✗ Not related to any benefit document → General knowledge question

  Step 2  ◆ General Answer

──────────────────────────────────────────────────────────────────────
  ANSWER
──────────────────────────────────────────────────────────────────────
  Nepal is a landlocked country in South Asia, known for its diverse
  geography including the Himalayas, and its rich cultural heritage.
════════════════════════════════════════════════════════════════════════
```

> Agent correctly identifies the question is not benefit-related and answers from general knowledge — no tool called.

---

### Voice Mode — SBC Document Query (benefit-related)

```
  COST SUMMARY
────────────────────────────────────────────────────────────────────
  Total LLM Calls :    7
  Total Tokens    :    In: 7,869  |  Out: 238
  Total Cost      :    $0.004831 USD
  Total LLM Time  :    3.010s

  Step               Model                      In     Out    Cost      Time
  domain_summary     llama-3.3-70b-versatile    106     21   $0.000079  0.409s
  query_rewrite      llama-3.3-70b-versatile    195      3   $0.000117  0.262s
  relevance_check    llama-3.3-70b-versatile    191     19   $0.000128  0.274s
  query_classification llama-3.3-70b-versatile  126     18   $0.000089  0.194s
  choose_root        llama-3.3-70b-versatile    555    100   $0.000406  0.530s
  choose_child       llama-3.3-70b-versatile  5,247     65   $0.003147  0.919s
  extract_answer     llama-3.3-70b-versatile  1,449     12   $0.000864  0.422s

  Trace logged → process.log   Query ID → e2416a1a-8bf3-4732-9c8e-cab382f62f06

════════════════════════════════════════════════════════════════════════
  AGENT QUERY RESULT
════════════════════════════════════════════════════════════════════════

  Step 1  ◈ Relevance Check
  ✓ Related to benefit document → SBC (Summary of Benefits and Coverage)

  Step 2  ◆ Calling Tool → @search_sbc  [SBC Document]

──────────────────────────────────────────────────────────────────────
  ANSWER
──────────────────────────────────────────────────────────────────────
  The overall deductible is $500 for an individual or $1,000 for a family.
════════════════════════════════════════════════════════════════════════

Playing WAVE '.../voice_interface/output.wav'
```

> Agent routes to `@search_sbc`, retrieves a grounded answer from the SBC document, prints it, and plays it as speech.

---

## 📁 Project Structure

```
VOICE AGENT WITH DUAL RAG TOOLS/
│
├── _backend/                          # FastAPI backend (API layer)
│   ├── api.py                         # REST API endpoints
│   └── schema.py                      # Request/response schemas
│
├── agent/                             # LangGraph agent core
│   ├── agent.py                       # ReAct agent, tool routing, LLM config, display logic
│   ├── search_tools.py                # Tool definitions for agent (search_sbc, search_spd)
│   ├── tool_summaries_cache.json      # Cached document summaries for tool selection
│   └── tools.py                       # Tool registration for LangGraph
│
├── indexing_for_sbc/                  # RAG pipeline for SBC documents
│   └── ...                            # Ingestion, indexing, retrieval (see SBC README)
│
├── indexing_for_spd/                  # RAG pipeline for SPD documents
│   └── ...                            # Ingestion, indexing, retrieval (see SPD README)
│
├── piper_libs/                        # Piper TTS shared libraries (.so files + espeak-ng-data)
├── venv/                              # Python virtual environment
│
├── voice_interface/                   # Voice I/O layer
│   ├── models/                        # Piper ONNX voice model
│   │   └── en_US-lessac-medium.onnx
│   ├── input.wav                      # Recorded microphone audio (runtime)
│   ├── output.wav                     # Generated TTS audio (runtime)
│   ├── recorder.py                    # Microphone capture via sounddevice
│   ├── transcriber.py                 # faster-whisper STT transcription
│   ├── tts.py                         # Piper TTS text-to-speech output
│   └── voice_rag.py                   # Voice + RAG integration utilities
│
├── .env                               # API keys — see template below (not committed)
├── .gitignore
├── piper                              # Piper TTS binary (Linux x86_64)
├── process.log                        # Query trace log
├── README.md
└── requirements.txt
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | [LangGraph](https://github.com/langchain-ai/langgraph) — ReAct agent with tool nodes |
| LLM Backend | [Groq](https://groq.com) (Llama 3.3 70B) · [Gemini](https://ai.google.dev) (2.5 Flash) |
| RAG — SBC | Custom TOC-based hierarchical indexing pipeline |
| RAG — SPD | Custom TOC-based hierarchical indexing pipeline (separate) |
| Speech-to-Text | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — Whisper base model, CPU/int8 |
| Text-to-Speech | [Piper](https://github.com/rhasspy/piper) — `en_US-lessac-medium` ONNX model |
| Audio Capture | [sounddevice](https://python-sounddevice.readthedocs.io/) |
| Audio Playback | `aplay` (Linux ALSA) |
| Language | Python 3.12 |

---

## 🔧 How the Agent Works

### Tool Routing Logic

The LangGraph agent is initialized with two tools and a system prompt that includes a condensed summary of each document. At query time it follows these rules:

- Query relates to **SBC** (deductibles, copays, out-of-pocket, coverage summaries) → calls `search_sbc` only
- Query relates to **SPD** (eligibility, exclusions, COBRA, HIPAA, appeals, definitions) → calls `search_spd` only
- Query relates to **both** → calls both tools and combines results
- Query is **unrelated to either document** → answers from general knowledge, no tool called

### Tool Summary Cache

On first run, the agent reads the root node summary from each document's index JSON, condenses it with an LLM call, and saves the result to `agent/tool_summaries_cache.json`. Subsequent runs load from cache — no extra LLM calls at startup.

### Two RAG Tools

```python
@tool
def search_sbc(query: str) -> str:
    """Search the Summary of Benefits and Coverage (SBC) document.
    Best for: coverage summaries, deductibles, copays, out-of-pocket maximums,
    what is covered or not covered, cost sharing details.
    """

@tool
def search_spd(query: str) -> str:
    """Search the Summary Plan Description (SPD) document.
    Best for: detailed plan rules, eligibility, exclusions, definitions,
    procedures, appeals, COBRA, HIPAA, legal provisions.
    """
```

Each tool runs the full RAG retrieval pipeline against its own document index and returns a grounded answer string to the agent.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Linux (Piper TTS uses `aplay` for playback)
- A working microphone (for voice mode only — text mode works without one)
- [Groq API key](https://console.groq.com/) and/or [Gemini API key](https://ai.google.dev/)
- SBC and SPD documents already ingested — indexes must exist under `indexing_for_sbc/` and `indexing_for_spd/` (refer to their individual READMEs)

---

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/voice-agent-dual-rag.git
cd voice-agent-dual-rag
```

### 2. Create & Activate Virtual Environment

```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the template and fill in your API keys:

```bash
cp .env.template .env
```
edit .env
GROQ_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_LLM_MODEL=llama-3.3-70b-versatile

# ── Gemini ──────────────────────────────────────────────────────────
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MODEL=gemini-2.5-flash
```



> You only need keys for the provider(s) you intend to use. The agent prompts you to choose Groq or Gemini at runtime.

### 5. Verify Piper Binary

The Piper TTS binary must be present at the project root:

```bash
# If not already extracted:
tar -xzf piper_linux_x86_64.tar.gz
# Confirm binary exists:
ls piper
```

### 6. Verify Document Indexes Exist

Before running the agent, make sure both RAG pipelines have been ingested. The agent expects index files at:

```
indexing_for_sbc/ingestion_results/.../Final_Indexing.json
indexing_for_spd/ingestion_results/.../master_indexing.json
```

Refer to the individual READMEs inside `indexing_for_sbc/` and `indexing_for_spd/` for ingestion instructions.

### 7. Run the Agent

```bash
python3 -m agent.agent
```

You will be prompted to select an LLM provider and then a mode:

```
Choose LLM Provider:
[1] Gemini
[2] Groq
Select Option (1-2):

Active Provider: GEMINI
════════════════════════════════════════════════════════════

[1] Text Mode
[2] Voice Mode
[q] Quit
Select Mode:
```

**Text Mode** — type questions directly into the terminal. No microphone needed.  
**Voice Mode** — speak into your microphone; the agent transcribes, reasons, and speaks the answer back. Answer is also printed to the terminal.

You can switch modes between questions without restarting.

---

## 🔑 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ If using Groq | Groq API key for Llama 3.3 70B inference |
| `GROQ_LLM_MODEL` | ⚙️ Optional | Override Groq model (default: `llama-3.3-70b-versatile`) |
| `GEMINI_API_KEY` | ✅ If using Gemini | Google API key for Gemini 2.5 Flash |
| `MODEL` | ⚙️ Optional | Override Gemini model name (default: `gemini-2.5-flash`) |

---

## 💡 Key Design Decisions

**Why two separate RAG indexes?**
SBC and SPD serve fundamentally different purposes. Mixing them into a single retrieval pool would cause the agent to retrieve irrelevant context. Keeping them isolated ensures every answer comes from the right document.

**Why tool summary caching?**
Rather than hardcoding document descriptions in the system prompt, the agent generates condensed summaries from the actual index content on first run and caches them. This makes tool routing adaptive to whatever documents were ingested, and costs only one LLM call ever.

**Why Piper over Coqui TTS?**
Piper produces high-quality natural speech with very low latency, runs fully offline with a single binary and ONNX model, and has no Python dependency conflicts. Audio playback uses `aplay` directly to avoid `playsound` library issues on Linux.

**Why faster-whisper?**
The base model on CPU with int8 quantization gives accurate transcription in under a second for short utterances, with zero API cost and no data leaving the machine.

**Why both text and voice modes?**
Voice mode is the primary interface but requires hardware setup. Text mode lets you develop, test, and demo the agent instantly without a microphone or audio output.

---

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change. Pull requests should target the `main` branch.

1. Fork the repo
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [LangGraph](https://github.com/langchain-ai/langgraph) for the ReAct agent framework
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for local, efficient speech recognition
- [Piper](https://github.com/rhasspy/piper) for fast, offline neural text-to-speech
- [Groq](https://groq.com) and [Google Gemini](https://ai.google.dev) for LLM inference

---

<p align="center">Built for anyone who has ever wished they could just <em>ask</em> their insurance plan a question.</p>