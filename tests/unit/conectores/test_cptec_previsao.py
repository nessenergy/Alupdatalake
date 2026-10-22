"""CPTEC — previsão do tempo por capital (webservice XML). Sem rede."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.cptec_previsao import CAPITAIS, CptecPrevisao, LayoutInesperadoError, PrevisaoDia
from src.core.config import get_settings
from src.core.execucao import Janela

FIXTURE = (Path(__file__).parents[2] / "fixtures" / "cptec_previsao_244.xml").read_bytes()


class _Resposta:
    def __init__(self, conteudo: bytes, status: int = 200) -> None:
        self.content = conteudo
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _Sessao:
    def __init__(self, respostas: dict[int, _Resposta]) -> None:
        self._respostas = respostas
        self.pedidos: list[str] = []

    def get(self, url: str, timeout: float) -> _Resposta:
        self.pedidos.append(url)
        cidade = int(url.split("/cidade/7dias/")[1].split("/")[0])
        return self._respostas[cidade]


@pytest.fixture(autouse=True)
def _dry_run() -> None:
    get_settings().dry_run = True


def _conector(monkeypatch: pytest.MonkeyPatch, respostas: dict[int, _Resposta]) -> tuple[CptecPrevisao, _Sessao]:
    sessao = _Sessao(respostas)
    monkeypatch.setattr("src.conectores.cptec_previsao.criar_sessao", lambda: sessao)
    monkeypatch.setattr("src.conectores.cptec_previsao.CAPITAIS", {244: ("São Paulo", "SP")})
    return CptecPrevisao(), sessao


def _linhas(conector: CptecPrevisao, ini: str, fim: str) -> list[PrevisaoDia]:
    return [PrevisaoDia.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto(ini, fim))]


def test_le_a_previsao_real_de_sao_paulo(monkeypatch) -> None:
    conector, sessao = _conector(monkeypatch, {244: _Resposta(FIXTURE)})

    linhas = _linhas(conector, "2026-10-23", "2026-10-28")

    assert len(linhas) == 6
    primeira = linhas[0]
    assert (primeira.cidade_id, primeira.cidade, primeira.uf) == (244, "São Paulo", "SP")
    assert primeira.data_referencia == date(2026, 10, 23)
    assert primeira.data_emissao == date(2026, 10, 22)
    assert primeira.codigo_tempo == "c"
    assert (primeira.temperatura_maxima_c, primeira.temperatura_minima_c) == (24, 18)
    assert primeira.indice_uv == Decimal("0.0")
    assert sessao.pedidos == ["https://servicos.cptec.inpe.br/XML/cidade/7dias/244/previsao.xml"]


def test_a_janela_nao_recorta_o_retrato_da_previsao(monkeypatch) -> None:
    conector, _ = _conector(monkeypatch, {244: _Resposta(FIXTURE)})

    # a janela da CLI termina ontem; a previsão é de hoje em diante e não pode sumir por isso
    linhas = _linhas(conector, "2026-10-01", "2026-10-21")

    assert len(linhas) == 6


@pytest.mark.parametrize("status", [403, 500])
def test_status_de_erro_derruba_a_execucao(monkeypatch, status: int) -> None:
    conector, _ = _conector(monkeypatch, {244: _Resposta(b"<html>403 Forbidden</html>", status)})

    with pytest.raises(RuntimeError):
        _linhas(conector, "2026-10-23", "2026-10-28")


@pytest.mark.parametrize("corpo", [b"", b"<html>manutencao</html>", b"<cidade><nome>X</nome><uf>SP</uf></cidade>"])
def test_corpo_sem_previsao_nao_vira_carga_vazia(monkeypatch, corpo: bytes) -> None:
    conector, _ = _conector(monkeypatch, {244: _Resposta(corpo)})

    with pytest.raises(LayoutInesperadoError):
        _linhas(conector, "2026-10-23", "2026-10-28")


def test_data_fora_de_aaaa_mm_dd_e_layout_inesperado(monkeypatch) -> None:
    corpo = FIXTURE.replace(b"2026-10-23", b"23/10/2026")
    conector, _ = _conector(monkeypatch, {244: _Resposta(corpo)})

    with pytest.raises(LayoutInesperadoError):
        _linhas(conector, "2026-10-23", "2026-10-28")


def test_xml_com_entidade_externa_e_recusado(monkeypatch) -> None:
    ataque = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><cidade>&e;</cidade>'
    conector, _ = _conector(monkeypatch, {244: _Resposta(ataque)})

    with pytest.raises(LayoutInesperadoError):
        _linhas(conector, "2026-10-23", "2026-10-28")


def test_cobre_as_27_capitais_com_ids_distintos() -> None:
    assert len(CAPITAIS) == 27
    assert len({uf for _, uf in CAPITAIS.values()}) == 27
