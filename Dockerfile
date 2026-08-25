# Imagem da CLI alupdata, executada como Cloud Run Job pelo Cloud Scheduler.
# O mesmo comando roda no laptop: `alupdata ingerir <conector> --de --ate`.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv

WORKDIR /app

# Dependências primeiro: mudança de código não invalida a camada de deps.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

ENTRYPOINT ["alupdata"]
CMD ["listar"]
