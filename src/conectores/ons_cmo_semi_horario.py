"""Conector ONS — Custo Marginal de Operação (CMO) semi-horário (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `cmo_tm`, um CSV por ano, desde 2020.
Documentação: https://dados.ons.org.br/dataset/cmo-semi-horario

Extração na base `OnsCsvAnual`. O CMO é quanto custa produzir o próximo MWh
em cada subsistema — a base de formação do PLD. **O passo é de 30 minutos**
(minutos 00 e 30), então a chave é o instante inteiro, como no constrained-off.
Chegou a R$ 7.854,60/MWh em 2026; só negativo é recusado.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import OnsCsvAnual, instante, submercado
from src.core.registry import registrar


class CmoSemiHorario(BaseModel):
    """CMO de um subsistema em uma meia hora, em R$/MWh."""

    data_referencia: date
    instante: datetime
    submercado: str
    cmo_reais_mwh: Decimal

    @field_validator("submercado")
    @classmethod
    def _sigla(cls, valor: str) -> str:
        sigla = submercado(valor)
        if sigla is None:
            raise ValueError("submercado vazio")
        return sigla

    @field_validator("cmo_reais_mwh")
    @classmethod
    def _nao_negativo(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"CMO negativo: {valor}")
        return valor


@registrar
class OnsCmoSemiHorario(OnsCsvAnual):
    """CMO semi-horário por subsistema."""

    entidade = "cmo_semi_horario"
    schema = CmoSemiHorario
    caminho = "cmo_tm/CMO_SEMIHORARIO_{ano}.csv"
    coluna_data = "din_instante"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["din_instante"][:10],
            "instante": instante(bruto["din_instante"]),
            "submercado": bruto.get("id_subsistema", ""),
            "cmo_reais_mwh": bruto["val_cmo"],
        }
