"""Confere os 7 componentes de cada fonte registrada (cláusula 2ª do contrato).

Para cada rótulo do registro de conectores, verifica que existem: a tabela Bronze, a view Silver, uma Gold que
cita a fonte, um teste, o agendamento e o dicionário de dados. O sétimo componente, o conector, é o próprio
registro. É verificação de **existência**, não de qualidade: a carga real é conferida por `Conferir cargas`.

Uso: `uv run python -m scripts.conferir_componentes` (sai com 1 se alguma fonte tiver falta).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _cita(rotulo: str, arquivos: list[Path]) -> bool:
    padrao = re.compile(rf"\b{re.escape(rotulo)}\b")
    return any(padrao.search(a.read_text(encoding="utf-8", errors="replace")) for a in arquivos)


def conferir(rotulos: list[str]) -> dict[str, list[str]]:
    """Devolve `{rótulo: [componentes que faltam]}`, só com os rótulos que têm falta."""
    gold = list((RAIZ / "definitions" / "gold").glob("*.sqlx"))
    testes = list((RAIZ / "tests" / "unit").rglob("*.py"))
    infra = list((RAIZ / "infra").rglob("*.tf"))
    dicionario = list((RAIZ / "docs" / "dicionario-dados").glob("*.md"))

    faltas: dict[str, list[str]] = {}
    for rotulo in rotulos:
        ausentes = []
        if not (RAIZ / "definitions" / "bronze" / f"{rotulo}.sqlx").is_file():
            ausentes.append("bronze")
        if not (RAIZ / "definitions" / "silver" / f"{rotulo}.sqlx").is_file():
            ausentes.append("silver")
        if not _cita(rotulo, gold):
            ausentes.append("gold")
        if not (any((RAIZ / "tests" / "unit").rglob(f"test_{rotulo}*.py")) or _cita(rotulo, testes)):
            ausentes.append("teste")
        if not _cita(rotulo, infra):
            ausentes.append("agendamento")
        if not ((RAIZ / "docs" / "dicionario-dados" / f"{rotulo}.md").is_file() or _cita(rotulo, dicionario)):
            ausentes.append("dicionario")
        if ausentes:
            faltas[rotulo] = ausentes
    return faltas


def principal(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analisador.add_argument("--rotulos", nargs="*", help="rótulos a conferir; sem isso, todo o registro")
    args = analisador.parse_args(argv)

    if args.rotulos:
        rotulos = list(args.rotulos)
    else:
        from src.core.registry import carregar_conectores, listar

        carregar_conectores()
        rotulos = listar()

    faltas = conferir(rotulos)
    print(f"{len(rotulos)} fontes conferidas; {len(rotulos) - len(faltas)} com todos os componentes de arquivo.")
    for rotulo, ausentes in sorted(faltas.items()):
        print(f"FALTA {rotulo}: {', '.join(ausentes)}")
    return 1 if faltas else 0


if __name__ == "__main__":
    sys.exit(principal())
