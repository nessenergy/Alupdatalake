"""Conector CCEE — ESS e serviços ancilares, por mês (Onda 1, público). Ordem 5 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `encargo_ess_ancilar`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/encargo_ess_ancilar

Uma linha por mês, valores do mercado inteiro em R$: o ESS que o B1 nomeia em
Mercado de Energia. Mesma forma da exposição financeira.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from src.conectores.ccee_ckan import CceeCsvCkan, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar

CAMPOS = {
    "ENCARGO_CONST_ON": "encargo_constrained_on",
    "ENCARGO_CONST_OFF": "encargo_constrained_off",
    "OUTROS_SERVICOS_ANCILARES": "outros_servicos_ancilares",
    "ENCARGO_CS": "encargo_cs",
    "ENCARGO_SEG_ENER": "encargo_seguranca_energetica",
    "RECEBIMENTO_ENCARGO_DH": "recebimento_encargo_dh",
    "ENCARGO_REST_OP_UNIT_COMT": "encargo_restricao_operativa_unit_commitment",
    "ENCARGO_IMPORTACAO": "encargo_importacao",
    "RECEBIMENTO_ENCARGO_RESERVA_OP": "recebimento_encargo_reserva_operativa",
    "RESSARCIMENTO_SERVICOS_ANCILARES": "ressarcimento_servicos_ancilares",
    "RESSARCIMENTO_CUSTO_OP_MNT_EQUIP": "ressarcimento_custo_operacao_manutencao_equipamento",
    "RESSARCIMENTO_CUSTO_OP_MNT_EQUIP_CAG": "ressarcimento_custo_operacao_manutencao_equipamento_cag",
    "RESSARCIMENTO_CUSTO_IMPL_OP_MNT_SEP": "ressarcimento_custo_implantacao_operacao_manutencao_sep",
    "RESSARCIMENTO_CUSTO_EMERGENCIAL": "ressarcimento_custo_emergencial",
    "RESSARCIMENTO_DIST_IMPL_OP_MNT": "ressarcimento_distribuidora_implantacao",
}


class EncargoEss(BaseModel):
    """Os encargos de serviço do sistema de um mês, em R$."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    encargo_constrained_on: Decimal | None = None
    encargo_constrained_off: Decimal | None = None
    outros_servicos_ancilares: Decimal | None = None
    encargo_cs: Decimal | None = None
    encargo_seguranca_energetica: Decimal | None = None
    recebimento_encargo_dh: Decimal | None = None
    encargo_restricao_operativa_unit_commitment: Decimal | None = None
    encargo_importacao: Decimal | None = None
    recebimento_encargo_reserva_operativa: Decimal | None = None
    ressarcimento_servicos_ancilares: Decimal | None = None
    ressarcimento_custo_operacao_manutencao_equipamento: Decimal | None = None
    ressarcimento_custo_operacao_manutencao_equipamento_cag: Decimal | None = None
    ressarcimento_custo_implantacao_operacao_manutencao_sep: Decimal | None = None
    ressarcimento_custo_emergencial: Decimal | None = None
    ressarcimento_distribuidora_implantacao: Decimal | None = None


@registrar
class CceeEncargoEss(CceeCsvCkan):
    """ESS mensal. CSV por ano, uma linha por mês."""

    dataset = "encargo_ess_ancilar"
    entidade = "encargo_ess"
    schema = EncargoEss

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        registro: dict[str, Any] = {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
        }
        for origem, destino in CAMPOS.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))
        return registro
