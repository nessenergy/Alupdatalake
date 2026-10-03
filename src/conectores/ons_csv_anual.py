"""Base dos conectores do ONS publicados como um CSV por ano (Aditivo 01).

O catálogo de Dados Abertos do ONS publica boa parte dos conjuntos no mesmo
formato: um CSV por ano em `ons-aws-prod-opendata`, separador `;`, com uma
coluna de data ISO. O que muda de um conjunto para outro é a URL, a coluna de
data, o schema e o `transformar()`; a extração é esta.

Os conectores do ONS anteriores ao Aditivo 01 (`ons_carga`, `ons_ear`,
`ons_ena`) têm a mesma lógica escrita à mão e ficam como estão — funcionam, e
migrá-los agora seria risco sem ganho para a entrega.
"""

from __future__ import annotations

import csv
import logging
from io import StringIO
from typing import TYPE_CHECKING, Any, ClassVar

from src.conectores.ccee_ckan import decodificar
from src.core.conector import Conector
from src.core.http import criar_sessao

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

BASE = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/"
SUBMERCADOS = frozenset({"N", "NE", "S", "SE"})


def vazio_e_nulo(valor: Any) -> Any:
    """Campo vazio na origem vira `None`: medição ausente, não zero."""
    if isinstance(valor, str):
        texto = valor.strip()
        return texto or None
    return valor


def submercado(valor: str | None) -> str | None:
    """Sigla com trim e maiúsculas; sigla desconhecida é erro, vazio é nulo."""
    if valor is None:
        return None
    sigla = valor.strip().upper()
    if not sigla:
        return None
    if sigla not in SUBMERCADOS:
        raise ValueError(f"submercado desconhecido: {valor}")
    return sigla


def instante(texto: str) -> str:
    """`din_instante` da origem (`AAAA-MM-DD HH:MM:SS`) no formato ISO que o Pydantic lê."""
    return texto.strip().replace(" ", "T")


class OnsCsvAnual(Conector):
    """Um CSV por ano, recortado pela janela na extração.

    A subclasse declara `entidade`, `schema`, `caminho` (relativo a `BASE`,
    com `{ano}`), `coluna_data` e `transformar()`.
    """

    fonte = "ons"
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por ano de arquivo, não por dias
    caminho: ClassVar[str]
    coluna_data: ClassVar[str]
    exige_algum_ano: ClassVar[bool] = False
    """Se verdadeiro, a janela cujos anos todos vieram sem arquivo falha alto em vez de devolver zero linhas."""

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _baixar_ano(self, ano: int) -> str | None:
        """CSV do ano decodificado, ou `None` quando o catálogo ainda não o publicou."""
        from src.core.config import get_settings

        resposta = self._sessao.get(BASE + self.caminho.format(ano=ano), timeout=get_settings().http_timeout)
        if resposta.status_code == 404:
            return None
        resposta.raise_for_status()
        return "\n".join(decodificar(linha) for linha in resposta.content.splitlines())

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        anos = range(janela.inicio.year, janela.fim.year + 1)
        publicados = 0
        for ano in anos:
            logger.info("%s: baixando %d", self.rotulo, ano)
            conteudo = self._baixar_ano(ano)
            if conteudo is None:
                logger.warning("%s: %d sem recurso publicado no catálogo, ignorado", self.rotulo, ano)
                continue
            publicados += 1
            for linha in csv.DictReader(StringIO(conteudo), delimiter=";"):
                referencia = (linha.get(self.coluna_data) or "")[:10]
                if not referencia:
                    continue
                if not (janela.inicio.isoformat() <= referencia <= janela.fim.isoformat()):
                    continue  # o arquivo é anual; a janela é o recorte pedido
                yield linha
        if self.exige_algum_ano and not publicados:
            raise RuntimeError(f"{self.rotulo}: nenhum arquivo publicado para {list(anos)}")
