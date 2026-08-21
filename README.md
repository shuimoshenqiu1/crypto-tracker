# CryptoTracker

Real-time cryptocurrency portfolio tracker with price alerts and market analytics.

## Quick Start

```bash
docker compose up --build
```

Access the application at: http://localhost:3000

API documentation: http://localhost:3000/api/v1/docs

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Celery
- **Frontend**: React, TypeScript
- **Database**: PostgreSQL 15
- **Cache/Broker**: Redis 7
- **Reverse Proxy**: Nginx
- **Containerization**: Docker Compose

## Development

```bash
# Start all services
make up

# View logs
make logs

# Rebuild and restart
make restart

# Stop all services
make down

# Clean up volumes
make clean
```

## Architecture

```
Client -> Nginx(:3000) -> Frontend(:80)  [static assets]
                       -> Backend(:8000)  [/api/*, /ws/*]
                       
Backend -> PostgreSQL(:5432)
        -> Redis(:6379)
```
