"""Cria os campos de acompanhamento semanal no GitHub Projects (Projects V2).

Os cinco campos existem para que uma semana sem reunião ainda produza um
relatório: quanto se gastou, em que semana, se a Alup validou, se houve
retrabalho e se algo atrasou. Cada um tem efeito na medição ou na cláusula 3ª
do contrato — ver `docs/runbook/acompanhamento-semanal.md`.

Idempotente: campo que já existe é deixado como está. Rodar duas vezes é
inofensivo, e o script nunca apaga nem renomeia campo.

    export GITHUB_TOKEN=<PAT classico com escopo `project`>
    uv run python -m scripts.campos_projeto --owner nessenergy --listar
    uv run python -m scripts.campos_projeto --owner nessenergy --numero 1 --dry-run
    uv run python -m scripts.campos_projeto --owner nessenergy --numero 1

Projects V2 só tem API GraphQL — não existe endpoint REST equivalente.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any

import requests

logger = logging.getLogger("campos-projeto")
API = "https://api.github.com/graphql"
TIMEOUT = 30

# As semanas do contrato (19 semanas, S1..S19) já são o vocabulário do plano de
# execução e do plano semanal. Reaproveitar a mesma nomenclatura evita ter de
# traduzir o quadro para o relatório.
SEMANAS = [f"S{n}" for n in range(1, 20)]

# `dataType` aceito por createProjectV2Field: TEXT, NUMBER, DATE, SINGLE_SELECT.
# ITERATION não é criável por API — só pela interface. Não existe tipo booleano
# nem checkbox em Projects V2; por isso os três indicadores são SINGLE_SELECT.
CAMPOS: list[dict[str, Any]] = [
    {
        "nome": "Horas",
        "tipo": "NUMBER",
        "porque": "horas gastas no item; é a base da medição por onda",
    },
    {
        "nome": "Semana",
        "tipo": "SINGLE_SELECT",
        "porque": "período de desenvolvimento, na nomenclatura S1..S19 do plano",
        "opcoes": [{"name": s, "color": "BLUE", "description": ""} for s in SEMANAS],
    },
    {
        "nome": "Validado",
        "tipo": "SINGLE_SELECT",
        "porque": "entrega marcada como Done já conferida por alguém da Alup",
        "opcoes": [
            {"name": "Sim", "color": "GREEN", "description": "conferido pela Alup"},
            {"name": "Não", "color": "GRAY", "description": "entregue, ainda não conferido"},
        ],
    },
    {
        "nome": "Correções",
        "tipo": "SINGLE_SELECT",
        "porque": "item refeito; separa entrega nova de retrabalho na contagem de horas",
        "opcoes": [
            {"name": "Sim", "color": "ORANGE", "description": "retrabalho sobre item já entregue"},
            {"name": "Não", "color": "GRAY", "description": "primeira execução"},
        ],
    },
    {
        "nome": "Atraso",
        "tipo": "SINGLE_SELECT",
        "porque": "sinaliza o que passou do prazo; alimenta o registro da cláusula 3ª",
        "opcoes": [
            {"name": "Sim", "color": "RED", "description": "passou do prazo acordado"},
            {"name": "Não", "color": "GREEN", "description": "dentro do prazo"},
        ],
    },
]

CONSULTA_PROJETOS = """
query($login: String!) {
  organization(login: $login) { projectsV2(first: 20) { nodes { number title } } }
  user(login: $login)         { projectsV2(first: 20) { nodes { number title } } }
}
"""

CONSULTA_CAMPOS = """
query($login: String!, $numero: Int!) {
  organization(login: $login) {
    projectV2(number: $numero) {
      id title
      fields(first: 50) { nodes { ... on ProjectV2FieldCommon { id name dataType } } }
    }
  }
  user(login: $login) {
    projectV2(number: $numero) {
      id title
      fields(first: 50) { nodes { ... on ProjectV2FieldCommon { id name dataType } } }
    }
  }
}
"""

MUTACAO_CAMPO = """
mutation($projeto: ID!, $nome: String!, $tipo: ProjectV2CustomFieldType!,
         $opcoes: [ProjectV2SingleSelectFieldOptionInput!]) {
  createProjectV2Field(input: {
    projectId: $projeto, name: $nome, dataType: $tipo, singleSelectOptions: $opcoes
  }) { projectV2Field { ... on ProjectV2FieldCommon { id name dataType } } }
}
"""


class GraphQLError(RuntimeError):
    """A API respondeu, mas com erro no corpo — o status HTTP não basta."""


def token() -> str:
    """PAT com escopo `project`. Sem ele não há como falar com Projects V2."""
    valor = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not valor:
        raise SystemExit("defina GITHUB_TOKEN (PAT clássico com escopo `project`)")
    return valor


def consultar(query: str, variaveis: dict[str, Any]) -> dict[str, Any]:
    """Executa uma operação GraphQL e devolve `data`, ou levanta com o erro."""
    resposta = requests.post(
        API,
        json={"query": query, "variables": variaveis},
        headers={"Authorization": f"bearer {token()}", "Content-Type": "application/json"},
        timeout=TIMEOUT,
    )
    resposta.raise_for_status()
    corpo = resposta.json()
    # Erro de permissão sobre um dos dois caminhos (org/user) é esperado: só um
    # deles existe. Só falha se `data` não trouxer nada aproveitável.
    if corpo.get("errors") and not corpo.get("data"):
        raise GraphQLError(json.dumps(corpo["errors"], ensure_ascii=False))
    return corpo.get("data") or {}


def projeto_de(dados: dict[str, Any], chave: str) -> dict[str, Any] | None:
    """O projeto vem sob `organization` ou sob `user`; um dos dois é nulo."""
    for dono in ("organization", "user"):
        no = (dados.get(dono) or {}).get(chave)
        if no:
            return no
    return None


def listar(login: str) -> int:
    """Imprime número e título dos projetos do dono, para achar o --numero."""
    dados = consultar(CONSULTA_PROJETOS, {"login": login})
    achou = False
    for dono in ("organization", "user"):
        for no in ((dados.get(dono) or {}).get("projectsV2") or {}).get("nodes") or []:
            logger.info("#%s  %s", no["number"], no["title"])
            achou = True
    if not achou:
        logger.warning("nenhum projeto visível para %s — confira o escopo `project` do token", login)
        return 1
    return 0


def aplicar(login: str, numero: int, *, dry_run: bool) -> int:
    dados = consultar(CONSULTA_CAMPOS, {"login": login, "numero": numero})
    projeto = projeto_de(dados, "projectV2")
    if not projeto:
        logger.error("projeto #%s não encontrado em %s", numero, login)
        return 1

    existentes = {no["name"] for no in projeto["fields"]["nodes"] if no}
    logger.info("projeto %r (#%s) — %d campos hoje", projeto["title"], numero, len(existentes))

    criados = 0
    for campo in CAMPOS:
        nome = campo["nome"]
        if nome in existentes:
            logger.info("já existe, mantido: %s", nome)
            continue
        if dry_run:
            logger.info("[dry-run] criaria %s (%s) — %s", nome, campo["tipo"], campo["porque"])
            criados += 1
            continue
        consultar(
            MUTACAO_CAMPO,
            {
                "projeto": projeto["id"],
                "nome": nome,
                "tipo": campo["tipo"],
                # A API recusa `singleSelectOptions` em campo que não é seleção.
                "opcoes": campo.get("opcoes") if campo["tipo"] == "SINGLE_SELECT" else None,
            },
        )
        logger.info("criado: %s (%s)", nome, campo["tipo"])
        criados += 1

    logger.info("%d campo(s) %s; %d já existiam", criados, "a criar" if dry_run else "criados", len(CAMPOS) - criados)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cria os campos de acompanhamento semanal no GitHub Projects")
    parser.add_argument("--owner", required=True, help="organização ou usuário dono do projeto")
    parser.add_argument("--numero", type=int, help="número do projeto (veja com --listar)")
    parser.add_argument("--listar", action="store_true", help="lista os projetos do dono e sai")
    parser.add_argument("--dry-run", action="store_true", help="mostra o que faria, sem criar nada")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.listar:
        return listar(args.owner)
    if args.numero is None:
        parser.error("informe --numero (ou use --listar para descobri-lo)")
    return aplicar(args.owner, args.numero, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
