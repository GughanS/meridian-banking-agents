# Workflow: /test-all

**Description:** Runs the entire test suite, coverage check, and type checks to ensure the codebase is green before proceeding.

**Steps:**
1. Run `make lint` (ruff).
2. Run `make typecheck` (mypy for Python, tsc for frontend).
3. Run `make test` (pytest for backend, vitest for frontend) with coverage constraints.
4. Report any failures and stop execution. If green, confirm success.
