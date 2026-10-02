"""Conector ONS — dados hidrológicos por reservatório, base horária (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `dados_hidrologicos_ho`, um CSV por mês, desde
2010-01 (~20 MB e ~120 mil linhas por mês, 170 reservatórios).
Documentação: https://dados.ons.org.br/dataset/dados-hidrologicos-ho

Extração na base `OnsCsvMensal`. O que o arquivo real impõe:

1. **Texto com espaço à direita**, em largura fixa (`N `, `Reservatório com Usina`
   com 18 espaços, bacia com 15 colunas, `id_reservatorio` com 6): tudo é aparado.
2. **O instante é a hora fim.** Segundo o dicionário do ONS, `01:00` cobre de
   00:00 a 00:59. O fim do dia vem como `23:59:00`, na mesma data. O instante
   inteiro é a chave, como no constrained-off; a Silver deriva `hora_fim`.
3. **Colunas vazias são ausência, não zero**: `val_vazaoturbinada` vem vazia em
   reservatório sem usina, `cod_usina` em reservatório fictício. Viram NULL.
4. **Há valores negativos** (volume útil até -1.917%, afluência até -93.681 m3/s)
   e volume acima de 100%. O Bronze guarda o que a origem publica; a regra de
   faixa vive na Gold, que a declara.
5. `cod_usina` é o código da usina **nos modelos de otimização**, não o CEG: vai
   para `codigo_usina_modelo`, e a dimensão `codigo_usina` da Silver fica nula.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import instante, submercado, vazio_e_nulo
from src.conectores.ons_csv_mensal import OnsCsvMensal, inteiro_ou_nulo
from src.core.registry import registrar

_MEDIDAS = {
    "nivel_montante_m": "val_nivelmontante",
    "nivel_jusante_m": "val_niveljusante",
    "volume_util_percentual": "val_volumeutil",
    "vazao_afluente_m3s": "val_vazaoafluente",
    "vazao_defluente_m3s": "val_vazaodefluente",
    "vazao_turbinada_m3s": "val_vazaoturbinada",
    "vazao_vertida_m3s": "val_vazaovertida",
    "vazao_outras_estruturas_m3s": "val_vazaooutrasestruturas",
    "vazao_transferida_m3s": "val_vazaotransferida",
    "vazao_vertida_nao_turbinavel_m3s": "val_vazaovertidanaoturbinavel",
}


class DadoHidrologico(BaseModel):
    """Situação de um reservatório em uma hora (hora fim), com níveis, volume e vazões."""

    data_referencia: date
    instante: datetime
    submercado: str
    nome_subsistema: str
    tipo_reservatorio: str
    bacia: str
    id_reservatorio: str
    nome_reservatorio: str
    codigo_usina_modelo: int | None = None
    nivel_montante_m: Decimal | None = None
    nivel_jusante_m: Decimal | None = None
    volume_util_percentual: Decimal | None = None
    vazao_afluente_m3s: Decimal | None = None
    vazao_defluente_m3s: Decimal | None = None
    vazao_turbinada_m3s: Decimal | None = None
    vazao_vertida_m3s: Decimal | None = None
    vazao_outras_estruturas_m3s: Decimal | None = None
    vazao_transferida_m3s: Decimal | None = None
    vazao_vertida_nao_turbinavel_m3s: Decimal | None = None

    @field_validator("submercado")
    @classmethod
    def _sigla(cls, valor: str) -> str:
        sigla = submercado(valor)
        if sigla is None:
            raise ValueError("submercado vazio")
        return sigla

    @field_validator("id_reservatorio", "nome_reservatorio")
    @classmethod
    def _preenchido(cls, valor: str) -> str:
        if not valor:
            raise ValueError("identificação do reservatório vazia")
        return valor

    @field_validator("codigo_usina_modelo", mode="before")
    @classmethod
    def _inteiro(cls, valor: Any) -> int | None:
        return inteiro_ou_nulo(valor)

    @field_validator(*_MEDIDAS, mode="before")
    @classmethod
    def _vazio_e_nulo(cls, valor: Any) -> Any:
        return vazio_e_nulo(valor)


@registrar
class OnsDadosHidrologicos(OnsCsvMensal):
    """Dados hidrológicos horários por reservatório. Um CSV por mês, em stream."""

    entidade = "dados_hidrologicos"
    schema = DadoHidrologico
    caminho = "dados_hidrologicos_ho/DADOS_HIDROLOGICOS_HO_{ano}_{mes:02d}.csv"
    primeiro_mes = (2010, 1)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        texto = {
            "nome_subsistema": "nom_subsistema",
            "tipo_reservatorio": "tip_reservatorio",
            "bacia": "nom_bacia",
            "id_reservatorio": "id_reservatorio",
            "nome_reservatorio": "nom_reservatorio",
        }
        return (
            {
                "data_referencia": bruto["din_instante"][:10],
                "instante": instante(bruto["din_instante"]),
                "submercado": bruto.get("id_subsistema", ""),
                "codigo_usina_modelo": bruto.get("cod_usina"),
            }
            | {destino: (bruto.get(origem) or "").strip() for destino, origem in texto.items()}
            | {destino: bruto.get(origem) for destino, origem in _MEDIDAS.items()}
        )
