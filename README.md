# 🏠 Real Estate Intelligence Platform — Prime Lands

A production-ready **Retrieval-Augmented Generation (RAG)** system built on top of real Sri Lankan property listings from [primelands.lk](https://www.primelands.lk). This platform combines async web crawling, multi-strategy chunking, intelligent caching, and corrective retrieval to deliver accurate, citation-backed answers to real estate queries.

---

## 🎯 Project Overview

This project builds a full end-to-end real estate Q&A system using modern RAG techniques. Starting from raw web crawling, it processes property data through five different chunking strategies, indexes them into a Qdrant vector database, and serves queries through three intelligent retrieval layers: standard RAG, Cache-Augmented Generation (CAG), and Corrective RAG (CRAG).

**Key Goals:**

- Crawl and structure property listings from primelands.lk
- Benchmark 5 chunking strategies for retrieval quality
- Implement CAG for sub-500ms FAQ responses
- Implement CRAG with confidence-based corrective retrieval
- Evaluate performance with rigorous quantitative metrics

---

## 📁 Project Structure

```
real_state/
│
├── src/
│   └── real_state/
│       │
│       ├── application/
│       │   └── chat_service/
│       │       ├── cag_cache.py        # Two-tier cache logic (FAQ + history)
│       │       ├── cag_service.py      # Cache-Augmented Generation service
│       │       └── rag_service.py      # Base RAG with LCEL chain & citations
│       │
│       ├── domain/
│       │   ├── prompts/                # Prompt templates
│       │   ├── __init__.py
│       │   ├── models.py               # Domain models & entities
│       │   └── utils.py                # Shared utility functions
│       │
│       ├── ingest_document_service/
│       │   ├── __init__.py
│       │   ├── chunkers.py             # All 5 chunking strategies
│       │   └── web_crawler.py          # Async Playwright crawler
│       │
│       └── infrastructure/
│           ├── db/
│           │   ├── __init__.py
│           │   └── vector_db.py        # Qdrant vector store integration
│           │
│           └── llm_provider/
│               ├── __init__.py
│               ├── embeddings.py       # Embedding model setup
│               └── llm_service.py      # LLM provider abstraction
│
├── main.py                             # Application entry point
├── config.py                           # Centralised configuration
├── .env                                # Environment variables (not committed)
├── .env-example                        # Environment variable template
├── .gitignore
├── .python-version
├── pyproject.toml                      # Project dependencies & metadata
├── uv.lock                             # Locked dependency versions
└── README.md
```

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js (for Playwright)
- Openrouter(Recommended) or openai API key

### Install Dependencies

This project uses [`uv`](https://github.com/astral-sh/uv) for fast dependency management.

```bash
git clone <repo-url>
cd real-state-rag

# Install uv if you don't have it
pip install uv

# Install all dependencies from lockfile
uv sync

# Install Playwright browser
uv run playwright install chromium
```

### Cofingure

Copy the environment template and fill in your values:

```bash
cp .env-example .env
```

Edit `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
# or
OPENAI_API_KEY=sk-proj-your-key-here

QDRANT_API_KEY=qdrant-api-key
QDRANT_URL=qdrant-url
QDRANT_COLLECTION_NAME='prime_lands'
```

All configuration are saved in `config.yaml` and `config.yaml` is loaded at the runtime.
You can change all configerations

## Part 1 — Web Crawler

- Async BFS traversal of primelands.lk with proper browser lifecycle management
- JavaScript rendering support for dynamic property listings
- Rate limiting to avoid overloading the server
- Extracts all metadata fields: `property_id`, `title`, `address`, `price`, `bedrooms`, `bathrooms`, `sqft`, `amenities`, `agent`
- Outputs: individual `.md` files per property + `data/primelands_corpus.jsonl`

**Quick Verify:**

```bash
wc -l data/primelands_corpus.jsonl
```

## Part 2 — Chunking Lab

Five chunking strategies implemented and benchmarked:

| Strategy          | Description                                |
| ----------------- | ------------------------------------------ |
| **Semantic**      | Splits on semantic similarity boundaries   |
| **Fixed**         | Token-based fixed-size windows             |
| **Sliding**       | Fixed size with configurable overlap       |
| **Parent-Child**  | Hierarchical chunks with parent linking    |
| **Late Chunking** | Embedding-aware chunking at retrieval time |

All 5 strategies are indexed into separate Qdrant collections with full embedding metadata.

## 🧠 Part 3 — Intelligence Layers

**Tool:** LangChain LCEL + Qdrant | **Points: 25**

### RAGService

- Modern LCEL `Runnable` chain
- Retriever integration with top-k semantic search
- Inline citations with source URLs in every response

### CAGService

- Two-tier cache: **FAQ cache** (pre-warmed) + **history cache** (session)
- Semantic similarity matching using cosine similarity (threshold > 0.90)
- Cache hit/miss tracking and statistics
- Sub-500ms response for cached FAQ queries

### CRAGService

- LLM-based confidence scoring on retrieved documents
- Triggers corrective retrieval when confidence < 0.6
- Demonstrates measurable answer quality improvement over baseline RAG

---

## 🛠️ Tech Stack

| Layer             | Technology                      |
| ----------------- | ------------------------------- |
| Web Crawling      | Playwright (async)              |
| Embeddings        | OpenAI `text-embedding-3-large` |
| Vector DB         | Qdrant (cloud)                  |
| LLM               | OpenAI GPT-4o-mini              |
| RAG Framework     | LangChain LCEL                  |
| Token Counting    | tiktoken                        |
| Package Manager   | uv                              |
| Config Management | `.env` + `config.py`            |

---
