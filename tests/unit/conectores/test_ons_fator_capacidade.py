"""Conector ONS — fator de capacidade de eólicas e solares: CSV mensal, sem rede.

A fixture tem linhas reais do arquivo de 09/2026: conjunto de usinas (CEG `-`), usina com CEG,
geração verificada negativa, geração programada vazia, sem localização e sem coordenada.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_fator_capacidade import FatorCapacidade, OnsFatorCapacidade
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_fator_capacidade_202609.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_mensal.criar_sessao", lambda: None)
    conector = OnsFatorCapacidade()
    monkeypatch.setattr(
        conector, "_abrir_mes", lambda _ano, _mes: iter(FIXTURE.read_text(encoding="utf-8").splitlines())
    )
    return conector


def _registros(conector, inicio="2026-09-01", fim="2026-09-30"):
    return [
        FatorCapacidade.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto(inicio, fim))
    ]


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    assert len(list(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-01")))) == 5
    assert len(list(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-30")))) == 7


def test_a_serie_mensal_comeca_em_2022_01():
    assert OnsFatorCapacidade.primeiro_mes == (2022, 1)


def test_janela_de_2021_e_recusada(conector):
    """Antes de 2022-01 o arquivo é anual (`FATOR_CAPACIDADE_AAAA.csv`, ~320 MB)."""
    with pytest.raises(ValueError, match="anual"):
        list(conector.extrair(Janela.de_texto("2021-12-01", "2022-01-31")))


def test_conjunto_de_usinas_tem_ceg_nulo_e_id_ons(conector):
    conjunto = _registros(conector)[0]

    assert conjunto.data_referencia == date(2026, 9, 1)
    assert conjunto.instante == datetime(2026, 9, 1, 0)
    assert conjunto.submercado == "N"
    assert conjunto.uf == "MA"
    assert conjunto.modalidade_operacao == "Conjunto de Usinas"
    assert conjunto.tipo_usina == "Eólica"
    assert conjunto.nome_usina_conjunto == "Conj. Paulino Neves"
    assert conjunto.id_ons == "CJU_MAPLN"
    assert conjunto.codigo_usina is None  # o ceg vem "-" em conjunto
    assert conjunto.geracao_verificada_mwmed == Decimal("371.755")
    assert conjunto.capacidade_instalada_mw == Decimal("426.000")
    assert conjunto.fator_capacidade == Decimal("0.872664319248826")


def test_usina_individual_traz_o_ceg(conector):
    usina = next(r for r in _registros(conector) if r.modalidade_operacao == "Tipo II-B")
    assert usina.codigo_usina == "EOL.CV.CE.033756-0.01"


def test_geracao_verificada_negativa_e_aceita(conector):
    """Achado no arquivo real: solar de madrugada, -1,352 MWmed, e fator -0,0039."""
    solar = next(r for r in _registros(conector) if r.tipo_usina == "Solar" and r.geracao_verificada_mwmed < 0)

    assert solar.geracao_verificada_mwmed == Decimal("-1.352")
    assert solar.fator_capacidade < 0


def test_geracao_programada_vazia_e_nula(conector):
    kairos = next(r for r in _registros(conector) if r.nome_usina_conjunto == "Conj. Kairos")

    assert kairos.geracao_programada_mwmed is None
    assert kairos.geracao_verificada_mwmed == Decimal("75.461")


def test_localizacao_e_coordenadas_vazias_sao_nulas(conector):
    registros = _registros(conector)
    paulino = registros[0]
    monte_verde = next(r for r in registros if r.nome_usina_conjunto == "Conj. Monte Verde Solar")

    assert paulino.localizacao is None  # só o Nordeste traz localização
    assert monte_verde.latitude_coletora is None
    assert monte_verde.longitude_coletora is None
    assert monte_verde.latitude_ponto_conexao == Decimal("-5.446399544259168")


def test_submercado_desconhecido_e_rejeitado(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-01"))))
    bruto["id_subsistema"] = "XX"

    with pytest.raises(ValidationError):
        FatorCapacidade.model_validate(conector.transformar(bruto))


def test_id_ons_vazio_e_rejeitado(conector):
    """O id da usina ou conjunto compõe a chave da Silver."""
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-01"))))
    bruto["id_ons"] = " "

    with pytest.raises(ValidationError):
        FatorCapacidade.model_validate(conector.transformar(bruto))


def test_ingerir_conta_as_linhas_da_janela(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-09-01", "2026-09-30"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 7
    assert execucao.linhas_invalidas == 0
