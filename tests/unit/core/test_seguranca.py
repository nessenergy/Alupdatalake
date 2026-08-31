"""Sanitização central: dado sensível não pode chegar a log nem controle."""

from __future__ import annotations

import uuid

from src.core.seguranca import sanitizar


def test_sanitizar_remove_credenciais_de_dsn_e_bearer() -> None:
    marcador = uuid.uuid4().hex
    mensagem = f"falha em mysql://usuario:{marcador}@db/base Authorization: Bearer {marcador}"

    saida = sanitizar(mensagem)

    assert marcador not in saida
    assert "[REDACTED]" in saida


def test_sanitizar_remove_parametro_sensivel_e_limita_tamanho() -> None:
    marcador = uuid.uuid4().hex
    mensagem = f"https://exemplo/api?api_token={marcador}&pagina=1 " + "x" * 5000

    saida = sanitizar(mensagem, limite=300)

    assert marcador not in saida
    assert len(saida) <= 300
