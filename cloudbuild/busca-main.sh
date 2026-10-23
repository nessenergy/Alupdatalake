#!/usr/bin/env bash
# Traz a main para o build com um token de leitura do GitHub App (ADR 030). O repositório é privado e o clone do
# Cloud Build não traz a main; a checagem de atribuição compara com ela. O token vive só em memória: sem rastreamento de comandos,
# e a saída do fetch passa por um filtro que o troca por ***.
set -euo pipefail

if [ -z "${CLIENT_ID_APP:-}" ]; then echo "CLIENT_ID_APP vazio: preencha github_app_ci_client_id no gatilho"; exit 1; fi
if [ -z "${CHAVE_APP:-}" ]; then echo "CHAVE_APP vazia: o segredo alupdata-github-ci-app-key precisa de uma versão"; exit 1; fi

UV_VERSAO="0.5.11"
curl -LsSf "https://astral.sh/uv/${UV_VERSAO}/install.sh" | sh
export PATH="$HOME/.local/bin:$PATH"

TOKEN="$(uv run --no-project --with cryptography --with requests \
  python -m scripts.github_app_token --dono nessenergy --permissao contents=read)"
if [ -z "$TOKEN" ]; then echo "token do GitHub App vazio: confira o client id, a chave e a instalação do App"; exit 1; fi
REPO="https://x-access-token:${TOKEN}@github.com/nessenergy/Alupdatalake.git"

# Filtra o token de qualquer mensagem do git.
sem_token() { sed "s/${TOKEN}/***/g"; }

# Clone raso não tem a base do intervalo; se já estiver completo, o erro é inofensivo.
git fetch --unshallow --quiet "$REPO" 2>&1 | sem_token || true
git fetch --quiet "$REPO" main:refs/remotes/origin/main 2>&1 | sem_token
