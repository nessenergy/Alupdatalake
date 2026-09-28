"""Conector ONS — energia armazenada (EAR) diária por bacia (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `ear_bacia_di`, um CSV por ano.
Documentação: https://dados.ons.org.br/dataset/ear-diario-por-bacia

Extração na base `OnsCsvAnual`. Duas diferenças do `ons_ear` que o dado impõe:

1. **Não há subsistema.** A unidade é a bacia (`nomecurto`); uma bacia pode
   atravessar subsistemas, então `submercado` fica nulo em vez de inventado.
2. **O percentual passa de 100.** Em 2026 a bacia do Paraguaçu ficou acima da
   própria capacidade máxima em 176 dias (até 154%), e o percentual bate com
   verificada/máxima. A regra 0-100 do `ons_ear` não vale aqui: só negativo é
   recusado.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import OnsCsvAnual
from src.core.registry import registrar


class EarBacia(BaseModel):
    """Energia armazenada verificada de uma bacia em um dia, em MWmês."""

    data_referencia: date
    bacia: str
    ear_max_mwmes: Decimal
    ear_verificada_mwmes: Decimal
    ear_verificada_percentual: Decimal
    """Pode passar de 100 (ver docstring do módulo)."""

    @field_validator("bacia")
    @classmethod
    def _bacia_preenchida(cls, valor: str) -> str:
        nome = valor.strip().upper()
        if not nome:
            raise ValueError("bacia vazia")
        return nome

    @field_validator("ear_max_mwmes", "ear_verificada_mwmes", "ear_verificada_percentual")
    @classmethod
    def _nao_negativo(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"valor negativo: {valor}")
        return valor


@registrar
class OnsEarBacia(OnsCsvAnual):
    """EAR diária por bacia."""

    entidade = "ear_bacia"
    schema = EarBacia
    caminho = "ear_bacia_di/EAR_DIARIO_BACIAS_{ano}.csv"
    coluna_data = "ear_data"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["ear_data"][:10],
            "bacia": bruto.get("nomecurto", ""),
            "ear_max_mwmes": bruto["ear_max_bacia"],
            "ear_verificada_mwmes": bruto["ear_verif_bacia_mwmes"],
            "ear_verificada_percentual": bruto["ear_verif_bacia_percentual"],
        }
