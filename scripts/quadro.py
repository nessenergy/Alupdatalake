"""Sincroniza o quadro de acompanhamento (Project 2) com o estado do repositório.

O quadro é o que a Alup acompanha. Este comando mantém nele o que se deduz sem
opinião: onda e responsável de cada item (do mapa em `quadro.toml`), Done e
semana de conclusão para o que foi fechado, e atraso para o que venceu. Decisão
humana — horas, validação da Alup, correção marcada como Sim, atraso já
registrado — nunca é sobrescrita.

Por padrão só simula. Gravar exige `--aplicar`, porque cada gravação e cada
comentário de atraso ficam visíveis para a contratante.

    export GITHUB_TOKEN=$(gh auth token)      # PAT com escopo `project`
    uv run python -m scripts.quadro            # simula
    uv run python -m scripts.quadro --aplicar  # grava e comenta os atrasos novos

Semântica dos campos em `docs/runbook/acompanhamento-semanal.md`.
"""

from __future__ import annotations

import argparse
import logging
import sys
import tomllib
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.campos_projeto import consultar
from scripts.verifica_atribuicao import infracoes

logger = logging.getLogger("quadro")
CONFIG = Path(__file__).with_name("quadro.toml")

# Brasília não tem horário de verão desde 2019: um fuso fixo evita depender do
# pacote tzdata, que não acompanha o Python no Windows.
BRASILIA = timezone(timedelta(hours=-3))

# Valor que só uma pessoa decide. Uma vez registrado, o comando não o desfaz.
DECISAO_HUMANA = {"Validado": "Sim", "Correções": "Sim", "Atraso": "Sim"}
# Campos que o comando só preenche quando estão vazios.
SO_SE_VAZIO = {"Semana", "Correções", "Validado"}

CONSULTA = """
query($login: String!, $numero: Int!, $cursor: String) {
  organization(login: $login) {
    projectV2(number: $numero) {
      id
      fields(first: 50) { nodes { ... on ProjectV2SingleSelectField { id name options { id name } } } }
      items(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          content {
            __typename
            ... on Issue { id number closedAt }
            ... on PullRequest { id number mergedAt }
          }
          fieldValues(first: 30) {
            nodes { ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } } }
          }
        }
      }
    }
  }
}
"""

MUTACAO_VALOR = """
mutation($projeto: ID!, $item: ID!, $campo: ID!, $opcao: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projeto, itemId: $item, fieldId: $campo, value: { singleSelectOptionId: $opcao }
  }) { projectV2Item { id } }
}
"""

MUTACAO_COMENTARIO = """
mutation($assunto: ID!, $corpo: String!) {
  addComment(input: { subjectId: $assunto, body: $corpo }) { commentEdge { node { url } } }
}
"""


# ------------------------------------------------------------ configuração


@dataclass(frozen=True)
class Config:
    dono: str
    numero: int
    inicio_s1: date
    onda_de: dict[int, str]
    alup: frozenset[int]
    vencimentos: dict[int, date]
    feriados: frozenset[date]


def carregar_config(caminho: Path = CONFIG) -> Config:
    """Lê o mapa do quadro. Recusa issue classificada em duas ondas."""
    dados = tomllib.loads(caminho.read_text(encoding="utf-8"))
    onda_de: dict[int, str] = {}
    for onda, numeros in dados["ondas"].items():
        for numero in numeros:
            if numero in onda_de:
                raise ValueError(f"#{numero} aparece em {onda_de[numero]} e em {onda}")
            onda_de[numero] = onda
    return Config(
        dono=dados["dono"],
        numero=dados["numero"],
        inicio_s1=dados["inicio_s1"],
        onda_de=onda_de,
        alup=frozenset(dados["alup"]),
        vencimentos={int(numero): dia for numero, dia in dados["vencimentos"].items()},
        feriados=frozenset(dados["feriados"]),
    )


# -------------------------------------------------------------- calendário


def semana(data: date, inicio_s1: date) -> str:
    """S1 a S19 do plano. O que foi concluído antes da S1 conta como S1."""
    indice = (data - inicio_s1).days // 7 + 1
    return f"S{min(max(indice, 1), 19)}"


def primeiro_dia_util_de_atraso(vencimento: date, feriados: frozenset[date]) -> date:
    """Primeiro dia útil depois do vencimento — é daí que a cláusula 3ª conta."""
    dia = vencimento + timedelta(days=1)
    while dia.weekday() >= 5 or dia in feriados:
        dia += timedelta(days=1)
    return dia


# ------------------------------------------------------------------ regras


@dataclass(frozen=True)
class Item:
    id: str
    conteudo_id: str
    numero: int
    tipo: str
    concluido_em: date | None
    valores: dict[str, str]


def desejado(item: Item, cfg: Config, hoje: date) -> dict[str, str]:
    """Valor de cada campo que se deduz do repositório, sem opinião."""
    alvo = {"Responsável": "Alup" if item.numero in cfg.alup else "ness."}
    if item.numero in cfg.onda_de:
        alvo["Onda"] = cfg.onda_de[item.numero]
    if item.concluido_em:
        alvo |= {
            "Status": "Done",
            "Semana": semana(item.concluido_em, cfg.inicio_s1),
            "Correções": "Não",
            "Validado": "Não",
        }
    if item.tipo == "Issue":
        vencimento = cfg.vencimentos.get(item.numero)
        atrasado = (
            vencimento is not None
            and item.concluido_em is None
            and hoje >= primeiro_dia_util_de_atraso(vencimento, cfg.feriados)
        )
        alvo["Atraso"] = "Sim" if atrasado else "Não"
    return alvo


def mudancas(item: Item, alvo: dict[str, str]) -> dict[str, str]:
    """O que gravar: só o que difere, sem desfazer decisão humana."""
    saida = {}
    for campo, valor in alvo.items():
        atual = item.valores.get(campo)
        if atual == valor or (campo in DECISAO_HUMANA and DECISAO_HUMANA[campo] == atual):
            continue
        if campo in SO_SE_VAZIO and atual:
            continue
        saida[campo] = valor
    return saida


def comentario_de_atraso(vencimento: date, hoje: date, feriados: frozenset[date]) -> str:
    """Registro datado do atraso, em tom de correspondência: a Alup lê."""
    primeiro = primeiro_dia_util_de_atraso(vencimento, feriados)
    return (
        f"Registro de {hoje:%d/%m/%Y}: o prazo útil deste item venceu em {vencimento:%d/%m/%Y}. "
        f"O atraso conta a partir de {primeiro:%d/%m/%Y}, primeiro dia útil após o vencimento, "
        "conforme a cláusula 3ª. Seguimos à disposição para o que for necessário."
    )


# --------------------------------------------------------------- GitHub


def _data(valor: str | None) -> date | None:
    if not valor:
        return None
    return datetime.fromisoformat(valor).astimezone(BRASILIA).date()


def ler_quadro(cfg: Config) -> tuple[str, dict[str, dict[str, Any]], list[Item]]:
    """Projeto, campos de seleção (nome -> id e opções) e itens, página a página."""
    campos: dict[str, dict[str, Any]] = {}
    itens: list[Item] = []
    cursor = None
    while True:
        projeto = consultar(CONSULTA, {"login": cfg.dono, "numero": cfg.numero, "cursor": cursor})["organization"][
            "projectV2"
        ]
        for campo in projeto["fields"]["nodes"]:
            if campo:  # campo que não é de seleção chega como nó vazio
                campos[campo["name"]] = {"id": campo["id"], "opcoes": {o["name"]: o["id"] for o in campo["options"]}}
        for no in projeto["items"]["nodes"]:
            conteudo = no.get("content") or {}
            tipo = conteudo.get("__typename")
            if tipo not in ("Issue", "PullRequest"):
                continue  # rascunho não tem número nem conclusão
            itens.append(
                Item(
                    id=no["id"],
                    conteudo_id=conteudo["id"],
                    numero=conteudo["number"],
                    tipo=tipo,
                    concluido_em=_data(conteudo.get("closedAt") if tipo == "Issue" else conteudo.get("mergedAt")),
                    valores={v["field"]["name"]: v["name"] for v in no["fieldValues"]["nodes"] if v},
                )
            )
        pagina = projeto["items"]["pageInfo"]
        if not pagina["hasNextPage"]:
            return projeto["id"], campos, itens
        cursor = pagina["endCursor"]


def sincronizar(cfg: Config, hoje: date, *, aplicar: bool) -> int:
    projeto_id, campos, itens = ler_quadro(cfg)
    total = 0
    for item in sorted(itens, key=lambda i: i.numero):
        mudou = mudancas(item, desejado(item, cfg, hoje))
        rotulo = "PR" if item.tipo == "PullRequest" else "issue"
        for campo, valor in mudou.items():
            logger.info("%s #%s: %s %s -> %s", rotulo, item.numero, campo, item.valores.get(campo) or "(vazio)", valor)
            if aplicar:
                consultar(
                    MUTACAO_VALOR,
                    {
                        "projeto": projeto_id,
                        "item": item.id,
                        "campo": campos[campo]["id"],
                        "opcao": campos[campo]["opcoes"][valor],
                    },
                )
        total += len(mudou)
        if mudou.get("Atraso") == "Sim":
            texto = comentario_de_atraso(cfg.vencimentos[item.numero], hoje, cfg.feriados)
            # Regra 6: comentário publicado não se desfaz, então a checagem vem antes.
            if infracoes(texto):
                raise RuntimeError(f"comentário de atraso recusado pela regra 6: {texto}")
            logger.info("%s #%s: comentário de atraso: %s", rotulo, item.numero, texto)
            if aplicar:
                consultar(MUTACAO_COMENTARIO, {"assunto": item.conteudo_id, "corpo": texto})

    sem_onda = sorted(i.numero for i in itens if i.numero not in cfg.onda_de)
    if sem_onda:
        logger.warning("sem onda em quadro.toml: %s", ", ".join(f"#{n}" for n in sem_onda))
    logger.info("%d mudança(s) %s", total, "gravada(s)" if aplicar else "a gravar; rode com --aplicar para gravar")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sincroniza o quadro de acompanhamento com o repositório")
    parser.add_argument(
        "--aplicar", action="store_true", help="grava no quadro e comenta os atrasos novos; sem ele, só simula"
    )
    parser.add_argument(
        "--hoje", type=date.fromisoformat, help="data de referência AAAA-MM-DD (padrão: hoje, em Brasília)"
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    hoje = args.hoje or datetime.now(BRASILIA).date()
    return sincronizar(carregar_config(), hoje, aplicar=args.aplicar)


if __name__ == "__main__":
    sys.exit(main())
