# App Directory Documentation

This document provides a detailed overview of the `app/` directory in the AIstudyguide project — a FastAPI-based backend that generates structured study guides by querying multiple AI providers, aggregating responses, and structuring them into organized study materials.

---

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [What It Does](#what-it-does)
3. [How It Works](#how-it-works)
4. [Component Details](#component-details)
5. [Data Flow Diagram](#data-flow-diagram)
6. [Database Schema](#database-schema)
7. [Environment Configuration](#environment-configuration)
8. [Technologies Used](#technologies-used)

---

## Directory Structure

```
app/
├── __init__.py
├── main.py                    # FastAPI application entry point
├── database.py                # PostgreSQL connection pooling
├── schemas.py                 # Pydantic data validation models
├── pipeline/                  # AI processing pipeline
│   ├── __init__.py
│   ├── orchestrator.py        # Pipeline coordinator
│   ├── call_ai.py             # Async AI provider dispatch
│   ├── connect_ai.py          # Individual AI provider connectors
│   └── cleaner.py             # Text cleaning & structuring
└── routers/                   # API endpoint groups
    ├── __init__.py
    ├── auth.py                # Authentication (signup/login)
    ├── chats.py               # Chat/Q&A management
    ├── subjects.py            # Subject CRUD
    ├── sessions.py            # Session management
    ├── resource.py            # Resource upload (PDF, URL, notes)
    └── pipeline_router.py     # Pipeline execution endpoint
```

---

## What It Does

The `app/` directory contains the entire backend application, which provides the following capabilities:

| Feature | Description |
|---------|-------------|
| **AI Study Guide Generation** | Takes a user prompt, queries multiple AI providers (OpenAI, Gemini, DeepSeek) concurrently, and produces a structured study guide with sections, overview, prerequisites, and tips. |
| **User Authentication** | Handles user signup and login with bcrypt password hashing. |
| **Subject Management** | Allows users to organize study materials under subjects. |
| **Session Management** | Supports study sessions within subjects for focused learning. |
| **Chat/Q&A** | Provides a question-answer interface within sessions. |
| **Resource Upload** | Accepts PDFs (with text extraction), URLs, and plain-text notes as study resources. |
| **Pipeline Execution** | Orchestrates the full AI query, aggregation, cleaning, and storage pipeline. |

---

## How It Works

### Application Startup

1. `main.py` initializes the FastAPI app and registers all routers.
2. On startup, it tests the PostgreSQL connection from the connection pool.
3. On shutdown, it closes all database connections.

### Request Lifecycle

1. **Incoming Request** hits a FastAPI router endpoint.
2. **Dependency Injection** provides a database connection via `get_db()`.
3. **Pydantic Validation** (via `schemas.py`) validates request body data.
4. **Business Logic** executes in the router or pipeline.
5. **Database Operations** persist results via connection pool.
6. **Response** is returned as JSON.

### Pipeline Execution (Core Feature)

When a user submits a study prompt via `POST /pipeline/run`:

1. **Job Creation** — A new job record is created in `pipeline.jobs` with `status=running`.
2. **Concurrent AI Calls** — `call_ai.py` dispatches async requests to all configured AI providers using `asyncio.gather()`.
3. **Response Collection** — Each provider connector (`connect_ai.py`) handles API-specific request/response formats and extracts text.
4. **Provider Output Storage** — Raw responses are saved to `pipeline.provider_outputs` with metadata (tokens, latency, model).
5. **Cleaning & Structuring** — `cleaner.py` normalizes whitespace, removes special characters, and organizes outputs into sections.
6. **Guide Storage** — The structured guide is persisted to `pipeline.guides` as JSON.
7. **Job Completion** — Job status is updated to `done` with a reference to the generated guide.

---

## Component Details

### `main.py` — Application Entry Point

- Initializes the FastAPI application instance
- Registers routers: `auth`, `chats`, `resource`, `subjects`, `sessions`, `pipeline`
- Implements lifecycle events (startup/shutdown) for database pool management
- Loads environment variables via `python-dotenv`

### `database.py` — Database Layer

- Creates a `SimpleConnectionPool` (1–10 connections) for PostgreSQL
- Provides `get_db()` generator for FastAPI dependency injection
- Ensures connections are returned to pool after each request

### `schemas.py` — Data Models

**Authentication:**
- `UserCreate` — name, email (validated), password
- `UserLogin` — email, password

**Application:**
- `ChatCreate` — session_id, question
- `SubjectCreate` — user_id, subject_name
- `SessionCreate` — subject_id, title

**Pipeline:**
- `JobCreate` — prompt, user_id
- `JobResponse` — job_id, user_id, prompt, status
- `GuideSection` — title, content
- `GuideResponse` — guide_id, job_id, overview, sections[], estimated_time_hours, prerequisites[], extra_tips[], sources[], summary

### `routers/auth.py` — Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/signup` | POST | Creates user with bcrypt-hashed password |
| `/login` | POST | Verifies credentials, returns user_id |

### `routers/chats.py` — Chat Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/submit-prompt` | POST | Submits a question, receives AI answer |
| `/my-chats/{session_id}` | GET | Retrieves all Q&A pairs for a session |

### `routers/subjects.py` — Subject Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/create-subject` | POST | Creates a new subject for a user |
| `/my-subjects/{user_id}` | GET | Lists all subjects for a user |

### `routers/sessions.py` — Session Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/create-session` | POST | Creates a session under a subject |
| `/my-sessions/{subject_id}` | GET | Lists all sessions for a subject |

### `routers/resource.py` — Resource Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/add-resource` | POST | Uploads PDF (extracts text), URL, or plain-text note |

Supports three source types:
- **PDF**: Saves to `uploads/`, extracts text via PyPDF2
- **URL**: Fetches content via HTTP
- **Note**: Stores raw text directly

### `routers/pipeline_router.py` — Pipeline Endpoint

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/pipeline/run` | POST | Executes the full study guide generation pipeline |

### `pipeline/orchestrator.py` — Pipeline Coordinator

Coordinates the entire generation workflow:
1. Creates a job tracking record
2. Invokes AI providers concurrently
3. Stores individual provider outputs
4. Runs the cleaner/structurer
5. Persists the final guide
6. Updates job status

### `pipeline/call_ai.py` — Provider Dispatch

- Checks which providers have API keys configured
- Calls all available providers concurrently via `asyncio.gather()`
- Normalizes responses into a consistent format:
  ```python
  {
      "provider": "openai|gemini|deepseek",
      "model": "model_name",
      "output_text": "extracted text",
      "raw": { ... },
      "error": None
  }
  ```

### `pipeline/connect_ai.py` — AI Connectors

| Provider | Model | Endpoint |
|----------|-------|----------|
| OpenAI | gpt-4 | `api.openai.com/v1/chat/completions` |
| Gemini | gemini-2.5-pro | `generativelanguage.googleapis.com/v1beta/...` |
| DeepSeek | deepseek-chat | `api.deepseek.com/v1/chat/completions` |

Each connector:
- Uses `httpx.AsyncClient` for non-blocking HTTP calls
- Has mock fallback responses for development without API keys
- Includes `extract_text()` to handle provider-specific response formats

### `pipeline/cleaner.py` — Text Processing

Performs two main operations:

1. **Cleaning**: Normalizes whitespace, strips special characters, extracts text from JSON responses
2. **Structuring**: Organizes cleaned outputs into:
   ```python
   {
       "overview": "Summary from first provider...",
       "sections": [{"title": "...", "content": "..."}],
       "prerequisites": [],
       "extra_tips": [],
       "sources": []
   }
   ```

---

## Data Flow Diagram

```
                            ┌─────────────────────────────┐
                            │         User/Client         │
                            └─────────────┬───────────────┘
                                          │
                              POST /pipeline/run
                              { prompt, user_id }
                                          │
                                          ▼
                            ┌─────────────────────────────┐
                            │     pipeline_router.py      │
                            │   (Validates input via      │
                            │    Pydantic schemas)        │
                            └─────────────┬───────────────┘
                                          │
                                          ▼
                            ┌─────────────────────────────┐
                            │      orchestrator.py        │
                            │   (Pipeline Coordinator)    │
                            └─────────────┬───────────────┘
                                          │
                     ┌────────────────────┼────────────────────┐
                     │                    │                    │
          ┌──────────▼──────┐  ┌──────────▼──────┐  ┌──────────▼──────┐
          │  Create Job     │  │   call_ai.py    │  │                 │
          │  (pipeline.jobs │  │  (Async Dispatch│  │                 │
          │   status=running│  │   to providers) │  │                 │
          └────────┬────────┘  └────────┬────────┘  │                 │
                   │                    │            │                 │
                   ▼                    ▼            │                 │
          ┌─────────────┐    ┌────────────────────┐ │                 │
          │  PostgreSQL  │    │   connect_ai.py   │ │                 │
          │  (Job Record)│    │                   │ │                 │
          └─────────────┘    └────────┬───────────┘ │                 │
                                      │             │                 │
                   ┌──────────────────┼─────────────┘                 │
                   │                  │                                │
        ┌──────────▼──┐  ┌───────────▼───┐  ┌────────────────────┐   │
        │   OpenAI    │  │    Gemini     │  │     DeepSeek       │   │
        │   (GPT-4)   │  │(gemini-2.5-pro│  │  (deepseek-chat)   │   │
        └──────┬──────┘  └──────┬────────┘  └────────┬───────────┘   │
               │                │                     │               │
               └────────────────┼─────────────────────┘               │
                                │                                     │
                      ┌─────────▼─────────┐                           │
                      │  Aggregated Raw   │                           │
                      │    Responses      │                           │
                      └─────────┬─────────┘                           │
                                │                                     │
                                ▼                                     │
                      ┌─────────────────────┐                         │
                      │  Save Provider      │                         │
                      │  Outputs to DB      │                         │
                      │  (provider_outputs) │                         │
                      └─────────┬───────────┘                         │
                                │                                     │
                                ▼                                     │
                      ┌─────────────────────┐                         │
                      │    cleaner.py       │                         │
                      │  - Extract text     │                         │
                      │  - Normalize        │                         │
                      │  - Structure into   │                         │
                      │    sections         │                         │
                      └─────────┬───────────┘                         │
                                │                                     │
                                ▼                                     │
                      ┌─────────────────────┐                         │
                      │  Save Structured    │◄────────────────────────┘
                      │  Guide to DB        │
                      │  (pipeline.guides)  │
                      └─────────┬───────────┘
                                │
                                ▼
                      ┌─────────────────────┐
                      │  Update Job Status  │
                      │  (status = done)    │
                      └─────────┬───────────┘
                                │
                                ▼
                      ┌─────────────────────┐
                      │   Return Response   │
                      │  { guide, outputs } │
                      └─────────────────────┘
```

### Simplified Flow

```
User Prompt ──► Router ──► Orchestrator ──► AI Providers (concurrent)
                                               │
                                               ▼
                                          Raw Responses
                                               │
                                               ▼
                                          Cleaner/Structurer
                                               │
                                               ▼
                                          Structured Guide ──► Database ──► User Response
```

### Supporting Features Data Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Signup/ │────►│ Subjects │────►│ Sessions │────►│  Chats/  │
│  Login   │     │          │     │          │     │ Resources│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
│  │  users  │ │ subjects │ │ sessions │ │ chats/resources│  │
│  └─────────┘ └──────────┘ └──────────┘ └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Schema: `studyguide`

| Table | Columns | Purpose |
|-------|---------|---------|
| `users` | id, name, email, password_hash, created_at | User accounts |
| `subjects` | id, user_id, subject_name, created_at | Study subjects |
| `sessions` | id, subject_id, title, created_at | Study sessions |
| `chats` | id, session_id, question, answer, created_at | Q&A records |
| `resources` | id, user_id, subject_id, title, source_type, file_path, url, raw_text, created_at | Uploaded materials |

### Schema: `pipeline`

| Table | Columns | Purpose |
|-------|---------|---------|
| `jobs` | id, user_id, session_id, prompt, status, result_guide_id, error, created_at, updated_at | Pipeline job tracking |
| `provider_outputs` | id, job_id, provider, model, output_json, output_text, tokens_used, latency_ms, error | Individual AI responses |
| `guides` | id, job_id, user_id, session_id, guide_json, summary, created_at | Generated study guides |

---

## Environment Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_HOST` | Yes | — | PostgreSQL host |
| `DB_NAME` | Yes | — | Database name |
| `DB_USER` | Yes | — | Database username |
| `DB_PASSWORD` | Yes | — | Database password |
| `DB_PORT` | No | 5432 | Database port |
| `OPENAI_API` | No | — | OpenAI API key (mock used if absent) |
| `GEMINI_API` | No | — | Gemini API key (mock used if absent) |
| `DEEPSEEK_API` | No | — | DeepSeek API key (mock used if absent) |

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Async web framework |
| **Pydantic v2** | Request/response validation |
| **psycopg2** | PostgreSQL driver with connection pooling |
| **httpx** | Async HTTP client for AI provider APIs |
| **PyPDF2** | PDF text extraction |
| **passlib + bcrypt** | Password hashing |
| **asyncio** | Concurrent AI provider calls |
| **python-dotenv** | Environment variable management |

---

## Design Patterns

- **Async/Await**: All AI calls run concurrently, reducing total latency.
- **Connection Pooling**: Efficient database resource usage with automatic cleanup.
- **Dependency Injection**: FastAPI's `Depends()` provides database connections to routes.
- **Separation of Concerns**: Routers handle HTTP, pipeline handles business logic, connectors handle external APIs.
- **Graceful Degradation**: Pipeline continues even if individual AI providers fail; mock responses available when API keys are missing.
- **Consistent Error Handling**: Try-except blocks with rollback in all database operations.
