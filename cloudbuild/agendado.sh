#!/usr/bin/env bash
# Agendados no Cloud Build (ADR 030): tradução dos workflows sca, atribuicao, quadro e painel. Cada yaml fixa a
# TAREFA; toda entrada chega por variável de ambiente (nunca por texto do shell). Tokens do GitHub App só em
# memória: sem rastreamento de comandos, nunca ecoados.
set -euo pipefail

[[ "${TAREFA:-}" =~ ^(sca|atribuicao|quadro|painel)$ ]] \
  || { echo "TAREFA inválida: '${TAREFA:-}' (sca, atribuicao, quadro ou painel)."; exit 1; }

REPO="nessenergy/Alupdatalake"
UV_VERSAO="0.5.11"

exige_app() {
  [[ -n "${CLIENT_ID_APP:-}" ]] || { echo "CLIENT_ID_APP vazio: preencha o client id do GitHub App no gatilho"; exit 1; }
  [[ -n "${CHAVE_APP:-}" ]] || { echo "CHAVE_APP vazia: o segredo do GitHub App precisa de uma versão"; exit 1; }
}

instala_uv() {
  curl -LsSf "https://astral.sh/uv/${UV_VERSAO}/install.sh" | sh
  export PATH="$HOME/.local/bin:$PATH"
}

# Token de instalação do App (scripts/github_app_token.py), com as permissões dadas.
token_do_app() {
  uv run --no-project --with cryptography --with requests \
    python -m scripts.github_app_token --dono nessenergy "$@"
}

case "$TAREFA" in
  sca)
    exec bash cloudbuild/ci.sh ci-sca
    ;;
  atribuicao)
    exige_app
    instala_uv
    # A varredura usa o `gh api`; a imagem do node não o traz.
    apt-get update -qq
    apt-get install -y -qq gh
    uv sync --frozen --extra dev
    # A autoverificação roda antes: se o detector estiver quebrado, falhar é melhor que reportar "limpo".
    uv run pytest tests/unit/test_verifica_atribuicao.py -q
    # Atribuição separada do uso: se o token falhar, o set -e para aqui (em `VAR=$(...) cmd` não pararia).
    GH_TOKEN="$(token_do_app --permissao contents=read --permissao issues=read --permissao pull_requests=read)"
    export GH_TOKEN
    uv run python scripts/verifica_atribuicao.py --github nessenergy/Alupdatalake
    ;;
  quadro)
    # Sem client id não há de onde tirar o token: pendência conhecida, aviso e sucesso (guarda do quadro.yml).
    if [[ -z "${CLIENT_ID_APP:-}" ]]; then
      echo "Quadro não sincronizado: falta o client id do GitHub App do quadro (github_app_quadro_client_id)."
      exit 0
    fi
    exige_app
    instala_uv
    uv sync --frozen --no-dev
    GITHUB_TOKEN="$(token_do_app --permissao organization_projects=write --permissao issues=write --permissao pull_requests=read)"
    export GITHUB_TOKEN
    uv run python -m scripts.quadro --aplicar
    ;;
  painel)
    exige_app
    for v in PAINEL_BUCKET PROJETO_DEV PROJETO_HML; do
      [[ -n "${!v:-}" ]] || { echo "$v vazio: vem do gatilho (módulo cicd)."; exit 1; }
    done
    [[ "$PAINEL_BUCKET" =~ ^[a-z0-9][a-z0-9._-]{1,220}[a-z0-9]$ ]] || { echo "PAINEL_BUCKET inválido."; exit 1; }
    for v in PROJETO_DEV PROJETO_HML; do
      [[ "${!v}" =~ ^[a-z][a-z0-9-]{4,28}[a-z0-9]$ ]] || { echo "$v inválido."; exit 1; }
    done
    instala_uv
    uv sync --frozen --no-dev
    GITHUB_TOKEN="$(token_do_app --permissao issues=read)"
    export GITHUB_TOKEN
    # hml: o painel lê com a própria conta, que entra por leitores_execucoes (infra/). Sem a concessão, falha aqui.
    uv run python -m scripts.painel --so-execucoes --ambiente "hml=${PROJETO_HML}" --saida execucoes-hml.json
    uv run python -m scripts.painel --ambiente "dev=${PROJETO_DEV}" \
      --execucoes-de execucoes-hml.json --repositorio "$REPO" --saida dados.json
    # Sem BigQuery nem GitHub: painel/aditivo.toml já traz o estado de cada item.
    uv run python -m scripts.painel_aditivo --saida dados-aditivo.json
    gcloud storage cp dados.json dados-aditivo.json painel/index.html painel/aditivo.html \
      "gs://${PAINEL_BUCKET}/" --cache-control=no-store
    echo "Painel publicado: $(date -u +%FT%TZ)"
    ;;
esac
