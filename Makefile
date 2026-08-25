.PHONY: install lint format test security audit all clean novo-conector deploy-views listar sync-skills

install:
	uv sync

lint:
	uv run ruff check src/ tests/ scripts/
	uv run ruff format --check src/ tests/ scripts/

format:
	uv run ruff format src/ tests/ scripts/
	uv run ruff check --fix src/ tests/ scripts/

test:
	uv run pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

security:
	uv run bandit -r src/ scripts/ -ll

audit:
	# audita as dependências resolvidas; o próprio pacote (editable) fica de fora
	uv export --no-emit-project --no-hashes --extra dev -o .requirements.txt -q
	uv run pip-audit --strict -r .requirements.txt
	rm -f .requirements.txt

all: lint test security audit

novo-conector:
	@test -n "$(fonte)" || (echo "uso: make novo-conector fonte=ons entidade=carga"; exit 1)
	@test -n "$(entidade)" || (echo "uso: make novo-conector fonte=ons entidade=carga"; exit 1)
	uv run python -m scripts.novo_conector --fonte $(fonte) --entidade $(entidade)

sync-skills:
	uv run python -m scripts.sync_skills_google

deploy-views:
	uv run python -m scripts.deploy_views

listar:
	uv run alupdata listar

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f coverage.xml bandit-report.json .requirements.txt
