"""Aplica o SQL versionado de `sql/` no BigQuery.

Idempotente: Bronze usa CREATE TABLE IF NOT EXISTS, Silver/Gold usam
CREATE OR REPLACE VIEW. Rodar duas vezes é inofensivo.

    uv run python -m scripts.deploy_views --camadas bronze silver gold
    uv run python -m scripts.deploy_views --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from string import Template

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger("deploy-views")
RAIZ_SQL = Path(__file__).resolve().parents[1] / "sql"
CAMADAS = ("bronze", "silver", "gold")  # ordem importa: view depende da tabela


def arquivos(camadas: list[str]) -> list[Path]:
    """SQL de cada camada, em ordem alfabética dentro da camada."""
    return [caminho for camada in camadas for caminho in sorted((RAIZ_SQL / camada).glob("*.sql"))]


def renderizar(caminho: Path) -> str:
    """Substitui ${projeto}/${bronze}/${silver}/${gold} pela configuração."""
    cfg = get_settings()
    return Template(caminho.read_text(encoding="utf-8")).substitute(
        projeto=cfg.gcp_project_id,
        bronze=cfg.bq_dataset_bronze,
        silver=cfg.bq_dataset_silver,
        gold=cfg.bq_dataset_gold,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aplica o SQL de sql/ no BigQuery")
    parser.add_argument("--camadas", nargs="+", choices=CAMADAS, default=list(CAMADAS))
    parser.add_argument("--dry-run", action="store_true", help="imprime o SQL sem executar")
    args = parser.parse_args(argv)

    alvos = arquivos(args.camadas)
    if not alvos:
        logger.warning("nenhum arquivo .sql encontrado em %s", args.camadas)
        return 0

    cliente = None
    if not args.dry_run:
        from google.cloud import bigquery

        cliente = bigquery.Client(project=get_settings().gcp_project_id)

    for caminho in alvos:
        sql = renderizar(caminho)
        rotulo = f"{caminho.parent.name}/{caminho.name}"
        if args.dry_run:
            logger.info("[dry-run] %s\n%s", rotulo, sql)
            continue
        cliente.query(sql).result()
        logger.info("aplicado: %s", rotulo)

    return 0


if __name__ == "__main__":
    sys.exit(main())
