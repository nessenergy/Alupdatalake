"""Conector ONS — energia armazenada (EAR) diária por reservatório (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `ear_reservatorio_di`, um CSV por ano.
Documentação: https://dados.ons.org.br/dataset/ear-diario-por-reservatorio

Extração na base `OnsCsvAnual`. O que o dado impõe:

- **Tem subsistema** (`id_subsistema`), e alimenta a dimensão `submercado`.
  Reservatório que contribui para outro subsistema a jusante traz também
  `id_subsistema_jusante`; na maioria das linhas esse par vem vazio.
- **Reservatório sem medição vem com os campos de EAR vazios** — 2.421 de
  20.444 linhas em 2026, tipicamente "Reservatório sem usina". Vazio vira
  nulo e a linha continua válida: é ausência, não erro.
- **O percentual passa de 100** (até 182% em 2026): só negativo é recusado.
- As oito colunas `val_contribear*` são a participação do reservatório na EAR
  da bacia, do subsistema e do SIN; vêm como fração (0-1) e passam fiéis.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import OnsCsvAnual, submercado, vazio_e_nulo
from src.core.registry import registrar

_NUMERICOS = (
    "ear_proprio_mwmes",
    "ear_jusante_mwmes",
    "ear_max_proprio_mwmes",
    "ear_max_jusante_mwmes",
    "ear_percentual",
    "ear_total_mwmes",
    "ear_max_total_mwmes",
    "contribuicao_ear_bacia",
    "contribuicao_ear_max_bacia",
    "contribuicao_ear_subsistema",
    "contribuicao_ear_max_subsistema",
    "contribuicao_ear_subsistema_jusante",
    "contribuicao_ear_max_subsistema_jusante",
    "contribuicao_ear_sin",
    "contribuicao_ear_max_sin",
)
_ORIGEM = {
    "ear_proprio_mwmes": "ear_reservatorio_subsistema_proprio_mwmes",
    "ear_jusante_mwmes": "ear_reservatorio_subsistema_jusante_mwmes",
    "ear_max_proprio_mwmes": "earmax_reservatorio_subsistema_proprio_mwmes",
    "ear_max_jusante_mwmes": "earmax_reservatorio_subsistema_jusante_mwmes",
    "ear_percentual": "ear_reservatorio_percentual",
    "ear_total_mwmes": "ear_total_mwmes",
    "ear_max_total_mwmes": "ear_maxima_total_mwmes",
    "contribuicao_ear_bacia": "val_contribearbacia",
    "contribuicao_ear_max_bacia": "val_contribearmaxbacia",
    "contribuicao_ear_subsistema": "val_contribearsubsistema",
    "contribuicao_ear_max_subsistema": "val_contribearmaxsubsistema",
    "contribuicao_ear_subsistema_jusante": "val_contribearsubsistemajusante",
    "contribuicao_ear_max_subsistema_jusante": "val_contribearmaxsubsistemajusante",
    "contribuicao_ear_sin": "val_contribearsin",
    "contribuicao_ear_max_sin": "val_contribearmaxsin",
}


class EarReservatorio(BaseModel):
    """EAR de um reservatório em um dia, com a participação nos agregados."""

    data_referencia: date
    reservatorio: str
    codigo_reservatorio_planejamento: str | None = None
    tipo_reservatorio: str | None = None
    bacia: str | None = None
    ree: str | None = None
    submercado: str
    subsistema_jusante: str | None = None
    ear_proprio_mwmes: Decimal | None = None
    ear_jusante_mwmes: Decimal | None = None
    ear_max_proprio_mwmes: Decimal | None = None
    ear_max_jusante_mwmes: Decimal | None = None
    ear_percentual: Decimal | None = None
    ear_total_mwmes: Decimal | None = None
    ear_max_total_mwmes: Decimal | None = None
    contribuicao_ear_bacia: Decimal | None = None
    contribuicao_ear_max_bacia: Decimal | None = None
    contribuicao_ear_subsistema: Decimal | None = None
    contribuicao_ear_max_subsistema: Decimal | None = None
    contribuicao_ear_subsistema_jusante: Decimal | None = None
    contribuicao_ear_max_subsistema_jusante: Decimal | None = None
    contribuicao_ear_sin: Decimal | None = None
    contribuicao_ear_max_sin: Decimal | None = None

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

    @field_validator("subsistema_jusante", mode="before")
    @classmethod
    def _jusante(cls, valor: Any) -> Any:
        return submercado(vazio_e_nulo(valor))

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
class OnsEarReservatorio(OnsCsvAnual):
    """EAR diária por reservatório."""

    entidade = "ear_reservatorio"
    schema = EarReservatorio
    caminho = "ear_reservatorio_di/EAR_DIARIO_RESERVATORIOS_{ano}.csv"
    coluna_data = "ear_data"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["ear_data"][:10],
            "reservatorio": bruto.get("nom_reservatorio", ""),
            "codigo_reservatorio_planejamento": bruto.get("cod_resplanejamento"),
            "tipo_reservatorio": bruto.get("tip_reservatorio"),
            "bacia": bruto.get("nom_bacia"),
            "ree": bruto.get("nom_ree"),
            "submercado": bruto.get("id_subsistema", ""),
            "subsistema_jusante": bruto.get("id_subsistema_jusante"),
            **{campo: bruto.get(origem) for campo, origem in _ORIGEM.items()},
        }
