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

    monkeypatch.setattr("src.core.conector.ler_raw", lambda _uri: brutos)
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
