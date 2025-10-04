.PHONY: help install install-dev test lint format clean docker-build docker-run setup pre-commit

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	python -m pip install -r requirements.txt

install-dev:  ## Install development dependencies
	python -m pip install -r requirements-dev.txt
	pre-commit install

setup:  ## Setup for deployment (production dependencies only)
	python -m pip install -r requirements.txt
	@echo "✅ Setup complete!"

setup-dev: install-dev  ## Complete development setup
	@echo "✅ Development environment setup complete!"

test:  ## Run tests with coverage
	pytest

test-verbose:  ## Run tests with verbose output
	pytest -vv

test-coverage:  ## Run tests and show coverage report
	pytest --cov-report=html --cov-report=term

lint:  ## Run linting checks
	black --check .
	isort --check-only .
	flake8 .
	bandit -r app.py -c pyproject.toml

format:  ## Format code with black and isort
	black .
	isort .

pre-commit:  ## Run pre-commit hooks on all files
	pre-commit run --all-files

clean:  ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete

docker-build:  ## Build Docker image
	docker build -t youtube-transcript-api:latest .

docker-run:  ## Run Docker container
	docker run -d -p 9585:8000 --name youtube-transcript-api youtube-transcript-api:latest

docker-compose-up:  ## Start services with docker-compose
	docker-compose up -d

docker-compose-down:  ## Stop services with docker-compose
	docker-compose down

docker-compose-logs:  ## View docker-compose logs
	docker-compose logs -f

run:  ## Run development server
	python app.py

run-prod:  ## Run production server with gunicorn
	gunicorn --bind ${GUNICORN_BIND:-0.0.0.0:${PORT:-9585}} \
		--workers ${GUNICORN_WORKERS:-4} \
		--timeout ${GUNICORN_TIMEOUT:-120} \
		--access-logfile - \
		--error-logfile - \
		app:app

check: lint test  ## Run all checks (lint + test)

ci:  ## Run CI checks (used by GitHub Actions)
	make lint
	make test

deploy-build:  ## Build for deployment
	make clean
	make test
	make docker-build

.DEFAULT_GOAL := help
