"""Base `OnsArquivoDiario` — um CSV por dia, descoberto pela URL, sem rede.

O que estes testes protegem:

- a janela vira a lista de URLs `{dataset}/{ARQUIVO}_{AAAA_MM_DD}.csv`, um GET
  por dia, sem listar o catálogo CKAN (que omitiu 9 arquivos que existem);
- dia sem arquivo (404) é aviso no log, não erro — o ONS tem buracos de 1 e 2
  dias seguidos;
- três ou mais dias sem arquivo e nenhum encontrado é URL quebrada, e vira erro
  (senão a execução fecha em SUCESSO com zero linha e o alerta de silêncio,
  que só olha sucesso, nunca dispara);
- o corpo é lido em stream e cada linha é decodificada sozinha (UTF-8, com
  ISO-8859-1 de reserva).
"""

from datetime import date
from typing import ClassVar

import pytest
from pydantic import BaseModel
from src.conectores.ons_arquivo_diario import OnsArquivoDiario
from src.core.execucao import Janela


class _Linha(BaseModel):
    dia: str
    valor: str


class _Conector(OnsArquivoDiario):
    entidade = "teste_diario"
    schema = _Linha
    caminho: ClassVar[str] = "dataset_x/ARQUIVO_X_{dia:%Y_%m_%d}.csv"

    def transformar(self, bruto):
        return {"dia": bruto["dia"], "valor": bruto["valor"]}


class _Resposta:
    def __init__(self, status: int, corpo: bytes = b""):
        self.status_code = status
        self._corpo = corpo
        self.fechada = False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def iter_lines(self):
        yield from self._corpo.splitlines()

    def close(self):
        self.fechada = True


class _Sessao:
    def __init__(self, respostas: dict[str, _Resposta]):
        self.respostas = respostas
        self.pedidos: list[tuple[str, bool]] = []

    def get(self, url, *, stream, timeout):
        self.pedidos.append((url, stream))
        return self.respostas.get(url.rsplit("/", 1)[1], _Resposta(404))


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_arquivo_diario.criar_sessao", lambda: None)
    return _Conector()


def _com_sessao(conector, respostas):
    conector._sessao = _Sessao(respostas)
    return conector._sessao


def _corpo(dia: str) -> bytes:
    return f"dia;valor\r\n{dia};1\r\n{dia};2\r\n".encode()


def test_um_get_por_dia_da_janela_em_stream_na_url_previsivel(conector):
    sessao = _com_sessao(
        conector,
        {
            "ARQUIVO_X_2026_10_01.csv": _Resposta(200, _corpo("a")),
            "ARQUIVO_X_2026_10_02.csv": _Resposta(200, _corpo("b")),
        },
    )

    registros = list(conector.extrair(Janela.de_texto("2026-10-01", "2026-10-02")))

    assert [r["dia"] for r in registros] == ["a", "a", "b", "b"]
    assert sessao.pedidos == [
        (f"https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/dataset_x/ARQUIVO_X_2026_10_0{d}.csv", True)
        for d in (1, 2)
    ]


def test_dia_sem_arquivo_e_tolerado(conector, caplog):
    _com_sessao(conector, {"ARQUIVO_X_2026_10_01.csv": _Resposta(200, _corpo("a"))})

    registros = list(conector.extrair(Janela.de_texto("2026-10-01", "2026-10-02")))

    assert len(registros) == 2
    assert "sem arquivo em 2026-10-02" in caplog.text


def test_tres_dias_sem_nenhum_arquivo_e_erro(conector):
    _com_sessao(conector, {})

    with pytest.raises(RuntimeError, match="nenhum arquivo"):
        list(conector.extrair(Janela.de_texto("2026-10-01", "2026-10-03")))


def test_um_ou_dois_dias_sem_arquivo_nao_e_erro(conector):
    _com_sessao(conector, {})

    assert list(conector.extrair(Janela.de_texto("2026-10-01", "2026-10-02"))) == []


def test_erro_http_diferente_de_404_sobe(conector):
    _com_sessao(conector, {"ARQUIVO_X_2026_10_01.csv": _Resposta(500)})

    with pytest.raises(RuntimeError, match="HTTP 500"):
        list(conector.extrair(Janela.de_texto("2026-10-01", "2026-10-01")))


def test_resposta_e_fechada_ao_fim_da_leitura(conector):
    resposta = _Resposta(200, _corpo("a"))
    _com_sessao(conector, {"ARQUIVO_X_2026_10_01.csv": resposta})

    list(conector.extrair(Janela.de_texto("2026-10-01", "2026-10-01")))

    assert resposta.fechada


def test_linha_latin1_e_decodificada_sem_derrubar_o_arquivo(conector):
    corpo = b"dia;valor\n" + "a;Sertão\n".encode("latin-1") + "b;Sertão\n".encode()
    _com_sessao(conector, {"ARQUIVO_X_2026_10_01.csv": _Resposta(200, corpo)})

    registros = list(conector.extrair(Janela.de_texto("2026-10-01", "2026-10-01")))

    assert [r["valor"] for r in registros] == ["Sertão", "Sertão"]


def test_janela_de_um_dia_usa_o_dia_pedido(conector):
    sessao = _com_sessao(conector, {})
    list(conector.extrair(Janela(date(2026, 10, 2), date(2026, 10, 2))))
    assert sessao.pedidos[0][0].endswith("ARQUIVO_X_2026_10_02.csv")
