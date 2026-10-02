"""Conector ONS — DESSEM, balanço de energia geral (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `balanco_dessem_geral`, um CSV por dia.
Documentação: https://dados.ons.org.br/dataset/balanco_dessem_geral

Extração na base `OnsArquivoDiario`. É a programação do modelo DESSEM para o
dia de referência, por subsistema e patamar de meia hora: a demanda e a
geração prevista por fonte (renovável, hidráulica, térmica), em MW, mais o
consumo das usinas elevatórias. O que o dado impõe:

- **A data vem ISO** (`AAAA-MM-DD`), ao contrário do `programacao_x_previsao`.
- **Quatro subsistemas** (N, NE, S, SE) × 48 patamares = 192 linhas por dia.
  Não há linha SIN.
- Nenhum valor veio negativo ou vazio nos 493 arquivos lidos, e o dicionário do
  ONS os proíbe: negativo é recusado.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from pydantic import BaseModel, field_validator

from src.conectores.ons_arquivo_diario import OnsArquivoDiario
from src.conectores.ons_csv_anual import submercado
from src.core.registry import registrar

_MEDIDAS = (
    "demanda_mw",
    "geracao_renovavel_mw",
    "geracao_hidraulica_mw",
    "geracao_termica_mw",
    "consumo_elevatoria_mw",
)


class BalancoDessem(BaseModel):
    """Demanda e geração programadas pelo DESSEM para um subsistema em um patamar, em MW."""

    data_referencia: date
    patamar: int
    submercado: str
    demanda_mw: Decimal
    geracao_renovavel_mw: Decimal
    geracao_hidraulica_mw: Decimal
    geracao_termica_mw: Decimal
    consumo_elevatoria_mw: Decimal

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        sigla = submercado(valor)
        if sigla is None:
            raise ValueError("submercado vazio")
        return sigla

    @field_validator(*_MEDIDAS)
    @classmethod
    def _nao_negativo(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"valor negativo: {valor}")
        return valor


@registrar
class OnsBalancoDessem(OnsArquivoDiario):
    """Balanço de energia do DESSEM, um arquivo por dia."""

    entidade = "balanco_dessem"
    schema = BalancoDessem
    caminho: ClassVar[str] = "balanco_dessem_geral/BALANCO_DESSEM_GERAL_{dia:%Y_%m_%d}.csv"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["din_programacaodia"].strip()[:10],
            "patamar": bruto["num_patamar"],
            "submercado": bruto["cod_subsistema"],
            "demanda_mw": bruto["val_demanda"],
            "geracao_renovavel_mw": bruto["val_geracao_renovavel"],
            "geracao_hidraulica_mw": bruto["val_geracao_hidraulica"],
            "geracao_termica_mw": bruto["val_geracao_termica"],
            "consumo_elevatoria_mw": bruto["val_cons_elevatoria"],
        }
