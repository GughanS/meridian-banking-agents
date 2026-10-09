# Meridian AI Agent Engineering Rules

## 1. Non-Negotiable Principles
*   **LLMs explain; deterministic code decides.** Fraud scores, loan eligibility, EMI math, and balances come from deterministic, unit-tested code. The LLM chooses tools, interprets results, and explains them. It never computes or invents numbers.
*   **Identity is never an LLM parameter.** `customer_id` comes from the verified JWT and is injected into tools server-side via request context. No tool schema exposes it. Every tool also performs object-level authorization (resource must belong to the caller).
*   **Writes are two-phase and human-confirmed.** Agents can only call `propose_*` tools, which create a `PendingAction` (expires in 5 mins). Execution happens only via `POST /actions/{id}/confirm`, which is not reachable by any LLM. Confirm is idempotent and audited.
*   **Money is never a float.** Use `Decimal` or integer minor units end to end, including JSON (serialize as strings).
*   **Tool output is untrusted data.** Wrap tool results so that instructions inside them (e.g., in a merchant name) are never obeyed. System prompts state this explicitly, and adversarial tests prove it.
*   **Every layer fails safely.** Timeouts, bounded retries with jittered backoff, a circuit breaker on the core-banking client, a model fallback, and a hard cap on agent loop iterations. Errors reach the user as clear, non-technical messages, never stack traces.
*   **Everything is traceable.** Each run records plan, agent steps, tool calls (arguments redacted), latency, tokens, and prompt versions. Each write is recorded in an append-only audit log.
*   **Reproducible.** Deterministic seed data, pinned dependencies, `.env.example`, Docker Compose, Makefile, CI.
*   **Works without an API key.** `LLM_PROVIDER=mock` runs a deterministic mock LLM so tests, CI, and offline demos pass. Real Gemini is the default for the demo.
*   **Honest UX.** A persistent banner states this is a simulation with fictional data. Credit outputs are labelled "indicative, not an offer".

## 2. Tech Decisions (Fixed - Do Not Re-litigate)
*   **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLModel + SQLite (async via aiosqlite; Postgres-ready), Alembic migrations, httpx (async), tenacity, structlog, sse-starlette, slowapi, PyJWT. Dependency management with `uv` and `pyproject.toml`.
*   **Tooling:** `ruff`, `mypy --strict` on `app/`, `pytest` + `pytest-asyncio` + `pytest-cov`.
*   **Orchestration:** LangGraph for the supervisor graph. Use the official `google-genai` SDK directly behind our own `LLMClient` protocol (no LangChain model wrappers).
*   **Frontend:** React 18 + Vite + TypeScript (strict) + Tailwind CSS + lucide-react + TanStack Query + Recharts + react-markdown. Vitest + Testing Library for component tests.
*   **Packaging:** Docker (multi-stage, non-root user) + Docker Compose, Makefile, GitHub Actions CI.
*   **Currency:** Configurable via `DEFAULT_CURRENCY`, default INR (₹) with Indian digit grouping in the UI.

## 3. Coding Standards
*   **Typing:** Strict typing everywhere. No `Any` without explicit justification.
*   **Modularity:** Keep functions small and single-purpose. Dependency injection for clients and repositories.
*   **Error Handling:** Use custom exceptions mapped to HTTP status codes centrally. Never leak internal details.
*   **Naming:** Descriptive, intention-revealing names. Follow PEP 8 for Python and standard camelCase for TS.

## 4. Testing Policy
*   All business logic (deterministic engines) must have 100% branch coverage.
*   Test every use case (UC1-UC8) in integration with the Mock Core and Mock LLM.
*   Security tests: cross-customer data access, prompt injection, input bounds.
*   Routing Evaluation: Target >= 90% accuracy, report in `docs/EVAL_REPORT.md`.

## 5. Never Invent Library APIs
*   **Read the docs:** When using a library or the Gemini API, read the current official docs first. Pin verified versions.
*   **No hardcoded model IDs:** Read the current Gemini API model list. At backend startup, validate configured model IDs dynamically.
