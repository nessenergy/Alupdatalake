"""Replay usa o raw já arquivado e nunca consulta novamente a fonte."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import BaseModel
from src.core.conector import Conector
from src.core.execucao import Janela
from src.core.storage import identificar_raw


class Registro(BaseModel):
    data_referencia: date
    valor: Decimal


class ConectorReplay(Conector):
    fonte = "teste"
    entidade = "medicao"
    schema = Registro

    def extrair(self, janela: Janela):
        del janela
        raise AssertionError("replay não pode consultar a fonte")


def test_identificar_raw_valida_e_extrai_a_ingestao_original() -> None:
    info = identificar_raw("gs://lake-raw/teste/medicao/dt=2026-01-01/origem123.json.gz")

    assert info.fonte == "teste"
    assert info.entidade == "medicao"
    assert info.ingestao_id == "origem123"


@pytest.mark.parametrize(
    "uri",
    ["https://exemplo/raw", "gs://bucket/caminho-curto", "gs://bucket/a/b/dt=invalida/id.json.gz"],
)
def test_identificar_raw_recusa_uri_invalida(uri: str) -> None:
    with pytest.raises(ValueError, match="raw"):
        identificar_raw(uri)


def test_reprocessar_raw_valida_carrega_e_preserva_linhagem(monkeypatch: pytest.MonkeyPatch) -> None:
    brutos = [{"data_referencia": "2026-01-01", "valor": "10.5"}]
    carregadas: list[dict] = []
    registradas = []

    monkeypatch.setattr("src.core.conector.ler_raw", lambda _uri: (r for r in brutos))
    monkeypatch.setattr(
        "src.core.conector.carregar_bronze",
        lambda _execucao, linhas: carregadas.extend(linhas) or len(linhas),
    )
    monkeypatch.setattr("src.core.conector.registrar_execucao", registradas.append)

    execucao = ConectorReplay().reprocessar_raw(
        "gs://lake-raw/teste/medicao/dt=2026-01-01/origem123.json.gz",
        Janela.de_texto("2026-01-01", "2026-01-02"),
    )

    assert execucao.status == "SUCESSO"
    assert execucao.modo == "REPLAY"
    assert execucao.origem_ingestao_id == "origem123"
    assert execucao.linhas_extraidas == 1
    assert execucao.linhas_carregadas == 1
    assert isinstance(carregadas[0]["_ingestao_timestamp"], str)
    assert datetime.fromisoformat(carregadas[0]["_ingestao_timestamp"])
    assert registradas == [execucao]


def test_replay_recusa_raw_de_outro_conector() -> None:
    with pytest.raises(ValueError, match="pertence"):
        ConectorReplay().reprocessar_raw(
            "gs://lake-raw/outra/entidade/dt=2026-01-01/origem123.json.gz",
            Janela.de_texto("2026-01-01", "2026-01-01"),
        )


@pytest.mark.parametrize("failure", [None, "read", "load"])
def test_replay_em_lotes_incrementais_fecha_e_registra_falha(monkeypatch, failure):
    loaded, registered, state = [], [], {"read": 0, "closed": False}

    def records(uri):
        try:
            for i in range(5):
                if failure == "read" and i == 2:
                    raise OSError("falha na leitura")
                state["read"] += 1
                yield {"data_referencia": "2026-01-01", "valor": "invalido" if i == 3 else str(i)}
        finally:
            state["closed"] = True

    def load(execution, rows):
        if failure == "load" and loaded:
            raise OSError("falha na carga")
        loaded.append((len(rows), state["read"]))
        return len(rows)

    monkeypatch.setattr("src.core.conector.ler_raw", records)
    monkeypatch.setattr("src.core.conector.carregar_bronze", load)
    monkeypatch.setattr("src.core.conector.registrar_execucao", registered.append)
    connector = ConectorReplay()
    connector.tamanho_do_lote = 2
    args = ("gs://lake-raw/teste/medicao/dt=2026-01-01/origem.json.gz", Janela.de_texto("2026-01-01", "2026-01-01"))
    if failure:
        with pytest.raises(OSError):
            connector.reprocessar_raw(*args)
        assert registered[0].status == "ERRO"
        assert registered[0].linhas_carregadas == 2
    else:
        result = connector.reprocessar_raw(*args)
        assert loaded == [(2, 2), (1, 4), (1, 5)]
        assert result.linhas_extraidas == 5
        assert result.linhas_invalidas == 1
        assert result.linhas_carregadas == 4
    assert loaded[0] == (2, 2)
    assert state["closed"]
    assert registered[0].origem_ingestao_id == "origem"


def test_replay_limita_lote_por_bytes(monkeypatch):
    row = {"data_referencia": "2026-01-01", "valor": "1", "payload": "x" * (1024 * 1024 - 100)}
    monkeypatch.setattr("src.core.conector.ler_raw", lambda uri: (dict(row) for _ in range(10)))
    sizes = []
    monkeypatch.setattr("src.core.conector.carregar_bronze", lambda e, rows: sizes.append(len(rows)) or len(rows))
    monkeypatch.setattr("src.core.conector.registrar_execucao", lambda e: None)
    result = ConectorReplay().reprocessar_raw(
        "gs://lake-raw/teste/medicao/dt=2026-01-01/origem.json.gz", Janela.de_texto("2026-01-01", "2026-01-01")
    )
    assert sizes == [8, 2]
    assert result.linhas_extraidas == result.linhas_carregadas == 10
