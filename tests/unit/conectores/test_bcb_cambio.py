"""Conector BCB PTAX — parsing, validação e ciclo de ingestão sem rede."""

import json
from datetime import date
from pathlib import Path

import pytest
from src.conectores.bcb_cambio import BcbCambioPtax, CotacaoDolar
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "bcb_ptax.json"


def _cotacao(data_hora: str, tipo_boletim: str) -> dict:
    """Registro no formato que a API do BCB devolve."""
    return {
        "cotacaoCompra": 5.0,
        "cotacaoVenda": 5.1,
        "dataHoraCotacao": data_hora,
        "tipoBoletim": tipo_boletim,
    }


@pytest.fixture
def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def conector(monkeypatch, payload):
    """Conector com a chamada HTTP substituída pela fixture."""
    monkeypatch.setattr("src.conectores.bcb_cambio.criar_sessao", lambda: None)
    monkeypatch.setattr("src.conectores.bcb_cambio.get_json", lambda *_args, **_kwargs: payload)
    return BcbCambioPtax()


def test_transformar_mapeia_campos_da_api_para_o_schema(conector, payload):
    registro = conector.transformar(payload["value"][0])

    assert registro["data_referencia"] == "2026-01-02"
    assert registro["tipo_boletim"] == "Fechamento"
    validado = CotacaoDolar.model_validate(registro)
    assert validado.data_referencia == date(2026, 1, 2)
    assert float(validado.cotacao_venda) == pytest.approx(5.4327)


def test_cotacao_negativa_e_rejeitada():
    with pytest.raises(ValueError):
        CotacaoDolar.model_validate(
            {
                "data_referencia": "2026-01-02",
                "data_hora_cotacao": "2026-01-02 13:03:24",
                "tipo_boletim": "Fechamento",
                "cotacao_compra": -1,
                "cotacao_venda": 5.4,
            }
        )


def test_extrair_devolve_os_registros_do_payload(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31")))
    assert len(registros) == 3


def test_janela_longa_e_quebrada_pelo_limite_da_api(conector, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "src.conectores.bcb_cambio.get_json",
        lambda _s, _u, params=None: chamadas.append(params) or {"value": []},
    )

    conector.ingerir(Janela.de_texto("2026-01-01", "2026-06-30"))

    assert len(chamadas) > 1, "janela de 6 meses deveria ser particionada"


def test_ingerir_em_dry_run_valida_sem_gravar(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 3
    assert execucao.linhas_invalidas == 0
    assert execucao.linhas_carregadas == 0  # dry-run não carrega


def test_registro_invalido_nao_derruba_a_ingestao(conector, monkeypatch):
    monkeypatch.setattr(
        "src.conectores.bcb_cambio.get_json",
        lambda *_a, **_k: {
            "value": [
                _cotacao("2026-01-02 13:00:00", "Fechamento"),
                _cotacao("2026-01-03 13:00:00", "   "),  # boletim vazio: registro inválido
            ]
        },
    )

    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-05"))

    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 1


def test_erro_na_fonte_encerra_a_execucao_como_erro(conector, monkeypatch):
    def explode(*_args, **_kwargs):
        raise ConnectionError("timeout na Olinda")

    monkeypatch.setattr("src.conectores.bcb_cambio.get_json", explode)

    with pytest.raises(ConnectionError):
        conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-05"))
