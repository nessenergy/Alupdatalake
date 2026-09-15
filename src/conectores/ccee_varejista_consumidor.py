"""Conector CCEE — consumo das parcelas de carga dos varejistas (Onda 1, público). Ordem 4 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `varejista_consumidor`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/varejista_consumidor

Uma linha por varejista, mês, UF da carga e distribuidora à qual a carga está
conectada — a chave tem cinco colunas, porque um varejista atende cargas em
várias UFs e distribuidoras. É o subtema "contratos de varejo" de Comercial e
Contratos (Tahigo Santos, B1), pela via pública.

A CCEE avisa no catálogo que os consumidores migrados pela migração
simplificada ainda não entram. A Alup classifica consumo vindo da CCEE como
confidencial (F1); o dataset é interno (F4) e a Gold não desce abaixo de
(mês, varejista, UF).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.conectores.ccee_pld import SIGLA_SUBMERCADO, SUBMERCADOS
from src.core.registry import registrar


class ConsumoVarejista(BaseModel):
    """O consumo das cargas de um varejista em uma UF e distribuidora, em um mês."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    codigo_perfil: str
    sigla_perfil: str
    nome_empresarial: str
    uf_carga: str
    submercado: str
    codigo_perfil_conectado: str | None = None
    sigla_perfil_conectado: str | None = None
    quantidade_parcelas_carga: int = Field(ge=0)
    consumo_total: Decimal = Field(ge=0)

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        if valor not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return valor

    @field_validator("uf_carga")
    @classmethod
    def _uf_com_duas_letras(cls, valor: str) -> str:
        uf = valor.strip().upper()
        if len(uf) != 2 or not uf.isalpha():
            raise ValueError(f"UF inválida: {valor!r}")
        return uf


@registrar
class CceeVarejistaConsumidor(CceeCsvCkan):
    """Consumo de varejo por varejista, UF e distribuidora. CSV por ano."""

    dataset = "varejista_consumidor"
    entidade = "varejista_consumidor"
    schema = ConsumoVarejista

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        nome = limpar(bruto.get("SUBMERCADO_CARGA")).upper()
        return {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "codigo_perfil": limpar(bruto.get("COD_PERF_AGENTE")),
            "sigla_perfil": limpar(bruto.get("SIGLA_PERFIL_AGENTE")),
            "nome_empresarial": limpar(bruto.get("NOME_EMPRESARIAL")),
            "uf_carga": limpar(bruto.get("ESTADO_UF_CARGA")),
            "submercado": SIGLA_SUBMERCADO.get(nome, nome),
            "codigo_perfil_conectado": limpar(bruto.get("COD_PERF_AGENTE_CONECTADO")) or None,
            "sigla_perfil_conectado": limpar(bruto.get("SIGLA_PERFIL_AGENTE_CONECTADO")) or None,
            "quantidade_parcelas_carga": numero_ou_nulo(bruto.get("QTD_PARCELA_CARGA")),
            "consumo_total": numero_ou_nulo(bruto.get("CONSUMO_TOTAL")),
        }
