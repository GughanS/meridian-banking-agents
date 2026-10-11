# Meridian Banking Backend

Production-ready asynchronous backend powering the Meridian Multi-Agent Core Banking System.

## Architecture

- **Framework:** FastAPI with Python 3.12, strict typing with Pydantic v2
- **Orchestration:** LangGraph multi-agent supervisor graph (`CustomerAgent`, `RiskAgent`, `CreditAgent`)
- **LLM Engine:** Direct Google GenAI SDK integration with built-in deterministic Mock LLM (`LLM_PROVIDER=mock`)
- **Persistence:** SQLModel + SQLite (`aiosqlite`) with Alembic migrations
- **Deterministic Engines:** Unit-tested modules for loan eligibility, EMI amortization, fraud scoring, and action authorization
- **Streaming & Events:** Server-Sent Events (SSE) via `sse-starlette` and async in-memory pub/sub event bus

## Development & Commands

```bash
# Sync dependencies
uv sync

# Run database seed
uv run python -m scripts.seed

# Run dev server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run test suite with coverage
uv run pytest --cov=app --cov-report=term-missing

# Lint & formatting check
uv run ruff check .

# Routing accuracy evaluation
uv run python scripts/eval_routing.py
```
