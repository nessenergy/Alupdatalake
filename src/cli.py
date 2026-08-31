"""CLI do AlupData.

O mesmo entrypoint roda no laptop, no Cloud Run Job e na DAG do Composer —
não existe caminho de código que só rode em produção.

    alupdata listar
    alupdata ingerir bcb_cambio_ptax --de 2026-01-01 --ate 2026-01-31
    alupdata ingerir bcb_cambio_ptax --ultimos-dias 7 --dry-run
"""

from __future__ import annotations

import argparse
import sys

from src.core.config import get_settings
from src.core.execucao import Janela
from src.core.observabilidade import configurar_logging
from src.core.registry import listar, obter

configurar_logging()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alupdata", description="Ingestão do DataLake AlupData")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("listar", help="lista os conectores registrados")

    ingerir = sub.add_parser("ingerir", help="executa a ingestão de uma fonte")
    ingerir.add_argument("conector", help="rótulo do conector (ver `alupdata listar`)")
    ingerir.add_argument("--de", help="início da janela (YYYY-MM-DD)")
    ingerir.add_argument("--ate", help="fim da janela (YYYY-MM-DD)")
    ingerir.add_argument("--ultimos-dias", type=int, help="janela terminando ontem")
    ingerir.add_argument("--dry-run", action="store_true", help="extrai e valida sem gravar")

    replay = sub.add_parser("reprocessar-raw", help="reprocessa um objeto raw já arquivado no GCS")
    replay.add_argument("conector", help="rótulo do conector dono do raw")
    replay.add_argument("--uri", required=True, help="objeto gs:// no layout raw canônico")
    replay.add_argument("--de", required=True, help="início da janela original (YYYY-MM-DD)")
    replay.add_argument("--ate", required=True, help="fim da janela original (YYYY-MM-DD)")
    return parser


def _janela(args: argparse.Namespace) -> Janela:
    if args.ultimos_dias:
        return Janela.ultimos_dias(args.ultimos_dias)
    if args.de and args.ate:
        return Janela.de_texto(args.de, args.ate)
    raise SystemExit("informe --de e --ate, ou --ultimos-dias")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.comando == "listar":
        for rotulo in listar():
            print(rotulo)
        return 0

    if args.comando == "reprocessar-raw":
        conector = obter(args.conector)
        execucao = conector.reprocessar_raw(args.uri, Janela.de_texto(args.de, args.ate))
        return 0 if execucao.status == "SUCESSO" else 1

    if args.dry_run:
        get_settings().dry_run = True

    conector = obter(args.conector)
    execucao = conector.ingerir(_janela(args))
    return 0 if execucao.status == "SUCESSO" else 1


if __name__ == "__main__":
    sys.exit(main())
