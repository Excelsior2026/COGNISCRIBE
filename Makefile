.PHONY: help install install-dev test test-cov lint format clean run docker-up docker-down db-init db-seed

help:
	@echo "COGNISCRIBE Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run tests"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make test-fast        - Run fast tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             - Run linters (black, ruff, mypy)"
	@echo "  make format           - Format code with black and ruff"
	@echo "  make pre-commit       - Run pre-commit hooks"
	@echo ""
	@echo "Database:"
	@echo "  make db-init          - Initialize database"
	@echo "  make db-seed          - Seed demo data"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        - Start all services"
	@echo "  make docker-down      - Stop all services"
	@echo "  make docker-logs      - View service logs"
	@echo ""
	@echo "Development:"
	@echo "  make run              - Run API server"
	@echo "  make clean            - Clean up temporary files"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -r requirements_dev.txt
	pre-commit install

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-fast:
	pytest tests/ -v -m "not slow"

lint:
	black --check src/ tests/
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/
	ruff check --fix src/ tests/

pre-commit:
	pre-commit run --all-files

db-init:
	python scripts/init_db.py --init

db-seed:
	python scripts/init_db.py --seed

db-reset:
	python scripts/init_db.py --drop
	python scripts/init_db.py --all

docker-up:
	docker-compose -f docker-compose-phase3.yml up -d

docker-down:
	docker-compose -f docker-compose-phase3.yml down

docker-logs:
	docker-compose -f docker-compose-phase3.yml logs -f api

run:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ coverage.xml .coverage test.db
