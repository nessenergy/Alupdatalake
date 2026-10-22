#!/usr/bin/env bash
# Constrói e publica a imagem da CLI no deploy (ADR 030). Tudo chega por variável de ambiente e é validado
# antes de qualquer docker: uma imagem nunca é publicada com entrada inválida.
set -euo pipefail

[[ "${AMBIENTE:-}" =~ ^(dev|hml|prod)$ ]] || { echo "AMBIENTE inválido: '${AMBIENTE:-}' (dev, hml ou prod)."; exit 1; }
[[ "${MODULO:-}" =~ ^(all|infra|connectors)$ ]] || { echo "MODULO inválido: '${MODULO:-}' (all, infra ou connectors)."; exit 1; }

if [ "$MODULO" = "infra" ]; then
  echo "módulo infra: imagem não é construída"
  exit 0
fi

[[ "${COMMIT_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || { echo "COMMIT_SHA inválido: informe o SHA completo."; exit 1; }
[[ "${IMAGEM_BASE:-}" =~ ^[a-z0-9-]+-docker\.pkg\.dev/[a-z0-9.:-]+/[a-z0-9._-]+/[a-z0-9._/-]+$ ]] \
  || { echo "IMAGEM_BASE inválida: '${IMAGEM_BASE:-}'."; exit 1; }
[[ "$IMAGEM_BASE" == "${REGIAO:-}-docker.pkg.dev/"* ]] || { echo "IMAGEM_BASE fora da região '${REGIAO:-}'."; exit 1; }

docker build -t "$IMAGEM_BASE:$COMMIT_SHA" -t "$IMAGEM_BASE:latest" .
docker push "$IMAGEM_BASE:$COMMIT_SHA"
docker push "$IMAGEM_BASE:latest"
