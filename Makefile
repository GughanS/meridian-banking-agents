.PHONY: setup up down seed dev test lint typecheck eval demo

setup:
	cd backend && uv sync
	cd frontend && npm install

up:
	docker compose up -d

down:
	docker compose down

seed:
	cd backend && uv run python scripts/seed.py

dev:
	start powershell -NoExit -Command "cd backend; uv run uvicorn app.main:app --reload --port 8000"
	start powershell -NoExit -Command "cd frontend; npm run dev"

test:
	cd backend && uv run pytest --cov=app tests/
	cd frontend && npm run test

lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint

typecheck:
	cd backend && uv run mypy --strict app/
	cd frontend && npm run typecheck

eval:
	cd backend && uv run python scripts/eval_routing.py

demo: seed up
	@echo "Demo ready at http://localhost:5173"
