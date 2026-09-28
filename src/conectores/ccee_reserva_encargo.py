"""Conector CCEE — encargo de reserva, por mês (Aditivo 01, público). Item 23.

Fonte: dados abertos da CCEE (CKAN), dataset `reserva_encargo`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/reserva_encargo

Uma linha por mês, R$, mercado inteiro: o custo da energia de reserva (CONER)
rateado entre os agentes. Mesma forma do ESS e do EER — série mensal, sem
agente e sem submercado.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from src.conectores.ccee_ckan import CceeCsvCkan, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar

CAMPOS = {
    "ENCARGO_ENERGIA_RESERVA": "encargo_energia_reserva",
    "TOTAL_PAGAMENTO_LIQ_ER": "total_pagamento_liquido_er",
    "FUNDO_GARANTIA_OPER_CONTR_ER": "fundo_garantia_operacional_contratos_er",
    "TOTAL_RECEITA_RETIDA_CONER": "total_receita_retida_coner",
    "CUSTO_ADIMN_FIN_TRIB_CCEE": "custo_administrativo_financeiro_tributario_ccee",
    "SALDO_EFETIVO_CONER": "saldo_efetivo_coner",
}


class ReservaEncargo(BaseModel):
    """O encargo de reserva (CONER) de um mês, em R$."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    encargo_energia_reserva: Decimal | None = None
    total_pagamento_liquido_er: Decimal | None = None
    fundo_garantia_operacional_contratos_er: Decimal | None = None
    total_receita_retida_coner: Decimal | None = None
    custo_administrativo_financeiro_tributario_ccee: Decimal | None = None
    saldo_efetivo_coner: Decimal | None = None


@registrar
class CceeReservaEncargo(CceeCsvCkan):
    """Encargo de reserva mensal. CSV por ano, uma linha por mês."""

    dataset = "reserva_encargo"
    entidade = "reserva_encargo"
    schema = ReservaEncargo

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
