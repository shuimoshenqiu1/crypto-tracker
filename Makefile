.PHONY: up down build logs clean restart ps

# Start all services (detached)
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Build (or rebuild) all images
build:
	docker compose build

# Tail logs for all services
logs:
	docker compose logs -f

# Stop services and remove volumes (full reset)
clean:
	docker compose down -v --remove-orphans

# Restart all services
restart:
	docker compose restart

# Show running containers
ps:
	docker compose ps
