"""Conector ONS/disponibilidade de usina — CSV mensal remoto, sem rede."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ons_disponibilidade_usina import DisponibilidadeUsina, OnsDisponibilidadeUsina
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_disponibilidade_usina_202608.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_disponibilidade_usina.criar_sessao", lambda: None)
    conector = OnsDisponibilidadeUsina()
    monkeypatch.setattr(conector, "_baixar_mes", lambda _ano, _mes: FIXTURE.read_text(encoding="utf-8"))
    return conector


def registros(conector, de, ate):
    return [
        DisponibilidadeUsina.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto(de, ate))
    ]


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    extraidos = list(conector.extrair(Janela.de_texto("2026-08-01", "2026-08-01")))

    assert len(extraidos) == 3
    assert {r["din_instante"][:10] for r in extraidos} == {"2026-08-01"}


def test_janela_que_cruza_o_mes_baixa_cada_mes(conector, monkeypatch):
    meses = []
    monkeypatch.setattr(conector, "_baixar_mes", lambda ano, mes: meses.append((ano, mes)) or "")

    list(conector.extrair(Janela.de_texto("2026-07-30", "2026-08-02")))

    assert meses == [(2026, 7), (2026, 8)]


def test_transformar_deriva_data_e_hora_e_normaliza_submercado(conector):
    primeiro = registros(conector, "2026-08-01", "2026-08-01")[0]

    assert primeiro.data_referencia == date(2026, 8, 1)
    assert primeiro.hora == 0
    assert primeiro.submercado == "N"  # veio " N " com espaço em volta


def test_ceg_entra_na_forma_canonica(conector):
    """A ANEEL publica o sufixo com um dígito e o ONS com dois; sem igualar, o
    de-para de usina não fecha (`src/core/ceg.py`)."""
    todos = registros(conector, "2026-08-01", "2026-08-02")
    termica = next(r for r in todos if r.nome_usina == "TERMO EXEMPLO")

    assert termica.codigo_usina == "UTE.CM.SP.000111-1.01"


def test_usina_sem_ceg_nao_e_descartada(conector):
    todos = registros(conector, "2026-08-01", "2026-08-02")
    sem_ceg = next(r for r in todos if r.nome_usina == "HIDRO SEM CEG")

    assert sem_ceg.codigo_usina is None
    assert sem_ceg.id_ons is None
    assert sem_ceg.potencia_instalada == Decimal("12")


def test_disponibilidade_zero_e_dado_nao_ausencia(conector):
    """Usina indisponível é o caso que esta fonte existe para mostrar: zero
    tem de chegar como zero, não virar NULL."""
    todos = registros(conector, "2026-08-01", "2026-08-01")
    parada = next(r for r in todos if r.nome_usina == "TERMO EXEMPLO")

    assert parada.disponibilidade_operacional == Decimal("0")
    assert parada.potencia_instalada == Decimal("500")


def test_valor_vazio_vira_nulo_e_a_linha_continua_valida(conector):
    todos = registros(conector, "2026-08-01", "2026-08-01")
    nuclear = next(r for r in todos if r.nome_usina == "NUCLEAR EXEMPLO")

    assert nuclear.disponibilidade_sincronizada is None
    assert nuclear.disponibilidade_operacional == Decimal("640")


def test_submercado_desconhecido_e_rejeitado():
    with pytest.raises(ValueError, match="submercado desconhecido"):
        DisponibilidadeUsina.model_validate(_registro_minimo(submercado="XX"))


def test_din_instante_malformado_e_rejeitado():
    with pytest.raises(ValueError, match="din_instante inválido"):
        DisponibilidadeUsina.model_validate(_registro_minimo(din_instante="01/08/2026"))


def test_ingerir_conta_as_linhas_da_janela(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-08-01", "2026-08-02"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 5
    assert execucao.linhas_invalidas == 0


def _registro_minimo(**troca):
    base = {
        "din_instante": "2026-08-01 00:00:00",
        "submercado": "N",
        "nome_subsistema": "Norte",
        "uf": "AP",
        "nome_uf": "Amapá",
        "tipo_usina": "UHE",
        "tipo_combustivel": "Hidráulica",
        "nome_usina": "X",
        "potencia_instalada": "10",
    }
    return base | troca
