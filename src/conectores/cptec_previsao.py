"""Conector CPTEC — previsão do tempo dos próximos dias nas 27 capitais (Onda 1, dado público, sem credencial).

Fonte: webservice XML do CPTEC/INPE, `https://servicos.cptec.inpe.br/XML/cidade/7dias/{id}/previsao.xml`, uma
requisição por cidade. A resposta vem em ISO-8859-1 e traz a data de emissão (`atualizacao`) e um bloco `previsao`
por dia, com o código de tempo, as temperaturas máxima e mínima e o índice UV. Não traz precipitação em mm.

O webservice respondeu 403 a toda requisição de 02 a 03/10/2026 (ADR 028 e 029). Em 22/10/2026 respondia 200, com
limite de 120 requisições por janela (`x-ratelimit-limit`); 27 cidades cabem folgado. Apesar do nome "7dias", a
resposta de 22/10 trazia 6 dias, de 23 a 28/10: o que vale é o que a origem devolve, e o dicionário diz isso.

A origem só publica a previsão vigente, sem histórico, e todo dia previsto é de hoje em diante, enquanto a janela
da CLI termina sempre ontem. Por isso é um retrato, como `ace_prc`: a janela não se aplica. O Bronze, que é
append-only, acumula uma foto por emissão, e é isso que forma o histórico de previsões. Reprocessar uma janela
antiga não recupera previsão passada: só a origem de hoje existe.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from pydantic import BaseModel

from src.core.conector import Conector
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://servicos.cptec.inpe.br/XML/cidade/7dias/{cidade_id}/previsao.xml"

# id do CPTEC -> (nome, UF). Ids conferidos em 22/10/2026 contra `XML/listaCidades?city=<nome>`.
CAPITAIS: dict[int, tuple[str, str]] = {
    240: ("Rio Branco", "AC"),
    233: ("Maceió", "AL"),
    232: ("Macapá", "AP"),
    234: ("Manaus", "AM"),
    242: ("Salvador", "BA"),
    229: ("Fortaleza", "CE"),
    224: ("Brasília", "DF"),
    246: ("Vitória", "ES"),
    230: ("Goiânia", "GO"),
    243: ("São Luís", "MA"),
    226: ("Cuiabá", "MT"),
    225: ("Campo Grande", "MS"),
    222: ("Belo Horizonte", "MG"),
    221: ("Belém", "PA"),
    231: ("João Pessoa", "PB"),
    227: ("Curitiba", "PR"),
    239: ("Recife", "PE"),
    245: ("Teresina", "PI"),
    241: ("Rio de Janeiro", "RJ"),
    235: ("Natal", "RN"),
    237: ("Porto Alegre", "RS"),
    238: ("Porto Velho", "RO"),
    223: ("Boa Vista", "RR"),
    228: ("Florianópolis", "SC"),
    244: ("São Paulo", "SP"),
    220: ("Aracaju", "SE"),
    236: ("Palmas", "TO"),
}

_DATA = re.compile(r"\d{4}-\d{2}-\d{2}")


class LayoutInesperadoError(RuntimeError):
    """A resposta do CPTEC não tem a forma que o conector conhece (403 em HTML, corpo vazio, XML sem previsão)."""


class PrevisaoDia(BaseModel):
    """A previsão de um dia para uma cidade, na emissão `data_emissao`."""

    cidade_id: int
    cidade: str
    uf: str
    data_referencia: date  # o dia previsto
    data_emissao: date  # quando o CPTEC emitiu a previsão
    codigo_tempo: str  # código do CPTEC (c, pn, ps...); o dicionário descreve
    temperatura_maxima_c: int
    temperatura_minima_c: int
    indice_uv: Decimal


def _texto(no: Any, nome: str) -> str:
    filho = no.find(nome)
    if filho is None or filho.text is None or not filho.text.strip():
        raise LayoutInesperadoError(f"resposta do CPTEC sem o campo {nome!r}")
    return filho.text.strip()


def _data(no: Any, nome: str) -> str:
    texto = _texto(no, nome)
    if not _DATA.fullmatch(texto):
        raise LayoutInesperadoError(f"{nome!r} fora de aaaa-mm-dd: {texto!r}")
    return texto


def _ler_cidade(conteudo: bytes, cidade_id: int) -> Iterator[dict[str, Any]]:
    try:
        raiz = ElementTree.fromstring(conteudo)
    except (ElementTree.ParseError, DefusedXmlException) as erro:
        raise LayoutInesperadoError(f"cidade {cidade_id}: a resposta não é um XML aceitável ({erro})") from erro
    if raiz.tag != "cidade":
        raise LayoutInesperadoError(f"cidade {cidade_id}: raiz {raiz.tag!r}, esperada 'cidade'")
    emissao = _data(raiz, "atualizacao")
    dias = raiz.findall("previsao")
    if not dias:
        raise LayoutInesperadoError(f"cidade {cidade_id}: a resposta não traz nenhuma previsão")
    for dia in dias:
        yield {
            "cidade_id": cidade_id,
            "data_emissao": emissao,
            "dia": _data(dia, "dia"),
            "codigo_tempo": _texto(dia, "tempo"),
            "maxima": _texto(dia, "maxima"),
            "minima": _texto(dia, "minima"),
            "iuv": _texto(dia, "iuv"),
        }


@registrar
class CptecPrevisao(Conector):
    """Previsão por capital. Uma requisição por cidade; devolve a previsão vigente inteira, sem recorte por janela."""

    fonte = "cptec"
    entidade = "previsao"
    schema = PrevisaoDia
    schema_versao = "1"
    max_dias_por_requisicao = None  # a origem devolve a previsão vigente inteira, não aceita janela

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        from src.core.config import get_settings

        del janela  # retrato da previsão vigente; ver o docstring do módulo
        for cidade_id in CAPITAIS:
            resposta = self._sessao.get(URL.format(cidade_id=cidade_id), timeout=get_settings().http_timeout)
            resposta.raise_for_status()
            yield from _ler_cidade(resposta.content, cidade_id)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        nome, uf = CAPITAIS[bruto["cidade_id"]]
        return {
            "cidade_id": bruto["cidade_id"],
            "cidade": nome,
            "uf": uf,
            "data_referencia": bruto["dia"],
            "data_emissao": bruto["data_emissao"],
            "codigo_tempo": bruto["codigo_tempo"],
            "temperatura_maxima_c": bruto["maxima"],
            "temperatura_minima_c": bruto["minima"],
            "indice_uv": bruto["iuv"],
        }
