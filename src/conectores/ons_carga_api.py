"""Base dos conectores de carga do ONS que só existem como API (Aditivo 01, público).

Os conjuntos `carga-energia-programada` e `carga-energia-verificada` não têm CSV
no catálogo: a origem é a API `apicarga.ons.org.br`, **pública, sem token**
(verificado em 02/10/2026). Os dois endpoints têm a mesma forma e o mesmo
catálogo de áreas; o que muda é o endpoint, as colunas e o `transformar()`.

Contrato da API (Swagger do ONS e chamadas reais):
- `dat_inicio` e `dat_fim` (`AAAA-MM-DD`), **inclusivas**, e `cod_areacarga`,
  obrigatório: sem ele a API devolve `[]` sem erro;
- limite documentado de 3 meses por chamada. Passar disso não dá erro: a
  verificada **trunca a resposta em silêncio** (~2,4 MB) — por isso a janela
  aqui é de 31 dias, bem dentro do que a API entrega inteiro;
- sem paginação; sem limite de taxa observado (várias centenas de chamadas
  seguidas em 02/10/2026, sem 429).

`ons_carga` (CSV diário por subsistema, média do dia) é outra coisa: esta é
semi-horária e por área de carga.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from src.core.conector import Conector
from src.core.http import criar_sessao

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

BASE = "https://apicarga.ons.org.br/prd/"

# Catálogo oficial do parâmetro `cod_areacarga` (descrição no Swagger do ONS):
# 4 subsistemas, 25 áreas geoelétricas (estados e agrupamentos) e 4 de perdas.
# A API também responde a `SIN` (só zeros) e `SE` (~650 MWmed até 04/2025, sem
# documentação): ficam de fora, e o dicionário registra o porquê.
AREAS_CARGA = (
    "SECO", "S", "NE", "N",  # subsistemas
    "RJ", "SP", "MG", "ES", "MT", "MS", "DF", "GO", "AC", "RO", "PR", "SC", "RS",
    "BASE", "BAOE", "ALPE", "PBRN", "CE", "PI", "TON", "PA", "MA", "AP", "AM", "RR",  # áreas geoelétricas
    "PESE", "PES", "PENE", "PEN",  # perdas por subsistema
)  # fmt: skip


def area_conhecida(valor: str) -> str:
    """Sigla em maiúsculas; fora do catálogo oficial é erro."""
    sigla = valor.strip().upper()
    if sigla not in AREAS_CARGA:
        raise ValueError(f"área de carga fora do catálogo: {valor}")
    return sigla


class OnsCargaApi(Conector):
    """Uma chamada por área de carga e por pedaço de 31 dias da janela."""

    fonte = "ons"
    schema_versao = "1"
    max_dias_por_requisicao = 31
    endpoint: ClassVar[str]

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _consultar(self, area: str, janela: Janela) -> list[dict[str, Any]]:
        from src.core.config import get_settings

        resposta = self._sessao.get(
            BASE + self.endpoint,
            params={"dat_inicio": janela.inicio.isoformat(), "dat_fim": janela.fim.isoformat(), "cod_areacarga": area},
            timeout=get_settings().http_timeout,
        )
        resposta.raise_for_status()
        corpo = resposta.json()
        if not isinstance(corpo, list):
            # erro do gateway vem como objeto; tratá-lo como "sem dado" apagaria a falha
            raise RuntimeError(f"{self.rotulo}: resposta inesperada da API para {area}: {str(corpo)[:200]}")
        return corpo

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        for area in AREAS_CARGA:
            linhas = self._consultar(area, janela)
            logger.info("%s: %s %s, %d linhas", self.rotulo, area, janela, len(linhas))
            yield from linhas
