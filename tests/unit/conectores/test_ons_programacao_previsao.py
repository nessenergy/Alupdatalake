"""Conector ONS — previsão versus programado de eólicas e solares, um CSV por dia.

O que estes testes protegem, e que vem do arquivo real (varredura dos 730
arquivos de 01/10/2024 a 02/10/2026, em 02/10/2026):

- `dat_programacao` vem como `AAAAMMDD` (sem hífen) e é o dia do nome do arquivo;
- o código da usina (PDP) vem com espaços à direita, e o nome também;
- 48 patamares por dia (de meia em meia hora), a chave é
  (dia, patamar, código) — nenhuma repetida em nenhum arquivo;
- nenhum valor negativo ou vazio, e o dicionário do ONS os proíbe.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_programacao_previsao import OnsProgramacaoPrevisao, ProgramacaoPrevisao
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_programacao_previsao_2026_10_02.csv"
DIA = Janela.de_texto("2026-10-02", "2026-10-02")


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_arquivo_diario.criar_sessao", lambda: None)
    conector = OnsProgramacaoPrevisao()
    monkeypatch.setattr(
        conector, "_abrir", lambda dia: FIXTURE.read_bytes().splitlines() if dia == date(2026, 10, 2) else None
    )
    return conector


def _registros(conector):
    return [ProgramacaoPrevisao.model_validate(conector.transformar(b)) for b in conector.extrair(DIA)]


def test_data_sem_hifen_e_codigo_sem_espaco(conector):
    r = next(r for r in _registros(conector) if r.codigo_usina_pdp == "MMRAL")

    assert r.data_referencia == date(2026, 10, 2)
    assert r.patamar == 20
    assert r.nome_usina == "CJFVRIOALTO"
    assert (r.previsao_mw, r.programado_mw) == (Decimal("136.00"), Decimal("109.00"))


def test_nome_com_acento_utf8(conector):
    assert "Eólio - Elétrica de Palmas" in {r.nome_usina for r in _registros(conector)}


def test_valor_negativo_e_rejeitado():
    base = {"data_referencia": "2026-10-02", "patamar": "1", "codigo_usina_pdp": "X", "nome_usina": "X"}
    with pytest.raises(ValidationError):
        ProgramacaoPrevisao.model_validate(base | {"previsao_mw": "-1", "programado_mw": "0"})


def test_ingere_as_dez_linhas(conector):
    execucao = conector.ingerir(DIA)
    assert (execucao.linhas_extraidas, execucao.linhas_invalidas) == (10, 0)
