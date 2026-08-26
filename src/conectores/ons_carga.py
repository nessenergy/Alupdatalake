"""Conector ONS — carga de energia diária por subsistema (Onda 1, público).

Fonte: Dados Abertos ONS, dataset `carga_energia_di`, um CSV por ano.
Documentação: https://dados.ons.org.br/dataset/carga-energia

Quarto formato do projeto: **CSV remoto particionado por ano**, não JSON. A
janela decide quais anos baixar; as linhas fora do intervalo são descartadas na
extração, para não carregar o ano inteiro quando se pede uma semana.

É a primeira fonte que preenche `submercado` — a dimensão que permite cruzar
carga com preço e com o parque gerador.
"""

from __future__ import annotations

import csv
import logging
from datetime import date
from decimal import Decimal
from io import StringIO
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, field_validator

from src.core.conector import Conector
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/carga_energia_di/CARGA_ENERGIA_{ano}.csv"

# O ONS publica o subsistema por sigla; o projeto usa as mesmas siglas como
# `submercado` (SE/CO aparece como SE nos dados do ONS).
SUBMERCADOS = frozenset({"N", "NE", "S", "SE"})

logger = logging.getLogger(__name__)


class CargaDiaria(BaseModel):
    """Carga de energia de um subsistema em um dia, em MWmed."""

    data_referencia: date
    submercado: str
    nome_subsistema: str
    carga_mwmed: Decimal

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        sigla = valor.strip().upper()
        if sigla not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return sigla


@registrar
class OnsCarga(Conector):
    """Carga diária por subsistema. Um CSV por ano, filtrado pela janela."""

    fonte = "ons"
    entidade = "carga"
    schema = CargaDiaria
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por ano de arquivo, não por dias

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _baixar_ano(self, ano: int) -> str:
        from src.core.config import get_settings

        resposta = self._sessao.get(URL.format(ano=ano), timeout=get_settings().http_timeout)
        resposta.raise_for_status()
        return resposta.text

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        for ano in range(janela.inicio.year, janela.fim.year + 1):
            logger.info("ONS carga: baixando %d", ano)
            leitor = csv.DictReader(StringIO(self._baixar_ano(ano)), delimiter=";")
            for linha in leitor:
                instante = linha.get("din_instante", "")[:10]
                if not instante:
                    continue
                if not (janela.inicio.isoformat() <= instante <= janela.fim.isoformat()):
                    continue  # o arquivo é anual; a janela é o recorte pedido
                yield linha

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["din_instante"][:10],
            "submercado": bruto["id_subsistema"],
            "nome_subsistema": bruto.get("nom_subsistema", ""),
            "carga_mwmed": bruto["val_cargaenergiamwmed"],
        }
