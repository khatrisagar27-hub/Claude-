.PHONY: up down build migrate seed audit logs clean

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python /app/scripts/seed_data.py

audit:
	docker compose exec backend python /app/scripts/run_first_audit.py

logs:
	docker compose logs -f backend worker

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U cae_user -d cae_db

clean:
	docker compose down -v
	docker system prune -f
