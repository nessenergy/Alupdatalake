"""Base dos CSV mensais pesados do ONS: janela, download em stream, 404 e série curta, sem rede."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
import requests
from src.conectores.ons_csv_mensal import OnsCsvMensal, inteiro_ou_nulo
from src.core.execucao import Janela

CSV = (
    "id;din_instante;valor\n"
    "A;2026-07-31 23:00:00;1\n"
    "A;2026-08-01 00:00:00;2\n"
    "A;2026-08-15 12:00:00;3\n"
    "A;2026-08-31 23:00:00;4\n"
)


class _Resposta:
    """O que o `requests` devolve com `stream=True`, sem rede."""

    def __init__(self, corpo: bytes = b"", status: int = 200) -> None:
        self.status_code = status
        self._corpo = corpo
        self.fechada = False

    def iter_lines(self, chunk_size: int = 512, **_: Any):
        yield from self._corpo.splitlines()

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def close(self) -> None:
        self.fechada = True

    def __enter__(self) -> _Resposta:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class _Sessao:
    def __init__(self, respostas: dict[str, _Resposta]) -> None:
        self.respostas = respostas
        self.chamadas: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, **kwargs: Any) -> _Resposta:
        self.chamadas.append((url, kwargs))
        return self.respostas.get(url.rsplit("/", 1)[1], _Resposta(status=404))


class _Exemplo(OnsCsvMensal):
    entidade = "exemplo"
    schema = dict  # type: ignore[assignment]
    caminho = "exemplo_ho/EXEMPLO_{ano}_{mes:02d}.csv"
    primeiro_mes = (2024, 1)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return bruto


def _conector(monkeypatch, respostas: dict[str, _Resposta]) -> tuple[_Exemplo, _Sessao]:
    sessao = _Sessao(respostas)
    monkeypatch.setattr("src.conectores.ons_csv_mensal.criar_sessao", lambda: sessao)
    return _Exemplo(), sessao


def test_baixa_um_arquivo_por_mes_da_janela_e_recorta_pelas_datas(monkeypatch):
    conector, sessao = _conector(monkeypatch, {"EXEMPLO_2026_08.csv": _Resposta(CSV.encode())})

    linhas = list(conector.extrair(Janela.de_texto("2026-08-01", "2026-08-15")))

    assert [x["valor"] for x in linhas] == ["2", "3"]  # 31/07 e 31/08 ficam fora da janela
    assert [url.rsplit("/", 1)[1] for url, _ in sessao.chamadas] == ["EXEMPLO_2026_08.csv"]


def test_janela_que_cruza_o_mes_baixa_os_dois_arquivos(monkeypatch):
    conector, sessao = _conector(monkeypatch, {})

    list(conector.extrair(Janela.de_texto("2026-07-20", "2026-09-02")))

    assert [url.rsplit("/", 1)[1] for url, _ in sessao.chamadas] == [
        "EXEMPLO_2026_07.csv",
        "EXEMPLO_2026_08.csv",
        "EXEMPLO_2026_09.csv",
    ]


def test_baixa_em_stream_com_timeout(monkeypatch):
    """Arquivo de 34 MB não pode ser lido inteiro para a memória: `stream=True`."""
    conector, sessao = _conector(monkeypatch, {"EXEMPLO_2026_08.csv": _Resposta(CSV.encode())})

    list(conector.extrair(Janela.de_texto("2026-08-01", "2026-08-31")))

    _, opcoes = sessao.chamadas[0]
    assert opcoes["stream"] is True
    assert opcoes["timeout"]


def test_fecha_a_conexao_ao_terminar_o_arquivo(monkeypatch):
    resposta = _Resposta(CSV.encode())
    conector, _ = _conector(monkeypatch, {"EXEMPLO_2026_08.csv": resposta})

    list(conector.extrair(Janela.de_texto("2026-08-01", "2026-08-31")))

    assert resposta.fechada


def test_decodifica_linha_em_latin1_quando_nao_e_utf8(monkeypatch):
    """O ONS publica utf-8 e latin-1 no mesmo catálogo; a linha decide, como no `ons_csv_anual`."""
    corpo = "id;din_instante;valor\nJoão;2026-08-02 00:00:00;1\n".encode("latin-1")
    conector, _ = _conector(monkeypatch, {"EXEMPLO_2026_08.csv": _Resposta(corpo)})

    linhas = list(conector.extrair(Janela.de_texto("2026-08-01", "2026-08-31")))

    assert linhas[0]["id"] == "João"


def test_mes_ainda_nao_publicado_e_ignorado(monkeypatch, caplog):
    """O mês corrente pode não existir no catálogo no dia 1: 404 não derruba a ingestão."""
    conector, _ = _conector(monkeypatch, {"EXEMPLO_2026_08.csv": _Resposta(CSV.encode())})

    linhas = list(conector.extrair(Janela.de_texto("2026-08-01", "2026-09-05")))

    assert len(linhas) == 3
    assert "2026-09" in caplog.text


def test_erro_http_que_nao_e_404_propaga(monkeypatch):
    conector, _ = _conector(monkeypatch, {"EXEMPLO_2026_08.csv": _Resposta(status=500)})

    with pytest.raises(requests.HTTPError):
        list(conector.extrair(Janela.de_texto("2026-08-01", "2026-08-31")))


def test_janela_anterior_ao_inicio_da_serie_mensal_e_recusada_sem_baixar(monkeypatch):
    """Antes de `primeiro_mes` o ONS publica um arquivo anual de ~190 MB, com outro nome: erro claro."""
    conector, sessao = _conector(monkeypatch, {})

    with pytest.raises(ValueError, match="2023-12.*2024-01.*anual"):
        list(conector.extrair(Janela.de_texto("2023-12-15", "2024-01-10")))

    assert sessao.chamadas == []


def test_inteiro_ou_nulo_aceita_ponto_zero_e_vazio():
    assert inteiro_ou_nulo("201.0") == 201
    assert inteiro_ou_nulo("201") == 201
    assert inteiro_ou_nulo("  ") is None
    assert inteiro_ou_nulo(None) is None
    assert inteiro_ou_nulo(Decimal("9")) == 9


def test_inteiro_ou_nulo_recusa_valor_fracionado():
    with pytest.raises(ValueError, match="inteiro"):
        inteiro_ou_nulo("1.5")
