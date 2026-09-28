"""Conector ONS — CVU das usinas térmicas, por semana operativa.

O que estes testes protegem:

- a semana é filtrada pelo **fim**: o arquivo de 2026 traz a semana de
  27/12/2025 a 02/01/2026, que o filtro pelo início deixaria de fora;
- cada revisão do PMO é uma semana diferente, não uma versão da mesma;
- a origem publica linhas **idênticas em dobro** (38 em 2026) — entram as duas,
  e a Silver deduplica.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ons_cvu_termica import CvuTermica, OnsCvuTermica
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_cvu_termica_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_anual.criar_sessao", lambda: None)
    conector = OnsCvuTermica()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def test_semana_que_comeca_no_ano_anterior_entra_pela_data_de_fim(conector):
    assert len(list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31")))) == 4


def test_transformar(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31"))))
    registro = CvuTermica.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2025, 12, 27)  # início da semana operativa
    assert registro.fim_semana == date(2026, 1, 2)
    assert registro.revisao == 0
    assert registro.submercado == "N"
    assert registro.usina == "BARCARENA"
    assert registro.cvu_reais_mwh == Decimal("0.0")  # CVU zero é valor, não ausência


def test_linha_duplicada_na_origem_entra_e_nao_e_invalida(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-31"))
    assert (execucao.linhas_extraidas, execucao.linhas_invalidas) == (4, 0)
