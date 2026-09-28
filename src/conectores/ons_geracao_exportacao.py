"""Conector ONS — geração comercial para exportação internacional, horária (Aditivo 01).

Fonte: Dados Abertos ONS, dataset `geracao_exportacao_internacional_ho`, um
CSV por ano, desde 2022.
Documentação: https://dados.ons.org.br/dataset/geracao-exportacao-internacional

Extração na base `OnsCsvAnual`. Uma linha por hora: a geração alocada para
exportação comercial (energia vertida turbinável para Argentina e Uruguai, e
térmica) e a exportação efetiva por país. Todos os valores de 2026 são zero ou
positivos; negativo é recusado.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import OnsCsvAnual, instante
from src.core.registry import registrar

_ORIGEM = {
    "geracao_exportacao_evt_argentina_mwmed": "val_gerexpevt_ar",
    "geracao_exportacao_evt_uruguai_mwmed": "val_gerexpevt_uy",
    "geracao_exportacao_termica_mwmed": "val_gerexptermica",
    "exportacao_argentina_mwmed": "val_exportacao_ar",
    "exportacao_uruguai_mwmed": "val_exportacao_uy",
}


class GeracaoExportacao(BaseModel):
    """Geração para exportação e exportação por país em uma hora, em MWmed."""

    data_referencia: date
    instante: datetime
    geracao_exportacao_evt_argentina_mwmed: Decimal
    """Energia vertida turbinável gerada para exportar à Argentina."""
    geracao_exportacao_evt_uruguai_mwmed: Decimal
    geracao_exportacao_termica_mwmed: Decimal
    exportacao_argentina_mwmed: Decimal
    exportacao_uruguai_mwmed: Decimal

    @field_validator(*_ORIGEM)
    @classmethod
    def _nao_negativo(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"valor negativo: {valor}")
        return valor


@registrar
class OnsGeracaoExportacao(OnsCsvAnual):
    """Geração comercial para exportação internacional, horária."""

    entidade = "geracao_exportacao"
    schema = GeracaoExportacao
    caminho = "geracao_exportacao_internacional_ho/GERACAO_EXPORTACAO_INTERNACIONAL_{ano}.csv"
    coluna_data = "din_instante"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["din_instante"][:10],
            "instante": instante(bruto["din_instante"]),
            **{campo: bruto[origem] for campo, origem in _ORIGEM.items()},
        }
