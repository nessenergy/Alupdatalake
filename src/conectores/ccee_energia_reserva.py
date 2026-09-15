"""Conector CCEE — liquidação da energia de reserva (EER), por mês (Onda 1, público). Ordem 5 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `energia_reserva_liquidacao`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/energia_reserva_liquidacao

Uma linha por mês, R$, mercado inteiro: o EER que o B1 nomeia em Mercado de
Energia. `AJUSTE` pode ser negativo — é ajuste, não montante.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from src.conectores.ccee_ckan import CceeCsvCkan, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar

CAMPOS = {
    "EFEITO_CCEAR_DISP_CER": "efeito_ccear_disponibilidade_cer",
    "REPASSE_USUARIOS_RESERVA": "repasse_usuarios_reserva",
    "AJUSTE": "ajuste",
    "VALOR_TOTAL_LIQUID": "valor_total_liquidado",
}


class EnergiaReserva(BaseModel):
    """A liquidação da energia de reserva em um mês, em R$."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    efeito_ccear_disponibilidade_cer: Decimal | None = None
    repasse_usuarios_reserva: Decimal | None = None
    ajuste: Decimal | None = None
    valor_total_liquidado: Decimal | None = None


@registrar
class CceeEnergiaReserva(CceeCsvCkan):
    """EER mensal. CSV por ano, uma linha por mês."""

    dataset = "energia_reserva_liquidacao"
    entidade = "energia_reserva"
    schema = EnergiaReserva

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
