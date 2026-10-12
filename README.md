# CodePilot AI — Repository-Aware Agentic Software Engineering Copilot

> **Enterprise GenAI Application**
> Built with Python 3.11+ (FastAPI), React 18 (TypeScript), Microsoft Azure AI Foundry / Azure OpenAI, PostgreSQL + pgvector, Redis, Docker, and Monaco Editor.

---

## 🚀 Overview

**CodePilot AI** is an AI-powered software engineering assistant that understands full software repositories. It enables engineers to connect codebases, perform hybrid semantic/symbol RAG searches, execute autonomous multi-step agent tool calls, investigate runtime bugs with patch generation, conduct automated code reviews, generate targeted unit test suites, synthesize technical documentation, and monitor token consumption, latency, and costs in real time.

```
                  ┌─────────────────────────────────────────────────────────┐
                  │      React / TypeScript Frontend (Monaco Editor)        │
                  └────────────────────────────┬────────────────────────────┘
                                               │ REST / SSE
                                               ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │         FastAPI Gateway, Rate Limiter & Auth            │
                  └──────┬─────────────────────┬────────────────────┬───────┘
                         │                     │                    │
                         │ Enqueue Index Job   │ Hybrid RAG         │ Agent Tool
                         │ (Lock + Hash + LPUSH)                    │ Loop (5 Steps)
                         ▼                     ▼                    ▼
              ┌─────────────────────┐  ┌──────────────────┐ ┌──────────────────┐
              │ Redis 7 / 5.0.14    │  │ Hybrid RAG       │ │ Azure OpenAI     │
              │ • Queue (FIFO LPUSH)│  │ Retriever        │ │ GPT-4.1-mini     │
              │ • Mutex Lock (NX EX)│  └─────────┬────────┘ └─────────┬────────┘
              │ • Job Status Hash   │            │                    │
              │ • Distributed Limiter│            └────────────────────┘
              └──────────┬──────────┘
                         │ BRPOP (Job ID)
                         ▼
              ┌──────────────────────────────────────────────┐
              │ Dedicated Background Worker Process          │
              │ (python -m app.worker)                       │
              │ • Heartbeat (codepilot:workers:<id>)         │
              │ • AST Symbol Parsing & Intelligent Chunking  │
              │ • Batch Embeddings (Azure text-embedding-3)  │
              │ • Retry Policy & Exponential Backoff         │
              │ • Atomic Lua Mutex Release                   │
              └──────────┬───────────────────────────────────┘
                         ▼
              ┌──────────────────────────────────┐
              │ PostgreSQL + pgvector / SQLite   │
              └──────────────────────────────────┘
```

---

## ✨ Core Capabilities

1. **Repository Ingestion & AST Symbol Chunking**
   - AST parser for TypeScript, JavaScript, Python, Java, Go, C#, SQL, JSON, YAML, HTML, CSS, and Markdown.
   - Preserves symbol names, types (`function`, `class`, `interface`), file paths, and exact line boundaries.
   - Graph extraction for file dependencies (`File A imports File B`) and caller symbols.

2. **Code-Aware RAG Pipeline**
   - **Hybrid Retrieval**: Combines 1536-dim vector embeddings (`pgvector`) with keyword full-text matching via Reciprocal Rank Fusion (RRF).
   - **Symbol & Graph Reranking**: Expands retrieved context using dependency graphs.
   - **Citations & Deep Linking**: Every response contains clickable citations (`src/auth/AuthProvider.ts:15-32`) that open Monaco Editor and highlight exact line ranges.

3. **Autonomous Agent Workflows**
   - Controlled tool loop (`search_repository`, `get_file`, `get_symbol`, `get_related_files`, `run_static_analysis`, `parse_git_diff`).
   - Loop limits (max 5 steps) and execution timeouts to prevent infinite loops.

4. **Automated Bug Investigator & Diff Proposal**
   - Stack trace parsing, root cause analysis, and proposed patch generation formatted as unified diffs with Approve/Reject controls.

5. **Code Review Agent**
   - Analyzes pull request diffs across Security, Performance, Maintainability, Error Handling, and Type Safety with severity ratings.

6. **Test & Documentation Generators**
   - Unit test generation for Pytest, Vitest, and Jest displayed in Monaco Editor with Copy / Download controls.
   - Architecture, README, and API documentation synthesis.

7. **RAG Evaluation Framework**
   - Measures **Context Precision**, **Context Recall**, **Groundedness**, and **Citation Accuracy** across benchmark developer questions.

8. **Observability & Cost Tracking**
   - Real-time tracking of prompt tokens, completion tokens, query latency (ms), tool calls, and estimated LLM cost in USD for models including `gpt-4.1-mini`.

9. **Security Controls & Defense in Depth**
   - Secret scanner redacting AWS keys, JWTs, DB connection strings, and private keys prior to vector storage or LLM prompts.
   - Prompt injection guard and ZIP traversal defense.

---

## 🛠️ Technology Stack & Dependencies

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Monaco Editor (`@monaco-editor/react`), TanStack Query, Lucide icons, Recharts |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, Pytest |
| **Vector DB & Cache** | PostgreSQL with `pgvector` extension (production) / SQLite with aiosqlite (local dev fallback), Redis |
| **AI / LLM** | Microsoft Azure AI Foundry & Azure OpenAI (`gpt-4.1-mini`), with built-in Mock Provider for offline dev and tests |
| **DevOps** | Docker, Docker Compose, Nginx |

---

## 📋 Prerequisites

Before setting up CodePilot AI, ensure you have:
1. **Python**: 3.11 or newer (Python 3.11, 3.12, 3.13, or 3.14).
2. **Node.js**: v18.0.0 or newer and `npm`.
3. **PowerShell** (Windows) or **Bash** (Linux/macOS).
4. **Git**: Installed and configured.
5. **Azure AI Account** (for live AI mode):
   - Access to **Microsoft Azure AI Foundry** (`https://ai.azure.com`) or **Azure OpenAI Service**.
   - A deployed chat model (e.g., `gpt-4.1-mini`).
   - (Optional for full vector RAG) A deployed embedding model (e.g., `text-embedding-3-small`).

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` in the repository root:

```powershell
Copy-Item .env.example .env
```

### Environment Variables Reference

| Variable | Description | Required For | Example / Default |
|---|---|---|---|
| `LLM_PROVIDER` | AI provider selector (`mock`, `azure`, `openai`) | All | `mock` (dev) / `azure` (production) |
| `EMBEDDING_PROVIDER` | Embedding provider override (`mock`, `azure`) | Optional | `mock` (if only chat model deployed in Azure) |
| `AZURE_OPENAI_ENDPOINT` | Azure AI Foundry Project or Azure OpenAI endpoint URL | Azure Mode | `https://<resource>.services.ai.azure.com/api/projects/<project>` |
| `AZURE_OPENAI_API_KEY` | Azure API Key | Azure Mode | `your-azure-api-key` |
| `AZURE_OPENAI_DEPLOYMENT` | Deployed model name in Azure | Azure Mode | `gpt-4.1-mini` |
| `AZURE_OPENAI_API_VERSION` | Azure API Version | Azure Mode | `2024-08-01-preview` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding model deployment name | Real Azure RAG | `text-embedding-3-small` |
| `DATABASE_URL` | Async database connection string | All | `sqlite+aiosqlite:///./codepilot.db` (local dev) |
| `REDIS_URL` | Redis URL for rate limiting & cache | Production | `redis://localhost:6379/0` |
| `SECRET_KEY` | Secret key for JWT generation | All | Change in production |
| `FERNET_KEY` | Fernet key for credential encryption | All | 32-byte base64 key |

---

## ☁️ Azure AI Foundry Deployment Guide

### Supported Endpoint Types

CodePilot AI automatically detects and supports two distinct Azure endpoint formats:

1. **Microsoft Azure AI Foundry Project Endpoints**:
   - Format: `https://<resource-name>.services.ai.azure.com/api/projects/<project-name>`
   - Endpoint auto-normalization: Trailing `/openai/v1/responses` or `/openai/v1/chat/completions` paths copied directly from the Azure AI Foundry Playground are handled automatically.
   - Request routing: Routes to `/openai/v1/chat/completions` with payload `{"model": "<deployment-name>", ...}`.

2. **Standard Azure OpenAI Service Endpoints**:
   - Format: `https://<resource-name>.openai.azure.com/`
   - Request routing: Routes to `/openai/deployments/<deployment-name>/chat/completions?api-version=<version>`.

### Model Deployment Steps in Azure AI Foundry

1. **Deploying the Chat Model (`gpt-4.1-mini`)**:
   - Navigate to [Microsoft Azure AI Foundry](https://ai.azure.com).
   - Open your Project -> **Deployments** (or **Models + endpoints**).
   - Select **Deploy model** -> Choose **gpt-4.1-mini** (or `gpt-4o-mini`).
   - Deployment Name: Set to `gpt-4.1-mini`.
   - Copy your **Project Endpoint** and **API Key** from the Project Overview or Playground.

2. **Deploying the Embedding Model (`text-embedding-3-small`)** *(Required for live Azure RAG)*:
   - In Azure AI Foundry, select **Deploy model** -> Choose **text-embedding-3-small**.
   - Deployment Name: Set to `text-embedding-3-small`.
   - Dimensionality: 1536 (matches the database schema).
   - *Note*: Chat models like `gpt-4.1-mini` cannot generate vector embeddings. If an embedding model is not yet deployed, set `EMBEDDING_PROVIDER=mock` to use real Azure chat generation alongside local mock embeddings.

---

## 🏃 Starting the Application

### 1. Mock Mode (Local Development & Testing)

Mock mode runs completely offline with deterministic responses, requiring zero cloud credentials:

```powershell
# In .env:
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=mock

# Start Backend
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Start Frontend (in separate terminal)
cd frontend
npm run dev
```

- Frontend URL: `http://localhost:5173`
- Backend API Docs: `http://localhost:8000/docs`
- Demo Login: `developer@codepilot.ai` / `Password123!`

### 2. Azure Mode (Real Cloud Model Inference)

Configure `.env` with your Azure AI Foundry credentials:

```ini
LLM_PROVIDER=azure
EMBEDDING_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project
AZURE_OPENAI_API_KEY=your-actual-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

> **Important (Embedding Space Compatibility)**:
> Vectors generated by the local Mock Embedding Provider (hashlib SHA-256) and vectors generated by real Azure `text-embedding-3-small` reside in completely different vector spaces. When switching an existing repository from mock mode to real Azure embedding mode, the repository must be re-indexed (`POST /api/v1/repositories/{id}/index`) so all chunks reside in the identical 1536-dimensional Azure embedding space.

Start the backend:
```powershell
uvicorn app.main:app --reload --port 8000
```

All Chat, RAG Retrieval, Bug Analysis, Code Review, Agent, and Test Generation requests will now execute against real `gpt-4.1-mini` and `text-embedding-3-small` models in Microsoft Azure AI Foundry.

---

## ⚡ Redis Background Processing & Job Queue Architecture

CodePilot AI implements genuine Redis-backed asynchronous background processing for repository indexing, AST chunking, and batch embedding generation.

### Architecture Highlights

- **Queue Library**: Production async Redis queue built directly on `redis.asyncio` using Redis protocol 2 (compatible across Redis 5.0+, Redis 6, Redis 7, Memurai, and cloud-managed caches like Azure Cache for Redis).
- **Separation of Concerns**: The FastAPI web service accepts index requests, creates persistent tracking records, acquires a distributed deduplication lock, and immediately returns a job ticket (`202 Accepted` / `QUEUED`).
- **Distributed Deduplication**: `codepilot:lock:index:<repository_id>` acquired with atomic `SET NX EX 300` to prevent duplicate concurrent indexing requests from double-submitting. Released atomically via Lua scripts only upon terminal completion or failure.
- **Dedicated Worker CLI**: Standalone background worker process (`python -m app.worker`) that consumes jobs via non-blocking `BRPOP` from `codepilot:queue:indexing`.
- **Worker Heartbeat & Health**: Workers register heartbeats in `codepilot:workers:<worker_id>` with a 15-second TTL, enabling real-time monitoring of active workers in `/api/v1/health`.
- **Bounded Retry Policy**: Transient errors trigger exponential backoff retries (`INDEXING_JOB_MAX_RETRIES=2`) before transitioning to terminal `FAILED`.
- **Credential & Payload Isolation**: Redis stores strictly job identifiers and repository IDs—no source code files, access tokens, or sensitive API keys are ever placed on Redis queues.

### Queue Modes

| `QUEUE_MODE` | Description | Worker Process Required | Behavior when Redis Down |
|---|---|:---:|---|
| `redis` | **Production Mode**: Full Redis queue, distributed lock, worker process | Yes (`python -m app.worker`) | Returns HTTP 503 (`REDIS_UNAVAILABLE`) with clear diagnostic message |
| `background_tasks` | **Local In-Process Fallback**: Executes indexing inside FastAPI event loop | No | Runs locally; clearly documented as single-process dev mode |

---

## 🚦 Distributed Rate Limiting

The application includes distributed rate limiting built on atomic Redis pipelines:
- **Atomic Execution**: Chained `pipe.incr(key)` and `pipe.expire(key, 60)` in an atomic transaction to guarantee race-condition-free counting.
- **Outage Handling**: When Redis is unreachable, the system gracefully falls back to an in-process sliding window and logs an explicit warning without falsely reporting distributed enforcement.
- **Observability**: `RateLimiter.get_status()` exposes `is_distributed` and `mode` ("redis" vs "in_memory_fallback") in system health checks.

---

## 🩺 System Health & Observability Endpoints

### 1. `GET /api/v1/health`
Comprehensive health check reporting database, Redis connection, active workers, queue depth, rate limiter status, and active AI model deployments.

### 2. `GET /api/v1/health/redis`
Dedicated Redis metrics endpoint for load balancers and container orchestrators.

### 3. `GET /api/v1/repositories/{repo_id}/jobs/{job_id}`
Authenticated endpoint returning real-time job status (`queued`, `running`, `completed`, `failed`), execution stage (`PARSING`, `CHUNKING`, `EMBEDDING`, `COMPLETED`), retry count, and timestamps.

---

## 🚀 Local Development Setup (Windows & Docker)

### Option A: Local Windows (PowerShell with Redis or Docker)

1. **Start Redis Server**:
```powershell
# Option 1: Start Redis container via Docker:
docker run -d -p 6379:6379 --name codepilot-redis redis:7-alpine

# Option 2: Run native Windows Redis, Memurai, or WSL Redis:
# redis-server

# Verify Redis is responding:
# redis-cli ping  # Returns PONG
```
> *Tip*: If you prefer not to run Redis during local offline development, set `QUEUE_MODE=background_tasks` in `.env` to execute indexing in-process using FastAPI `BackgroundTasks`.

2. **Start Background Indexing Worker**:
```powershell
# In PowerShell Terminal 2:
cd backend
.\venv\Scripts\python -m app.worker
```

3. **Start FastAPI Backend**:
```powershell
# In PowerShell Terminal 3:
cd backend
.\venv\Scripts\uvicorn app.main:app --reload --port 8000
```

4. **Verify Health Check**:
```powershell
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/redis
```

### Option B: Docker Compose

If Docker is available, start Redis, PostgreSQL with pgvector, backend, and worker together:
```powershell
docker compose up -d
docker compose ps
docker compose logs -f worker
```

---

## 🧪 Running Automated Tests

CodePilot AI includes unit tests, Redis queue tests, live Redis integration tests, and live Azure tests:

### 1. Run All Backend Tests (53 passing, 56 total with live Azure)
```powershell
cd backend
.\venv\Scripts\pytest -v
```

### 2. Run Redis Queue Unit Tests (Mock Mode)
Validates job enqueueing, deduplication locks, status transitions, and rate limiting with mocks:
```powershell
cd backend
.\venv\Scripts\pytest tests/test_redis_queue.py -v
```

### 3. Run Live Redis Integration Tests
Validates real Redis connectivity, atomic concurrency rate limiting, lock deduplication, multi-process worker execution (`python -m app.worker`), and retry backoff against a live Redis instance:
```powershell
cd backend
.\venv\Scripts\pytest tests/test_redis_integration.py -v
```

### 4. Run Live Azure Integration Tests
Executes real network requests against your live Azure AI Foundry deployment (`gpt-4.1-mini` and `text-embedding-3-small`):
```powershell
cd backend
$env:RUN_LIVE_AZURE_TESTS="1"
.\venv\Scripts\pytest tests/test_azure_integration.py -v
$env:RUN_LIVE_AZURE_TESTS="0"
```

### 5. Run Frontend Production Build & Typecheck
```powershell
cd frontend
npm run build
```

---

## 🔧 Troubleshooting Matrix

| Error Code / Symptom | Root Cause | Resolution |
|---|---|---|
| `REDIS_UNAVAILABLE` (503) | `QUEUE_MODE=redis` but Redis server is not running | Start Redis (`redis-server.exe` or `docker compose up -d redis`) or set `QUEUE_MODE=background_tasks` for in-memory dev. |
| `INDEXING_IN_PROGRESS` (409) | Duplicate indexing request while a job is already queued/running | Wait for active job to finish or verify job status via `GET /api/v1/repositories/{id}/jobs/{job_id}`. Deduplication lock has a 300s safety TTL. |
| `RATE_LIMIT_EXCEEDED` (429) | Per-minute request threshold exceeded | Distributed counter enforces 60 req/min. Requests will automatically succeed in the next 60s sliding window. |
| `AI_AUTHENTICATION_ERROR` (401/403) | Invalid `AZURE_OPENAI_API_KEY` or wrong endpoint | Verify the API key in `.env` under Azure AI Foundry Project Overview -> Keys. |
| `AI_DEPLOYMENT_NOT_FOUND` (404) | Deployment name mismatch | Verify `AZURE_OPENAI_DEPLOYMENT` matches the exact deployment name in Azure AI Foundry (e.g. `gpt-4.1-mini`). |
| `EMBEDDING_DEPLOYMENT_MISSING` (400) | No embedding model deployed in Azure Foundry | Deploy `text-embedding-3-small` in Azure Foundry or set `EMBEDDING_PROVIDER=mock` in `.env`. |
| `AI_TIMEOUT` (504) | Network latency or request > 30s | Handled by automatic worker retry policy (`INDEXING_JOB_MAX_RETRIES=2`). Verify network connectivity to Azure endpoint. |

---

## 🧩 Service Dependency Matrix

| Feature | Mock Mode | Azure Mode (`gpt-4.1-mini`) | Requires PostgreSQL + pgvector | Requires Redis |
|---|:---:|:---:|:---:|:---:|
| **Authentication & JWT** | ✅ Yes | ✅ Yes | SQLite (dev) / PG (prod) | Optional (memory fallback) |
| **Repository Ingestion** | ✅ Yes | ✅ Yes | SQLite (dev) / PG (prod) | Not required |
| **Code Search / Chat** | ✅ Deterministic | ✅ Real GPT-4.1-mini | SQLite (dev) / PG (prod) | Optional |
| **Bug Investigator** | ✅ Mock Patch | ✅ Real GPT-4.1-mini Patch | SQLite (dev) / PG (prod) | Optional |
| **Code Review Agent** | ✅ Mock Findings | ✅ Real GPT-4.1-mini Review | SQLite (dev) / PG (prod) | Optional |
| **Test Generation** | ✅ Spec Template | ✅ Real GPT-4.1-mini Tests | SQLite (dev) / PG (prod) | Optional |
| **Documentation Gen** | ✅ Template Doc | ✅ Real GPT-4.1-mini Doc | SQLite (dev) / PG (prod) | Optional |
| **Rate Limiting** | ✅ Local | ✅ Local | Not required | ✅ Recommended |
| **Vector Similarity (RAG)** | ✅ 1536-dim Mock | Requires Embedding Model | ✅ PG with pgvector | Optional |

---

## 🔒 Security Best Practices

1. **Credentials Isolation**: Never commit `.env` or files containing keys. `.gitignore` is preconfigured to exclude all `.env*`, `*.db`, and credentials.
2. **Secret Redaction**: CodePilot AI scans and redacts AWS keys, private certificates, and connection strings prior to AST chunking or sending context to Azure.
3. **No Credential Leakage**: Error messages, exception details, and observability logs sanitize headers to prevent API keys from appearing in frontend responses or log files.
