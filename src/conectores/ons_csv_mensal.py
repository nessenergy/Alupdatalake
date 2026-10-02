"""Base dos conectores ONS publicados como um CSV pesado por mês (Aditivo 01).

Dados hidrológicos horários (20 MB/mês), energia vertida turbinável (14 MB),
geração térmica por motivo de despacho (30 MB) e fator de capacidade (34 MB, 170
mil linhas) têm a mesma forma: um CSV `;` por mês em `ons-aws-prod-opendata`,
com a coluna `din_instante`. A subclasse declara URL, início da série mensal,
schema e `transformar()`; a extração é esta.

Dois cuidados que o tamanho impõe:

1. **Download em stream.** O arquivo é lido linha a linha (`stream=True` +
   `iter_lines`) e entregue ao `csv.DictReader` sem nunca existir inteiro em
   memória; o runner, por sua vez, valida e carrega em lotes.
2. **Série mensal curta.** Antes de `primeiro_mes` o ONS publica um CSV **anual**
   (190 a 320 MB), com outro nome de arquivo. Este conector não o lê: janela que
   comece antes da série mensal é recusada com erro claro, em vez de descartar
   meses em silêncio. O histórico que o projeto precisa (24 meses) cabe na série
   mensal dos quatro conjuntos.

A janela é por mês de arquivo; as linhas fora do intervalo pedido são
descartadas na extração, como no `ons_geracao_usina`.
"""

from __future__ import annotations

import csv
import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any, ClassVar

from src.conectores.ccee_ckan import decodificar
from src.conectores.ons_csv_anual import BASE
from src.conectores.ons_geracao_usina import _meses
from src.core.conector import Conector
from src.core.http import criar_sessao

if TYPE_CHECKING:
    from collections.abc import Iterator

    import requests

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

_BLOCO_DO_STREAM = 1 << 16


def inteiro_ou_nulo(valor: Any) -> int | None:
    """Inteiro que o ONS às vezes publica como `201.0`; vazio é nulo, fração é erro."""
    if isinstance(valor, str):
        valor = valor.strip()
    if valor is None or valor == "":
        return None
    numero = Decimal(valor) if not isinstance(valor, Decimal) else valor
    if numero != numero.to_integral_value():
        raise ValueError(f"esperava inteiro, veio {valor}")
    return int(numero)


class OnsCsvMensal(Conector):
    """Um CSV por mês, em stream, recortado pela janela na extração.

    A subclasse declara `entidade`, `schema`, `caminho` (relativo a `BASE`, com
    `{ano}` e `{mes}`), `primeiro_mes` (`(ano, mês)` do primeiro arquivo mensal)
    e `transformar()`.
    """

    fonte = "ons"
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por mês de arquivo, não por dias
    caminho: ClassVar[str]
    primeiro_mes: ClassVar[tuple[int, int]]

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _abrir_mes(self, ano: int, mes: int) -> Iterator[str] | None:
        """Linhas do CSV do mês, decodificadas uma a uma; `None` se o catálogo ainda não o publicou."""
        from src.core.config import get_settings

        resposta = self._sessao.get(
            BASE + self.caminho.format(ano=ano, mes=mes), timeout=get_settings().http_timeout, stream=True
        )
        if resposta.status_code == 404:
            resposta.close()
            return None
        try:
            resposta.raise_for_status()
        except Exception:
            resposta.close()
            raise
        return _linhas(resposta)

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        meses = _meses(janela)
        if meses[0] < self.primeiro_mes:
            raise ValueError(
                f"{self.rotulo}: janela começa em {meses[0][0]}-{meses[0][1]:02d}, mas o arquivo mensal só existe "
                f"desde {self.primeiro_mes[0]}-{self.primeiro_mes[1]:02d}; antes disso o ONS publica um CSV "
                "anual, que este conector não lê"
            )
        for ano, mes in meses:
            logger.info("%s: baixando %d-%02d", self.rotulo, ano, mes)
            linhas = self._abrir_mes(ano, mes)
            if linhas is None:
                logger.warning("%s: %d-%02d sem arquivo publicado no catálogo, ignorado", self.rotulo, ano, mes)
                continue
            for linha in csv.DictReader(linhas, delimiter=";"):
                referencia = (linha.get("din_instante") or "")[:10]
                if not referencia:
                    continue
                if not (janela.inicio.isoformat() <= referencia <= janela.fim.isoformat()):
                    continue  # o arquivo é mensal; a janela é o recorte pedido
                yield linha


def _linhas(resposta: requests.Response) -> Iterator[str]:
    """Linhas decodificadas, fechando a conexão ao fim (ou se o consumidor abandonar)."""
    with resposta:
        for linha in resposta.iter_lines(chunk_size=_BLOCO_DO_STREAM):
            yield decodificar(linha)
