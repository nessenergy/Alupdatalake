"""Conector ONS — intercâmbio entre subsistemas, horário (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `intercambio_nacional_ho`, um CSV por ano.
Documentação: https://dados.ons.org.br/dataset/intercambio-nacional

Extração na base `OnsCsvAnual`. Uma linha por hora e par origem→destino,
com o intercâmbio verificado e o programado. O verificado veio sempre positivo
em 2026 (o sentido está no par); o **programado chega a negativo** (-5.507
MWmed), então sinal não é validado. O nome do subsistema vem com espaço à
esquerda (`" NORTE"`); o lake usa a sigla.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import OnsCsvAnual, instante, submercado
from src.core.registry import registrar


class IntercambioNacional(BaseModel):
    """Fluxo de energia entre dois subsistemas em uma hora, em MWmed."""

    data_referencia: date
    instante: datetime
    subsistema_origem: str
    subsistema_destino: str
    intercambio_mwmed: Decimal
    intercambio_programado_mwmed: Decimal

    @field_validator("subsistema_origem", "subsistema_destino")
    @classmethod
    def _sigla(cls, valor: str) -> str:
        sigla = submercado(valor)
        if sigla is None:
            raise ValueError("subsistema vazio")
        return sigla


@registrar
class OnsIntercambioNacional(OnsCsvAnual):
    """Intercâmbio horário entre subsistemas."""

    entidade = "intercambio_nacional"
    schema = IntercambioNacional
    caminho = "intercambio_nacional_ho/INTERCAMBIO_NACIONAL_{ano}.csv"
    coluna_data = "din_instante"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["din_instante"][:10],
            "instante": instante(bruto["din_instante"]),
            "subsistema_origem": bruto.get("id_subsistema_origem", ""),
            "subsistema_destino": bruto.get("id_subsistema_destino", ""),
            "intercambio_mwmed": bruto["val_intercambiomwmed"],
            "intercambio_programado_mwmed": bruto["val_intercambioprogmwmed"],
        }
