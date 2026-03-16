# SecureRelay Web

[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED?logo=docker&logoColor=white)](docker-compose.yml)

SecureRelay is a local privacy gateway for LLM-assisted security workflows. It detects sensitive entities, enforces a human review checkpoint, anonymizes approved data, sends only sanitized prompts to the LLM, and restores readable responses locally.

## Core Workflow

1. Analyst starts a session.
2. Prompt is analyzed by a hybrid NER pipeline (regex + GLiNER).
3. HITL sidebar lets the analyst review, remove, edit, or add entities.
4. Approved entities are tokenized and stored in an encrypted SQLCipher vault.
5. Sanitized prompt is streamed to the configured LLM provider.
6. Streamed response is restored locally using vault mappings.
7. Audit events are written to JSONL.

## Features

- Mandatory HITL checkpoint before sending prompts
- Hybrid NER: deterministic regex plus GLiNER model inference
- SQLCipher-backed encrypted token vault
- SSE streaming response pipeline
- Audit export per session (JSONL)
- Session TTL and startup cleanup for expired tokens
- Provider abstraction with support for:
  - Groq
  - OpenRouter
  - Anthropic
  - Ollama (OpenAI-compatible local endpoint)

## Project Structure

- backend: FastAPI app, NER pipeline, anonymizer, providers, and tests
- frontend: React + Vite + Tailwind UI for chat, HITL review, and vault inspection
- docker-compose.yml: local/dev stack (frontend on 3000, backend on 8000)
- docker-compose.prod.yml: production-style stack (frontend on 80, backend on 8000)

## API Overview

Base path: /api

- GET /api/health
- POST /api/session/new
- DELETE /api/session/{session_id}
- POST /api/analyze
- POST /api/send (SSE: token, done, error, warning)
- GET /api/vault/{session_id}
- GET /api/audit/{session_id}/export

## Environment Configuration

Copy and edit the example file:

```bash
cp .env.example .env
```

Required variables in .env:

- API_KEY: provider API key (use a placeholder for Ollama)
- VAULT_PASSWORD: strong random secret, minimum 16 characters
- PROVIDER_NAME: groq | openrouter | anthropic | ollama
- PROVIDER_MODEL: provider model name

Compose maps these into backend settings (SECURERELAY_* variables).

## Quick Start (Docker)

```bash
git clone https://github.com/0xPwn3z/nullsend.git
cd nullsend
cp .env.example .env
# edit .env (API_KEY, VAULT_PASSWORD, provider/model)
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

Stop:

```bash
docker compose down
```

## Production Compose

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Default exposed ports:

- 80 -> frontend (nginx)
- 8000 -> backend

Persistent data in production compose:

- Host path ~/.securerelay mounted to /data

## Local Development

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Run backend tests:

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend build/lint:

```bash
cd frontend
npm run build
npm run lint
```

## Security Notes

- Vault password is validated at startup and weak defaults are rejected.
- Raw sensitive values are stored only in encrypted vault records.
- Only anonymized prompt text is sent to external LLM APIs.
- CORS defaults to localhost:3000.
- Backend container runs as a non-root user.

## Known Operational Considerations

- Backend image pre-downloads GLiNER model artifacts during build for offline runtime inference.
- The /api/send endpoint estimates token usage from word counts for streaming responses when provider usage metadata is unavailable.

## License

MIT
