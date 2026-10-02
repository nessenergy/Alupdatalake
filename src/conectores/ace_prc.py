"""Conector ACE Comercializadora — Preços de Referência Comparáveis (Onda 1, página pública).

Fonte: https://alup.io/valores-de-energia/ — a ACE Comercializadora de Energia (Alup) divulga o PRC ali, como
exige o submódulo 1.6 dos Procedimentos de Comercialização da CCEE (REN ANEEL 1.011/22): uma tabela HTML com
4 submercados × 2 tipos de energia × 3 prazos (anual, trianual, quinquenal), em R$/MWh.

É um **retrato**, como o cadastro da ANEEL: a página não tem janela. A data que vale é a que ela mesma declara
("Atualizado em: dd/mm/aaaa"), e a janela do runner só identifica a execução. Quando a ACE republicar com outra
data, a Silver passa a ter as duas e a Gold escolhe a mais recente.

O HTML é de uma tabela do TablePress, com `rowspan` no submercado. O que a tabela não garante é o layout: se ela
sumir, ganhar prazo novo ou perder a data, o conector **falha alto** em vez de carregar zero linhas como sucesso
(o alerta de silêncio só enxergaria dias depois).
"""

from __future__ import annotations

import logging
import re
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any

from src.conectores.planilha_prc import PrecoReferencia
from src.core.conector import Conector
from src.core.http import criar_sessao
from src.core.planilha import decimal_br
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://alup.io/valores-de-energia/"
COMERCIALIZADORA = "ACE Comercializadora"
PRECOS_ESPERADOS = 24  # 4 submercados × 2 tipos de energia × 3 prazos

# O PRC da página usa "SE/CO"; a dimensão comum do projeto é a sigla do submercado.
SUBMERCADOS = {"SE/CO": "SE", "S": "S", "NE": "NE", "N": "N"}

logger = logging.getLogger(__name__)


class LayoutInesperadoError(RuntimeError):
    """A página mudou de forma: não dá para ler o PRC sem olhar o que ela virou."""


class _Tabela(HTMLParser):
    """Linhas da primeira `<table>` da página, como listas de texto de célula."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.linhas: list[list[str]] = []
        self._dentro = False
        self._ja_leu = False
        self._celula: list[str] | None = None
        self._linha: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table" and not self._ja_leu:
            self._dentro = True
        elif self._dentro and tag == "tr":
            self._linha = []
        elif self._dentro and tag in {"td", "th"} and self._linha is not None:
            self._celula = []
        elif self._celula is not None and tag == "br":
            self._celula.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "table" and self._dentro:
            self._dentro, self._ja_leu = False, True
        elif tag in {"td", "th"} and self._celula is not None and self._linha is not None:
            self._linha.append(re.sub(r"\s+", " ", "".join(self._celula)).strip())
            self._celula = None
        elif tag == "tr" and self._linha is not None:
            self.linhas.append(self._linha)
            self._linha = None

    def handle_data(self, data: str) -> None:
        if self._celula is not None:
            self._celula.append(data)


def _prazos(cabecalho: list[str]) -> list[int]:
    """Prazo em meses de cada coluna de preço, lido do cabeçalho ("Trianual (3 anos)" vira 36)."""
    prazos = []
    for texto in cabecalho[2:]:
        achado = re.search(r"\((\d+)\s*anos?\)", texto)
        if not achado:
            raise LayoutInesperadoError(f"prazo ilegível no cabeçalho do PRC: {texto!r}")
        prazos.append(int(achado.group(1)) * 12)
    if prazos != [12, 36, 60]:
        raise LayoutInesperadoError(f"prazo(s) diferentes de anual, trianual e quinquenal no PRC: {prazos}")
    return prazos


@registrar
class AcePrc(Conector):
    """PRC da ACE Comercializadora. Um retrato da página por execução; a janela não filtra."""

    fonte = "ace"
    entidade = "prc"
    schema = PrecoReferencia
    schema_versao = "1"
    max_dias_por_requisicao = None

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _baixar(self) -> str:
        from src.core.config import get_settings

        resposta = self._sessao.get(URL, timeout=get_settings().http_timeout)
        resposta.raise_for_status()
        return resposta.content.decode("utf-8")  # a página declara UTF-8; erro de decodificação é para aparecer

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        html = self._baixar()
        data = re.search(r"Atualizado em:\s*(\d{2}/\d{2}/\d{4})", html)
        if not data:
            raise LayoutInesperadoError("a página do PRC não traz mais 'Atualizado em: dd/mm/aaaa'")
        parser = _Tabela()
        parser.feed(html)
        cabecalho = next((linha for linha in parser.linhas if linha and linha[0] == "Submercado"), None)
        if cabecalho is None:
            raise LayoutInesperadoError("a página do PRC não traz mais a tabela de preços (cabeçalho 'Submercado')")
        prazos = _prazos(cabecalho)

        submercado = ""
        total = 0
        for linha in parser.linhas[parser.linhas.index(cabecalho) + 1 :]:
            if len(linha) == 2 + len(prazos):  # abre um submercado: a célula dele vale para a linha de baixo (rowspan)
                submercado, tipo, precos = linha[0], linha[1], linha[2:]
            elif len(linha) == 1 + len(prazos) and submercado:
                tipo, precos = linha[0], linha[1:]
            else:
                continue
            for prazo, texto in zip(prazos, precos, strict=True):
                total += 1
                yield {
                    "data_atualizacao": data.group(1),
                    "submercado": submercado,
                    "tipo_energia": tipo,
                    "prazo_meses": prazo,
                    "preco": texto,
                }
        if total == 0:
            raise LayoutInesperadoError("a tabela do PRC não trouxe nenhuma linha de preço")
        if total != PRECOS_ESPERADOS:
            logger.warning(
                "PRC da ACE com %d preços, esperados %d: confira se a tabela ganhou linha", total, PRECOS_ESPERADOS
            )

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        sigla = SUBMERCADOS.get(bruto["submercado"].strip().upper())
        if sigla is None:
            raise ValueError(f"submercado desconhecido no PRC: {bruto['submercado']!r}")
        tipo = bruto["tipo_energia"].strip().lower()
        if "incentivada" in tipo:
            tipo_energia = "incentivada_50"
        elif tipo.startswith("conve"):  # a página já escreveu "Convecional" numa linha
            tipo_energia = "convencional"
        else:
            raise ValueError(f"tipo de energia desconhecido no PRC: {bruto['tipo_energia']!r}")
        preco = re.search(r"R\$\s*([\d.]+,\d+)", bruto["preco"])
        if not preco:
            raise ValueError(f"preço ilegível no PRC: {bruto['preco']!r}")
        return {
            "comercializadora": COMERCIALIZADORA,
            "data_atualizacao": bruto["data_atualizacao"],
            "submercado": sigla,
            "tipo_energia": tipo_energia,
            "ano": None,
            "prazo_meses": bruto["prazo_meses"],
            "preco_rs_mwh": str(decimal_br(preco.group(1))),
            "indexador": None,
            "premissas": None,
        }
