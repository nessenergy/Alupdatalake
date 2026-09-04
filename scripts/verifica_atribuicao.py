"""Recusa atribuição de autoria a ferramenta de IA em mensagem de commit.

O repositório é artefato do contrato CPS-01025/2026, cuja cláusula 7ª trata de
propriedade intelectual. Registrar co-autoria de terceiro no histórico cria
ambiguidade sobre titularidade. Ver regra 6 em `AGENTS.md`.

Três modos:

    verifica_atribuicao.py .git/COMMIT_EDITMSG   # arquivos (hook commit-msg)
    verifica_atribuicao.py --intervalo A..B      # commits de um range (CI)
    verifica_atribuicao.py --github dono/repo    # issues, PRs e comentários

O terceiro existe porque os dois primeiros só alcançam o histórico do git. O
contratante acompanha o projeto pelo GitHub, e comentário de issue é tão
visível quanto código — foi por essa fresta que passaram 15 rodapés de
ferramenta, removidos à mão em 04/09. Comentário não pode ser barrado antes de
ser publicado, então aqui o portão é detecção, não bloqueio.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

# Referências de caminho que existem de verdade no repositório e não são
# atribuição. São removidas antes da checagem: sem isso, todo texto que cita
# `.claude/skills/` ou `CLAUDE.md` viraria falso positivo — e monitor que grita
# à toa deixa de ser lido.
CAMINHOS_LEGITIMOS = re.compile(r"\.claude/[\w./-]*|\bCLAUDE\.md\b", re.IGNORECASE)

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
Texto recusado: menciona ferramenta de IA.

  {origem}
{trechos}
O histórico deste repositório é artefato contratual (CPS-01025/2026, cláusula
7ª). Não registre co-autoria, assinatura de ferramenta nem menção a IA em
commit, branch, issue, comentário ou corpo de PR. Regra 6 em AGENTS.md.

Reescreva o texto descrevendo o que mudou e por quê.
"""


def infracoes(texto: str) -> list[str]:
    """Linhas que violam a regra, ignorando comentários do git e caminhos reais."""
    achados = []
    for linha in texto.splitlines():
        if linha.lstrip().startswith("#"):
            continue
        if PADRAO.search(CAMINHOS_LEGITIMOS.sub("", linha)):
            achados.append(linha.strip())
    return achados


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


# ------------------------------------------------------------------- GitHub

# O que o contratante lê. `issues` traz também os PRs, porque a API do GitHub
# trata PR como issue; `pulls/comments` traz os comentários de revisão de
# código, que não aparecem em nenhum dos outros dois.
ENDPOINTS = (
    ("issues/comments", "comentário"),
    ("issues?state=all", "corpo"),
    ("pulls/comments", "comentário de revisão"),
)


def _buscar(repo: str, endpoint: str) -> list[dict]:
    """Coleta paginada via `gh`, que já resolve autenticação e paginação."""
    juncao = "&" if "?" in endpoint else "?"
    saida = subprocess.run(  # noqa: S603
        ["gh", "api", "--paginate", f"repos/{repo}/{endpoint}{juncao}per_page=100"],  # noqa: S607
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout
    # `--paginate` concatena arrays JSON; normalizamos para uma lista só.
    itens: list[dict] = []
    for pedaco in re.split(r"(?<=\])\s*(?=\[)", saida.strip()):
        if pedaco:
            itens.extend(json.loads(pedaco))
    return itens


def verificar_github(repo: str, buscador: Callable[[str, str], list[dict]] = _buscar) -> int:
    """Varre issues, PRs e comentários do repositório publicados no GitHub.

    Comentário não passa por hook nem por CI de PR: quando é publicado, já está
    visível. Por isso aqui não há como bloquear — o que existe é detectar e
    falhar alto, para que a limpeza seja uma correção pontual e não uma
    arqueologia.
    """
    problemas = 0
    for endpoint, rotulo in ENDPOINTS:
        for item in buscador(repo, endpoint):
            achados = infracoes(item.get("body") or "")
            if achados:
                _reportar(f"{rotulo} {item.get('html_url', item.get('id', '?'))}", achados)
                problemas += 1
    return problemas


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--intervalo":
        return 1 if verificar_intervalo(argv[1]) else 0
    if argv and argv[0] == "--github":
        achados = verificar_github(argv[1])
        if achados:
            print(file=sys.stderr)
            print(
                f"{achados} item(ns) publicados no GitHub mencionam ferramenta.",
                file=sys.stderr,
            )
            return 1
        print("GitHub limpo: nenhuma issue, PR ou comentário menciona ferramenta.")
        return 0
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
