.PHONY: dev lint test docker-build help

# Default target
help:
	@echo "Available targets:"
	@echo "  dev          - Start development server with auto-reload"
	@echo "  lint         - Run code linting with flake8 and black"
	@echo "  test         - Run unit tests with pytest"
	@echo "  docker-build - Build Docker image"

# Development server
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Linting
lint:
	black --check app/ tests/
	flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503

# Format code
format:
	black app/ tests/

# Testing
test:
	pytest tests/ -v --tb=short

# Test with coverage
test-cov:
	pytest tests/ -v --cov=app --cov-report=term-missing

# Docker build
docker-build:
	docker build -t cost-architect:latest .

# Docker run
docker-run:
	docker run -p 8000:8000 --env-file .env cost-architect:latest

# Install dependencies
install:
	pip install -r requirements.txt

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 