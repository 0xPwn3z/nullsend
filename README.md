# Nullsend

[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED?logo=docker&logoColor=white)](docker-compose.yml)

> **A local privacy gateway for LLM-assisted security workflows.**
> Nullsend intercepts every prompt before it leaves your machine, forces a human review of detected sensitive entities, anonymizes approved data, and restores readable responses locally — so only sanitized text ever reaches an external LLM API.

---

## Why Nullsend?

Security analysts, incident responders, and red teamers increasingly rely on LLMs to accelerate investigations. The problem: pasting raw logs, IPs, hostnames, credentials, or internal identifiers into a cloud model is an unacceptable data-leak risk in most organizations.

Nullsend solves this by acting as a transparent local proxy:

- **Nothing leaves without your approval.** A mandatory Human-in-the-Loop (HITL) sidebar lets you review, edit, add, or remove every detected entity before the prompt is sent.
- **Sensitive data never reaches the wire.** Approved entities are replaced with opaque tokens. The LLM sees only sanitized text.
- **Responses are de-anonymized locally.** Token-to-value mappings are stored in an encrypted vault on your machine and applied to the streamed response before it is displayed.
- **Full audit trail.** Every session event is written to a JSONL audit log that you can export at any time.

---

## How It Works

```
  Your Prompt
      │
      ▼
┌─────────────────────────┐
│   NER Pipeline          │  Hybrid analysis: deterministic regex + GLiNER
│   (regex + GLiNER)      │  detects IPs, hostnames, credentials, PII, etc.
└───────────┬─────────────┘
            │ detected entities
            ▼
┌─────────────────────────┐
│   HITL Sidebar          │  You review, edit, add, or discard entities.
│   (human checkpoint)    │  Nothing proceeds without your explicit approval.
└───────────┬─────────────┘
            │ approved entities
            ▼
┌─────────────────────────┐
│   Anonymizer +          │  Entities are tokenized (e.g. [IP_1]) and stored
│   SQLCipher Vault       │  in an AES-encrypted local vault.
└───────────┬─────────────┘
            │ sanitized prompt
            ▼
┌─────────────────────────┐
│   LLM Provider          │  Groq · OpenRouter · Anthropic · Ollama
│   (SSE streaming)       │  The model never sees the original values.
└───────────┬─────────────┘
            │ tokenized response (SSE stream)
            ▼
┌─────────────────────────┐
│   Local De-anonymizer   │  Vault mappings are applied in-stream.
└───────────┬─────────────┘
            │
            ▼
  Readable Response
```

---

## Features

| Capability | Details |
|---|---|
| **Mandatory HITL checkpoint** | Every prompt is gated behind a human review step — there is no bypass. |
| **Hybrid NER pipeline** | Deterministic regex patterns combined with [GLiNER](https://github.com/urchade/GLiNER) model inference for high-recall entity detection. |
| **Encrypted token vault** | Entity mappings are stored in a SQLCipher-encrypted database. The vault password is validated at startup; weak defaults are rejected. |
| **SSE streaming** | Full server-sent event pipeline from provider to browser. Responses are de-anonymized token-by-token as they stream. |
| **Multi-provider support** | Groq, OpenRouter, Anthropic, and any OpenAI-compatible local endpoint (Ollama). |
| **Per-session audit export** | Session events (analyze, send, restore) are appended to a JSONL log and exportable via API. |
| **Session lifecycle management** | Configurable TTL with automatic cleanup of expired session tokens at startup. |
| **Vault inspection UI** | Dedicated panel to inspect active token–value mappings for the current session. |
| **Non-root container** | Backend container runs as an unprivileged user. GLiNER model artifacts are pre-downloaded at image build time for fully offline runtime inference. |

---

## Tech Stack

**Backend** — Python 3.11+, FastAPI, SQLCipher (via `pysqlcipher3`), GLiNER, SSE via `starlette`

**Frontend** — React 18, Vite, Tailwind CSS, Radix UI, Zustand

**Infrastructure** — Docker Compose (dev + production variants), nginx reverse proxy

---

## Project Structure

```
nullsend/
├── backend/
│   ├── pipeline/        # NER analysis, anonymizer, audit logger
│   ├── providers/       # LLM provider adapters (Anthropic, Groq, OpenRouter, Ollama)
│   ├── routers/         # FastAPI route handlers (analyze, send, vault, audit, session)
│   └── tests/           # pytest integration tests
├── frontend/
│   ├── src/
│   │   ├── api/         # Typed API client functions
│   │   ├── components/  # Chat UI, HITL sidebar, vault panel, status bar
│   │   ├── hooks/       # useSession, useAnalyze, useStream, useVault
│   │   └── store/       # Zustand state slices
│   └── nginx.conf       # Production nginx configuration
├── docker-compose.yml           # Dev stack (frontend :3000, backend :8000)
└── docker-compose.prod.yml      # Production stack (frontend :80, backend :8000)
```

---

## Quick Start (Docker)

**Prerequisites:** Docker and Docker Compose.

```bash
git clone https://github.com/0xPwn3z/nullsend.git
cd nullsend

# 1. Create your environment file
cp .env.example .env

# 2. Edit .env — set your API key, vault password, and provider
#    (see Environment Configuration below)

# 3. Build and start
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API docs | http://localhost:8000/docs |

```bash
# Stop
docker compose down
```

---

## Environment Configuration

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `API_KEY` | Provider API key. Use any placeholder value for Ollama (local only). |
| `VAULT_PASSWORD` | Strong random secret, **minimum 16 characters**. Weak defaults are rejected at startup. |
| `PROVIDER_NAME` | `groq` \| `openrouter` \| `anthropic` \| `ollama` |
| `PROVIDER_MODEL` | Model identifier as required by the chosen provider (e.g. `llama-3.3-70b-versatile`). |

Docker Compose maps these into the backend as `NULLSEND_*` environment variables.

---

## Production Deployment

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

| Port | Service |
|---|---|
| `80` | Frontend (nginx) |
| `8000` | Backend API |

Persistent vault data is stored in `~/.nullsend` on the host, mounted to `/data` inside the container.

---

## Local Development

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Run tests:

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # dev server on :5173, proxying /api to :8000
```

Build and lint:

```bash
npm run build
npm run lint
```

---

## API Reference

All routes are prefixed with `/api`. Interactive docs are available at `http://localhost:8000/docs` when running locally.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/session/new` | Create a new session |
| `DELETE` | `/api/session/{session_id}` | Destroy a session and its vault entries |
| `POST` | `/api/analyze` | Run NER pipeline on a prompt |
| `POST` | `/api/send` | Anonymize, send to LLM, and stream the de-anonymized response (SSE) |
| `GET` | `/api/vault/{session_id}` | List active token–value mappings for a session |
| `GET` | `/api/audit/{session_id}/export` | Export the session audit log as JSONL |

SSE event types emitted by `/api/send`: `token`, `done`, `error`, `warning`.

---

## Security Notes

- Raw sensitive values are **never** logged or transmitted — only their opaque token representations leave the vault.
- The vault password is validated at startup; the server refuses to start with a weak or default password.
- CORS is restricted to `localhost:3000` by default. Adjust `NULLSEND_CORS_ORIGINS` for other deployment scenarios.
- The backend container runs as a non-root user.
- Only anonymized prompt text is sent to external LLM APIs.

---

## License

[MIT](LICENSE)
