"""Conector ONS — energia natural afluente (ENA) diária por bacia (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `ena_bacia_di`, um CSV por ano.
Documentação: https://dados.ons.org.br/dataset/ena-diario-por-bacia

Extração na base `OnsCsvAnual`. Como a ENA por subsistema (`ons_ena`), o
percentual é **sobre a média de longo termo (MLT)**, não sobre uma capacidade:
passa de 100 sempre que a afluência está acima da média histórica — chegou a
1.048% em 2026. Só negativo é recusado. Não há subsistema na origem.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import OnsCsvAnual
from src.core.registry import registrar


class EnaBacia(BaseModel):
    """Energia natural afluente de uma bacia em um dia, em MWmed e % da MLT."""

    data_referencia: date
    bacia: str
    ena_bruta_mwmed: Decimal
    ena_bruta_percentual_mlt: Decimal
    ena_armazenavel_mwmed: Decimal
    ena_armazenavel_percentual_mlt: Decimal

    @field_validator("bacia")
    @classmethod
    def _bacia_preenchida(cls, valor: str) -> str:
        nome = valor.strip().upper()
        if not nome:
            raise ValueError("bacia vazia")
        return nome

    @field_validator(
        "ena_bruta_mwmed", "ena_bruta_percentual_mlt", "ena_armazenavel_mwmed", "ena_armazenavel_percentual_mlt"
    )
    @classmethod
    def _nao_negativo(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"valor negativo: {valor}")
        return valor


@registrar
class OnsEnaBacia(OnsCsvAnual):
    """ENA diária por bacia."""

    entidade = "ena_bacia"
    schema = EnaBacia
    caminho = "ena_bacia_di/ENA_DIARIO_BACIAS_{ano}.csv"
    coluna_data = "ena_data"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["ena_data"][:10],
            "bacia": bruto.get("nom_bacia", ""),
            "ena_bruta_mwmed": bruto["ena_bruta_bacia_mwmed"],
            "ena_bruta_percentual_mlt": bruto["ena_bruta_bacia_percentualmlt"],
            "ena_armazenavel_mwmed": bruto["ena_armazenavel_bacia_mwmed"],
            "ena_armazenavel_percentual_mlt": bruto["ena_armazenavel_bacia_percentualmlt"],
        }
