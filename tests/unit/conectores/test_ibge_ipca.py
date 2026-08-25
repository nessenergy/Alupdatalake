"""Conector IBGE/IPCA — achatamento do payload aninhado, período mensal, sem rede."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ibge_ipca import IbgeIpca, IpcaRegistro
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ibge_ipca.json"


@pytest.fixture
def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def conector(monkeypatch, payload):
    monkeypatch.setattr("src.conectores.ibge_ipca.criar_sessao", lambda: None)
    monkeypatch.setattr("src.conectores.ibge_ipca.get_json", lambda *_a, **_k: payload)
    return IbgeIpca()


def test_janela_de_datas_vira_intervalo_de_meses(conector):
    janela = Janela.de_texto("2026-01-15", "2026-03-02")
    assert conector._intervalo_mensal(janela) == "202601-202603"


def test_extrair_achata_uma_linha_por_periodo_e_variavel(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-04-30")))

    # 2 variáveis × 3 meses publicados; o 4º mês vem como "..." e não vira linha
    assert len(registros) == 6
    assert {r["variavel_id"] for r in registros} == {"63", "69"}


def test_mes_sem_publicacao_nao_vira_linha(conector):
    periodos = {r["periodo"] for r in conector.extrair(Janela.de_texto("2026-01-01", "2026-04-30"))}
    assert "202604" not in periodos


def test_transformar_deriva_a_data_do_periodo(conector, payload):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-01-01", "2026-03-31"))))
    registro = IpcaRegistro.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 1, 1)
    assert registro.periodo == "202601"
    assert registro.valor == Decimal("0.33")


def test_periodo_fora_do_formato_e_rejeitado():
    with pytest.raises(ValueError):
        IpcaRegistro.model_validate(
            {
                "data_referencia": "2026-01-01",
                "periodo": "2026-01",  # com hífen: não é AAAAMM
                "variavel_id": "63",
                "variavel": "IPCA - Variação mensal",
                "unidade": "%",
                "valor": "0.33",
            }
        )


def test_ingerir_em_dry_run_valida_todos_os_registros(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-04-30"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 6
    assert execucao.linhas_invalidas == 0
