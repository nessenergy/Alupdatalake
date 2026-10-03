"""Conector ONS — contornos das bacias hidrográficas do SIN (Onda 1, apoio à chuva por bacia).

Fonte: conjunto aberto `bacia_contorno` do ONS (https://dados.ons.org.br/dataset/bacia_contorno), licença
Creative Commons Attribution (CC-BY): o autor é o ONS e o crédito acompanha o dado (dicionário e linhagem).
O recurso é um zip, `Bacias_Hidrograficas_SIN.zip`, com um shapefile em WGS84 (31 polígonos em 03/10/2026,
atributos `ID` e `Nome_Bacia`, `.dbf` em UTF-8). Decisão: ADR 026.

É um **retrato**, como o `ace_prc`: o conjunto não tem janela e muda raramente. A data que vale é a que o CKAN
declara (`metadata_modified`), e a janela do runner só identifica a execução. Ler o mesmo zip toda vez repete os
polígonos na Bronze (append-only); a Silver deduplica por nome da bacia e data de referência.

A geometria sai como **WKT** (longitude e latitude), do jeito que o shapefile a traz. Seis dos 31 polígonos têm
autointerseção: o conector não os descarta nem os conserta, o reparo é do BigQuery (`ST_GEOGFROMTEXT(...,
make_valid => TRUE)`, na Silver). O leitor é o `pyshp`, puro Python, sem GDAL.

O que mudar no zip (sem `.shp`, sem polígono, sem o campo do nome) **falha alto**: carregar zero linha como sucesso
só apareceria dias depois, no alerta de silêncio.
"""

from __future__ import annotations

import io
import logging
import zipfile
from typing import TYPE_CHECKING, Any

import shapefile
from pydantic import BaseModel, Field, field_validator

from src.core.conector import Conector
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL_CKAN = "https://dados.ons.org.br/api/3/action/package_show"
CONJUNTO = "bacia_contorno"
CAMPO_NOME = "Nome_Bacia"
CAMPO_ID = "ID"

logger = logging.getLogger(__name__)


class LayoutInesperadoError(RuntimeError):
    """O conjunto mudou de forma: não dá para ler os contornos sem olhar o que ele virou."""


class ContornoBacia(BaseModel):
    """O contorno de uma bacia, como o ONS o publica."""

    data_referencia: str  # `metadata_modified` do CKAN, ISO
    nome_bacia: str = Field(min_length=1)
    id_bacia: int | None = None
    wkt: str = Field(min_length=1)

    @field_validator("nome_bacia")
    @classmethod
    def _sem_espaco_nas_pontas(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("nome_bacia vazio")
        return valor


def _area_assinada(anel: list[tuple[float, float]]) -> float:
    """Fórmula do cadarço: negativa no anel horário (externo no shapefile), positiva no anti-horário (furo)."""
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(anel, anel[1:] + anel[:1], strict=True)) / 2


def _texto_anel(anel: list[tuple[float, float]]) -> str:
    if anel[0] != anel[-1]:
        anel = [*anel, anel[0]]
    return "(" + ", ".join(f"{x} {y}" for x, y in anel) + ")"


def _wkt(forma: shapefile.Shape) -> str:
    """POLYGON, ou MULTIPOLYGON quando há mais de um anel externo.

    ponytail: o furo (anel anti-horário) entra no último externo lido; é a ordem em que o shapefile os grava.
    O ONS hoje publica um anel por polígono. Se um dia vierem furos fora de ordem, ligar por contenção.
    """
    pontos = [(float(x), float(y)) for x, y in forma.points]
    inicios = [*forma.parts, len(pontos)]
    poligonos: list[list[list[tuple[float, float]]]] = []
    for inicio, fim in zip(inicios, inicios[1:], strict=False):
        anel = pontos[inicio:fim]
        if len(anel) < 4:
            continue
        if poligonos and _area_assinada(anel) > 0:
            poligonos[-1].append(anel)
        else:
            poligonos.append([anel])
    if not poligonos:
        raise LayoutInesperadoError("polígono sem anel válido no shapefile")
    textos = ["(" + ", ".join(_texto_anel(a) for a in aneis) + ")" for aneis in poligonos]
    if len(textos) == 1:
        return f"POLYGON {textos[0]}"
    return f"MULTIPOLYGON ({', '.join(textos)})"


@registrar
class OnsBaciaContorno(Conector):
    """Contornos das bacias do SIN. Um retrato do zip por execução; a janela não filtra."""

    fonte = "ons"
    entidade = "bacia_contorno"
    schema = ContornoBacia
    schema_versao = "1"
    max_dias_por_requisicao = None

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _baixar(self) -> tuple[bytes, str]:
        """O zip (1,6 MB, cabe na memória) e a data que o CKAN declara para o conjunto."""
        from src.core.config import get_settings

        timeout = get_settings().http_timeout
        resposta = self._sessao.get(URL_CKAN, params={"id": CONJUNTO}, timeout=timeout)
        resposta.raise_for_status()
        try:
            conjunto = resposta.json()["result"]
            urls = [r["url"] for r in conjunto["resources"] if r["url"].lower().endswith(".zip")]
            data_referencia = conjunto["metadata_modified"][:10]
        except (KeyError, TypeError, ValueError) as exc:
            raise LayoutInesperadoError(f"a resposta do CKAN para {CONJUNTO} mudou de forma: {exc!r}") from exc
        if len(urls) != 1:
            raise LayoutInesperadoError(f"o conjunto {CONJUNTO} trouxe {len(urls)} recursos zip, esperado 1")
        zip_ = self._sessao.get(urls[0], timeout=timeout)
        zip_.raise_for_status()
        return zip_.content, data_referencia

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        del janela  # retrato: o conjunto não tem recorte de período
        conteudo, data_referencia = self._baixar()
        try:
            arquivo = zipfile.ZipFile(io.BytesIO(conteudo))
        except zipfile.BadZipFile as exc:
            raise LayoutInesperadoError("o recurso de contornos não é um zip") from exc
        with arquivo:
            shp = next((n for n in arquivo.namelist() if n.lower().endswith(".shp")), None)
            if shp is None:
                raise LayoutInesperadoError("o zip de contornos não traz mais um arquivo .shp")
            base = shp[:-4]
            for extensao in (".shx", ".dbf"):
                if base + extensao not in arquivo.namelist():
                    raise LayoutInesperadoError(f"o zip de contornos não traz mais o arquivo {extensao}")
            leitor = shapefile.Reader(
                shp=arquivo.open(shp),
                shx=arquivo.open(base + ".shx"),
                dbf=arquivo.open(base + ".dbf"),
                encoding="utf-8",  # o .cpg declara UTF-8; erro de decodificação é para aparecer
                encodingErrors="strict",
            )
            with leitor:
                campos = {c[0] for c in leitor.fields}
                if CAMPO_NOME not in campos:
                    raise LayoutInesperadoError(f"o shapefile não traz mais o campo {CAMPO_NOME}: {sorted(campos)}")
                total = 0
                for item in leitor.iterShapeRecords():
                    if item.shape.shapeType not in {shapefile.POLYGON, shapefile.POLYGONZ, shapefile.POLYGONM}:
                        continue
                    atributos = item.record.as_dict()
                    total += 1
                    yield {
                        "data_referencia": data_referencia,
                        "nome_bacia": atributos[CAMPO_NOME],
                        "id_bacia": atributos.get(CAMPO_ID),
                        "wkt": _wkt(item.shape),
                    }
        if total == 0:
            raise LayoutInesperadoError("o shapefile de contornos não trouxe nenhum polígono")
        logger.info("ONS bacia_contorno: %d polígonos, referência %s", total, data_referencia)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return bruto
