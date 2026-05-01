# Insurance Claim Support AI Agent

An AI-assisted claims operations workspace for insurance support teams and adjusters. The project combines a FastAPI backend, a Streamlit workbench, SQLite persistence, Chroma-based retrieval, and LangGraph-powered draft generation to help teams produce grounded claim responses faster while keeping the final decision with a human reviewer.

## Overview

This project is designed for first notice of loss (FNOL) and claim-support workflows. It helps an adjuster or support operator:

- register a new claim
- look up customer and claim history
- retrieve relevant policy and process guidance from a knowledge base
- generate a draft recommendation with traceable context
- approve or discard the draft inside a review flow
- store approved outcomes back into memory for future assistance

The system is intentionally human-in-the-loop. AI generates recommendations, but a licensed adjuster or support professional remains responsible for the final decision.

## Key Capabilities

- FastAPI service with routes for tickets, drafts, knowledge ingestion, memory lookup, and health checks
- Streamlit workbench for claim registration, draft review, and claim-history probing
- SQLite repositories for customers, tickets, and drafts
- ChromaDB-backed retrieval over local markdown and text knowledge documents
- LangMem-based customer and company memory with graceful fallback behavior
- Groq-powered draft generation using LangGraph and tool calling
- Draft context capture, including knowledge hits, memory hits, and tool execution summaries

## Architecture

```text
Streamlit UI (app.py)
        |
        v
FastAPI application (main.py -> app_factory.py)
        |
        +-- Tickets router
        +-- Drafts router
        +-- Knowledge router
        +-- Memory router
        +-- Health router
        |
        v
Service layer
        +-- DraftService
        +-- KnowledgeService
        +-- SupportCopilot
                +-- Groq chat model
                +-- LangGraph agent
                +-- Support tools
                +-- CustomerMemoryStore
                +-- KnowledgeBaseService
        |
        v
Persistence layer
        +-- SQLite (tickets, customers, drafts)
        +-- Chroma RAG store
        +-- LangMem / InMemoryStore-backed memory
```

## Tech Stack

| Area | Technology |
| --- | --- |
| Language | Python 3.12 |
| API | FastAPI, Uvicorn |
| UI | Streamlit |
| Agent runtime | LangGraph, LangChain |
| LLM | Groq |
| Retrieval | ChromaDB |
| Embeddings | Google Gemini embeddings |
| Memory | LangMem with LangGraph `InMemoryStore` |
| Database | SQLite |
| Settings | `pydantic-settings` |
| Package manager | `uv` |
| Testing | `pytest` |

## Repository Layout

```text
.
|-- app.py
|-- main.py
|-- pyproject.toml
|-- customer_support_agent/
|   |-- api/
|   |-- core/
|   |-- integration/
|   |   |-- memory/
|   |   |-- rag/
|   |   `-- tools/
|   |-- repositories/
|   |   `-- sqlite/
|   |-- schemas/
|   `-- services/
|-- knowledge_base/
|-- notebooks/
|-- docs/
`-- tests/
```

## Getting Started

### Prerequisites

- Python 3.12 or later
- `uv`
- A Groq API key for AI draft generation
- A Google API key for Gemini embeddings if you want semantic retrieval and memory indexing

### Install Dependencies

Install the backend dependencies:

```bash
uv sync
```

Install the Streamlit UI dependency as well:

```bash
uv sync --extra dashboard
```

### Configure Environment

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key

GROQ_MODEL=llama-3.1-8b-instant
LLM_TEMPERATURE=0.2

API_HOST=0.0.0.0
API_PORT=8000
```

Important notes:

- `GROQ_API_KEY` is required to generate drafts.
- `GOOGLE_API_KEY` is recommended for Gemini embeddings used by retrieval and semantic memory.
- The RAG layer sets both `GOOGLE_API_KEY` and `GEMINI_API_KEY` internally when possible to stay compatible with dependency differences.

## Running the Application

### 1. Start the API

```bash
uv run python main.py
```

The API will be available at `http://localhost:8000`.

Interactive API docs are available at:

```text
http://localhost:8000/docs
```

### 2. Start the Streamlit Workbench

In a second terminal:

```bash
uv run streamlit run app.py
```

By default, the dashboard talks to `http://localhost:8000`. You can override it with:

```env
API_BASE_URL=http://localhost:8000
```

## Knowledge Base Ingestion

Knowledge documents are read from `knowledge_base/` and indexed into ChromaDB.

You can ingest them from the dashboard sidebar or by calling the API:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/knowledge/ingest" `
  -ContentType "application/json" `
  -Body '{"clear_existing": false}'
```

The ingestion response includes:

- `files_indexed`
- `chunks_indexed`
- `collection_count`

## Typical Workflow

1. Start the API and dashboard.
2. Ingest the knowledge base.
3. Register a new claim from the Streamlit workbench.
4. Let the system auto-generate a draft or trigger generation manually.
5. Review the draft, tool output, knowledge hits, and memory hits.
6. Approve or discard the recommendation.
7. On approval, the claim is marked resolved and the accepted resolution is stored as memory.

## API Summary

### Health

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service health check |

### Tickets

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/tickets` | Create a ticket and optionally queue background draft generation |
| `GET` | `/api/tickets` | List tickets |
| `GET` | `/api/tickets/{ticket_id}` | Fetch a ticket |
| `POST` | `/api/tickets/{ticket_id}/generate-draft` | Generate and store a draft immediately |

### Drafts

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/tickets/{ticket_id}/drafts/latest` | Get the latest draft for a ticket |
| `PATCH` | `/api/drafts/{draft_id}` | Update draft content and/or status |

Draft status values:

- `pending`
- `accepted`
- `discarded`

### Knowledge

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/knowledge/ingest` | Ingest local knowledge documents into Chroma |

### Memory

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/customers/{customer_id}/memories` | List stored customer and company memories |
| `GET` | `/api/customers/{customer_id}/memory-search` | Search memory using a query and limit |

## Example Ticket Payload

```json
{
  "customer_email": "claimant@example.com",
  "customer_name": "Alex Rivera",
  "customer_company": "Acme Fleet",
  "subject": "Rear-end collision claim",
  "description": "Vehicle was struck from behind at a stoplight. Rear bumper damage and towing required.",
  "priority": "high",
  "auto_generate": true
}
```

## Configuration Reference

Core settings are defined in `customer_support_agent/core/settings.py`.

| Variable | Default | Description |
| --- | --- | --- |
| `GROQ_API_KEY` | empty | Required for AI draft generation |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Groq model identifier |
| `LLM_TEMPERATURE` | `0.2` | Draft generation temperature |
| `GOOGLE_API_KEY` | empty | Recommended for Gemini embeddings |
| `GOOGLE_EMBEDDING_MODEL` | `gemini-embedding-001` | Embedding model for retrieval and memory |
| `WORKSPACE_DIR` | auto-detected | Project root used for relative paths |
| `DATA_DIR` | `data` | Root data directory |
| `DB_PATH` | `data/support.db` | SQLite database file |
| `CHROMA_RAG_DIR` | `data/chroma_rag` | Chroma persistence directory for RAG |
| `CHROMA_MEM0_DIR` | `data/chroma_mem0` | Memory-related local data directory |
| `KNOWLEDGE_BASE_DIR` | `knowledge_base` | Source directory for knowledge documents |
| `RAG_CHUNK_SIZE` | `800` | Chunk size for document ingestion |
| `RAG_CHUNK_OVERLAP` | `120` | Chunk overlap for document ingestion |
| `RAG_TOP_K` | `4` | Number of knowledge hits retrieved |
| `MEM0_TOP_K` | `5` | Number of memory hits retrieved |
| `API_HOST` | `0.0.0.0` | API bind host |
| `API_PORT` | `8000` | API bind port |
| `DASHBOARD_API_URL` | derived | API base URL used by the dashboard when not explicitly set |

## Testing

Run the test suite with:

```bash
uv run pytest
```

The current tests cover:

- basic API health
- draft status lifecycle behavior
- LangMem store add/search/list fallback behavior

## Current State

- FastAPI application and routers
- Streamlit operator workbench
- SQLite repositories and schema initialization
- Chroma-based knowledge ingestion and retrieval
- Groq-backed draft generation service
- claim-memory persistence and search
- basic automated tests


## License

This project is licensed under the MIT License. See `LICENSE` for details.
