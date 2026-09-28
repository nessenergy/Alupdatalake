"""Conector ONS — CVU das usinas térmicas, por semana operativa (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `cvu_usitermica_se`, um CSV por ano, desde 2020.
Documentação: https://dados.ons.org.br/dataset/cvu-usitermica

Extração na base `OnsCsvAnual`. O Custo Variável Unitário que o ONS usa para
decidir a ordem de despacho das térmicas, por semana operativa do PMO. Não é o
CVU estrutural da CCEE (`ccee_cvu_estrutural`): este é o valor semanal usado na
operação. O que o dado impõe:

- **A semana é filtrada pelo fim** (`dat_fimsemana`). O arquivo de 2026 traz a
  semana de 27/12/2025 a 02/01/2026; filtrar pelo início a deixaria de fora.
  `data_referencia` continua sendo o início da semana.
- **Cada revisão do PMO é uma semana diferente** (revisão 0 é a primeira semana
  do mês, a 1 a segunda...), não uma versão da mesma semana. A chave é
  (semana, usina); a revisão é atributo.
- **A origem publica linhas idênticas em dobro** — 38 em 2026. Entram as duas
  no Bronze (fiel à origem) e a Silver fica com uma.
- CVU zero é valor (usina a custo zero), não ausência.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import OnsCsvAnual, submercado
from src.core.registry import registrar


class CvuTermica(BaseModel):
    """CVU de uma térmica numa semana operativa, em R$/MWh."""

    data_referencia: date
    """Início da semana operativa."""
    fim_semana: date
    ano_referencia: int
    mes_referencia: int
    revisao: int
    semana_operativa: str
    codigo_usina_planejamento: str
    submercado: str
    usina: str
    cvu_reais_mwh: Decimal

    @field_validator("submercado")
    @classmethod
    def _sigla(cls, valor: str) -> str:
        sigla = submercado(valor)
        if sigla is None:
            raise ValueError("submercado vazio")
        return sigla

    @field_validator("codigo_usina_planejamento", "usina", "semana_operativa")
    @classmethod
    def _preenchido(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("campo obrigatório vazio")
        return texto

    @field_validator("cvu_reais_mwh")
    @classmethod
    def _nao_negativo(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"CVU negativo: {valor}")
        return valor


@registrar
class OnsCvuTermica(OnsCsvAnual):
    """CVU semanal das usinas térmicas."""

    entidade = "cvu_termica"
    schema = CvuTermica
    caminho = "cvu_usitermica_se/CVU_USINA_TERMICA_{ano}.csv"
    coluna_data = "dat_fimsemana"  # ver docstring: o filtro é pelo fim da semana

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["dat_iniciosemana"][:10],
            "fim_semana": bruto["dat_fimsemana"][:10],
            "ano_referencia": bruto["ano_referencia"],
            "mes_referencia": bruto["mes_referencia"],
            "revisao": bruto["num_revisao"],
            "semana_operativa": bruto.get("nom_semanaoperativa", ""),
            "codigo_usina_planejamento": bruto.get("cod_usinaplanejamento", ""),
            "submercado": bruto.get("id_subsistema", ""),
            "usina": bruto.get("nom_usina", ""),
            "cvu_reais_mwh": bruto["val_cvu"],
        }
