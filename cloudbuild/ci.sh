#!/usr/bin/env bash
# Roda as etapas de CI do Makefile dentro do Cloud Build (ADR 030). Não usa credencial: o CI só lê o repositório.
set -euo pipefail

ALVOS="${1:-ci}"

# A checagem de atribuição compara com a main; quem a busca é o passo busca-main (ci-com-atribuicao.yaml).
case " $ALVOS " in *" ci "* | *" ci-atribuicao "*)
  git rev-parse --verify --quiet origin/main >/dev/null || {
    echo "ci-atribuicao exige origin/main, e o passo busca-main não a trouxe (use cloudbuild/ci-com-atribuicao.yaml)"
    exit 1
  }
  ;;
esac

UV_VERSAO="0.5.11"
TERRAFORM_VERSAO="1.15.8"

curl -LsSf "https://astral.sh/uv/${UV_VERSAO}/install.sh" | sh
export PATH="$HOME/.local/bin:$PATH"

curl -sSfL -o /tmp/terraform.zip \
  "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSAO}/terraform_${TERRAFORM_VERSAO}_linux_amd64.zip"
python3 -m zipfile -e /tmp/terraform.zip /tmp/terraform-bin
install -m 0755 /tmp/terraform-bin/terraform /usr/local/bin/terraform

# shellcheck disable=SC2086  # ALVOS é uma lista de alvos separados por espaço, de propósito
make $ALVOS BASE=origin/main
