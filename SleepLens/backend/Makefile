.PHONY: help install test test-app lint format migrate mm makemigrations run worker beat up down logs shell hooks hooks-run clean

# This project runs on the system Python (all dependencies are installed globally
# on the development machine). No virtualenv is required.

help:
	@echo "install      Install deps into the system Python + pre-commit"
	@echo "test         Run the whole test suite"
	@echo "test-app APP=accounts   Run tests for one app"
	@echo "lint         ruff check ."
	@echo "format       black + isort + ruff --fix"
	@echo "migrate      Apply migrations"
	@echo "mm APP=accounts         Make migrations for one app"
	@echo "run          Run the dev server on :8000"
	@echo "worker       Run a Celery worker"
	@echo "up/down/logs Compose dev stack (postgres + redis [+ web/worker profile])"
	@echo "hooks        Install pre-commit hooks"
	@echo "hooks-run    Run pre-commit on all files"
	@echo "clean        Remove caches and build artifacts"

install:
	python -m pip install -e ".[dev]"
	pre-commit install

test:
	python -m pytest

test-app:
	python -m pytest apps/$(APP)

lint:
	python -m ruff check .

format:
	python -m black .
	python -m isort .
	python -m ruff check . --fix

migrate:
	python manage.py migrate --noinput

mm:
	python manage.py makemigrations $(APP)

makemigrations:
	python manage.py makemigrations

run:
	python manage.py runserver 0.0.0.0:8000

worker:
	python -m celery -A sleeplens worker -l info

beat:
	python -m celery -A sleeplens beat -l info

up:
	docker-compose -f compose/dev/docker-compose.yml up -d

down:
	docker-compose -f compose/dev/docker-compose.yml down

logs:
	docker-compose -f compose/dev/docker-compose.yml logs -f web worker

shell:
	python manage.py shell

hooks:
	pre-commit install

hooks-run:
	pre-commit run --all-files

clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__ .pytest_cache .ruff_cache htmlcov .coverage
