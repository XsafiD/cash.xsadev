.PHONY: help dev migrate-init migrate-up migrate-down migrate-revision seed-owner mysql-up mysql-down mysql-ps mysql-shell mysql-logs prod-build prod-up prod-down prod-ps prod-logs prod-migrate prod-seed

help: ## Show all commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

dev: ## Run Flask development server (venv, port 5000)
	venv/bin/flask run --host 0.0.0.0 --port 5001 --debug

migrate-init: ## Setup folder migrations (sekali saja)
	venv/bin/flask db init

migrate-up: ## Run Alembic migrations up
	venv/bin/flask db upgrade

migrate-down: ## Rollback latest migration (default -1)
	venv/bin/flask db downgrade

migrate-revision: ## Create new migration file (MESSAGE="...")
	venv/bin/flask db migrate -m "$(MESSAGE)"

seed-owner: ## Buat akun owner awal dari OWNER_USERNAME/OWNER_PASSWORD
	venv/bin/flask seed-owner

mysql-up: ## Start MySQL container (Docker hanya untuk MySQL di fase ini)
	docker compose up -d mysql

mysql-down: ## Stop MySQL container
	docker compose stop mysql

mysql-ps: ## Show MySQL container status
	docker compose ps

mysql-shell: ## Enter MySQL shell
	docker compose exec mysql mysql -u cashxsadev -psecret cashxsadev

mysql-logs: ## View MySQL logs
	docker compose logs -f mysql

# --- Production (docker-compose.prod.yml) ---
prod-build: ## Build image production
	docker compose -f docker-compose.prod.yml build

prod-up: ## Start stack production (detached)
	docker compose -f docker-compose.prod.yml up -d

prod-down: ## Stop stack production
	docker compose -f docker-compose.prod.yml down

prod-ps: ## Show production container status
	docker compose -f docker-compose.prod.yml ps

prod-logs: ## View production app logs
	docker compose -f docker-compose.prod.yml logs -f app

prod-migrate: ## Apply migrations di production (sekali, manual)
	docker compose -f docker-compose.prod.yml run --rm app flask db upgrade

prod-seed: ## Buat owner awal di production (sekali, manual)
	docker compose -f docker-compose.prod.yml run --rm app flask seed-owner
