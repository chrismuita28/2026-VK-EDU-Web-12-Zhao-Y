.PHONY: up down build migrate fill-db

up:
	docker-compose --env-file .env.docker up -d

down:
	docker-compose --env-file .env.docker down

build:
	docker-compose --env-file .env.docker build

migrate:
	docker-compose --env-file .env.docker exec web python manage.py migrate

fill-db:
	docker-compose --env-file .env.docker exec web python manage.py fill_db 50
	