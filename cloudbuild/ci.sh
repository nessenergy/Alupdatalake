#!/usr/bin/env bash
# Roda as etapas de CI do Makefile dentro do Cloud Build (ADR 030). Não usa credencial: o CI só lê o repositório.
set -euo pipefail

ALVOS="${1:-ci}"
UV_VERSAO="0.5.11"
TERRAFORM_VERSAO="1.15.8"

# A checagem de atribuição e o gitleaks precisam do histórico e da referência da main.
# O Cloud Build baixa o código como FETCH_HEAD e não cria o remoto `origin`; o repositório é público, então a URL basta.
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/nessenergy/Alupdatalake.git"
git fetch --unshallow --quiet origin 2>/dev/null || true
# Sem `|| true`: se a main não vier, a checagem de atribuição não tem com o que comparar e o build deve dizer isso.
git fetch --quiet origin main:refs/remotes/origin/main

curl -LsSf "https://astral.sh/uv/${UV_VERSAO}/install.sh" | sh
export PATH="$HOME/.local/bin:$PATH"

curl -sSfL -o /tmp/terraform.zip \
  "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSAO}/terraform_${TERRAFORM_VERSAO}_linux_amd64.zip"
python3 -m zipfile -e /tmp/terraform.zip /tmp/terraform-bin
install -m 0755 /tmp/terraform-bin/terraform /usr/local/bin/terraform

# shellcheck disable=SC2086  # ALVOS é uma lista de alvos separados por espaço, de propósito
make $ALVOS BASE=origin/main
