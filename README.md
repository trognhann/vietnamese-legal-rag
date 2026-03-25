# Vietnamese Legal RAG Q&A System

An enterprise-grade Retrieval-Augmented Generation (RAG) system specifically engineered for high-precision querying of Vietnamese Legal Documents. This project bridges the gap between complex legal terminology and AI-driven insights by implementing advanced retrieval strategies, local LLM execution, and strict safety guardrails.

## 📁 Project Structure

This repository is organized into professional, decoupled modules to ensure maintainability, testability, and ease of updates.

```text
vietnamese-legal-rag/
│
├── .agents/skills/          # Agent instructions for automated AI development
├── data/                    # Local storage for data pipelines
│   ├── chroma_db/           # Persistent vector database storage (Chroma)
│   ├── processed/           # Processed and chunked legal textual data
│   └── raw/                 # Raw PDF and web scrape documents
│
├── docker/                  # Dockerfiles and deployment configurations
│
├── logs/                    # Execution and application logs
│
├── notebooks/               # Jupyter notebooks for experiments and data exploration
│
├── src/                     # Core application source code
│   ├── api/                 # FastAPI backend entrypoints and routes
│   ├── core/                # Core settings, configurations, and environment variables
│   ├── evaluation/          # RAGAS metrics evaluation scripts and tests
│   ├── generation/          # LLM prompt templates and output generation chains
│   ├── ingestion/           # Data loading, PDF parsing, and document chunking
│   ├── model/               # Initialization for LLM (Ollama) and Embedding models (BGE-M3)
│   ├── retrieval/           # Hybrid search logic (Chroma + BM25) and retrieval pipelines
│   ├── ui/                  # Streamlit frontend application code
│   └── utils/               # Helper functions and shared utilities
│
├── tests/                   # Unit and integration tests (pytest)
│
├── .env.example             # Example environment variables definition
├── README.md                # Project documentation (this file)
└── requirements.txt         # Python project dependencies
```

## 🚀 Key Technologies

### Vectorization & Retrieval
- **LangChain:** Core orchestration framework.
- **ChromaDB:** Lightning-fast local persistent vector search.
- **BGE-M3 embeddings:** Multilingual embeddings heavily optimized for Vietnamese semantics.
- **BM25 Search:** Hybrid retrieval to complement semantic weakness.

### LLM Inference
- **Ollama:** Private & localized LLM execution.
- Models targeted: `Llama 3.1 8B`, `Gemma2 9B`. Cloud alternatives for Version 2: Grok API, OpenAI.

### Backend & UI
- **FastAPI:** High-performance, async REST API for querying endpoints.
- **Streamlit:** Interactive Chat UI interface for direct interactions.
- **Docker:** Consistent containerization for deployability (Streamlit Cloud, Render.com).

### Quality Assurance
- **RAGAS:** State-of-the-art evaluation pipeline for RAG systems (Targeting >92% faithfulness).
- **Safety Guardrails:** Input and Output filtering to guarantee factual outputs.
