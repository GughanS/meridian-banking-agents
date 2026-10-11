.PHONY: setup up down test lint typecheck eval demo

setup:
	cd backend && uv sync
	cd frontend && npm install

up:
	docker-compose up --build

down:
	docker-compose down

test:
	cd backend && uv run pytest --cov=app/engines --cov-fail-under=95
	cd frontend && npm run test

lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint

typecheck:
	cd backend && uv run mypy --strict app/
	cd frontend && npm run build

eval:
	cd backend && uv run python scripts/eval_routing.py

demo:
	cd backend && uv run python -m scripts.seed
	docker-compose up -d
	@echo "Demo running at http://localhost:5173"
