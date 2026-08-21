.PHONY: up down logs build clean restart

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

clean:
	docker compose down -v

restart:
	docker compose down
	docker compose up -d --build
