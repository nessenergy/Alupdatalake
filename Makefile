.PHONY: install lint format test security audit all clean novo-conector listar sync-skills campos-projeto dataform-compile quadro quadro-aplicar

install:
	uv sync --extra dev

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

campos-projeto: ## Cria os campos de acompanhamento semanal no GitHub Projects
	@test -n "$(owner)" || (echo "uso: make campos-projeto owner=nessenergy numero=1"; exit 1)
	@test -n "$(numero)" || (echo "uso: make campos-projeto owner=nessenergy numero=1"; exit 1)
	uv run python -m scripts.campos_projeto --owner $(owner) --numero $(numero)

quadro: ## Simula a sincronização do quadro de acompanhamento (Project 2)
	uv run python -m scripts.quadro

quadro-aplicar: ## Grava a sincronização no quadro e comenta os atrasos novos
	uv run python -m scripts.quadro --aplicar

sync-skills:
	uv run python -m scripts.sync_skills_google

listar:
	uv run alupdata listar

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f coverage.xml bandit-report.json .requirements.txt

questionario-pdf: ## Reemite o PDF de envio do Questionario de Gaps
	uv run --with markdown python scripts/gerar_documento.py docs/questionario-gaps.md 		--pdf --classe questionario --saida-pdf docs/envio/Questionario-de-Gaps-AlupData.pdf

relatorio: ## Gera o HTML de um relatorio: make relatorio ARQ=docs/relatorios/AAAA-MM-DD-x.md
	uv run --with markdown python scripts/gerar_documento.py $(ARQ) --html

dataform-compile: ## Compila o projeto Dataform (definitions/) sem credencial
	npx --yes @dataform/cli@3.0.69 compile
