"""Conector ONS — volume de espera recomendado, diário por reservatório (Aditivo 01).

Fonte: Dados Abertos ONS, dataset `res_volumeespera`, um CSV por ano, desde 2006.
Documentação: https://dados.ons.org.br/dataset/res_volumeespera

Extração na base `OnsCsvAnual`. O volume de espera é o limite de enchimento
que o ONS recomenda para cada reservatório, reservando espaço para amortecer
cheias — em % do volume útil (50,4 a 100 em 2026; acima de 100 é recusado).

O que o dado impõe:

- a série tem **anos faltando** (2008 não existe no catálogo) e um arquivo do
  ano seguinte; a base trata ano ausente como aviso;
- bacia e REE vêm com espaços à direita; o trim vive no validador;
- a ordem na cascata (`num_ordemcs`) vem vazia em 310 linhas de 2026.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import OnsCsvAnual, submercado, vazio_e_nulo
from src.core.registry import registrar


class VolumeEspera(BaseModel):
    """Volume de espera recomendado de um reservatório em um dia, em % do volume útil."""

    data_referencia: date
    submercado: str
    tipo_reservatorio: str | None = None
    bacia: str | None = None
    ree: str | None = None
    codigo_reservatorio: str
    reservatorio: str
    ordem_cascata: int | None = None
    codigo_usina_ons: str | None = None
    volume_espera_percentual: Decimal

    @field_validator("submercado")
    @classmethod
    def _sigla(cls, valor: str) -> str:
        sigla = submercado(valor)
        if sigla is None:
            raise ValueError("submercado vazio")
        return sigla

    @field_validator("tipo_reservatorio", "bacia", "ree", "codigo_usina_ons", "ordem_cascata", mode="before")
    @classmethod
    def _vazio_e_nulo(cls, valor: Any) -> Any:
        return vazio_e_nulo(valor)

    @field_validator("codigo_reservatorio", "reservatorio")
    @classmethod
    def _preenchido(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("campo obrigatório vazio")
        return texto

    @field_validator("volume_espera_percentual")
    @classmethod
    def _entre_zero_e_cem(cls, valor: Decimal) -> Decimal:
        if not (Decimal(0) <= valor <= Decimal(100)):
            raise ValueError(f"volume de espera fora de [0,100]: {valor}")
        return valor


@registrar
class OnsVolumeEspera(OnsCsvAnual):
    """Volume de espera recomendado, diário por reservatório."""

    entidade = "volume_espera"
    schema = VolumeEspera
    caminho = "res_volumeespera/RES_VOLUMEESPERA_{ano}.csv"
    coluna_data = "din_instante"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["din_instante"][:10],
            "submercado": bruto.get("id_subsistema", ""),
            "tipo_reservatorio": bruto.get("tip_reservatorio"),
            "bacia": bruto.get("nom_bacia"),
            "ree": bruto.get("nom_ree"),
            "codigo_reservatorio": bruto.get("id_reservatorio", ""),
            "reservatorio": bruto.get("nom_reservatorio", ""),
            "ordem_cascata": bruto.get("num_ordemcs"),
            "codigo_usina_ons": bruto.get("cod_usina"),
            "volume_espera_percentual": bruto["val_volumeespera"],
        }
