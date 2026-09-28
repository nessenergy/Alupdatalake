"""Conector ONS/EAR por bacia — CSV anual remoto, recorte pela janela, sem rede.

O que estes testes protegem, e que não é óbvio no código:

- a EAR por bacia **passa de 100%**: em 2026 a bacia do Paraguaçu ficou acima
  da própria capacidade máxima em 176 dias (até 154%). É dado real e
  consistente — o percentual bate com verificada/máxima. A regra 0-100 do
  `ons_ear` (subsistema) não vale aqui;
- a origem não traz subsistema: a bacia é a unidade, e `submercado` fica nulo.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_ear_bacia import EarBacia, OnsEarBacia
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_ear_bacia_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_ear_bacia.criar_sessao", lambda: None)
    conector = OnsEarBacia()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-03-04", "2026-03-04")))

    assert len(registros) == 3
    assert {r["ear_data"] for r in registros} == {"2026-03-04"}


def test_janela_fora_do_arquivo_devolve_vazio(conector):
    assert list(conector.extrair(Janela.de_texto("2026-06-01", "2026-06-30"))) == []


def test_ano_sem_recurso_publicado_e_ignorado(conector, monkeypatch, caplog):
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: None)

    with caplog.at_level("WARNING"):
        registros = list(conector.extrair(Janela.de_texto("1970-01-01", "1970-01-02")))

    assert registros == []
    assert any("1970" in r.message for r in caplog.records)


def test_transformar_leva_a_bacia_e_os_valores(conector):
    linhas = conector.extrair(Janela.de_texto("2026-03-04", "2026-03-04"))
    bruto = next(r for r in linhas if r["nomecurto"] == "AMAZONAS")
    registro = EarBacia.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 3, 4)
    assert registro.bacia == "AMAZONAS"
    assert registro.ear_max_mwmes == Decimal("2028.231")
    assert registro.ear_verificada_percentual == Decimal("28.2176")


def test_percentual_acima_de_100_e_aceito():
    """Paraguaçu, 05/03/2026: 410,012 MWmês verificados para 335,383 de máxima."""
    registro = EarBacia.model_validate(
        {
            "data_referencia": "2026-03-05",
            "bacia": "PARAGUACU",
            "ear_max_mwmes": "335.383",
            "ear_verificada_mwmes": "410.012",
            "ear_verificada_percentual": "122.2519",
        }
    )
    assert registro.ear_verificada_percentual == Decimal("122.2519")


def test_valor_negativo_e_rejeitado():
    with pytest.raises(ValidationError):
        EarBacia.model_validate(
            {
                "data_referencia": "2026-03-05",
                "bacia": "TIETE",
                "ear_max_mwmes": "4870.2",
                "ear_verificada_mwmes": "-1.0",
                "ear_verificada_percentual": "-0.0205",
            }
        )


def test_ingerir_descarta_a_linha_invalida_e_conta(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-03-04", "2026-03-05"))

    assert execucao.linhas_extraidas == 7
    assert execucao.linhas_invalidas == 1
