"""Descoberta de conectores por rótulo."""

import pytest
from src.core.registry import listar, obter


def test_conector_do_projeto_esta_registrado():
    assert "bcb_cambio_ptax" in listar()


def test_rotulo_desconhecido_lista_os_disponiveis():
    with pytest.raises(KeyError, match="bcb_cambio_ptax"):
        obter("fonte_inexistente")
