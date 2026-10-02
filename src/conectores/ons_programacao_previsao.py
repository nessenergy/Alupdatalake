"""Conector ONS — previsão versus programado de eólicas e solares (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `programacao_x_previsao`, um CSV por dia.
Documentação: https://dados.ons.org.br/dataset/programacao_x_previsao

Extração na base `OnsArquivoDiario`. Por usina do PDP e patamar de meia hora:
quanto o ONS previu de geração e quanto programou, em MW. O que o dado impõe:

- **A data vem como `AAAAMMDD`**, sem hífen.
- **A unidade é a usina do PDP** (`cod_usinapdp`, ex.: `MMRAL`), um código
  próprio do ONS que não é o CEG; `codigo_usina` fica nulo na Silver. Muitas
  são conjuntos de usinas (`CJFVRIOALTO`).
- **Código e nome vêm preenchidos com espaços à direita.**
- **48 patamares por dia** (meia em meia hora); o dicionário do ONS não diz
  qual hora cada um cobre, então o patamar fica como vem.
- Previsão e programado nunca vieram negativos nem vazios nos 730 arquivos
  lidos, e o dicionário os proíbe: negativo é recusado.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, ClassVar

from pydantic import BaseModel, field_validator

from src.conectores.ons_arquivo_diario import OnsArquivoDiario
from src.core.registry import registrar


class ProgramacaoPrevisao(BaseModel):
    """Previsão e programação de uma usina em um patamar de meia hora, em MW."""

    data_referencia: date
    patamar: int
    codigo_usina_pdp: str
    nome_usina: str
    previsao_mw: Decimal
    programado_mw: Decimal

    @field_validator("codigo_usina_pdp", "nome_usina")
    @classmethod
    def _trim_e_preenchido(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("texto vazio")
        return texto

    @field_validator("previsao_mw", "programado_mw")
    @classmethod
    def _nao_negativo(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"valor negativo: {valor}")
        return valor


@registrar
class OnsProgramacaoPrevisao(OnsArquivoDiario):
    """Previsão versus programado de eólicas e solares, um arquivo por dia."""

    entidade = "programacao_previsao"
    schema = ProgramacaoPrevisao
    caminho: ClassVar[str] = "programacao_x_previsao/PROGRAMACAO_X_PREVISAO_{dia:%Y_%m_%d}.csv"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": datetime.strptime(bruto["dat_programacao"].strip(), "%Y%m%d").date().isoformat(),
            "patamar": bruto["num_patamar"],
            "codigo_usina_pdp": bruto["cod_usinapdp"],
            "nome_usina": bruto["nom_usinapdp"],
            "previsao_mw": bruto["val_previsao"],
            "programado_mw": bruto["val_programado"],
        }
