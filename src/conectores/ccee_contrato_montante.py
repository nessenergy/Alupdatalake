"""Conector CCEE — montantes contratados de compra e venda por perfil (Onda 1, público). Ordem 4 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `contrato_montante_compra_venda_perfil_agente`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/contrato_montante_compra_venda_perfil_agente

Uma linha por perfil e mês: quanto o perfil vendeu e quanto comprou em
contratos registrados na CCEE. É a via pública de Comercial e Contratos — a
visão que a Câmara tem de cada agente, não o book interno (esse segue preso ao
A7). 80% dos perfis só compram: `CONTRATACAO_VENDA` vazia é o normal, e vira
nulo.

Os nomes de coluna diferem da contabilização: `CODIGO_AGENTE` e
`CODIGO_PERFIL_AGENTE`, não `COD_*`. A unidade dos montantes não está
documentada no catálogo; a Gold não afirma MWmed nem MWh.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar


class ContratoMontante(BaseModel):
    """Os montantes contratados de um perfil de agente em um mês."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    codigo_agente: str
    codigo_perfil: str
    sigla_perfil: str
    nome_empresarial: str
    cnpj: str
    contratacao_venda: Decimal | None = Field(default=None, ge=0)
    contratacao_compra: Decimal | None = Field(default=None, ge=0)

    @field_validator("cnpj")
    @classmethod
    def _cnpj_normalizado(cls, valor: str) -> str:
        digitos = "".join(c for c in valor if c.isdigit())
        if len(digitos) != 14:
            raise ValueError(f"CNPJ deve ter 14 dígitos, veio com {len(digitos)}")
        return digitos


@registrar
class CceeContratoMontante(CceeCsvCkan):
    """Montantes de compra e venda por perfil. CSV por ano, uma linha por perfil e mês."""

    dataset = "contrato_montante_compra_venda_perfil_agente"
    entidade = "contrato_montante"
    schema = ContratoMontante

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        return {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "codigo_agente": limpar(bruto.get("CODIGO_AGENTE")),
            "codigo_perfil": limpar(bruto.get("CODIGO_PERFIL_AGENTE")),
            "sigla_perfil": limpar(bruto.get("SIGLA_PERFIL_AGENTE")),
            "nome_empresarial": limpar(bruto.get("NOME_EMPRESARIAL")),
            "cnpj": limpar(bruto.get("CNPJ")),
            "contratacao_venda": numero_ou_nulo(bruto.get("CONTRATACAO_VENDA")),
            "contratacao_compra": numero_ou_nulo(bruto.get("CONTRATACAO_COMPRA")),
        }
