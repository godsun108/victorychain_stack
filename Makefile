.PHONY: help setup run test up down logs logs-worker reset-db seed retry-once

help:
	@echo "setup      Create .venv and install deps"
	@echo "run        Run API locally"
	@echo "test       Run test suite"
	@echo "up         Start docker-compose stack"
	@echo "down       Stop docker-compose stack"
	@echo "logs       Follow API logs"
	@echo "logs-worker Follow webhook worker logs"
	@echo "reset-db   Recreate docker database volume"
	@echo "seed       Seed local dev data"
	@echo "retry-once Run one webhook retry batch locally"

setup:
	python3 -m venv .venv
	. .venv/bin/activate && python -m pip install -r requirements.txt

run:
	. .venv/bin/activate && uvicorn src.victory_impact.main:app --reload

test:
	. .venv/bin/activate && pytest -q

up:
	cp -n .env.example .env || true
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

reset-db:
	docker compose down -v
	docker compose up -d db

seed:
	. .venv/bin/activate && python scripts/reseed_demo_data.py

retry-once:
	. .venv/bin/activate && python scripts/retry_webhooks.py --limit 100
