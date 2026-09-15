"""Conector ONS/geração de usina — CSV mensal remoto, recorte pela janela, sem rede."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ons_geracao_usina import GeracaoUsina, OnsGeracaoUsina
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_geracao_usina_202607.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_geracao_usina.criar_sessao", lambda: None)
    conector = OnsGeracaoUsina()
    monkeypatch.setattr(conector, "_baixar_mes", lambda _ano, _mes: FIXTURE.read_text(encoding="utf-8"))
    return conector


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-01")))

    assert len(registros) == 3
    assert {r["din_instante"][:10] for r in registros} == {"2026-07-01"}


def test_janela_maior_pega_os_dois_dias(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-02")))
    assert len(registros) == 5


def test_janela_que_cruza_o_mes_baixa_cada_mes(conector, monkeypatch):
    meses = []
    monkeypatch.setattr(conector, "_baixar_mes", lambda ano, mes: meses.append((ano, mes)) or "")

    list(conector.extrair(Janela.de_texto("2026-06-30", "2026-07-02")))

    assert meses == [(2026, 6), (2026, 7)]


def test_transformar_deriva_data_e_hora_e_normaliza_submercado(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-01"))))
    registro = GeracaoUsina.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.hora == 0
    assert registro.submercado == "N"  # veio " N " com espaço em volta


def test_ceg_traco_vira_codigo_usina_e_id_ons_nulos(conector):
    registros = [
        GeracaoUsina.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-01"))
    ]
    mmgd = next(r for r in registros if r.nome_usina == "PQU MMAM MMGD")

    assert mmgd.codigo_usina is None
    assert mmgd.id_ons is None
    assert mmgd.geracao_mw == Decimal("0.0")


def test_ceg_presente_preenche_codigo_usina(conector):
    registros = [
        GeracaoUsina.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-01"))
    ]
    balbina = next(r for r in registros if r.nome_usina == "BALBINA")

    assert balbina.codigo_usina == "UHE.PH.AM.000190-2.01"
    assert balbina.id_ons == "AMBA"


def test_geracao_negativa_e_aceita(conector):
    registros = [
        GeracaoUsina.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-01"))
    ]
    reversivel = next(r for r in registros if r.nome_usina == "PIRATININGA REV")

    assert reversivel.geracao_mw == Decimal("-12.5")


def test_geracao_vazia_vira_nula_nao_e_rejeitada(conector):
    """Achado do dry-run real (15/09/2026): ~12% das linhas do arquivo de
    julho/2026 vêm com `val_geracao` vazio — usina sem medição naquela hora,
    não dado malformado. Vazio é ausência, não erro: vira NULL, a linha
    continua válida."""
    registros = [
        GeracaoUsina.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-02"))
    ]
    sem_medicao = next(r for r in registros if r.nome_usina == "CAVALINHOS II")

    assert sem_medicao.geracao_mw is None


def test_submercado_desconhecido_e_rejeitado():
    with pytest.raises(ValueError, match="submercado desconhecido"):
        GeracaoUsina.model_validate(_registro_minimo(submercado="XX"))


def test_din_instante_malformado_e_rejeitado():
    """Um `ValueError` do `strptime` roda dentro do `model_validator`, não em
    `transformar()` — vira `ValidationError` (linha inválida), não crash."""
    with pytest.raises(ValueError, match="din_instante inválido"):
        GeracaoUsina.model_validate(_registro_minimo(din_instante="01/07/2026"))


def test_ingerir_conta_as_linhas_da_janela(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-07-01", "2026-07-02"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 5
    assert execucao.linhas_invalidas == 0


def _registro_minimo(**troca):
    base = {
        "din_instante": "2026-07-01 00:00:00",
        "submercado": "N",
        "nome_subsistema": "NORTE",
        "uf": "AM",
        "nome_uf": "AMAZONAS",
        "modalidade_operacao": "TIPO I",
        "tipo_usina": "TERMICA",
        "tipo_combustivel": "Gás",
        "nome_usina": "X",
        "geracao_mw": "10",
    }
    return base | troca
