"""Conector ONS — energia natural afluente (ENA) diária por reservatório (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `ena_reservatorio_di`, um CSV por ano.
Documentação: https://dados.ons.org.br/dataset/ena-diario-por-reservatorio

Extração na base `OnsCsvAnual`. O que o dado impõe:

- **Tem subsistema** (`id_subsistema`), e alimenta a dimensão `submercado`.
- **Sem medição, os campos de ENA vêm vazios** — 269 de 41.695 linhas em
  2026. Vazio vira nulo e a linha continua válida.
- O percentual é sobre a média de longo termo (MLT) e passa de 100 com
  folga — até 1.750% em 2026, em reservatório pequeno com cheia. Só negativo é
  recusado.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import OnsCsvAnual, submercado, vazio_e_nulo
from src.core.registry import registrar

_ORIGEM = {
    "ena_bruta_mwmed": "ena_bruta_res_mwmed",
    "ena_bruta_percentual_mlt": "ena_bruta_res_percentualmlt",
    "ena_armazenavel_mwmed": "ena_armazenavel_res_mwmed",
    "ena_armazenavel_percentual_mlt": "ena_armazenavel_res_percentualmlt",
    "ena_queda_bruta_mwmed": "ena_queda_bruta",
    "mlt_ena_mwmed": "mlt_ena",
}
_NUMERICOS = tuple(_ORIGEM)


class EnaReservatorio(BaseModel):
    """ENA de um reservatório em um dia, em MWmed e % da MLT."""

    data_referencia: date
    reservatorio: str
    codigo_reservatorio_planejamento: str | None = None
    tipo_reservatorio: str | None = None
    bacia: str | None = None
    ree: str | None = None
    submercado: str
    ena_bruta_mwmed: Decimal | None = None
    ena_bruta_percentual_mlt: Decimal | None = None
    ena_armazenavel_mwmed: Decimal | None = None
    ena_armazenavel_percentual_mlt: Decimal | None = None
    ena_queda_bruta_mwmed: Decimal | None = None
    mlt_ena_mwmed: Decimal | None = None

    @field_validator("reservatorio")
    @classmethod
    def _reservatorio_preenchido(cls, valor: str) -> str:
        nome = valor.strip()
        if not nome:
            raise ValueError("reservatório vazio")
        return nome

    @field_validator("codigo_reservatorio_planejamento", "tipo_reservatorio", "bacia", "ree", mode="before")
    @classmethod
    def _texto_vazio_e_nulo(cls, valor: Any) -> Any:
        return vazio_e_nulo(valor)

    @field_validator("submercado")
    @classmethod
    def _submercado_obrigatorio(cls, valor: str) -> str:
        sigla = submercado(valor)
        if sigla is None:
            raise ValueError("submercado vazio")
        return sigla

    @field_validator(*_NUMERICOS, mode="before")
    @classmethod
    def _numero_vazio_e_nulo(cls, valor: Any) -> Any:
        return vazio_e_nulo(valor)

    @field_validator(*_NUMERICOS)
    @classmethod
    def _nao_negativo(cls, valor: Decimal | None) -> Decimal | None:
        if valor is not None and valor < 0:
            raise ValueError(f"valor negativo: {valor}")
        return valor


@registrar
class OnsEnaReservatorio(OnsCsvAnual):
    """ENA diária por reservatório."""

    entidade = "ena_reservatorio"
    schema = EnaReservatorio
    caminho = "ena_reservatorio_di/ENA_DIARIO_RESERVATORIOS_{ano}.csv"
    coluna_data = "ena_data"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["ena_data"][:10],
            "reservatorio": bruto.get("nom_reservatorio", ""),
            "codigo_reservatorio_planejamento": bruto.get("cod_resplanejamento"),
            "tipo_reservatorio": bruto.get("tip_reservatorio"),
            "bacia": bruto.get("nom_bacia"),
            "ree": bruto.get("nom_ree"),
            "submercado": bruto.get("id_subsistema", ""),
            **{campo: bruto.get(origem) for campo, origem in _ORIGEM.items()},
        }
