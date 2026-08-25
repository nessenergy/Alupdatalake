"""Conector ANEEL/SIGA — cadastro paginado, número em formato brasileiro, sem rede."""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.aneel_siga import AneelSiga, Empreendimento, _decimal_br
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "aneel_siga.json"
JANELA = Janela.de_texto("2026-01-01", "2026-01-31")


@pytest.fixture
def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def conector(monkeypatch, payload):
    monkeypatch.setattr("src.conectores.aneel_siga.criar_sessao", lambda: None)
    monkeypatch.setattr("src.conectores.aneel_siga.get_json", lambda *_a, **_k: payload)
    return AneelSiga()


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("1400,00", Decimal("1400.00")),
        ("1.400,00", Decimal("1400.00")),  # separador de milhar
        (",00", Decimal("0.00")),  # ANEEL omite o zero inteiro
        ("-20,12", Decimal("-20.12")),
        ("", None),  # vazio não é zero
        (None, None),
        ("texto", None),
    ],
)
def test_decimal_brasileiro(entrada, esperado):
    assert _decimal_br(entrada) == esperado


def test_transformar_mapeia_codceg_para_codigo_usina(conector, payload):
    bruto = payload["result"]["records"][0]
    registro = Empreendimento.model_validate(conector.transformar(bruto))

    assert registro.codigo_usina == bruto["CodCEG"]
    assert registro.data_referencia == bruto["DatGeracaoConjuntoDados"]


def test_empreendimento_sem_codigo_e_rejeitado():
    with pytest.raises(ValueError, match="obrigatório"):
        Empreendimento.model_validate({"data_referencia": "2026-08-07", "codigo_usina": "  ", "nome": "X"})


def test_paginacao_para_quando_cobre_o_total(conector, monkeypatch):
    chamadas = []

    def paginar(_sessao, _url, params=None):
        chamadas.append(params["offset"])
        offset = params["offset"]
        registros = [
            {"DatGeracaoConjuntoDados": "2026-08-07", "CodCEG": f"CEG-{offset + i}", "NomEmpreendimento": "U"}
            for i in range(2)
        ]
        return {"result": {"records": registros if offset < 4 else [], "total": 4}}

    monkeypatch.setattr("src.conectores.aneel_siga.get_json", paginar)

    registros = list(conector.extrair(JANELA))

    assert len(registros) == 4
    assert chamadas == [0, 2]  # parou ao cobrir o total, sem requisição extra


def test_ingerir_valida_o_cadastro(conector):
    execucao = conector.ingerir(JANELA)

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 3
    assert execucao.linhas_invalidas == 0
