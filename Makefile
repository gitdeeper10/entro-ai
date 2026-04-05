# ENTRO-AI Makefile
# Entropy-Resistant Inference Architecture for LLMs

.PHONY: help install install-dev clean test lint format build docker run

help:
	@echo "ENTRO-AI Makefile Commands:"
	@echo "  make install      - Install production package"
	@echo "  make install-dev  - Install with dev dependencies"
	echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make build        - Build package"
	@echo "  make docker       - Build Docker image"
	@echo "  make run          - Run ENTRO-AI dashboard"
	@echo "  make clean        - Clean build artifacts"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=entro_ai

lint:
	black --check entro_ai/ tests/
	isort --check-only entro_ai/ tests/
	flake8 entro_ai/ tests/
	mypy entro_ai/

format:
	black entro_ai/ tests/
	isort entro_ai/ tests/

build:
	python -m build
	twine check dist/*

docker:
	docker build -f Dockerfile -t gitdeeper10/entro-ai:latest .

run:
	entro-ai dashboard --host 0.0.0.0 --port 8080

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
