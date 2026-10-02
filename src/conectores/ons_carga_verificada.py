"""Conector ONS — Carga de Energia Verificada, semi-horária por área de carga (Aditivo 01, público).

Fonte: API `apicarga.ons.org.br/prd/cargaverificada`, dataset `carga-energia-verificada`.
Documentação: https://dados.ons.org.br/dataset/carga-energia-verificada

Carga realizada, com a parcela supervisionada pelo ONS, a não supervisionada
(medição da CCEE) e a micro e minigeração distribuída (MMGD). O ONS revisa o
dado publicado (`din_atualizacao`); a Silver fica com a ingestão mais recente.
Mecânica da API em `ons_carga_api`.

Valores negativos existem na origem (carga líquida e supervisionada onde a MMGD
passa da carga, perdas e consistência): nada é recusado por sinal.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_carga_api import OnsCargaApi, area_conhecida
from src.core.registry import registrar


class CargaVerificada(BaseModel):
    """Carga verificada de uma área no fim de uma meia hora, em MWmed."""

    data_referencia: date
    instante_utc: datetime
    area_carga: str
    atualizado_em: datetime
    carga_global_mwmed: Decimal
    carga_global_consistida_mwmed: Decimal
    carga_global_sem_mmgd_mwmed: Decimal
    carga_mmgd_mwmed: Decimal
    carga_supervisionada_mwmed: Decimal
    carga_nao_supervisionada_mwmed: Decimal
    consistencia_mwmed: Decimal

    @field_validator("area_carga")
    @classmethod
    def _area(cls, valor: str) -> str:
        return area_conhecida(valor)


@registrar
class OnsCargaVerificada(OnsCargaApi):
    """Carga verificada por área de carga."""

    entidade = "carga_verificada"
    schema = CargaVerificada
    endpoint = "cargaverificada"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["dat_referencia"],
            "instante_utc": bruto["din_referenciautc"],
            "area_carga": bruto["cod_areacarga"],
            "atualizado_em": bruto["din_atualizacao"],
            "carga_global_mwmed": bruto["val_cargaglobal"],
            "carga_global_consistida_mwmed": bruto["val_cargaglobalcons"],
            "carga_global_sem_mmgd_mwmed": bruto["val_cargaglobalsmmgd"],
            "carga_mmgd_mwmed": bruto["val_cargammgd"],
            "carga_supervisionada_mwmed": bruto["val_cargasupervisionada"],
            "carga_nao_supervisionada_mwmed": bruto["val_carganaosupervisionada"],
            "consistencia_mwmed": bruto["val_consistencia"],
        }
