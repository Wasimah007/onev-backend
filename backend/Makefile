# FastAPI Backend Makefile

.PHONY: help install dev migrate test lint format clean docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Run development server"
	@echo "  migrate     - Run database migrations"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean cache files"
	@echo "  docker-up   - Start Docker services"
	@echo "  docker-down - Stop Docker services"

# Install dependencies
install:
	pip install -r requirements.txt

# Run development server
dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run database migrations
migrate:
	chmod +x migrate.sh
	./migrate.sh

# Run tests
test:
	pytest app/tests/ -v

# Run linting
lint:
	flake8 app/
	black --check app/
	isort --check-only app/

# Format code
format:
	black app/
	isort app/

# Clean cache files
clean:
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# Create superuser (admin)
create-superuser:
	python -c "import asyncio; from app.auth.service import auth_service; asyncio.run(auth_service.create_user('admin@example.com', 'admin', 'admin123', 'Admin', 'User', is_admin=True))"

# Database backup
backup-db:
	mysqldump -h$(MYSQL_HOST) -u$(MYSQL_USER) -p$(MYSQL_PASSWORD) $(MYSQL_DATABASE) > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Database restore
restore-db:
	@echo "Usage: make restore-db BACKUP_FILE=backup_file.sql"
	@if [ -z "$(BACKUP_FILE)" ]; then echo "Please specify BACKUP_FILE"; exit 1; fi
	mysql -h$(MYSQL_HOST) -u$(MYSQL_USER) -p$(MYSQL_PASSWORD) $(MYSQL_DATABASE) < $(BACKUP_FILE)