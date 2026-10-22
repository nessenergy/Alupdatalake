#!/usr/bin/env bash
# Operações sob demanda no Cloud Build (ADR 030): tradução dos workflows executar-ingestao, conferir-cargas,
# sondar-rede e testar-conexao. Roda como a conta de deploy. Toda entrada chega por variável de ambiente
# (nunca por texto do shell); a validação fina de cada valor é de scripts/operacoes.py.
set -euo pipefail

UV_VERSAO="0.5.11"

# Valida antes de qualquer efeito colateral.
[[ "${OPERACAO:-}" =~ ^(executar-ingestao|conferir-cargas|sondar-rede|testar-conexao)$ ]] \
  || { echo "OPERACAO inválida: '${OPERACAO:-}' (executar-ingestao, conferir-cargas, sondar-rede ou testar-conexao)."; exit 1; }
[[ -n "${PROJETO:-}" ]] || { echo "PROJETO vazio."; exit 1; }

curl -LsSf "https://astral.sh/uv/${UV_VERSAO}/install.sh" | sh
export PATH="$HOME/.local/bin:$PATH"
uv sync --frozen --no-dev

# Flag vazia vale como ausente; só entram as que vieram preenchidas.
ARGS=()
[[ -z "${REGIAO:-}" ]] || ARGS+=(--regiao "$REGIAO")
[[ -z "${CONECTOR:-}" ]] || ARGS+=(--conector "$CONECTOR")
[[ -z "${DE:-}" ]] || ARGS+=(--de "$DE")
[[ -z "${ATE:-}" ]] || ARGS+=(--ate "$ATE")
[[ -z "${URI:-}" ]] || ARGS+=(--uri "$URI")
[[ -z "${FONTE:-}" ]] || ARGS+=(--fonte "$FONTE")
[[ -z "${SONDA:-}" ]] || ARGS+=(--sonda "$SONDA")

uv run python -m scripts.operacoes "$OPERACAO" --projeto "$PROJETO" "${ARGS[@]}"
