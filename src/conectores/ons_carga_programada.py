"""Conector ONS — Carga de Energia Programada, semi-horária por área de carga (Aditivo 01, público).

Fonte: API `apicarga.ons.org.br/prd/cargaprogramada`, dataset `carga-energia-programada`.
Documentação: https://dados.ons.org.br/dataset/carga-energia-programada

É a carga que o ONS usa na programação diária (modelo DESSEM). Par da carga
verificada (`ons_carga_verificada`): a diferença entre as duas é o erro da
programação. Mecânica da API em `ons_carga_api`.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_carga_api import OnsCargaApi, area_conhecida
from src.core.registry import registrar


class CargaProgramada(BaseModel):
    """Carga programada de uma área no fim de uma meia hora, em MWmed."""

    data_referencia: date
    instante_utc: datetime
    area_carga: str
    carga_programada_mwmed: Decimal

    @field_validator("area_carga")
    @classmethod
    def _area(cls, valor: str) -> str:
        return area_conhecida(valor)


@registrar
class OnsCargaProgramada(OnsCargaApi):
    """Carga programada por área de carga."""

    entidade = "carga_programada"
    schema = CargaProgramada
    endpoint = "cargaprogramada"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["dat_referencia"],
            "instante_utc": bruto["din_referenciautc"],
            "area_carga": bruto["cod_areacarga"],
            "carga_programada_mwmed": bruto["val_cargaglobalprogramada"],
        }
