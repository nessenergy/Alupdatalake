"""Conector ONS — balanço de energia nos subsistemas, horário (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `balanco_energia_subsistema_ho`, um CSV por ano.
Documentação: https://dados.ons.org.br/dataset/balanco-energia-subsistema

Extração na base `OnsCsvAnual`. Por hora e subsistema: geração por fonte
(hidráulica, térmica, eólica, solar), carga e intercâmbio líquido. O que o dado
impõe:

- **Há uma linha "SIN"**, o total do sistema, junto com N, NE, S e SE. Ela
  fica — é fiel à origem e evita somar na consulta —, com a sigla em
  `subsistema`; a Silver deixa `submercado` nulo nela, porque SIN não é
  submercado.
- A sigla vem com espaços à direita (`"N  "`).
- **Carga e intercâmbio podem ser negativos**: a carga chegou a -4.729 MWmed
  em 2026, e intercâmbio negativo é importação líquida. Geração negativa é
  recusada.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import SUBMERCADOS, OnsCsvAnual, instante
from src.core.registry import registrar

SUBSISTEMAS = SUBMERCADOS | {"SIN"}
_GERACAO = ("geracao_hidraulica_mwmed", "geracao_termica_mwmed", "geracao_eolica_mwmed", "geracao_solar_mwmed")


class BalancoEnergia(BaseModel):
    """Geração por fonte, carga e intercâmbio de um subsistema em uma hora, em MWmed."""

    data_referencia: date
    instante: datetime
    subsistema: str
    """N, NE, S, SE ou SIN (total do sistema)."""
    nome_subsistema: str
    geracao_hidraulica_mwmed: Decimal
    geracao_termica_mwmed: Decimal
    geracao_eolica_mwmed: Decimal
    geracao_solar_mwmed: Decimal
    carga_mwmed: Decimal
    intercambio_mwmed: Decimal
    """Líquido; negativo é importação."""

    @field_validator("subsistema")
    @classmethod
    def _subsistema_conhecido(cls, valor: str) -> str:
        sigla = valor.strip().upper()
        if sigla not in SUBSISTEMAS:
            raise ValueError(f"subsistema desconhecido: {valor}")
        return sigla

    @field_validator("nome_subsistema")
    @classmethod
    def _trim(cls, valor: str) -> str:
        return valor.strip()

    @field_validator(*_GERACAO)
    @classmethod
    def _geracao_nao_negativa(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"geração negativa: {valor}")
        return valor


@registrar
class OnsBalancoEnergia(OnsCsvAnual):
    """Balanço de energia horário por subsistema."""

    entidade = "balanco_energia"
    schema = BalancoEnergia
    caminho = "balanco_energia_subsistema_ho/BALANCO_ENERGIA_SUBSISTEMA_{ano}.csv"
    coluna_data = "din_instante"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["din_instante"][:10],
            "instante": instante(bruto["din_instante"]),
            "subsistema": bruto.get("id_subsistema", ""),
            "nome_subsistema": bruto.get("nom_subsistema", ""),
            "geracao_hidraulica_mwmed": bruto["val_gerhidraulica"],
            "geracao_termica_mwmed": bruto["val_gertermica"],
            "geracao_eolica_mwmed": bruto["val_gereolica"],
            "geracao_solar_mwmed": bruto["val_gersolar"],
            "carga_mwmed": bruto["val_carga"],
            "intercambio_mwmed": bruto["val_intercambio"],
        }
