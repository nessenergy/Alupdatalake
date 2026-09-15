"""Conector CCEE — exposição financeira do mercado, por mês (Onda 1, público). Ordem 2 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `exposicao_financeira_mensal`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/exposicao_financeira_mensal

Uma linha por mês, valores do mercado inteiro em R$. É a "exposição" que o B1
nomeia em Risco e Compliance — e a menor fonte do lake: 968 bytes em 2026.
Sem agente, sem submercado; o que ela responde é quanto o MCP ficou exposto
e quanto disso foi coberto.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from src.conectores.ccee_ckan import CceeCsvCkan, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar

# Coluna da origem → coluna do lake. A ordem é a do arquivo.
CAMPOS = {
    "EXCEDENTE_FINANCEIRO": "excedente_financeiro",
    "EXCEDENTE_FINANCEIRO_POSITIVO": "excedente_financeiro_positivo",
    "TOTAL_RECURSO_DISPONIVEL": "total_recurso_disponivel",
    "TOTAL_EXPOSICAO_NEGATIVA": "total_exposicao_negativa",
    "COBERTURA_EXPOSICAO_NEGATIVA": "cobertura_exposicao_negativa",
    "TOTAL_EXPOSICAO_NEGATIVA_REM": "total_exposicao_negativa_remanescente",
    "TOTAL_EXPOSICAO_NEGATIVA_LIQ": "total_exposicao_negativa_liquidada",
    "TOTAL_RECURSO_DISPONIVEL_EF_ANT": "total_recurso_disponivel_ef_anterior",
    "TOTAL_RECURSO_COMPENSACAO_EF_N": "total_recurso_compensacao_ef",
    "RESERVA_ALIVIO_ESS": "reserva_alivio_ess",
}


class ExposicaoFinanceira(BaseModel):
    """A exposição financeira do MCP em um mês, em R$."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    excedente_financeiro: Decimal | None = None
    excedente_financeiro_positivo: Decimal | None = None
    total_recurso_disponivel: Decimal | None = None
    total_exposicao_negativa: Decimal | None = None
    cobertura_exposicao_negativa: Decimal | None = None
    total_exposicao_negativa_remanescente: Decimal | None = None
    total_exposicao_negativa_liquidada: Decimal | None = None
    total_recurso_disponivel_ef_anterior: Decimal | None = None
    total_recurso_compensacao_ef: Decimal | None = None
    reserva_alivio_ess: Decimal | None = None


@registrar
class CceeExposicaoFinanceira(CceeCsvCkan):
    """Exposição financeira mensal. CSV por ano, uma linha por mês."""

    dataset = "exposicao_financeira_mensal"
    entidade = "exposicao_financeira"
    schema = ExposicaoFinanceira

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        registro: dict[str, Any] = {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
        }
        for origem, destino in CAMPOS.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))
        return registro
