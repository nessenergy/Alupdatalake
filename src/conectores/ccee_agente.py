"""Conector CCEE — lista mensal de agentes (Onda 1, público). Ordem 1 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `lista_agente_associado`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/lista_agente_associado

Um retrato por mês de todos os agentes da CCEE — cerca de 16.400 — com classe,
situação como comercializador e como varejista, UF e categoria. Diferente do
`ccee_perfil`, aqui **há histórico**: cada `MES_REFERENCIA` é um retrato, e a
Silver guarda todos.

**Não há coluna de perfil.** O elo agente ↔ perfil está em `lista_perfil_v1`
(`COD_AGENTE` + `COD_PERF_AGENTE`). Esta fonte enriquece o agente; não o liga
a nada.

Este é o arquivo que misturava UTF-8 e ISO-8859-1 linha a linha; a base
`CceeCsvCkan` decodifica por linha por causa dele.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, periodo_ccee, primeiro_dia
from src.core.registry import registrar

# Os valores que a CCEE publicava em 14/09/2026. Valor novo sem revisão do
# contrato de dados entraria como dado silenciosamente errado.
CLASSES = (
    "Autoprodutor",
    "Comercializador",
    "Consumidor Especial",
    "Consumidor Livre",
    "Distribuidor",
    "Gerador",
    "Produtor Independente",
)
CATEGORIAS = ("Comercialização", "Consumo", "Distribuição", "Geração")


class AgenteCcee(BaseModel):
    """Um agente da CCEE, como estava no mês de referência."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    cnpj: str
    agente_ccee: str  # SIGLA_AGENTE — dimensão comum do projeto
    razao_social: str
    classe_agente: Literal[CLASSES]  # type: ignore[valid-type]
    situacao_comercializador: str | None = None
    situacao_varejista: str | None = None
    uf: str
    categoria_agente: Literal[CATEGORIAS]  # type: ignore[valid-type]
    varejista: bool = False

    @field_validator("cnpj")
    @classmethod
    def _cnpj_normalizado(cls, valor: str) -> str:
        digitos = "".join(c for c in valor if c.isdigit())
        if len(digitos) != 14:
            raise ValueError(f"CNPJ deve ter 14 dígitos, veio com {len(digitos)}")
        return digitos

    @field_validator("uf")
    @classmethod
    def _uf_com_duas_letras(cls, valor: str) -> str:
        uf = valor.strip().upper()
        if len(uf) != 2 or not uf.isalpha():
            raise ValueError(f"UF inválida: {valor!r}")
        return uf


@registrar
class CceeAgente(CceeCsvCkan):
    """Lista mensal de agentes. CSV por ano; um retrato por mês."""

    dataset = "lista_agente_associado"
    entidade = "agente"
    schema = AgenteCcee

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        return {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "cnpj": limpar(bruto.get("CNPJ")),
            "agente_ccee": limpar(bruto.get("SIGLA_AGENTE")),
            "razao_social": limpar(bruto.get("RAZAO_SOCIAL")),
            "classe_agente": limpar(bruto.get("CLASSE_AGENTE")),
            "situacao_comercializador": limpar(bruto.get("SITUACAO_COMERCIALIZADOR")) or None,
            "situacao_varejista": limpar(bruto.get("SITUACAO_VAREJISTA")) or None,
            "uf": limpar(bruto.get("ESTADO")),
            "categoria_agente": limpar(bruto.get("CATEGORIA_AGENTE")),
            "varejista": limpar(bruto.get("INDICADOR_VAREJISTA")).lower().startswith("s"),
        }
