.PHONY: help install test lint format clean build publish

help:
	@echo "deburger - AI Code Quality Guardian"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install package and dependencies"
	@echo "  make test       - Run tests with coverage"
	@echo "  make lint       - Run code linting"
	@echo "  make format     - Format code with black"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make build      - Build distribution packages"
	@echo "  make publish    - Publish to PyPI"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,llm]"

test:
	pytest tests/ -v --cov=src/deburger --cov-report=term-missing

test-fast:
	pytest tests/ -v -x

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

build: clean
	python setup.py sdist bdist_wheel

publish: build
	twine upload dist/*

run-analyze:
	python -m deburger.cli.main analyze

run-security:
	python -m deburger.cli.main security
