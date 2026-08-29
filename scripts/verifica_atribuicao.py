"""Recusa atribuição de autoria a ferramenta de IA em mensagem de commit.

O repositório é artefato do contrato CPS-01025/2026, cuja cláusula 7ª trata de
propriedade intelectual. Registrar co-autoria de terceiro no histórico cria
ambiguidade sobre titularidade. Ver regra 6 em `AGENTS.md`.

Dois modos:

    verifica_atribuicao.py .git/COMMIT_EDITMSG   # arquivos (hook commit-msg)
    verifica_atribuicao.py --intervalo A..B      # commits de um range (CI)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Cobre o trailer de co-autoria, assinaturas de ferramenta e menção direta.
PADRAO = re.compile(
    r"co-authored-by:\s*(claude|.*anthropic)"
    r"|generated with .*claude"
    r"|\bclaude(\.ai|\s+code|\s+opus|\s+sonnet|\s+haiku)?\b"
    r"|\banthropic\b"
    r"|🤖",
    re.IGNORECASE,
)

AVISO = """
Mensagem de commit recusada: menciona ferramenta de IA.

  {origem}
{trechos}
O histórico deste repositório é artefato contratual (CPS-01025/2026, cláusula
7ª). Não registre co-autoria, assinatura de ferramenta nem menção a IA em
commit, branch ou corpo de PR. Regra 6 em AGENTS.md.

Reescreva a mensagem descrevendo o que mudou e por quê.
"""


def infracoes(texto: str) -> list[str]:
    """Linhas da mensagem que violam a regra, ignorando comentários do git."""
    return [
        linha.strip()
        for linha in texto.splitlines()
        if not linha.lstrip().startswith("#") and PADRAO.search(linha)
    ]


def _reportar(origem: str, achados: list[str]) -> None:
    trechos = "".join(f"    → {linha}\n" for linha in achados)
    print(AVISO.format(origem=origem, trechos=trechos), file=sys.stderr)


def verificar_arquivos(caminhos: list[str]) -> int:
    problemas = 0
    for caminho in caminhos:
        achados = infracoes(Path(caminho).read_text(encoding="utf-8"))
        if achados:
            _reportar(caminho, achados)
            problemas += 1
    return problemas


def verificar_intervalo(intervalo: str) -> int:
    """Confere as mensagens de todos os commits de `intervalo` (ex.: main..HEAD)."""
    shas = subprocess.run(  # noqa: S603
        ["git", "rev-list", intervalo],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    problemas = 0
    for sha in shas:
        msg = subprocess.run(  # noqa: S603
            ["git", "log", "-1", "--format=%B", sha],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        achados = infracoes(msg)
        if achados:
            _reportar(f"commit {sha[:8]}", achados)
            problemas += 1
    return problemas


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--intervalo":
        return 1 if verificar_intervalo(argv[1]) else 0
    return 1 if verificar_arquivos(argv) else 0


def demo() -> None:
    """Auto-verificação: `python scripts/verifica_atribuicao.py --demo`."""
    reprovar = [
        "fix: algo\n\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>",
        "docs: x\n\n🤖 Generated with Claude Code",
        "feat: escrito com ajuda da Anthropic",
        "chore: ver claude.ai",
    ]
    aprovar = [
        "fix: conserta a janela de ingestão do conector ONS",
        "docs: datar o cronograma das cinco ondas",
        # 'clausula' e 'inclui' contêm 'cla'/'clau' — não podem casar.
        "docs: cláusula 7ª no resumo; inclui o rateio entre coligadas",
        # Linha de comentário do git é ignorada.
        "fix: algo\n# Co-Authored-By: Claude <x@anthropic.com>",
    ]
    for msg in reprovar:
        assert infracoes(msg), f"deveria reprovar: {msg!r}"
    for msg in aprovar:
        assert not infracoes(msg), f"deveria aprovar: {msg!r}"
    print(f"ok — {len(reprovar)} reprovadas, {len(aprovar)} aprovadas")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        sys.exit(main(sys.argv[1:]))
