# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mnemo** — a FastAPI + Celery application backed by MySQL and RabbitMQ. The project name in `pyproject.toml` is `mnemo`; the repo directory is `auto-notes`.

## Commands

All commands use `uv` as the package manager.

```bash
# Install dependencies
uv sync

# Run the FastAPI dev server (outside Docker)
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run Celery worker
uv run celery -A tasks worker --loglevel=info --concurrency=1

# Run tests
uv run pytest

# Run a single test
uv run pytest path/to/test_file.py::test_function_name

# Alembic migrations
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
uv run alembic downgrade -1
```

## Docker

```bash
# Start all services (MySQL, RabbitMQ, app, Celery worker)
docker compose up -d

# Start only infrastructure (MySQL + RabbitMQ)
docker compose up -d mysql rabbitmq
```

Copy `.env.sample` to `.env` and fill in values before running.

## Architecture

The application follows a layered structure that is currently being built out:

- **`main.py`** — FastAPI application entrypoint (currently a stub)
- **`settings.py`** — Pydantic `BaseSettings` reading from `.env`; exposes a singleton `settings` object and a `database_url` property
- **`base/databases.py`** — SQLAlchemy engine + `SessionLocal`; provides `create_session()` (generator, for FastAPI `Depends`) and `session_context()` (context manager, for Celery tasks)
- **`tasks/__init__.py`** — Celery app configured with RabbitMQ broker; workers run with `--max-tasks-per-child=5` and `--max-memory-per-child=400000`; GC is called after every task via `task_postrun` signal
- **`entities/`** — SQLAlchemy models (empty, to be populated)
- **`services/`** — Business logic layer (empty, to be populated)
- **`v1/`** — FastAPI routers (empty, to be populated)
- **`alembic/`** — Database migrations; `env.py` imports `models.Base` for autogenerate and renders custom `PendulumDateTimeDecorator` and `UuidTypeDecorator` types as standard SQLAlchemy types

## Key Conventions

- MySQL 9.0 with `utf8mb4` charset; timezone `Asia/Tokyo` (+09:00) enforced at both DB and app level
- SQLAlchemy sessions: use `create_session()` for FastAPI dependency injection, `session_context()` for Celery tasks (auto-commit/rollback)
- Celery tasks use `task_acks_late=True` and `task_reject_on_worker_lost=True` for reliability
- The `alembic/env.py` reads DB credentials directly from environment variables (not via `settings.database_url`); keep both in sync when adding new DB config
