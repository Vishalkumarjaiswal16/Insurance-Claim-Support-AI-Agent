# Insurance Claim Support AI Agent

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136.1-00a393.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.56.0-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-assisted claims intake and recommendation workspace for insurance support teams. The project combines a FastAPI backend, a Streamlit workbench, a local SQLite data store, Chroma-backed knowledge retrieval, and LangGraph/LangMem-powered claim recommendation flows.

The system is built around a human-in-the-loop model: AI generates draft recommendations and supporting context, while an adjuster reviews, edits, approves, or discards the result.

## What it does

- Register a new insurance claim from the dashboard or API.
- Auto-generate a draft recommendation in the background when a claim is created.
- Manually re-run draft generation for an existing claim.
- Ground recommendations with knowledge base documents stored in `knowledge_base/`.
- Store and search customer claim history with semantic memory.
- Review tool calls, knowledge hits, and memory hits used to produce a draft.

## Architecture

```text
Streamlit dashboard (app.py)
        |
        v
FastAPI application (main.py / customer_support_agent.api)
        |
        +-- SQLite repositories for customers, tickets, drafts
        +-- Draft service + support copilot
        +-- Chroma knowledge retrieval
        +-- LangMem semantic memory
        +-- LLM/tool integrations
```

## Tech stack

| Area | Technology |
| --- | --- |
| Language | Python 3.12+ |
| API | FastAPI, Uvicorn |
| Dashboard | Streamlit |
| Agent runtime | LangGraph, LangChain |
| LLM provider | Groq |
| Embeddings | Google Gemini embeddings |
| Knowledge retrieval | ChromaDB |
| Memory | LangMem |
| Relational storage | SQLite |
| Settings | pydantic-settings |
| Package manager | uv |
| Tests / CI | pytest, GitHub Actions |

## Repository layout

```text
customer_support_agent/   FastAPI app, services, repositories, integrations
knowledge_base/           Local markdown knowledge sources for ingestion
data/                     SQLite DB and local vector stores
docs/                     Deployment and supporting docs
tests/                    Test suite
app.py                    Streamlit dashboard
main.py                   FastAPI entry point
```

## Prerequisites

- Python 3.12+
- `uv` installed (`pip install uv`)
- A Groq API key for draft generation
- A Google API key for embeddings and retrieval

## Environment setup

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key

GROQ_MODEL=llama-3.1-8b-instant
LLM_TEMPERATURE=0.2

API_HOST=0.0.0.0
API_PORT=8000

# Optional overrides
API_BASE_URL=http://localhost:8000
DASHBOARD_API_URL=http://localhost:8000
ENABLE_LOCAL_EMBEDDINGS=false
```

Important paths default to local workspace directories:

- `data/support.db`
- `data/chroma_rag`
- `data/chroma_mem0`
- `knowledge_base`

## Install dependencies

API only:

```bash
uv sync
```

API + Streamlit dashboard:

```bash
uv sync --extra dashboard
```

## Run locally

Start the API:

```bash
uv run python main.py
```

Available at:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`

Start the Streamlit dashboard in a second terminal:

```bash
uv run --extra dashboard streamlit run app.py
```

Dashboard URL:

- `http://localhost:8501`

## Knowledge base ingestion

The recommendation pipeline can ingest markdown files from `knowledge_base/` into the local Chroma knowledge store.

You can trigger ingestion either from the dashboard sidebar or through the API:

```bash
curl -X POST "http://localhost:8000/api/knowledge/ingest" -H "Content-Type: application/json" -d '{"clear_existing": false}'
```

## Main API endpoints

- `GET /health` - basic health check
- `POST /api/tickets` - create a claim/ticket, with optional background draft generation
- `GET /api/tickets` - list claims
- `GET /api/tickets/{ticket_id}` - fetch a single claim
- `POST /api/tickets/{ticket_id}/generate-draft` - generate a draft on demand
- `GET /api/tickets/{ticket_id}/drafts/latest` - fetch the most recent draft for a claim
- `PATCH /api/drafts/{draft_id}` - edit, accept, or discard a draft
- `POST /api/knowledge/ingest` - ingest knowledge base files into Chroma
- `GET /api/customers/{customer_id}/memories` - list stored customer memories
- `GET /api/customers/{customer_id}/memory-search` - search customer memory semantically

## Dashboard workflow

The Streamlit workbench supports the full operator flow:

- Register a claim with claimant details, policy number, loss location, and FNOL narrative.
- Auto-generate or manually generate a recommendation.
- Review recommendation context, including knowledge hits, memory hits, and tool calls.
- Approve or discard the recommendation.
- Probe prior claim history for the selected customer.

## Docker

The repo includes both a `Dockerfile` and `docker-compose.yml`.

Start both the API and dashboard with Docker Compose:

```bash
docker compose up -d --build
```

Useful URLs after startup:

- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:8501`

Notes:

- The `api` and `dashboard` services both read from `.env`.
- `./data` and `./knowledge_base` are mounted into the containers.
- The plain `Dockerfile` defaults to starting the API service.

## Testing

Run the test suite with:

```bash
uv run --with pytest pytest -q
```

## CI/CD

GitHub Actions is configured in `.github/workflows/ci.yml` to run tests on pull requests and non-`main` pushes.

There is also an EC2 deployment guide in [docs/EC2_deployment_flow.md](docs/EC2_deployment_flow.md) for a simple SSH + Docker Compose deployment flow.

## Notes

- Claim recommendations depend on configured external model providers.
- Data is stored locally by default, which makes the project easy to run for development and demos.
- Accepting a draft marks the related ticket as resolved and attempts to save the approved resolution into semantic memory.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
