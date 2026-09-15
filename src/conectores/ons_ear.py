"""Conector ONS — energia armazenada (EAR) diária por subsistema (Onda 1, público).

Fonte: Dados Abertos ONS, dataset `ear_subsistema_di`, um CSV por ano.
Documentação: https://dados.ons.org.br/dataset/ear-diario-por-subsistema

Mesmo formato do `ons_carga`: CSV remoto particionado por ano, delimitador
`;`. Duas diferenças da carga: a data já vem ISO (`ear_data`, sem componente
de hora) e o `id_subsistema` aparece com espaço à direita em alguns anos —
por isso o trim vive no validador, não na extração.
"""

from __future__ import annotations

import csv
import logging
from datetime import date
from decimal import Decimal
from io import StringIO
from typing import TYPE_CHECKING, Any

import requests
from pydantic import BaseModel, field_validator

from src.core.conector import Conector
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/ear_subsistema_di/EAR_DIARIO_SUBSISTEMA_{ano}.csv"

# Mesmas siglas de `submercado` que o `ons_carga` já usa; aqui só chega com
# espaço à direita em alguns anos do catálogo.
SUBMERCADOS = frozenset({"N", "NE", "S", "SE"})

logger = logging.getLogger(__name__)


class EarDiario(BaseModel):
    """Energia armazenada verificada de um subsistema em um dia, em MWmês."""

    data_referencia: date
    submercado: str
    nome_subsistema: str
    ear_max_mwmes: Decimal
    """Capacidade máxima de armazenamento do subsistema."""
    ear_verificada_mwmes: Decimal
    """Energia armazenada verificada no dia."""
    ear_verificada_percentual: Decimal
    """`ear_verificada_mwmes` como percentual de `ear_max_mwmes` — não pode
    passar de 100: é armazenamento sobre a própria capacidade máxima."""

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        sigla = valor.strip().upper()
        if sigla not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return sigla

    @field_validator("ear_max_mwmes", "ear_verificada_mwmes")
    @classmethod
    def _nao_negativo(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"valor negativo: {valor}")
        return valor

    @field_validator("ear_verificada_percentual")
    @classmethod
    def _percentual_entre_zero_e_cem(cls, valor: Decimal) -> Decimal:
        if not (Decimal(0) <= valor <= Decimal(100)):
            raise ValueError(f"percentual de EAR fora de [0,100]: {valor}")
        return valor


@registrar
class OnsEar(Conector):
    """EAR diária por subsistema. Um CSV por ano, filtrado pela janela."""

    fonte = "ons"
    entidade = "ear"
    schema = EarDiario
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por ano de arquivo, não por dias

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _baixar_ano(self, ano: int) -> str | None:
        """CSV do ano, ou `None` quando o catálogo ainda não publicou aquele ano."""
        from src.core.config import get_settings

        resposta = self._sessao.get(URL.format(ano=ano), timeout=get_settings().http_timeout)
        if resposta.status_code == 404:
            return None
        resposta.raise_for_status()
        return resposta.text

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        for ano in range(janela.inicio.year, janela.fim.year + 1):
            logger.info("ONS EAR: baixando %d", ano)
            try:
                conteudo = self._baixar_ano(ano)
            except requests.exceptions.HTTPError as exc:
                resposta = exc.response
                if resposta is not None and resposta.status_code == 404:
                    conteudo = None
                else:
                    raise
            if conteudo is None:
                logger.warning("ONS EAR: %d sem recurso publicado no catálogo, ignorado", ano)
                continue

            leitor = csv.DictReader(StringIO(conteudo), delimiter=";")
            for linha in leitor:
                referencia = linha.get("ear_data", "")[:10]
                if not referencia:
                    continue
                if not (janela.inicio.isoformat() <= referencia <= janela.fim.isoformat()):
                    continue  # o arquivo é anual; a janela é o recorte pedido
                yield linha

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["ear_data"][:10],
            "submercado": bruto["id_subsistema"],
            "nome_subsistema": bruto.get("nom_subsistema", ""),
            "ear_max_mwmes": bruto["ear_max_subsistema"],
            "ear_verificada_mwmes": bruto["ear_verif_subsistema_mwmes"],
            "ear_verificada_percentual": bruto["ear_verif_subsistema_percentual"],
        }
