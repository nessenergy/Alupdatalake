"""Modelo de planilha do PRC — Preço de Referência Comparável, comercialização varejista.

O PRC (Procedimentos de Comercialização da CCEE, submódulo 1.6; REN ANEEL 1.011/22) é divulgado por
cada comercializadora varejista no próprio site, em PDF, e o layout muda de uma para outra (uns por ano
civil, outros por prazo de 12, 36 e 60 meses; uns em blocos de submercado). Não há base pública única nem
API, então a entrada é a planilha: a Alup, ou quem ela indicar, preenche este modelo a cada atualização.

Uma linha por submercado, tipo de energia e ano (ou prazo). A tabela de origem que agrupa "SE/CO e Sul" é
repetida nas duas siglas: a dimensão comum `submercado` do projeto é a sigla de um submercado.

O canal que leva o arquivo ao job (bucket de entrada) é da Onda 4, e por isso a classe **não é
registrada**: ela fica pronta para quando o canal existir. Modelo para preencher:
`docs/modelos/modelo-prc.csv`.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from src.conectores.planilha import ConectorPlanilha
from src.core.planilha import TemplatePlanilha

# Faixa de sanidade em R$/MWh: preço de comercialização varejista fica em centenas; fora disso é erro de digitação.
PRECO_MINIMO = Decimal("1")
PRECO_MAXIMO = Decimal("2000")

TEMPLATE_PRC = TemplatePlanilha(
    colunas={
        "Comercializadora": "comercializadora",
        "Data de atualização": "data_atualizacao",
        "Submercado": "submercado",
        "Tipo de energia": "tipo_energia",
        "Ano": "ano",
        "Prazo (meses)": "prazo_meses",
        "Preço (R$/MWh)": "preco_rs_mwh",
        "Indexador": "indexador",
        "Premissas": "premissas",
    },
    colunas_decimais=frozenset({"preco_rs_mwh"}),
)


class PrecoReferencia(BaseModel):
    """Um PRC: o preço de referência de uma comercializadora para um submercado, tipo de energia e período."""

    comercializadora: str = Field(min_length=1)
    data_atualizacao: date
    submercado: Literal["N", "NE", "S", "SE"]
    tipo_energia: Literal["convencional", "incentivada_50"]
    ano: int | None = Field(default=None, ge=2000, le=2100)
    prazo_meses: int | None = Field(default=None, ge=1, le=240)
    preco_rs_mwh: Decimal = Field(ge=PRECO_MINIMO, le=PRECO_MAXIMO)
    indexador: str | None = None
    premissas: str | None = None

    @field_validator("comercializadora")
    @classmethod
    def _linha_de_exemplo_nao_carrega(cls, valor: str) -> str:
        if valor.strip().lower().startswith("exemplo"):
            raise ValueError("linha de exemplo do modelo: apague-a antes de enviar")
        return valor.strip()

    @field_validator("data_atualizacao", mode="before")
    @classmethod
    def _data_brasileira(cls, valor: Any) -> Any:
        if isinstance(valor, str) and "/" in valor:
            return datetime.strptime(valor.strip(), "%d/%m/%Y").date()  # noqa: DTZ007
        return valor

    @field_validator("ano", "prazo_meses", "indexador", "premissas", mode="before")
    @classmethod
    def _vazio_e_ausencia(cls, valor: Any) -> Any:
        if isinstance(valor, str) and not valor.strip():
            return None
        return valor

    @model_validator(mode="after")
    def _ano_ou_prazo(self) -> PrecoReferencia:
        if (self.ano is None) == (self.prazo_meses is None):
            raise ValueError("informe o ano ou o prazo em meses, e só um dos dois")
        return self


class PlanilhaPrc(ConectorPlanilha):
    """PRC por planilha. Não registrado: depende do canal de entrada de arquivos (Onda 4)."""

    fonte = "s2"
    entidade = "prc"
    schema = PrecoReferencia
    schema_versao = "1"
    template = TEMPLATE_PRC

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return dict(bruto)
