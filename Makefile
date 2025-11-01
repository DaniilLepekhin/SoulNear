.PHONY: help build up down restart logs clean backup

# Определяем окружение (по умолчанию prod)
ENV ?= prod

help: ## Показать эту справку
	@echo "SoulNear Docker Management"
	@echo ""
	@echo "Использование: make [target] [ENV=prod|test|dev]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Собрать все образы
	docker-compose --env-file .env.$(ENV) build

up: ## Запустить все сервисы
	@./validate-env.sh || exit 1
	docker-compose --env-file .env.$(ENV) up -d

down: ## Остановить все сервисы
	docker-compose down

restart: ## Перезапустить все сервисы
	docker-compose restart

restart-bot: ## Перезапустить только бота
	docker-compose restart bot

restart-api: ## Перезапустить только API
	docker-compose restart api

logs: ## Показать логи всех сервисов
	docker-compose logs -f --tail=100

logs-bot: ## Показать логи бота
	docker-compose logs -f --tail=100 bot

logs-api: ## Показать логи API
	docker-compose logs -f --tail=100 api

logs-db: ## Показать логи PostgreSQL
	docker-compose logs -f --tail=100 postgres

ps: ## Показать статус сервисов
	docker-compose ps

stats: ## Показать использование ресурсов
	docker stats --no-stream

rebuild: ## Пересобрать и запустить
	docker-compose --env-file .env.$(ENV) up -d --build

clean: ## Остановить и удалить контейнеры (без volumes)
	docker-compose down

clean-all: ## Остановить и удалить контейнеры с volumes (УДАЛИТ БД!)
	@echo "⚠️  ВНИМАНИЕ! Это удалит все данные из БД!"
	@read -p "Продолжить? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
	fi

shell-bot: ## Зайти в shell бота
	docker exec -it soulnear_bot bash

shell-api: ## Зайти в shell API
	docker exec -it soulnear_api bash

shell-db: ## Подключиться к PostgreSQL
	docker exec -it soulnear_postgres psql -U postgres -d soul_bot

backup: ## Создать бэкап БД
	@mkdir -p backups
	docker exec soulnear_postgres pg_dump -U postgres soul_bot > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Бэкап создан в backups/"

restore: ## Восстановить последний бэкап БД
	@LATEST=$$(ls -t backups/*.sql | head -1); \
	echo "Восстанавливаем $$LATEST..."; \
	docker exec -i soulnear_postgres psql -U postgres soul_bot < $$LATEST

health: ## Проверить здоровье сервисов
	@echo "🔍 Проверка PostgreSQL..."
	@docker exec soulnear_postgres pg_isready -U postgres && echo "✅ PostgreSQL OK" || echo "❌ PostgreSQL NOT OK"
	@echo ""
	@echo "🔍 Проверка API..."
	@curl -s http://localhost:8888/health | python3 -m json.tool && echo "✅ API OK" || echo "❌ API NOT OK"

setup: ## Первичная настройка (создать .env.prod из примера)
	@if [ ! -f .env.prod ]; then \
		cp .env.example .env.prod; \
		echo "✅ Создан .env.prod - заполните его реальными значениями!"; \
	else \
		echo "⚠️  .env.prod уже существует"; \
	fi

# Development mode с hot reload
dev: ## Запустить в dev режиме с hot reload
	docker-compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up

dev-build: ## Собрать и запустить в dev режиме
	docker-compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up --build

dev-down: ## Остановить dev режим
	docker-compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml down

# Shortcuts
start: up ## Алиас для up
stop: down ## Алиас для down

