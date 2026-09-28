"""Conector CCEE — consumo por classe de agente, por mês (Aditivo 01, público). Item 25.

Fonte: dados abertos da CCEE (CKAN), dataset `consumo_classe_agente`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/consumo_classe_agente

Uma linha por mês e por classe de agente (Distribuidor, Consumidor Livre,
Autoprodutor, Comercializador, Consumidor Especial e outras — a CCEE não
publica a lista fechada, então `classe_agente` fica como texto livre, não
como enum). Consumo total e a repartição entre ambiente regulado (ACR) e livre
(ACL) no ponto de conexão. A CCEE não documenta a unidade.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar


class ConsumoClasseAgente(BaseModel):
    """O consumo de uma classe de agente no mês. Unidade não documentada pela CCEE."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    classe_agente: str
    consumo: Decimal
    consumo_ponto_conexao_classe_acr: Decimal
    consumo_ponto_conexao_classe_acl: Decimal

    @field_validator("classe_agente")
    @classmethod
    def _preenchido(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("classe_agente vazia")
        return texto


@registrar
class CceeConsumoClasseAgente(CceeCsvCkan):
    """Consumo mensal por classe de agente. CSV por ano."""

    dataset = "consumo_classe_agente"
    entidade = "consumo_classe_agente"
    schema = ConsumoClasseAgente

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        return {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "classe_agente": limpar(bruto.get("CLASSE_AGENTE")),
            "consumo": numero_ou_nulo(bruto.get("CONSUMO")),
            "consumo_ponto_conexao_classe_acr": numero_ou_nulo(bruto.get("CONSUMO_PONTO_CONEXAO_CLASSE_ACR")),
            "consumo_ponto_conexao_classe_acl": numero_ou_nulo(bruto.get("CONSUMO_PONTO_CONEXAO_CLASSE_ACL")),
        }
