"""Base dos conectores do ONS publicados como um CSV por dia (Aditivo 01, padrão C).

Dois conjuntos entram aqui: `programacao_x_previsao` e `balanco_dessem_geral`.
Cada dia tem o seu arquivo em `ons-aws-prod-opendata`, com o dia no nome
(`..._AAAA_MM_DD.csv`) e o mesmo dia na coluna de data. O que muda de um
conjunto para outro é o caminho, o schema e o `transformar()`.

Como a janela vira arquivos: **um GET por dia da janela, na URL previsível**,
sem listar o catálogo CKAN. O catálogo é pior fonte do que a URL: em 02/10/2026
ele omitia 9 arquivos do `programacao_x_previsao` que existem no S3 e listava
um do `balanco_dessem_geral` que dá 404. O custo é uma requisição por dia
mesmo quando o dia não existe (404 em ~0,5 s).

Dia sem arquivo é aviso, não erro: o ONS tem buracos de 1 a 2 dias seguidos
(02/2025 e 03/2025 no `programacao_x_previsao`; 5 dias soltos no DESSEM). Mas
`LIMITE_SEM_ARQUIVO` dias ou mais sem nenhum arquivo é URL quebrada, e vira
erro: sem isso a execução fecha em SUCESSO com zero linha, e o alerta de
silêncio, que só enxerga sucesso, nunca dispara.

O corpo é lido em stream, linha a linha, e cada linha é decodificada sozinha
(UTF-8, com ISO-8859-1 de reserva) — o `programacao_x_previsao` tem 2 MB e
30 mil linhas por dia.
"""

from __future__ import annotations

import csv
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from src.conectores.ccee_ckan import decodificar
from src.conectores.ons_csv_anual import BASE
from src.core.conector import Conector
from src.core.http import criar_sessao

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from datetime import date

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

# O maior buraco visto no S3 foi de 2 dias seguidos (24 meses de histórico).
LIMITE_SEM_ARQUIVO = 3


class OnsArquivoDiario(Conector):
    """Um CSV por dia, na URL `BASE + caminho.format(dia=...)`.

    A subclasse declara `entidade`, `schema`, `caminho` (relativo a `BASE`, com
    `{dia:%Y_%m_%d}`) e `transformar()`.
    """

    fonte = "ons"
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por dia de arquivo; a janela já é a lista de arquivos
    caminho: ClassVar[str]

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _abrir(self, dia: date) -> Iterable[bytes] | None:
        """Linhas do arquivo do dia, em stream, ou `None` quando ele não existe (404).

        É o seam dos testes: eles devolvem as linhas de uma fixture.
        """
        from src.core.config import get_settings

        resposta = self._sessao.get(
            BASE + self.caminho.format(dia=dia), stream=True, timeout=get_settings().http_timeout
        )
        if resposta.status_code == 404:
            resposta.close()
            return None
        resposta.raise_for_status()
        return _linhas_e_fecha(resposta)

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        sem_arquivo = 0
        encontrados = 0
        for dia in janela.dias():
            linhas = self._abrir(dia)
            if linhas is None:
                sem_arquivo += 1
                logger.warning("%s: sem arquivo em %s, ignorado", self.rotulo, dia)
                continue
            encontrados += 1
            logger.info("%s: lendo %s", self.rotulo, dia)
            yield from csv.DictReader((decodificar(linha) for linha in linhas), delimiter=";")
        if not encontrados and sem_arquivo >= LIMITE_SEM_ARQUIVO:
            raise RuntimeError(f"{self.rotulo}: nenhum arquivo em {sem_arquivo} dias ({janela}); URL ou janela erradas")


def _linhas_e_fecha(resposta: Any) -> Iterator[bytes]:
    try:
        yield from resposta.iter_lines()
    finally:
        resposta.close()
