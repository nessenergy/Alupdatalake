"""Janela e Execucao — a base do reprocessamento e do log operacional."""

from datetime import date

import pytest
from src.core.execucao import Execucao, Janela


def test_janela_invertida_e_rejeitada():
    with pytest.raises(ValueError, match="invertida"):
        Janela(date(2026, 2, 1), date(2026, 1, 1))


def test_janela_de_um_dia_tem_um_dia():
    janela = Janela(date(2026, 1, 10), date(2026, 1, 10))
    assert janela.dias() == [date(2026, 1, 10)]


def test_particionar_cobre_a_janela_inteira_sem_sobreposicao():
    janela = Janela.de_texto("2026-01-01", "2026-03-31")
    pedacos = janela.particionar(30)

    assert pedacos[0].inicio == janela.inicio
    assert pedacos[-1].fim == janela.fim
    assert sum(len(p.dias()) for p in pedacos) == len(janela.dias())
    for anterior, seguinte in zip(pedacos, pedacos[1:], strict=False):
        assert (seguinte.inicio - anterior.fim).days == 1


def test_particionar_maior_que_a_janela_devolve_uma_so():
    janela = Janela.de_texto("2026-01-01", "2026-01-05")
    assert len(janela.particionar(90)) == 1


def test_ultimos_dias_termina_na_data_pedida():
    janela = Janela.ultimos_dias(7, ate=date(2026, 1, 31))
    assert janela.fim == date(2026, 1, 31)
    assert len(janela.dias()) == 7


def test_execucao_encerrada_com_erro_vira_status_erro():
    execucao = Execucao(fonte="bcb", entidade="cambio_ptax", janela=Janela.de_texto("2026-01-01", "2026-01-02"))
    assert execucao.status == "EM_EXECUCAO"

    execucao.encerrar(erro="HTTPError: 503")

    assert execucao.status == "ERRO"
    assert execucao.to_row()["erro"] == "HTTPError: 503"
    assert execucao.duracao_segundos >= 0
