"""Anotação das tabelas Gold no Knowledge Catalog (ADR 014, item 4.3) — sem rede."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.anotar_catalogo import ANOTACOES, OPERACIONAIS, anotar, corpo

RAIZ = Path(__file__).resolve().parents[2]
DOMINIOS_MD = (RAIZ / "docs" / "arquitetura" / "dominios-analiticos.md").read_text(encoding="utf-8")
ASPECTOS_TF = (RAIZ / "infra" / "modules" / "catalogo" / "aspectos.tf").read_text(encoding="utf-8")
GOLD_DEFINIDAS = {p.stem for p in (RAIZ / "definitions" / "gold").glob("*.sqlx")}

# Título da seção em dominios-analiticos.md → valor do enum `dominio` em aspectos.tf.
SECOES = {
    "Mercado de Energia": "mercado_de_energia",
    "Geração e Operacional": "geracao_e_operacional",
    "Meteorologia": "meteorologia",
    "Comercial e Contratos": "comercial_e_contratos",
    "CRM e Marketing": "crm_e_marketing",
    "Risco e Compliance": "risco_e_compliance",
    "Econômico": "economico",
    "Planejamento": "planejamento",
}


def _gold_por_dominio() -> dict[str, set[str]]:
    """As tabelas da linha **Gold hoje** de cada domínio, lidas do documento."""
    resultado: dict[str, set[str]] = {}
    for titulo, dominio in SECOES.items():
        secao = re.split(rf"### \d · {titulo}\n", DOMINIOS_MD, maxsplit=1)[1].split("\n### ", 1)[0]
        linha = re.search(r"\| \*\*Gold hoje\*\* \| (.*) \|", secao)
        resultado[dominio] = set(re.findall(r"`([a-z_]+)`", linha.group(1))) if linha else set()
    return resultado


def test_toda_gold_documentada_esta_anotada_com_um_dos_seus_dominios():
    """O documento é a fonte; a anotação só pode escolher entre os domínios em que ele lista a tabela."""
    dominios_de: dict[str, set[str]] = {}
    for dominio, tabelas in _gold_por_dominio().items():
        for tabela in tabelas:
            dominios_de.setdefault(tabela, set()).add(dominio)

    assert dominios_de, "nenhuma Gold encontrada em dominios-analiticos.md"
    assert set(dominios_de) == set(ANOTACOES)
    for tabela, dominios in dominios_de.items():
        assert ANOTACOES[tabela]["dominio"] in dominios, tabela


def test_toda_gold_do_dataform_e_anotada_ou_declarada_operacional():
    """Gold nova sem classificação falha aqui, e não em silêncio no catálogo."""
    assert set(ANOTACOES) | OPERACIONAIS == GOLD_DEFINIDAS
    assert not set(ANOTACOES) & OPERACIONAIS


def test_dominios_e_responsaveis_validos():
    enum = set(re.findall(r'\{ name = "([a-z_]+)", index = \d \}', ASPECTOS_TF.split('"dominio-analitico"', 1)[1]))
    assert enum
    for tabela, anotacao in ANOTACOES.items():
        assert anotacao["dominio"] in enum, tabela
        assert anotacao["responsavel"].strip(), tabela


def test_corpo_so_leva_os_dois_aspects_do_projeto():
    aspects = corpo("123", "us-central1", {"dominio": "economico", "responsavel": "Fulano"})["aspects"]

    assert set(aspects) == {"123.us-central1.origem", "123.us-central1.dominio-analitico"}
    assert aspects["123.us-central1.origem"]["data"]["origem"] == "curada"
    assert aspects["123.us-central1.dominio-analitico"]["data"] == {"dominio": "economico", "responsavel": "Fulano"}


class Resposta:
    def raise_for_status(self) -> None:
        return None


class SessaoFalsa:
    def __init__(self) -> None:
        self.chamadas: list[tuple[str, dict, dict]] = []

    def patch(self, url: str, params: dict, json: dict) -> Resposta:
        self.chamadas.append((url, params, json))
        return Resposta()


def test_anotar_atualiza_so_os_aspects_listados_de_cada_tabela():
    """`aspectKeys` limita a escrita: os aspects de sistema do BigQuery ficam intactos."""
    sessao = SessaoFalsa()

    total = anotar(
        sessao, "proj-x", "123", "us-central1", {"cambio_mensal": {"dominio": "economico", "responsavel": "F"}}
    )

    assert total == 1
    url, params, _ = sessao.chamadas[0]
    assert url.endswith(
        "projects/proj-x/locations/us-central1/entryGroups/@bigquery/entries/"
        "bigquery.googleapis.com/projects/proj-x/datasets/gold/tables/cambio_mensal"
    )
    assert params["updateMask"] == "aspects"
    assert set(params["aspectKeys"]) == {"123.us-central1.origem", "123.us-central1.dominio-analitico"}
