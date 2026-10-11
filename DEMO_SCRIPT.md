# Meridian AI Banking Agents - Demo Script

Welcome to the Meridian AI Banking Agents demo. This guide will walk you through a fully functioning prototype of an agentic core banking experience.

## Prerequisites
- Docker & Docker Compose
- Node.js (for local frontend development)
- Python 3.12 + `uv` (for local backend development)
- **No API key required:** Runs 100% locally out-of-the-box using the deterministic Mock LLM engine.
- Optional: `GEMINI_API_KEY` only if live Google GenAI generation is explicitly desired.

## Step 1: Start the Demo
We provide a unified Makefile command to launch everything:
```bash
make setup
make demo
```

*(If you are on Windows and don't have `make` installed, you can run these PowerShell equivalents instead):*
```powershell
cd backend; C:\Users\gugha\.local\bin\uv.exe sync; cd ..
cd frontend; npm install; cd ..
cd backend; C:\Users\gugha\.local\bin\uv.exe run python -m scripts.seed; cd ..
docker-compose up -d
```

This will:
1. Sync Python dependencies via `uv`.
2. Install Node dependencies via `npm`.
3. Seed the local SQLite database with deterministically generated personas (Virat, Rohit, Mahi).
4. Spin up the backend (FastAPI) and frontend (React/Vite) via Docker Compose.

Visit **http://localhost:5173** to view the app.

## Step 2: Explore Personas
Use the dropdown in the top left to switch personas:
- **Virat (Tech Worker):** High income, stable. Perfect for testing large loan applications.
- **Rohit (Small Business):** High transaction volume. Perfect for testing anomaly detection (fraud).
- **Mahi (Student):** Low balance. Perfect for testing rejected transactions or eligibility failures.

## Step 3: Run the Use Cases

### UC1: Transaction Intent Routing & Retrieval
**Persona:** Virat
**Input:** "What is my balance and what were my last 3 transactions?"
**Watch for:** The Agent Inspector pane will show the `supervisor` routing the intent to the `customer_agent`. The UI will stream a summary of the transactions.

### UC2: Agent-to-Agent Handoff & Human-in-the-Loop Write
**Persona:** Virat
**Input:** "I lost my card, please block it."
**Watch for:** 
1. The `supervisor` hands off to the `risk_agent`.
2. The `risk_agent` creates a `PendingAction` and returns an action ID.
3. The UI renders a **Confirm Card** block requiring explicit user consent.
4. Click **Confirm** to execute the two-phase write.

### UC3: Multi-Step Credit Evaluation
**Persona:** Rohit
**Input:** "I need a 50,000 loan for my business over 24 months. Am I eligible and what's the EMI?"
**Watch for:** 
1. Handoff to `credit_agent`.
2. The agent calls `check_loan_eligibility` (deterministic Engine).
3. The agent calls `calculate_emi` (deterministic math).
4. The agent formulates a proposal without computing numbers in the prompt.

### UC8: Real-Time Event Bus & Proactive Agent
**Input:** *(Trigger via API)*
```bash
curl -X POST http://localhost:8000/simulator/inject
```
**Watch for:** 
1. The transaction simulator fires a massive overseas charge.
2. The Fraud Monitor intercepts it via the Async Event Bus.
3. The UI's Live Alerts feed immediately pops up a red warning.

## Notes for Evaluators
- **Identity is secure:** At no point do we pass `customer_id` via the chat prompt. It is injected via JWT into the FastAPI request context.
- **Deterministic Math:** We use Python `Decimal` and specific engines. The LLM only plans and synthesizes.
- **Fail-Safe:** If the LLM produces a hallucinated `merchant_name` containing a prompt injection, our tools sanitize output and do not execute scripts.

Enjoy the demo!
