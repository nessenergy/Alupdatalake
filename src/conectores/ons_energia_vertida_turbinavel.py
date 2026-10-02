"""Conector ONS — energia vertida turbinável (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `energia-vertida-turbinavel` (arquivos em
`energia_vertida_turbinavel_ho/`), um CSV por mês desde **2024-01** (~14 MB, ~110
mil linhas, 153 usinas hidrelétricas). Antes disso o ONS publica **um CSV por
ano** (2015 a 2023, ~190 MB cada, outro nome de arquivo), que o conector não lê:
janela anterior a 2024-01 é recusada com erro claro (ver `OnsCsvMensal`).
Documentação: https://dados.ons.org.br/dataset/energia-vertida-turbinavel

Energia vertida turbinável é a água que a usina verteu **podendo** ter turbinado:
geração que deixou de existir, em MWmed. Responde, para a hidrelétrica, o que o
constrained-off responde para a eólica e a solar.

O que o arquivo real mostra: sem espaço sobrando, sem coluna vazia (todas as 18
preenchidas em 109.464 linhas de 09/2026), passo de uma hora no instante de
**início** (`00:00` cobre 00:00 a 00:59, ao contrário do hidrológico, que usa a
hora fim), e floats com até 20 casas decimais — o runner ajusta às 9 do NUMERIC.
`cod_usina` é o código nos modelos de otimização, não o CEG.
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
    "geracao_mwmed": "val_geracao",
    "disponibilidade_mwmed": "val_disponibilidade",
    "vazao_turbinada_m3s": "val_vazaoturbinada",
    "vazao_vertida_m3s": "val_vazaovertida",
    "vazao_vertida_nao_turbinavel_m3s": "val_vazaovertidanaoturbinavel",
    "produtividade_mw_por_m3s": "val_produtividade",
    "folga_geracao_mwmed": "val_folgadegeracao",
    "energia_vertida_mwmed": "val_energiavertida",
    "vazao_vertida_turbinavel_m3s": "val_vazaovertidaturbinavel",
    "energia_vertida_turbinavel_mwmed": "val_energiavertidaturbinavel",
}


class EnergiaVertidaTurbinavel(BaseModel):
    """Uma usina em uma hora: o que gerou, o que podia gerar e o que verteu."""

    data_referencia: date
    instante: datetime
    submercado: str
    nome_subsistema: str
    bacia: str
    rio: str
    agente: str
    reservatorio: str
    codigo_usina_modelo: int
    geracao_mwmed: Decimal | None = None
    disponibilidade_mwmed: Decimal | None = None
    vazao_turbinada_m3s: Decimal | None = None
    vazao_vertida_m3s: Decimal | None = None
    vazao_vertida_nao_turbinavel_m3s: Decimal | None = None
    produtividade_mw_por_m3s: Decimal | None = None
    folga_geracao_mwmed: Decimal | None = None
    energia_vertida_mwmed: Decimal | None = None
    vazao_vertida_turbinavel_m3s: Decimal | None = None
    energia_vertida_turbinavel_mwmed: Decimal | None = None

    @field_validator("submercado")
    @classmethod
    def _sigla(cls, valor: str) -> str:
        sigla = submercado(valor)
        if sigla is None:
            raise ValueError("submercado vazio")
        return sigla

    @field_validator("codigo_usina_modelo", mode="before")
    @classmethod
    def _inteiro_obrigatorio(cls, valor: Any) -> int:
        codigo = inteiro_ou_nulo(valor)
        if codigo is None:
            raise ValueError("cod_usina vazio")
        return codigo

    @field_validator(*_MEDIDAS, mode="before")
    @classmethod
    def _vazio_e_nulo(cls, valor: Any) -> Any:
        return vazio_e_nulo(valor)


@registrar
class OnsEnergiaVertidaTurbinavel(OnsCsvMensal):
    """Energia vertida turbinável por usina e hora. Um CSV por mês, em stream."""

    entidade = "energia_vertida_turbinavel"
    schema = EnergiaVertidaTurbinavel
    caminho = "energia_vertida_turbinavel_ho/ENERGIA_VERTIDA_TURBINAVEL_{ano}_{mes:02d}.csv"
    primeiro_mes = (2024, 1)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        texto = {
            "nome_subsistema": "nom_subsistema",
            "bacia": "nom_bacia",
            "rio": "nom_rio",
            "agente": "nom_agente",
            "reservatorio": "nom_reservatorio",
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
