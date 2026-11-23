# OmniTest

> Curriculum-grounded GED & Digital SAT preparation backend built with FastAPI, async PostgreSQL (`pgvector`), Google Gemini, and FastMCP.

<p>
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" height="20" style="height:20px; width:auto; max-width:90px; display:inline-block; vertical-align:middle; margin-right:4px;" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/FastAPI-0.165+-009688.svg" height="20" style="height:20px; width:auto; max-width:110px; display:inline-block; vertical-align:middle; margin-right:4px;" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-16_pgvector-336791.svg" height="20" style="height:20px; width:auto; max-width:150px; display:inline-block; vertical-align:middle; margin-right:4px;" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/License-AGPL--3.0-blue.svg" height="20" style="height:20px; width:auto; max-width:120px; display:inline-block; vertical-align:middle;" alt="License: AGPL-3.0" />
</p>

[Live Web App](https://omnitest-1.onrender.com) · [Live API Docs (Swagger)](https://omnitest-6fed.onrender.com/docs) · [Demo Video](https://drive.google.com/file/d/YOUR_VIDEO_ID/view?usp=sharing) · [GitHub Repository](https://github.com/MushfiqPlabon/OmniTest)

---

## Overview

OmniTest is an exam-preparation API and AI tutoring agent built for **GED and Digital SAT coaching-center instructors** (who manage study guides, quizzes, and essay prompts) and **self-study students** (who practice quizzes, submit essays for rubric grading, and ask curriculum-grounded questions). Subjects, topics, and essay grading rubrics live as structured data in PostgreSQL, so this prototype can later serve additional exam boards and local-language curricula with minimal core changes.

### Key Capabilities
- **Curriculum-Grounded RAG (`pgvector`)**: Splits study guides into `500`-character chunks (`50`-character overlap), embeds them into `384`-dimensional vectors (`gemini-embedding-2`), and queries an HNSW cosine index in PostgreSQL. Explicitly informs users when no matching chunks pass the similarity threshold (`0.70`).
- **Schema-Validated Tool Calling**: Gemini routes requests through Pydantic-validated `ToolSpec` tools (`generate_practice_quiz`, `get_student_progress`, `search_study_materials`) executed inside isolated `AsyncSessionLocal()` database sessions with `user_id` bound in closures.
- **Rubric-Based Essay Grading**: Evaluates student essays against structured 12-point JSON rubrics with prompt-injection delimiting and per-criterion score clamping.
- **Authenticated FastMCP Server**: Exposes 2 tools, 1 resource (`study-material://{material_id}`), and 1 prompt (`ged_sat_tutor_prompt`) over Bearer-guarded HTTP (`/mcp`) and local stdio (`python -m app.mcp.server`).
- **Role-Based Authentication**: Argon2id password hashing (`pwdlib[argon2]`), constant-time verification when accounts do not exist, uniform `401` login responses, `HS256` JWTs (`60`-minute default expiry), and DB-backed `student` vs. `admin` role checks.

---

## Architecture & Request Flow

```mermaid
flowchart TD
    subgraph Clients["Clients"]
        UI["Web Frontend (frontend branch)"]
        MCPClient["MCP Client (IDE / CLI Agent)"]
    end

    subgraph Gateway["FastAPI Gateway (:8000)"]
        API["REST API (/api/v1/*)"]
        MCP_HTTP["Bearer-Protected FastMCP (/mcp & stdio)"]
    end

    subgraph Core["Core & Services"]
        DEP["Depends (DB Session, JWT Auth, RBAC)"]
        SVC["Domain Services (Auth, Materials, Quizzes, Essays, Chat)"]
    end

    subgraph Integrations["AI Integrations (app/integrations/)"]
        LLM["Gemini Chat, Tools & Structured JSON (gemini-3.1-flash-lite)"]
        EMBED["Gemini Embeddings (gemini-embedding-2, 384d)"]
    end

    subgraph Storage["PostgreSQL + pgvector"]
        DB[("11 Relational Tables + HNSW Cosine Index")]
    end

    UI -->|HTTP /api/v1| API
    MCPClient -->|Bearer JWT /mcp or stdio| MCP_HTTP
    API --> DEP --> SVC
    MCP_HTTP --> SVC
    SVC --> EMBED
    SVC --> LLM
    LLM --> SVC
    SVC --> DB
```

```mermaid
sequenceDiagram
    autonumber
    actor User as Student / Admin
    participant API as FastAPI (/api/v1)
    participant Svc as Domain Services
    participant DB as PostgreSQL (pgvector)
    participant LLM as Gemini API

    rect rgb(240, 248, 255)
    note over User,LLM: Flow 1: Auth & CRUD (JWT + RBAC)
    User->>API: POST /auth/login or POST /materials (Bearer JWT)
    API->>DB: Verify Argon2id hash / check admin role
    DB-->>API: Validated user
    API-->>User: 200 OK / 201 Created
    end

    rect rgb(255, 250, 240)
    note over User,LLM: Flow 2: RAG Search + Schema-Validated Tool Calling
    User->>API: POST /chat
    API->>DB: pgvector cosine search (<=>) on knowledge_chunks
    DB-->>API: Matched curriculum chunks (or empty context)
    API->>LLM: Prompt + Chunks + ToolSpec declarations
    LLM-->>API: FunctionCall (generate_practice_quiz / progress / search)
    API->>DB: Run validated tool in isolated AsyncSessionLocal
    DB-->>API: Tool result
    API->>LLM: FunctionResponse (role='user')
    LLM-->>API: Final grounded answer
    API-->>User: ChatResponse
    end
```

---

## Project Structure

```text
app/
├── main.py             # FastAPI app, security headers, CORS, /api/v1 & Bearer-guarded /mcp mount
├── filters.py          # fastapi-filter query specs (subject, topic, difficulty, search)
├── core/               # Settings, async DB, BaseRepository, Argon2id/JWT security, URL helper, errors, utils
├── integrations/       # Retry-enabled Gemini client, structured JSON, ToolSpec gateway, 384d embeddings
├── mcp/                # FastMCP server (server.py) + ASGI Bearer auth middleware (auth.py)
└── modules/            # auth, materials, quizzes, essays, chat (controllers/services/repos/schemas/models/deps)
alembic/                # Async Alembic schema migration (0001_initial_schema.py with 11 tables + HNSW index)
scripts/                # Idempotent seeding (seed.py + scripts/data/) and markdown ingestion (ingest.py)
```

All `58` non-`__init__.py` source files across `app/` and `scripts/` are kept concise (`<= 150` lines each) with module and public-function docstrings.

---

## Quickstart

### Prerequisites
- [uv package manager](https://docs.astral.sh/uv/) (Python 3.12+) or Docker & Docker Compose
- PostgreSQL 16 with `pgvector` (included automatically in Docker Compose)
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### 1. Environment Setup
```bash
git clone https://github.com/MushfiqPlabon/OmniTest.git
cd OmniTest
cp .env.example .env
```

Update `.env` with your Gemini API key and a 32+ character `SECRET_KEY`:
```ini
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_API_VERSION=v1
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
SECRET_KEY=change-this-to-a-super-secret-random-key-at-least-32-chars
DATABASE_URL=postgresql+asyncpg://omnitest:devpassword@localhost:5432/omnitest
```

### 2. Run Full Stack with Docker Compose
Starts **PostgreSQL (`pgvector/pgvector:pg16`)** and **FastAPI Backend (`:8000`)**:
```bash
docker compose up --build
```
On boot, the backend runs `alembic upgrade head`, seeds domain data (`python -m scripts.seed`), ingests `data/materials/*.md` (`python -m scripts.ingest`), and starts Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Run Locally (Without Docker)
```bash
# Install dependencies into .venv
uv sync

# Run database migrations, seed starter data, and ingest markdown guides
uv run alembic upgrade head
uv run python -m scripts.seed
uv run python -m scripts.ingest

# Start API & FastMCP backend
uv run uvicorn app.main:app --reload
```

---

## API & MCP Reference

Interactive OpenAPI documentation is served at `/docs` (Swagger UI) and `/redoc` (`29` `/api/v1` operations across `20` versioned endpoints plus `/health`, `40` schemas).

### Authentication
```bash
# Register
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "student@omnitest.com", "password": "StudentPass123!", "full_name": "Rahim Ahmed"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "student@omnitest.com", "password": "StudentPass123!"}'
```

### Study Materials (CRUD & Filtering)
```bash
# List materials with subject filter & keyword search
curl -X GET "http://localhost:8000/api/v1/materials?subject=math&search=slope" \
  -H "Authorization: Bearer <TOKEN>"

# Create material (Admin only)
curl -X POST "http://localhost:8000/api/v1/materials" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "SAT Geometry: Circles",
    "subject": "math",
    "topic": "geometry",
    "difficulty": "medium",
    "content": "Standard circle equation: (x - h)^2 + (y - k)^2 = r^2",
    "source": "Official SAT Study Guide"
  }'
```

### Multi-Turn AI Chat (RAG + Tools) & Student Quiz History
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you generate a 3-question practice quiz on algebra for me?",
    "history": []
  }'

# Fetch current user's quiz attempt history
curl -X GET "http://localhost:8000/api/v1/quizzes/attempts/my" \
  -H "Authorization: Bearer <TOKEN>"
```

### MCP Server (HTTP `/mcp` & stdio)
```bash
# Unauthenticated requests to /mcp return 401
curl -i -X POST "http://localhost:8000/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}'

# Authenticated MCP initialize handshake over HTTP
curl -X POST "http://localhost:8000/mcp" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "cli", "version": "1.0"}
    }
  }'

# Local stdio transport
uv run python -m app.mcp.server
```

---

## Pre-Configured Demo Accounts (`ENABLE_DEMO_ACCOUNTS=true`)

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@omnitest.com` | `AdminPass123!` | Full domain CRUD writes, material upload/ingestion, quiz & prompt creation |
| **Student** | `student@omnitest.com` | `StudentPass123!` | Taking quizzes, submitting essays, RAG chat tutor, `/mcp` Bearer access |

---

## License

Copyright © 2026 **Mushfiqur Rahman Plaban**.

Licensed under the [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE). See [NOTICE](NOTICE) for attribution details; commercial and white-label licensing is available from the author.
