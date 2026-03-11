# nullsend

[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED?logo=docker&logoColor=white)](docker-compose.yml)
[![Stars](https://img.shields.io/github/stars/0xPwn3z/nullsend?style=social)](https://github.com/0xPwn3z/nullsend)

> **Send nothing. Know everything.** — A local privacy proxy for LLM-assisted pentesting.

---

## What is nullsend?

nullsend is a **local privacy proxy** that sits between you and any LLM provider during a penetration testing engagement.

When you type a prompt, nullsend intercepts it, runs a **hybrid NER pipeline** (Regex + GLiNER) to detect sensitive entities — IP addresses, credentials, hostnames, domain names, person names, paths, and more — then holds everything at a mandatory **Human-in-the-Loop (HITL) checkpoint**. You review, adjust, and approve before a single byte reaches the LLM. The anonymized prompt goes out; the response comes back; nullsend **de-anonymizes it locally** so you read clean output — while raw client data never leaves your machine.

Key guarantees:
- **Automatic detection** of sensitive entities via dual NER engine (fast Regex patterns + deep-learning GLiNER model)
- **AES-256 encrypted vault** (SQLCipher) stores every token↔original mapping for the session
- **Mandatory HITL checkpoint** — no prompt is sent without explicit analyst approval
- **Automatic de-anonymization** of LLM responses, invisibly restoring original values in context

---

## How It Works

```
  Analyst Input
       │
       ▼
  ┌─────────────────────────────────────┐
  │  NER Pipeline                       │
  │  Regex patterns + GLiNER model      │
  │  → detects IPs, creds, hosts, names │
  └────────────────┬────────────────────┘
                   │  detected entities
                   ▼
  ┌─────────────────────────────────────┐
  │  HITL Review (Sidebar)              │
  │  → analyst approves / edits / adds  │
  │  → analyst clicks Approve & Send    │
  └────────────────┬────────────────────┘
                   │  approved entity list
                   ▼
  ┌─────────────────────────────────────┐
  │  Anonymizer                         │
  │  → replaces entities with tokens    │
  │  → stores map in SQLCipher vault    │
  └────────────────┬────────────────────┘
                   │  sanitized prompt
                   ▼
          ┌────────────────┐
          │  LLM Provider  │
          │  (API / local) │
          └───────┬────────┘
                  │  streamed response
                  ▼
  ┌─────────────────────────────────────┐
  │  De-anonymizer                      │
  │  → swaps tokens back to originals   │
  │  → streams clean text to analyst    │
  └─────────────────────────────────────┘
```

---

## Features

| Feature | Details |
|---|---|
| **Offline-first** | NER runs fully local; Ollama supported for fully air-gapped setups |
| **Dual NER engine** | Fast deterministic Regex + GLiNER deep-learning model for high-recall detection |
| **Encrypted token vault** | SQLCipher AES-256; tokens survive the session, originals never persist in plaintext |
| **Mandatory HITL checkpoint** | The analyst is always the final gate — no silent sends, ever |
| **Multi-provider support** | Groq · OpenRouter · Anthropic · Ollama |
| **Docker Compose one-liner** | Full stack (backend + frontend + data volume) with a single command |
| **Dark UI** | React/Vite frontend with Tailwind, built for long sessions |

---

## Quick Start

```bash
git clone https://github.com/0xPwn3z/nullsend.git && cd nullsend
cp .env.example .env
# Edit .env — set your API key and a strong VAULT_PASSWORD
docker compose up
# Open http://localhost:3000
```

### Provider configuration (`.env`)

**Groq** (default)
```env
SECURERELAY_PROVIDER__NAME=groq
SECURERELAY_PROVIDER__MODEL=llama-3.1-8b-instant
SECURERELAY_API_KEY=gsk_...
```

**OpenRouter**
```env
SECURERELAY_PROVIDER__NAME=openrouter
SECURERELAY_PROVIDER__MODEL=meta-llama/llama-3.1-8b-instruct:free
SECURERELAY_API_KEY=sk-or-v1-...
```

**Anthropic**
```env
SECURERELAY_PROVIDER__NAME=anthropic
SECURERELAY_PROVIDER__MODEL=claude-3-5-sonnet-20241022
SECURERELAY_API_KEY=sk-ant-...
```

**Ollama** (fully local)
```env
SECURERELAY_PROVIDER__NAME=ollama
SECURERELAY_PROVIDER__MODEL=qwen2.5:latest
SECURERELAY_API_KEY=not-needed
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser  :3000                                             │
│                                                             │
│  React + Vite + Tailwind                                    │
│  ┌──────────────────────┬──────────────────────────────┐   │
│  │  Conversation Feed   │  HITL Sidebar                │   │
│  │  (Markdown / stream) │  Entity review · Vault view  │   │
│  ├──────────────────────┴──────────────────────────────┤   │
│  │  Prompt Input                                       │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │  REST + SSE
┌───────────────────────────▼─────────────────────────────────┐
│  Backend  :8000                                             │
│                                                             │
│  FastAPI                                                    │
│  ├── /analyze   NER detection (pre-HITL)                   │
│  ├── /send      anonymize → stream → de-anonymize          │
│  ├── /vault     session token viewer                       │
│  └── /audit     append-only JSONL export                   │
│                                                             │
│  Pipeline: Regex NER + GLiNER → Anonymizer → Vault         │
│  Storage:  SQLCipher AES-256 (vault.db) + audit.jsonl      │
└───────────────────────────┬─────────────────────────────────┘
                            │
               ┌────────────▼───────────┐
               │     LLM Provider       │
               │  Groq / OpenRouter /   │
               │  Anthropic / Ollama    │
               └────────────────────────┘
```

### Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| NER | GLiNER (ONNX), custom Regex patterns |
| Vault | SQLCipher (AES-256), sqlcipher3-binary |
| Frontend | React 18, Vite, Tailwind CSS, shadcn/ui |
| Container | Docker Compose v2 |

---

## Security Model

| Concern | Mitigation |
|---|---|
| Data at rest | SQLCipher AES-256 encrypted vault |
| Data in transit to LLM | Only anonymized tokens leave the machine |
| Prompt audit trail | Append-only JSONL with SHA-256 of anonymized prompts |
| API key storage | Environment variables only, never in source |
| SQL injection | All queries use parameterized statements |
| Container security | Backend runs as non-root user |
| CORS | Restricted to localhost origins |
| HITL enforcement | No prompt sent without analyst explicit approval |
| Vault reveal | Original values auto-hide after 5 seconds |

---

## Development

```bash
# Backend
cd backend
pip install -e ".[dev]"
pytest

# Frontend
cd frontend
npm install
npm run dev
```

---

## License

[MIT](LICENSE) — © 2026 0xPwn3z

## The Problem

During pentesting engagements, analysts use LLMs to help draft reports,
analyze findings, and get technical guidance. But client data is covered
by NDAs — IP addresses, hostnames, credentials, and internal references
should **never** leave the engagement environment unreviewed.

SecureRelay sits between the analyst and the LLM. It detects sensitive
entities via NER, lets the analyst review and adjust them (HITL), swaps
them for opaque tokens, sends the sanitized prompt to the LLM, and
de-tokenizes the response locally.

**Raw client data never reaches the LLM.**

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Browser :3000                       │
│  ┌───────────────────────┬──────────────────────────┐    │
│  │  Conversation Feed    │  HITL Sidebar             │   │
│  │  (Markdown rendering) │  (Entity review/approve)  │   │
│  │                       │  (Vault token viewer)      │   │
│  ├───────────────────────┴──────────────────────────┤    │
│  │  Prompt Input                                     │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────┘
                       │  REST + SSE
┌──────────────────────▼───────────────────────────────────┐
│                   Backend :8000                           │
│  FastAPI + Presidio NER + SQLCipher Vault                │
│                                                          │
│  POST /analyze  → detect entities (pre-HITL)             │
│  POST /send     → anonymize → LLM stream → de-anon      │
│  GET  /vault    → view session tokens                    │
│  GET  /audit    → export audit log                       │
└──────────────────────┬───────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  LLM Provider   │
              │  (Groq/OR/      │
              │   Anthropic/    │
              │   Ollama)       │
              └─────────────────┘
```

## How HITL Works

1. Analyst types a prompt
2. Backend runs NER → detects IPs, hosts, creds, paths, etc.
3. Sidebar shows all detected entities (pre-approved)
4. Analyst **removes** entities they don't want anonymized,
   **edits** entity types, or **adds** entities the NER missed
5. Analyst clicks **Approve & Send**
6. Only then is the prompt anonymized and sent to the LLM
7. The analyst is always the final gatekeeper

## Prerequisites

- Docker + Docker Compose v2
- An API key for one of: Groq, OpenRouter, Anthropic, or a local Ollama instance

## Quickstart

```bash
git clone <repo-url> securerelay && cd securerelay
cp .env.example .env
# Edit .env — add your API key and set a vault password
docker compose up
# Open http://localhost:3000
```

## Provider Setup

### Groq (default)

```env
PROVIDER_NAME=groq
PROVIDER_MODEL=llama-3.1-8b-instant
API_KEY=gsk_...
```

### OpenRouter

```env
PROVIDER_NAME=openrouter
PROVIDER_MODEL=meta-llama/llama-3.1-8b-instruct:free
API_KEY=sk-or-v1-...
```

### Anthropic

```env
PROVIDER_NAME=anthropic
PROVIDER_MODEL=claude-3-5-sonnet-20241022
API_KEY=sk-ant-...
```

### Ollama (local)

```env
PROVIDER_NAME=ollama
PROVIDER_MODEL=qwen2.5:latest
API_KEY=not-needed
```

Make sure Ollama is running on the host. The backend connects to
`http://localhost:11434/v1`.

## Security Model

| Concern                | Mitigation                                           |
| ---------------------- | ---------------------------------------------------- |
| Data at rest           | SQLCipher AES-256 encrypted vault                    |
| Data in transit to LLM | Only anonymized tokens leave the machine             |
| Prompt audit trail     | Append-only JSONL with SHA-256 of anonymized prompts |
| API key storage        | Environment variables only, never in source          |
| SQL injection          | All queries use parameterized statements             |
| Container security     | Backend runs as non-root user                        |
| CORS                   | Restricted to localhost origins                      |
| HITL enforcement       | No prompt sent without analyst explicit approval     |
| Vault reveal           | Original values auto-hide after 5 seconds            |

## Keyboard Shortcuts

| Key            | Action                  |
| -------------- | ----------------------- |
| Enter          | Send prompt / Analyze   |
| Shift+Enter    | New line in prompt      |
| Escape         | Cancel HITL review      |

## Development

### Backend only

```bash
cd backend
pip install -e ".[dev]"
pytest
```

### Frontend only

```bash
cd frontend
npm install
npm run dev
```

### Full stack (Docker)

```bash
docker compose up --build
```

### Production

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add my feature"`
4. Push to branch: `git push origin feature/my-feature`
5. Open a Pull Request

Please ensure:
- All Python code is typed and has docstrings
- All TypeScript is strict-mode compliant with no `any`
- Tests pass: `pytest` (backend) and `npm run build` (frontend)
- New endpoints have corresponding tests

## License

MIT
