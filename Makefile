.PHONY: install lint format test security audit all clean

install:
	uv sync

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

test:
	uv run pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

security:
	uv run bandit -r src/ -ll

audit:
	uv run pip-audit --strict

all: lint test security audit

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f coverage.xml bandit-report.json
