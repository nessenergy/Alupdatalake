# Painel vivo (docs/planos/2026-09-25-painel-vivo.md): só o servidor. A página e
# o dados.json vêm do bucket do painel, montado no Cloud Run.
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
