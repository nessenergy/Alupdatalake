"""Conector ONS — intercâmbio do SIN com outros países, horário (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `intercambio_internacional_ho`, um CSV por ano.
Documentação: https://dados.ons.org.br/dataset/intercambio-internacional

Extração na base `OnsCsvAnual`. Uma linha por hora e país. **O sinal é o
sentido do fluxo**: positivo é exportação, negativo é importação (em janeiro
de 2026, -500 MWmed da Argentina). Sinal, portanto, não é validado. O nome do
país vem com espaços à direita; o trim vive no validador.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import OnsCsvAnual, instante
from src.core.registry import registrar


class IntercambioInternacional(BaseModel):
    """Fluxo de energia entre o SIN e um país em uma hora, em MWmed."""

    data_referencia: date
    instante: datetime
    pais: str
    intercambio_mwmed: Decimal
    """Positivo: exportação. Negativo: importação."""
    intercambio_programado_mwmed: Decimal

    @field_validator("pais")
    @classmethod
    def _pais_preenchido(cls, valor: str) -> str:
        nome = valor.strip()
        if not nome:
            raise ValueError("país vazio")
        return nome


@registrar
class OnsIntercambioInternacional(OnsCsvAnual):
    """Intercâmbio horário do SIN com outros países."""

    entidade = "intercambio_internacional"
    schema = IntercambioInternacional
    caminho = "intercambio_internacional_ho/INTERCAMBIO_INTERNACIONAL_{ano}.csv"
    coluna_data = "din_instante"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["din_instante"][:10],
            "instante": instante(bruto["din_instante"]),
            "pais": bruto.get("nom_paisdestino", ""),
            "intercambio_mwmed": bruto["val_intercambiomwmed"],
            "intercambio_programado_mwmed": bruto["val_intercambioprogmwmed"],
        }
