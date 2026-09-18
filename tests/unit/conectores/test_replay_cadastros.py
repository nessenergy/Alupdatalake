"""Replay de cadastro preserva a data da origem sem estado ou rede."""

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from src.conectores.ccee_perfil import CceePerfil
from src.conectores.ons_capacidade import OnsCapacidade
from src.core.execucao import Janela

FIXTURES = Path(__file__).parents[2] / "fixtures"
WINDOW = Janela.de_texto("2026-09-14", "2026-09-14")


@pytest.fixture(params=[CceePerfil, OnsCapacidade], ids=["ccee_perfil", "ons_capacidade"])
def snapshot(request, monkeypatch):
    connector = request.param()
    if isinstance(connector, CceePerfil):
        monkeypatch.setattr(connector, "_recurso_mais_recente", lambda: ("https://example.test/raw", date(2026, 9, 1)))
        monkeypatch.setattr(
            connector, "_baixar", lambda _url: (FIXTURES / "ccee_perfil_2026.csv").read_text("iso-8859-1")
        )
    else:
        monkeypatch.setattr(
            connector, "_baixar", lambda: ((FIXTURES / "ons_capacidade.csv").read_text("utf-8"), date(2026, 9, 1))
        )
    records = json.loads(json.dumps(list(connector.extrair(WINDOW)), default=str))
    return request.param, records


def setup_replay(monkeypatch, connector_type, records):
    connector = connector_type()

    def no_network(*args, **kwargs):
        raise AssertionError("replay não consulta a fonte")

    monkeypatch.setattr(connector._sessao, "get", no_network)
    monkeypatch.setattr(connector, "extrair", no_network)
    monkeypatch.setattr("src.core.conector.ler_raw", lambda _uri: (record for record in records))
    loaded, executions = [], []
    monkeypatch.setattr("src.core.conector.carregar_bronze", lambda _execution, rows: loaded.extend(rows) or len(rows))
    monkeypatch.setattr("src.core.conector.registrar_execucao", executions.append)
    uri = f"gs://raw/{connector.fonte}/{connector.entidade}/dt=2026-09-14/original.json.gz"
    return connector, uri, loaded, executions


def test_replay_fresh_instance_preserves_source_snapshot(snapshot, monkeypatch):
    connector_type, records = snapshot
    connector, uri, loaded, _ = setup_replay(monkeypatch, connector_type, records)
    execution = connector.reprocessar_raw(uri, Janela.de_texto("2026-08-01", "2026-08-01"))
    assert execution.status == "SUCESSO"
    assert execution.linhas_carregadas == len(records)
    assert execution.linhas_invalidas == 0
    assert execution.origem_ingestao_id == "original"
    assert {row["data_referencia"] for row in loaded} == {"2026-09-01"}


@pytest.mark.parametrize("metadata", [None, "", "invalida", "2026-02-30"])
def test_replay_rejects_missing_or_invalid_snapshot(snapshot, monkeypatch, metadata):
    connector_type, records = snapshot
    for record in records:
        record.pop("_data_retrato", None)
        if metadata is not None:
            record["_data_retrato"] = metadata
    connector, uri, loaded, executions = setup_replay(monkeypatch, connector_type, records)
    connector._data_retrato = date(2026, 9, 18)  # Estado residual não é evidência do raw.
    with pytest.raises(ValueError, match="data do retrato"):
        connector.reprocessar_raw(uri, WINDOW)
    assert loaded == []
    assert executions[0].status == "ERRO"


@pytest.mark.parametrize("value", [None, "", "invalida"])
def test_ons_does_not_invent_source_date(value):
    with pytest.raises(ValueError, match="Last-Modified"):
        OnsCapacidade._data_do_cabecalho(value)


@pytest.mark.parametrize("value", [None, "", "invalida"])
def test_ccee_does_not_invent_source_date(monkeypatch, value):
    connector = CceePerfil()
    response = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {
            "result": {"resources": [{"name": "2026", "url": "https://example.test/raw", "last_modified": value}]}
        },
    )
    monkeypatch.setattr(connector._sessao, "get", lambda *args, **kwargs: response)
    with pytest.raises(ValueError, match="last_modified"):
        connector._recurso_mais_recente()
