# 📄 PageIndexing RAG — Insurance & SPD Document QA

<p align="center">
  <strong>TOC-driven RAG for SPD & insurance documents — no embeddings, no vector DB, just a tree built from the document's own Table of Contents.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/LLM-Llama%203.3%2070B-blueviolet?logo=meta"/>
  <img src="https://img.shields.io/badge/Inference-Groq-orange"/>
  <img src="https://img.shields.io/badge/Parsing-Docling-green"/>
  <img src="https://img.shields.io/badge/License-MIT-lightgrey"/>
</p>

---

> A production-ready **Retrieval-Augmented Generation (RAG)** pipeline for querying **insurance and Summary Plan Description (SPD) documents**. Unlike generic RAG approaches, this system leverages the document's own **Table of Contents** to build a hierarchical index tree — then traverses that tree at query time using LLM reasoning to pinpoint the exact section containing the answer.

---

## 🧠 Why This Project?

SPD and insurance documents are notoriously hard to query:

- Chunk-based RAG loses the document's **hierarchical structure** and returns noisy, out-of-context results
- Standard embedding search has no awareness of **section boundaries or document hierarchy**
- SPD documents **do have a Table of Contents** — but it's rarely exploited for structured retrieval

This project solves those problems by:

1. **Parsing** the PDF into structured, page-aware HTML
2. **Extracting headings** from all pages to enrich the structural understanding
3. **Building a hierarchical index tree** directly from the document's Table of Contents
4. **Traversing the tree** at query time — node by node — guided by LLM reasoning
5. **Extracting** a precise, grounded answer with full cost and trace logging

---

## ✨ Features

- 🌲 **TOC-Driven Tree Indexing** — the index hierarchy is built directly from the document's own Table of Contents, preserving its logical structure
- 🔍 **4-Phase Retrieval Pipeline** — query understanding → tree traversal → context extraction → answer
- 💡 **Smart Query Planning** — rewrites, relevance checks, and intent classification before retrieval
- 💰 **Per-query Cost Tracking** — token counts, USD cost, and latency for every LLM step
- 🗂️ **Chat History Support** — multi-turn conversation memory
- 📊 **RAG Evaluation Module** — built-in eval script using OpenRouter (Claude 3 Haiku)
- 🧾 **Trace Logging** — every query logged to `process.log` with a unique Query ID
- ⚡ **Ultra-low cost** — ~$0.006 per query with Groq + Llama 3.3 70B

---

## 🏗️ Architecture Overview

### How It Works

```
PDF / SPD Document (contains a Table of Contents)
       │
       ▼
┌──────────────────────────────┐
│         INGESTION             │
│                               │
│  ┌────────────────────────┐  │
│  │       Parsing          │  │  Docling + Structured HTML
│  │  parse.py              │  │
│  │  page_mapper.py        │  │
│  │  structured_html.py    │  │
│  └──────────┬─────────────┘  │
│             │                 
│  ┌──────────▼─────────────┐  │
│  │       Indexing         │  │
│  │                           │
│  │                           │  Builds the index tree from the TOC
│  │                           │   Aggregates pages into nodes
│  │                                Summarizes each node
│  └──────────┬─────────────┘  │
└─────────────┼────────────────┘
              │
              ▼
     TOC-Based Document Index Tree (JSON)
              │
              ▼
┌─────────────────────────────────────────┐
│           QUERY RETRIEVAL               │
│                                         │
│  Phase 1 ── Query Understanding         │
│    • Query Rewrite                      │
│    • Relevance Check                    │
│    • Classification (Simple/Complex)    │
│    • Query Planning (Single/Multi)      │
│                                         │
│  Phase 2 ── Tree Traversal              │
│    • Choose Root Node (from TOC tree)   │
│    • Choose Child Node (recursive)      │
│    • Land on Best Leaf Section          │
│                                         │
│  Phase 3 ── Context Extraction          │
│    • Extract full content of leaf node  │
│                                         │
│  Phase 4 ── Final Answer                │
│    • Grounded answer from context       │
└─────────────────────────────────────────┘
              │
              ▼
   Answer + Cost Summary + Trace Log
```

---

### 🌲 Document Index Tree Structure

The index tree is built directly from the SPD document's Table of Contents. Each node corresponds to a real section in the document, with a title, page range, semantic summary, and child nodes — forming a navigable hierarchy that mirrors how the document itself is organized.

Each node schema:

```json
{
  "title": "COMPREHENSIVE EMPLOYEE HEALTH BENEFIT PLAN",
  "node_id": "0001",
  "start_index": 0,
  "end_index": 141,
  "summary": "Establishment and adoption of the plan...",
  "content": null,
  "nodes": [
    { "title": "ESTABLISHMENT AND ADOPTION OF THE PLAN", "node_id": "0002", ... },
    { "title": "INTRODUCTION AND PURPOSE",               "node_id": "0003", ... },
    { "title": "REQUIRED NOTICES",                      "node_id": "0004", ... },
    { "title": "PLAN DEFINITIONS",                      "node_id": "0005", ... },
    { "title": "ELIGIBILITY, TERMINATION, AND CONTINUATION OF COVERAGE", "node_id": "0006", ... }
  ]
}
```

> The tree structure directly reflects the document's own TOC — so traversal at query time always follows the document's intended organization.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| LLM Inference | [Groq](https://groq.com) — Llama 3.3 70B Versatile |
| Evaluation LLM | [OpenRouter](https://openrouter.ai) — Claude 3 Haiku |
| Parsing Engine | [Docling](https://github.com/DS4SD/docling) + Custom HTML Structuring |
| Indexing Strategy | TOC-Based Hierarchical Tree Indexing |
| Language | Python 3.13 |
| Environment | Virtual Environment (`venv`) |

---

## 📁 Project Structure

```
PageIndexingWithoutTOC/
│
├── ingestion/                              # Document ingestion pipeline
│   ├── indexing/
│   │   ├── __init__.py
│   │   ├── heading_extractor.py            # Extracts headings from all pages of the document
│   │   ├── indexing_aggregator.py          # Aggregates pages into hierarchical tree nodes
│   │   ├── indexing_main.py                # Indexing entry point
│   │   ├── markdown_toc.py                 # Markdown TOC utilities
│   │   ├── page_schema.py                  # Page-level data schema
│   │   ├── parent_node_summerizer.py       # Generates summaries for parent nodes in the tree
│   │   ├── schema.py                       # Node/tree data schema
│   │   ├── semantic_page_extractor.py      # Extracts semantic structure per page
│   │   └── toc_indexing.py                 # Builds the hierarchical index tree from the document's TOC
│   │
│   ├── parsing/
│   │   ├── __init__.py
│   │   ├── page_mapper.py                  # Maps parsed output to page objects
│   │   ├── parse_main.py                   # Parsing entry point
│   │   ├── parse.py                        # Core PDF parsing logic (Docling)
│   │   └── structured_html.py              # Converts parsed content to structured HTML
│   │
│   ├── __init__.py
│   ├── config.py                           # Ingestion configuration & constants
│   └── ingestion_start_pipeline.py         # Full ingestion pipeline runner
│
├── ingestion_results/                      # Output JSON index trees (per document)
├── logs/                                   # Query trace logs (process.log)
│
├── query_retrieval/                        # Query & retrieval engine
│   ├── __init__.py
│   ├── chat_history.py                     # Multi-turn conversation memory
│   ├── cost_estimation.py                  # Per-query cost & token tracking
│   ├── indexing_summery.py                 # Index summary utilities
│   ├── pretty_query.py                     # Formatted terminal output
│   ├── retrieval_engine.py                 # Core TOC-tree traversal & retrieval logic
│   └── retrieval_main.py                   # Retrieval entry point / CLI
│
├── venv/                                   # Python virtual environment
├── rag_evaluation.py                       # RAG evaluation script (Claude 3 Haiku via OpenRouter)
├── utils.py                                # Shared utility functions
├── requirements.txt                        # Python dependencies
├── .env.template                           # Environment variable template
├── .env                                    # Your local secrets (not committed)
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- A [Groq API key](https://console.groq.com/) (free tier available)
- An [OpenRouter API key](https://openrouter.ai/) (for evaluation only)

---

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/PageIndexingWithoutTOC.git
cd PageIndexingWithoutTOC
```

---

### 2. Create & Activate Virtual Environment

```bash
python3.13 -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

```bash
cp .env.template .env
```

Edit `.env`:

```env
# ── Groq ────────────────────────────────────────────────────────────
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_LLM_MODEL=llama-3.3-70b-versatile

# ── Gemini ──────────────────────────────────────────────────────────
GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MODEL=gemini-2.5-flash

```

---

### 5. Add Your Document

Place your SPD or insurance PDF in the `data/` directory:

```bash
cp your_insurance_doc.pdf data/
```

---

### 6. Run the Ingestion Pipeline

This parses the PDF, extracts headings, reads the Table of Contents, and builds the hierarchical index tree:

```bash
python ingestion/ingestion_start_pipeline.py --file data/your_insurance_doc.pdf
```

The index JSON will be saved under `ingestion_results/`.

---

### 7. Query Your Document

```bash
python query_retrieval/retrieval_main.py
```

You'll be prompted to enter questions in an interactive loop. Each query outputs:
- ✅ The 4-phase retrieval trace
- 💬 The final grounded answer
- 💰 A full cost summary (tokens, USD, latency per step)

---

## 📊 Evaluation

Run the built-in RAG evaluation script (uses Claude 3 Haiku via OpenRouter):

```bash
python rag_evaluation.py
```

This scores the pipeline across dimensions like faithfulness, relevance, and completeness.

---

## 🔑 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Groq API key for LLM inference (Llama 3.3 70B) |
| `OPENROUTER_API_KEY` | ⚠️ Eval only | OpenRouter key for evaluation (Claude 3 Haiku) |

---

## 💡 Key Design Decisions

**Why use the document's TOC for indexing?**
SPD documents are long and dense, but they always ship with a structured Table of Contents. Rather than ignoring it, this system reads the TOC to build the index tree — so the hierarchy is grounded in the document's own organization, not inferred heuristically.

**Why tree traversal instead of vector search?**
Chunk-based vector search loses document hierarchy and often retrieves semantically similar but contextually wrong passages. By traversing the TOC-based tree, the retrieval follows the document's own logical structure — narrowing scope at each level for far more precise results with fewer tokens consumed.

**Why Groq + Llama 3.3 70B?**
Ultra-fast inference (~2.5s end-to-end for 6 LLM calls) at under $0.006 per query, making it practical for high-volume document QA.

---

## 📌 Roadmap

- [ ] Automated evaluation benchmarks

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

- [Groq](https://groq.com) for blazing-fast LLM inference
- [Docling](https://github.com/DS4SD/docling) for robust PDF parsing
- [OpenRouter](https://openrouter.ai) for multi-model evaluation access
- Meta's **Llama 3.3 70B** for powering the retrieval pipeline

---

<p align="center">Built with ❤️ for anyone who has ever had to read a 60-page insurance document.</p>