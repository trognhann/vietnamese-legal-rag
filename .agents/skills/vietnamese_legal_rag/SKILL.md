---
name: Vietnamese Legal RAG Development
description: Guidelines and instructions for building and maintaining the Vietnamese Legal RAG Q&A System.
---

# Vietnamese Legal RAG Q&A System

This skill provides the comprehensive guide, architectural decisions, and tasks for developing the production-ready RAG Q&A system for Vietnamese legal documents.

## Project Overview
**Goal:** Develop a highly accurate, production-ready document chatbot for querying Vietnamese law using hybrid search, vector embeddings, and LLMs.
**Key Features:** Hybrid Search (BM25 + Vector), Safety Guardrails, RAGAS evaluation pipeline (targeting >92% faithfulness), Docker containerization, and an interactive chatbot UI.

## Tech Stack (2026 Recommended)
To optimize for cost and performance, the following stack is used:

- **Framework:** [LangChain](https://python.langchain.com/) (Chosen for easy scaling and large community support)
- **Vector Database:** [Chroma](https://trychroma.com/) (Local, fast, and easy to persist)
- **Embedding Models:** `BGE-M3` (Best for Vietnamese based on 2026 benchmarks) OR `nomic-embed-text` (Lightweight alternative).
- **LLM Engine:**
  - **Version 1 (Local/Private):** Ollama running `Llama 3.1 8B` or `Gemma2 9B` for a fully local pipeline.
  - **Version 2 (Cloud APIs):** Grok API or OpenAI for performance comparison and scalability.
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/)
- **UI:** Streamlit (For rapid prototyping and demo)
- **Advanced RAG Features:** Hybrid Search (BM25 + Chroma), Guardrails for response safety, RAGAS for evaluation.
- **Deployment:** Dockerized application deployed on Render.com or Streamlit Community Cloud (Free tiers).

## Development Versions

### Version 1: Full Local Pipeline (CV/Demo Focus)
- Uses Ollama for local LLM inference.
- Ensures absolute data privacy (no data leaves the local environment).
- Great for local demonstrations.

### Version 2: Cloud API Integration (Performance Focus)
- Swaps out local Ollama with Grok API or OpenAI models (e.g., GPT-4o-mini).
- Used to benchmark response quality and latency against the local model.

## Implementation Steps

1. **Document Ingestion & Preprocessing:**
   - Parse PDFs and Web data containing Vietnamese legal text.
   - Chunking strategy configured for legal clauses.
2. **Indexing (Hybrid Search):**
   - Embed documents using BGE-M3 and store in Chroma.
   - Setup BM25 index for keyword-based search to complement semantic retrieval.
3. **Retrieval & Generation:**
   - Setup LangChain retrieval pipelines combining BM25 and Chroma results.
   - Build prompts optimized for legal context in Vietnamese.
4. **Evaluation (RAGAS):**
   - Create a test set of legal questions.
   - Run RAGAS metrics (Faithfulness, Answer Relevance, Context Precision/Recall). Target metric: >92% faithfulness.
5. **Safety Guardrails:**
   - Implement input/output validation to prevent hallucinations or illegal advice generation.
6. **API & UI Development:**
   - Expose endpoints via FastAPI.
   - Consume endpoints using a Streamlit frontend.
7. **Containerization & Deployment:**
   - Write `Dockerfile` and `docker-compose.yml`.
   - Deploy to target platforms.
   
## Commands and Workflows

*When executing tasks in this repository, always align with the exact tech stack versions and instructions above.*
