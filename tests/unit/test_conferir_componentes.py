"""Verificação reproduzível dos 7 componentes por fonte (cláusula 2ª): o que a auditoria roda para conferir."""

import pytest
from scripts import conferir_componentes as cc
from src.core.registry import carregar_conectores, listar

# Montado em tempo de execução: o literal neste arquivo contaria como "teste que cita a fonte".
INEXISTENTE = "fonte_" + "inexistente_" + "zzz"


def test_todo_conector_registrado_tem_os_componentes_de_arquivo():
    """Bronze, Silver, Gold, teste, agendamento e dicionário existem para cada rótulo do registro."""
    carregar_conectores()
    faltas = cc.conferir(listar())

    assert faltas == {}, faltas


def test_um_rotulo_sem_nada_acusa_os_seis_componentes_que_dependem_de_arquivo():
    faltas = cc.conferir([INEXISTENTE])

    assert set(faltas[INEXISTENTE]) == {"bronze", "silver", "gold", "teste", "agendamento", "dicionario"}


def test_codigo_de_saida_e_zero_sem_faltas_e_um_com_faltas(capsys: pytest.CaptureFixture[str]):
    assert cc.principal(["--rotulos", "bcb_cambio_ptax"]) == 0
    assert cc.principal(["--rotulos", INEXISTENTE]) == 1
    saida = capsys.readouterr().out
    assert INEXISTENTE in saida
