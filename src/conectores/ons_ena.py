"""Conector ONS — energia natural afluente (ENA) diária por subsistema (Onda 1, público).

Fonte: Dados Abertos ONS, dataset `ena_subsistema_di`, um CSV por ano.
Documentação: https://dados.ons.org.br/dataset/ena-diario-por-subsistema

Mesmo formato do `ons_ear` — mesma origem (S3 do ONS), mesma armadilha do
`id_subsistema` com espaço à direita, mesma data já ISO.

Os percentuais aqui comparam com a **MLT** (média de longo termo), não com uma
capacidade física: um subsistema recebendo mais afluência que a sua própria
média histórica passa de 100% em ano úmido, e isso é dado correto, não erro
de captura — diferente do percentual de EAR, que é fração da capacidade
máxima e não pode ultrapassar 100.
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

URL = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/ena_subsistema_di/ENA_DIARIO_SUBSISTEMA_{ano}.csv"

SUBMERCADOS = frozenset({"N", "NE", "S", "SE"})

# Sanidade contra erro de captura/parsing (vírgula decimal trocada, campo
# deslocado) sem rejeitar ano úmido de verdade — MLT já documentado acima de
# 150% em anos de El Niño forte.
PERCENTUAL_MLT_MAXIMO = Decimal(500)

logger = logging.getLogger(__name__)


class EnaDiario(BaseModel):
    """Energia natural afluente de um subsistema em um dia, em MWmed."""

    data_referencia: date
    submercado: str
    nome_subsistema: str
    ena_bruta_mwmed: Decimal
    """Afluência bruta da região."""
    ena_bruta_percentual_mlt: Decimal
    """`ena_bruta_mwmed` como percentual da MLT (média de longo termo) da região."""
    ena_armazenavel_mwmed: Decimal
    """Parcela da afluência que é armazenável (não fio d'água)."""
    ena_armazenavel_percentual_mlt: Decimal
    """`ena_armazenavel_mwmed` como percentual da MLT."""

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        sigla = valor.strip().upper()
        if sigla not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return sigla

    @field_validator("ena_bruta_mwmed", "ena_armazenavel_mwmed")
    @classmethod
    def _nao_negativo(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"valor negativo: {valor}")
        return valor

    @field_validator("ena_bruta_percentual_mlt", "ena_armazenavel_percentual_mlt")
    @classmethod
    def _percentual_mlt_plausivel(cls, valor: Decimal) -> Decimal:
        if not (Decimal(0) <= valor <= PERCENTUAL_MLT_MAXIMO):
            raise ValueError(f"percentual de MLT fora da faixa plausível [0,{PERCENTUAL_MLT_MAXIMO}]: {valor}")
        return valor


@registrar
class OnsEna(Conector):
    """ENA diária por subsistema. Um CSV por ano, filtrado pela janela."""

    fonte = "ons"
    entidade = "ena"
    schema = EnaDiario
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
            logger.info("ONS ENA: baixando %d", ano)
            try:
                conteudo = self._baixar_ano(ano)
            except requests.exceptions.HTTPError as exc:
                resposta = exc.response
                if resposta is not None and resposta.status_code == 404:
                    conteudo = None
                else:
                    raise
            if conteudo is None:
                logger.warning("ONS ENA: %d sem recurso publicado no catálogo, ignorado", ano)
                continue

            leitor = csv.DictReader(StringIO(conteudo), delimiter=";")
            for linha in leitor:
                referencia = linha.get("ena_data", "")[:10]
                if not referencia:
                    continue
                if not (janela.inicio.isoformat() <= referencia <= janela.fim.isoformat()):
                    continue  # o arquivo é anual; a janela é o recorte pedido
                yield linha

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["ena_data"][:10],
            "submercado": bruto["id_subsistema"],
            "nome_subsistema": bruto.get("nom_subsistema", ""),
            "ena_bruta_mwmed": bruto["ena_bruta_regiao_mwmed"],
            "ena_bruta_percentual_mlt": bruto["ena_bruta_regiao_percentualmlt"],
            "ena_armazenavel_mwmed": bruto["ena_armazenavel_regiao_mwmed"],
            "ena_armazenavel_percentual_mlt": bruto["ena_armazenavel_regiao_percentualmlt"],
        }
