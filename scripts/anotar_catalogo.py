"""Anota as tabelas Gold no Knowledge Catalog com domínio, responsável e origem.

ADR 014, item 4.3. Os *aspect types* `origem` e `dominio-analitico` são
estrutura e vivem em `infra/modules/catalogo/aspectos.tf`; este script escreve o
**conteúdo** nas entradas que o BigQuery já mantém no grupo `@bigquery`.

Por que script e não `google_dataplex_entry`: no provider travado (6.50), o
recurso exige importar cada entrada de sistema e atualiza com
`deleteMissingAspects=true`, o que tentaria apagar os aspects que o próprio
BigQuery mantém. Aqui o `PATCH` leva `aspectKeys` com só os dois aspects do
projeto: o resto da entrada não é tocado. Idempotente; roda no deploy, depois
do Dataform, com a conta de deploy (ADR 015).

    uv run python -m scripts.anotar_catalogo --projeto <id> --regiao <regiao>

O mapa vem de `docs/arquitetura/dominios-analiticos.md` (domínio e data owner)
e `tests/unit/test_anotar_catalogo.py` reprova divergência entre os dois.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

from src.core.observabilidade import configurar_logging
from src.core.seguranca import sanitizar

configurar_logging()
logger = logging.getLogger("anotar-catalogo")

API = "https://dataplex.googleapis.com/v1"
DATASET = "gold"

# Data da última revisão humana deste mapa. Não é a data do deploy: o aspect
# `origem` diz quando uma pessoa conferiu, e reescrever a cada deploy mentiria.
REVISADA_EM = "2026-09-26T00:00:00Z"

INTELIGENCIA = "Taina Mota · Inteligência de Mercado"
TRADING = "Gabriel Barreto · Trading"
PORTFOLIO = "Letícia Ferreira · Gestão de Portfólio e Back-Office"
COMERCIAL = "Tahigo Santos · Comercial"

ANOTACOES: dict[str, dict[str, str]] = {
    # 1 · Mercado de Energia
    "pld_mensal_submercado": {"dominio": "mercado_de_energia", "responsavel": INTELIGENCIA},
    "carga_mensal_submercado": {"dominio": "mercado_de_energia", "responsavel": INTELIGENCIA},
    "mercado_mensal_submercado": {"dominio": "mercado_de_energia", "responsavel": INTELIGENCIA},
    "armazenamento_e_afluencia_mensal": {"dominio": "mercado_de_energia", "responsavel": INTELIGENCIA},
    "curva_forward_vigente": {"dominio": "mercado_de_energia", "responsavel": TRADING},  # BBCE e prêmio
    "agentes_ccee": {"dominio": "mercado_de_energia", "responsavel": INTELIGENCIA},
    "agentes_por_classe_mensal": {"dominio": "mercado_de_energia", "responsavel": INTELIGENCIA},
    "encargos_setoriais_mensal": {"dominio": "mercado_de_energia", "responsavel": INTELIGENCIA},
    "cvu_estrutural_vigente_usina": {"dominio": "mercado_de_energia", "responsavel": INTELIGENCIA},
    # 2 · Geração e Operacional — usinas do SIN, dado público
    "parque_gerador": {"dominio": "geracao_e_operacional", "responsavel": INTELIGENCIA},
    "geracao_mensal_usina": {"dominio": "geracao_e_operacional", "responsavel": INTELIGENCIA},
    "geracao_mensal_usina_ons": {"dominio": "geracao_e_operacional", "responsavel": INTELIGENCIA},
    "capacidade_instalada_vigente_usina": {"dominio": "geracao_e_operacional", "responsavel": INTELIGENCIA},
    "disponibilidade_mensal_usina": {"dominio": "geracao_e_operacional", "responsavel": INTELIGENCIA},
    "restricao_coff_mensal_usina": {"dominio": "geracao_e_operacional", "responsavel": INTELIGENCIA},
    "de_para_usina": {"dominio": "geracao_e_operacional", "responsavel": INTELIGENCIA},
    # 3 · Meteorologia
    "cobertura_boletins_tempook": {"dominio": "meteorologia", "responsavel": INTELIGENCIA},
    "cobertura_ena_prevs_tempook": {"dominio": "meteorologia", "responsavel": INTELIGENCIA},
    # 4 · Comercial e Contratos
    "posicao_contratual_mensal_perfil": {"dominio": "comercial_e_contratos", "responsavel": PORTFOLIO},
    "consumo_varejista_mensal_uf": {"dominio": "comercial_e_contratos", "responsavel": COMERCIAL},  # varejo
    # 5 · CRM e Marketing — o documento lista o funil também em Comercial; o
    # aspect aceita um domínio só, e funil de negócio é CRM. O dono é o mesmo.
    "funil_comercial": {"dominio": "crm_e_marketing", "responsavel": COMERCIAL},
    # 6 · Risco e Compliance
    "exposicao_mercado_mensal": {"dominio": "risco_e_compliance", "responsavel": PORTFOLIO},
    "resultado_contabilizacao_mensal_perfil": {"dominio": "risco_e_compliance", "responsavel": PORTFOLIO},
    # 7 · Econômico
    "cambio_mensal": {"dominio": "economico", "responsavel": PORTFOLIO},
    "juros_mensal": {"dominio": "economico", "responsavel": PORTFOLIO},
    "inflacao_mensal": {"dominio": "economico", "responsavel": PORTFOLIO},
}

# Gold de operação da plataforma, não de negócio: fica fora dos domínios do B1.
OPERACIONAIS = {"custo_consultas", "saude_ingestao", "volumetria_lake"}


def _chaves(numero: str, regiao: str) -> tuple[str, str]:
    return f"{numero}.{regiao}.origem", f"{numero}.{regiao}.dominio-analitico"


def corpo(numero: str, regiao: str, anotacao: dict[str, str]) -> dict[str, Any]:
    """Corpo do `PATCH`: só os dois aspects do projeto."""
    origem, dominio = _chaves(numero, regiao)
    return {
        "aspects": {
            origem: {"data": {"origem": "curada", "revisada_em": REVISADA_EM}},
            dominio: {"data": {"dominio": anotacao["dominio"], "responsavel": anotacao["responsavel"]}},
        }
    }


def anotar(sessao: Any, projeto: str, numero: str, regiao: str, anotacoes: dict[str, dict[str, str]]) -> int:
    """Grava os aspects em cada tabela Gold; devolve quantas foram anotadas."""
    chaves = list(_chaves(numero, regiao))
    for tabela, anotacao in anotacoes.items():
        entrada = (
            f"projects/{projeto}/locations/{regiao}/entryGroups/@bigquery/entries/"
            f"bigquery.googleapis.com/projects/{projeto}/datasets/{DATASET}/tables/{tabela}"
        )
        resposta = sessao.patch(
            f"{API}/{entrada}",
            params={"updateMask": "aspects", "aspectKeys": chaves},
            json=corpo(numero, regiao, anotacao),
        )
        try:
            resposta.raise_for_status()
        except Exception:
            logger.error("falha ao anotar %s: %s", tabela, sanitizar(str(getattr(resposta, "text", ""))))
            raise
        logger.info("anotada: %s (%s)", tabela, anotacao["dominio"])
    return len(anotacoes)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - E/S
    parser = argparse.ArgumentParser(description="Anota as tabelas Gold no Knowledge Catalog")
    parser.add_argument("--projeto", required=True, help="ID do projeto GCP")
    parser.add_argument("--regiao", required=True, help="região do dataset gold")
    args = parser.parse_args(argv)

    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    credenciais, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    sessao = AuthorizedSession(credenciais)
    # A chave do aspect usa o número do projeto, não o ID.
    resposta = sessao.get(f"https://cloudresourcemanager.googleapis.com/v3/projects/{args.projeto}")
    resposta.raise_for_status()
    numero = resposta.json()["name"].split("/")[-1]

    total = anotar(sessao, args.projeto, numero, args.regiao, ANOTACOES)
    logger.info("%d tabelas Gold anotadas em %s", total, args.projeto)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
