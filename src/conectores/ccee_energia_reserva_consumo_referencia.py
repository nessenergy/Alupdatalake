"""Conector CCEE — TRC de segurança energética, por mês (Aditivo 01, público). Item 24.

Fonte: dados abertos da CCEE (CKAN), dataset `energia_reserva_consumo_referencia`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/energia_reserva_consumo_referencia

Uma linha por mês, mercado inteiro: o total de referência de consumo (TRC) de
segurança energética. Não é o EER (`ccee_energia_reserva`, dataset
`energia_reserva_liquidacao`) — a entidade leva o nome completo do dataset
para não colidir com aquela.

A CCEE não documenta a unidade nem o que `TRC_SEG_ENER_SUC` distingue de
`TRC_SEG_ENER`; perfilado em 28/09/2026, `_SUC` veio sempre vazio nos 7 meses
de 2026. Os dois campos entram como a origem os nomeia, sem inventar unidade.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from src.conectores.ccee_ckan import CceeCsvCkan, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar


class ConsumoReferenciaEnergiaReserva(BaseModel):
    """O TRC de segurança energética de um mês. Unidade não documentada pela CCEE."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    trc_seguranca_energetica: Decimal
    trc_seguranca_energetica_suc: Decimal | None = None


@registrar
class CceeEnergiaReservaConsumoReferencia(CceeCsvCkan):
    """TRC de segurança energética mensal. CSV por ano, uma linha por mês."""

    dataset = "energia_reserva_consumo_referencia"
    entidade = "energia_reserva_consumo_referencia"
    schema = ConsumoReferenciaEnergiaReserva

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        return {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "trc_seguranca_energetica": numero_ou_nulo(bruto.get("TRC_SEG_ENER")),
            "trc_seguranca_energetica_suc": numero_ou_nulo(bruto.get("TRC_SEG_ENER_SUC")),
        }
