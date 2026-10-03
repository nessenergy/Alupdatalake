"""Conector ONS — contornos das bacias (shapefile em zip).

O zip é montado aqui com o escritor do pyshp (nenhum binário versionado): um polígono simples, um com
autointerseção (a origem tem 6 assim) e um multipolígono com furo. Sem rede.
"""

from __future__ import annotations

import io
import re
import zipfile
from typing import Any

import pytest
import shapefile
from src.conectores.ons_bacia_contorno import ContornoBacia, LayoutInesperadoError, OnsBaciaContorno
from src.core.config import get_settings
from src.core.execucao import Janela

JANELA = Janela.de_texto("2026-10-01", "2026-10-02")
DATA = "2024-05-27"

QUADRADO = [[(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]]  # horário: anel externo no shapefile
GRAVATA = [[(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)]]  # autointerseção
DUAS_ILHAS_COM_FURO = [
    [(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)],  # externo, horário
    [(2, 2), (4, 2), (4, 4), (2, 4), (2, 2)],  # furo, anti-horário
    [(20, 20), (20, 22), (22, 22), (22, 20), (20, 20)],  # segundo externo
]


@pytest.fixture(autouse=True)
def _dry_run() -> None:
    get_settings().dry_run = True


def _zip(
    poligonos: list[tuple[int, str, list[list[tuple[float, float]]]]],
    *,
    campo_nome: str = "Nome_Bacia",
    com_shp: bool = True,
) -> bytes:
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    with shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON, encoding="utf-8") as w:
        w.field("ID", "N", 11, 0)
        w.field(campo_nome, "C", 50)
        for ident, nome, aneis in poligonos:
            w.poly(aneis)
            w.record(ident, nome)
    saida = io.BytesIO()
    with zipfile.ZipFile(saida, "w") as z:
        if com_shp:
            z.writestr("Bacias.shp", shp.getvalue())
        z.writestr("Bacias.shx", shx.getvalue())
        z.writestr("Bacias.dbf", dbf.getvalue())
    return saida.getvalue()


def _conector(monkeypatch: pytest.MonkeyPatch, conteudo: bytes) -> OnsBaciaContorno:
    monkeypatch.setattr("src.conectores.ons_bacia_contorno.criar_sessao", lambda: None)
    conector = OnsBaciaContorno()
    monkeypatch.setattr(conector, "_baixar", lambda: (conteudo, DATA))
    return conector


def _brutos(conector: OnsBaciaContorno) -> list[dict[str, Any]]:
    return list(conector.extrair(JANELA))


def test_um_registro_por_poligono_com_o_nome_lido(monkeypatch: pytest.MonkeyPatch) -> None:
    conteudo = _zip([(0, "Paraná", QUADRADO), (1, "Itajaí-Açu", QUADRADO)])
    conector = _conector(monkeypatch, conteudo)

    registros = [ContornoBacia.model_validate(conector.transformar(b)) for b in _brutos(conector)]

    assert [(r.id_bacia, r.nome_bacia, r.data_referencia) for r in registros] == [
        (0, "Paraná", DATA),
        (1, "Itajaí-Açu", DATA),
    ]


def test_wkt_poligono_fecha_o_anel_em_longitude_e_latitude(monkeypatch: pytest.MonkeyPatch) -> None:
    conector = _conector(monkeypatch, _zip([(0, "Doce", [[(-43.5, -19.25), (-43.5, -18.0), (-42.0, -18.0)]])]))

    [registro] = [conector.transformar(b) for b in _brutos(conector)]

    # o anel sai fechado; a ordem é x (longitude) antes de y (latitude)
    assert registro["wkt"] == "POLYGON ((-43.5 -19.25, -43.5 -18.0, -42.0 -18.0, -43.5 -19.25))"


def test_autointerseccao_nao_e_descartada_nem_derruba(monkeypatch: pytest.MonkeyPatch) -> None:
    """O reparo é do BigQuery (`make_valid`): o conector grava a geometria como veio."""
    conector = _conector(monkeypatch, _zip([(0, "Grande", QUADRADO), (1, "Iguaçu", GRAVATA)]))

    registros = [conector.transformar(b) for b in _brutos(conector)]

    assert [r["nome_bacia"] for r in registros] == ["Grande", "Iguaçu"]
    assert registros[1]["wkt"] == "POLYGON ((0.0 0.0, 2.0 2.0, 2.0 0.0, 0.0 2.0, 0.0 0.0))"


def test_varias_partes_viram_multipoligono_e_o_furo_fica_no_externo(monkeypatch: pytest.MonkeyPatch) -> None:
    conector = _conector(monkeypatch, _zip([(0, "Tocantins", DUAS_ILHAS_COM_FURO)]))

    [registro] = [conector.transformar(b) for b in _brutos(conector)]

    wkt = registro["wkt"]
    assert wkt.startswith("MULTIPOLYGON (((")
    assert wkt.count(")), ((") == 1  # duas ilhas
    assert re.search(
        r"\(\(0\.0 0\.0.*\), \(2\.0 2\.0.*\)\), \(\(20\.0 20\.0", wkt
    )  # externo, furo; depois a outra ilha


def test_todo_wkt_comeca_por_poligono_e_fecha_cada_anel(monkeypatch: pytest.MonkeyPatch) -> None:
    conector = _conector(monkeypatch, _zip([(0, "A", QUADRADO), (1, "B", DUAS_ILHAS_COM_FURO)]))

    for bruto in _brutos(conector):
        wkt = conector.transformar(bruto)["wkt"]
        assert wkt.startswith(("POLYGON", "MULTIPOLYGON"))
        for anel in re.findall(r"\(([^()]+)\)", wkt):
            pontos = [p.strip() for p in anel.split(",")]
            assert pontos[0] == pontos[-1]


def test_zip_sem_shp_falha_alto(monkeypatch: pytest.MonkeyPatch) -> None:
    conector = _conector(monkeypatch, _zip([(0, "Doce", QUADRADO)], com_shp=False))

    with pytest.raises(LayoutInesperadoError, match=r"\.shp"):
        _brutos(conector)


def test_shapefile_vazio_falha_alto(monkeypatch: pytest.MonkeyPatch) -> None:
    conector = _conector(monkeypatch, _zip([]))

    with pytest.raises(LayoutInesperadoError, match="nenhum polígono"):
        _brutos(conector)


def test_campo_do_nome_ausente_falha_alto(monkeypatch: pytest.MonkeyPatch) -> None:
    conector = _conector(monkeypatch, _zip([(0, "Doce", QUADRADO)], campo_nome="Outro"))

    with pytest.raises(LayoutInesperadoError, match="Nome_Bacia"):
        _brutos(conector)


def test_arquivo_que_nao_e_zip_falha_alto(monkeypatch: pytest.MonkeyPatch) -> None:
    conector = _conector(monkeypatch, b"<html>pagina de erro</html>")

    with pytest.raises(LayoutInesperadoError, match="zip"):
        _brutos(conector)


def test_zip_sem_dbf_ou_shx_falha_alto_e_nao_com_keyerror(monkeypatch: pytest.MonkeyPatch) -> None:
    saida = io.BytesIO()
    with zipfile.ZipFile(saida, "w") as z:
        z.writestr("Bacias.shp", b"")
    conector = _conector(monkeypatch, saida.getvalue())

    with pytest.raises(LayoutInesperadoError, match=r"\.shx|\.dbf"):
        _brutos(conector)


class _Resposta:
    def __init__(self, dados: dict[str, Any]) -> None:
        self._dados = dados

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._dados


class _Sessao:
    def __init__(self, dados: dict[str, Any]) -> None:
        self._dados = dados

    def get(self, *args: Any, **kwargs: Any) -> _Resposta:
        return _Resposta(self._dados)


@pytest.mark.parametrize(
    "resultado",
    [
        {"resources": [{"name": "sem url"}], "metadata_modified": "2024-05-27T18:02:14"},
        {"resources": [{"url": "https://x/a.zip"}]},  # sem metadata_modified
        {"metadata_modified": "2024-05-27T18:02:14"},  # sem recursos
    ],
)
def test_resposta_do_ckan_fora_do_formato_falha_alto(
    monkeypatch: pytest.MonkeyPatch, resultado: dict[str, Any]
) -> None:
    monkeypatch.setattr("src.conectores.ons_bacia_contorno.criar_sessao", lambda: _Sessao({"result": resultado}))

    with pytest.raises(LayoutInesperadoError, match="CKAN"):
        OnsBaciaContorno()._baixar()


def test_nome_vazio_e_recusado_pelo_schema() -> None:
    with pytest.raises(ValueError, match="nome_bacia"):
        ContornoBacia(data_referencia=DATA, nome_bacia="  ", id_bacia=1, wkt="POLYGON ((0 0, 0 1, 1 1, 0 0))")
