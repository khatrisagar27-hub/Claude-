.PHONY: setup up down logs demo psql test dev-api dev-web build-web

PY ?= python3

setup:            ## create .env with random secrets (does nothing if it exists)
	$(PY) scripts/make_env.py

up: setup         ## build and start; app on http://localhost:8080
	docker compose up -d --build

down:             ## stop (data is kept)
	docker compose down

logs:
	docker compose logs -f app

demo:             ## load the demo engagement into the running stack
	docker compose exec app python -m app.demo

psql:
	docker compose exec db psql -U cae cae

test:             ## backend tests (SQLite, no Docker)
	cd backend && $(PY) -m pytest -q

# Without Docker: `make dev-api` and `make dev-web` in two terminals, then http://localhost:5173
dev-api:
	cd backend && $(PY) -m uvicorn app.main:app --reload --port 8000

dev-web:
	cd frontend && npm install && npm run dev

build-web:
	cd frontend && npm ci && npm run build
