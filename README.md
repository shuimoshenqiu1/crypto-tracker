# CryptoTracker

AI-powered cryptocurrency portfolio tracking and analysis platform.

## Quick Start

```bash
docker compose up --build
```

Access the application at **http://localhost:3000**

API documentation (Swagger): **http://localhost:3000/api/v1/docs**

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Celery |
| Frontend | React 18, TypeScript, Ant Design Pro |
| Database | PostgreSQL 15 |
| Cache/Broker | Redis 7 |
| Reverse Proxy | Nginx |
| Container | Docker Compose |

## Project Structure

```
crypto-tracker/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/     # Route handlers
│   │   ├── core/    # Config, security, dependencies
│   │   ├── crud/    # Database operations
│   │   ├── models/  # SQLAlchemy models
│   │   ├── schemas/ # Pydantic schemas
│   │   └── tasks/   # Celery async tasks
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         # React SPA
│   ├── src/
│   ├── Dockerfile    # Multi-stage build (build + nginx serve)
│   └── package.json
├── nginx/
│   └── nginx.conf    # Outer reverse proxy config
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

## Architecture

```
Client :3000 -> Nginx (outer)
                  ├── /api/*  -> Backend :8000 (FastAPI)
                  ├── /ws/*   -> Backend :8000 (WebSocket)
                  └── /*      -> Frontend :80 (internal nginx, static SPA)
```

## Available Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services (detached) |
| `make down` | Stop all services |
| `make build` | Build/rebuild all images |
| `make logs` | Tail logs for all services |
| `make clean` | Stop services + remove volumes (full reset) |
| `make restart` | Restart all services |
| `make ps` | Show running containers |

## Environment Variables

Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

Key variables:
- `SECRET_KEY` — JWT signing key (≥32 chars in production)
- `DATABASE_URL` — PostgreSQL connection string (async driver)
- `REDIS_URL` — Redis connection for caching
- `CELERY_BROKER_URL` — Redis connection for task queue
