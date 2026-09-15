"""Conectores ONS/constrained-off — eólica e fotovoltaica, mesmo CSV de meia hora."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ons_restricao_coff import RestricaoCoff
from src.conectores.ons_restricao_coff_eolica import OnsRestricaoCoffEolica
from src.conectores.ons_restricao_coff_fotovoltaica import OnsRestricaoCoffFotovoltaica
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_restricao_coff_202608.csv"


@pytest.fixture(params=[OnsRestricaoCoffEolica, OnsRestricaoCoffFotovoltaica])
def conector(request, monkeypatch):
    """As duas fontes têm o mesmo schema; o que muda é a URL e o rótulo."""
    monkeypatch.setattr("src.conectores.ons_restricao_coff.criar_sessao", lambda: None)
    conector = request.param()
    monkeypatch.setattr(conector, "_baixar_mes", lambda _ano, _mes: FIXTURE.read_text(encoding="utf-8"))
    return conector


def registros(conector, de, ate):
    return [RestricaoCoff.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto(de, ate))]


def test_as_duas_fontes_apontam_para_recursos_diferentes():
    assert "EOLICA" in OnsRestricaoCoffEolica.url_mes
    assert "FOTOVOLTAICA" in OnsRestricaoCoffFotovoltaica.url_mes
    assert OnsRestricaoCoffEolica.entidade != OnsRestricaoCoffFotovoltaica.entidade


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    extraidos = list(conector.extrair(Janela.de_texto("2026-08-01", "2026-08-01")))

    assert len(extraidos) == 3


def test_o_instante_e_de_meia_em_meia_hora_nao_de_hora_em_hora(conector):
    """A origem publica dois registros por hora (`:00` e `:30`). Derivar só a
    hora perderia metade do arquivo na deduplicação."""
    todos = registros(conector, "2026-08-01", "2026-08-01")
    instantes = sorted(r.instante for r in todos if r.nome_usina == "Conj. Exemplo")

    assert instantes == [datetime(2026, 8, 1, 0, 0), datetime(2026, 8, 1, 0, 30)]
    assert todos[0].data_referencia == date(2026, 8, 1)


def test_meia_hora_sem_restricao_e_dado_valido(conector):
    """47,5% das linhas do arquivo real de agosto/2026 não têm restrição: é a
    usina gerando livre, não linha incompleta."""
    livre = registros(conector, "2026-08-01", "2026-08-01")[0]

    assert livre.razao_restricao is None
    assert livre.geracao_nao_realizada_mw is None
    assert livre.geracao_mw == Decimal("83.365")
    assert livre.disponibilidade_mw == Decimal("411.0")


def test_meia_hora_com_restricao_traz_a_razao_e_a_energia_nao_gerada(conector):
    todos = registros(conector, "2026-08-01", "2026-08-01")
    restrita = next(r for r in todos if r.razao_restricao == "ENE")

    assert restrita.origem_restricao == "SIS"
    assert restrita.geracao_nao_realizada_mw == Decimal("68.000")
    assert restrita.minutos_restricao == 30
    assert restrita.minutos_ene == 30


def test_ceg_quando_existe_entra_na_forma_canonica(conector):
    """Só 7,2% das linhas reais trazem CEG — a granularidade é o conjunto, que
    não tem CEG próprio. Quando vem, tem de casar com o de-para."""
    todos = registros(conector, "2026-08-01", "2026-08-01")
    com_ceg = next(r for r in todos if r.nome_usina == "USINA COM CEG")
    sem_ceg = next(r for r in todos if r.nome_usina == "Conj. Exemplo")

    assert com_ceg.codigo_usina == "EOL.CV.RS.028443-2.01"
    assert sem_ceg.codigo_usina is None
    assert sem_ceg.id_ons == "CJU_RNEXE"  # é o id_ons que identifica o conjunto


def test_geracao_negativa_e_aceita(conector):
    """Medição de usina parada consumindo da rede; 4 linhas do mês real."""
    todos = registros(conector, "2026-08-02", "2026-08-02")

    assert todos[0].geracao_mw == Decimal("-0.250")


def test_submercado_desconhecido_e_rejeitado():
    with pytest.raises(ValueError, match="submercado desconhecido"):
        RestricaoCoff.model_validate(_registro_minimo(submercado="XX"))


def test_din_instante_malformado_e_rejeitado():
    with pytest.raises(ValueError, match="din_instante inválido"):
        RestricaoCoff.model_validate(_registro_minimo(din_instante="01/08/2026 00:00"))


def test_ingerir_conta_as_linhas_da_janela(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-08-01", "2026-08-02"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 4
    assert execucao.linhas_invalidas == 0


def _registro_minimo(**troca):
    base = {
        "din_instante": "2026-08-01 00:00:00",
        "submercado": "NE",
        "nome_subsistema": "Nordeste",
        "uf": "RN",
        "nome_uf": "Rio Grande do Norte",
        "nome_usina": "X",
        "id_ons": "X",
    }
    return base | troca
