"""Conector BCB IGP-M — parsing, janela mensal e ciclo sem rede.

Payload real do SGS (série 189, variação mensal em %), colhido em 02/10/2026 para
09/2024 a 09/2026: 25 meses, com valores negativos (o índice cai em deflação do atacado).
"""

import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.bcb_igpm import SERIE_SGS, BcbIgpm, VariacaoIgpm
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "bcb_igpm.json"


@pytest.fixture
def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["189"]


@pytest.fixture
def chamadas():
    return []


@pytest.fixture
def conector(monkeypatch, payload, chamadas):
    monkeypatch.setattr("src.conectores.bcb_igpm.criar_sessao", lambda: None)

    def falso(_sessao, url, params=None):
        chamadas.append((url, params))
        return payload

    monkeypatch.setattr("src.conectores.bcb_igpm.get_json", falso)
    return BcbIgpm()


def test_a_serie_e_a_189_do_sgs():
    assert SERIE_SGS == 189


def test_transformar_converte_o_primeiro_dia_do_mes_e_aceita_negativo(conector):
    registro = conector.transformar({"data": "01/07/2026", "valor": "-1.16"})

    assert registro["data_referencia"] == "2026-07-01"
    validado = VariacaoIgpm.model_validate(registro)
    assert validado.data_referencia == date(2026, 7, 1)
    assert float(validado.variacao_percentual_mes) == pytest.approx(-1.16)


def test_extrair_pede_a_janela_a_partir_do_primeiro_dia_do_mes(conector, chamadas):
    """O SGS data o mês no dia 1: uma janela que começa no dia 15 perderia o próprio mês."""
    list(conector.extrair(Janela.de_texto("2026-09-15", "2026-09-30")))

    [(url, params)] = chamadas
    assert url.endswith("sgs.189/dados")
    assert params == {"formato": "json", "dataInicial": "01/09/2026", "dataFinal": "30/09/2026"}


def test_extrair_devolve_o_que_a_origem_publicou(conector, payload):
    registros = list(conector.extrair(Janela.de_texto("2024-09-01", "2026-09-30")))

    assert len(registros) == len(payload) == 25


def test_toda_a_fixture_real_passa_no_schema(conector, payload):
    validos = [VariacaoIgpm.model_validate(conector.transformar(r)) for r in payload]

    assert [v.data_referencia.day for v in validos] == [1] * 25
    assert any(v.variacao_percentual_mes < 0 for v in validos)


@pytest.mark.parametrize("valor", ["-25", "150"])
def test_variacao_fora_da_faixa_e_erro_de_origem(valor):
    with pytest.raises(ValidationError):
        VariacaoIgpm.model_validate({"data_referencia": "2026-01-01", "variacao_percentual_mes": valor})
