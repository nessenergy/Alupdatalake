"""Retry exercitado contra um servidor local, sem depender da internet."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from src.core.http import criar_sessao, get_json


@pytest.fixture
def servidor_instavel():
    chamadas = {"GET": 0, "POST": 0}

    class Handler(BaseHTTPRequestHandler):
        def _responder(self, metodo: str) -> None:
            chamadas[metodo] += 1
            status = 503 if chamadas[metodo] == 1 else 200
            corpo = json.dumps({"ok": status == 200}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_GET(self) -> None:  # noqa: N802 — assinatura do BaseHTTPRequestHandler
            self._responder("GET")

        def do_POST(self) -> None:  # noqa: N802 — assinatura do BaseHTTPRequestHandler
            self._responder("POST")

        def log_message(self, _format: str, *_args) -> None:
            return

    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{servidor.server_port}", chamadas
    finally:
        servidor.shutdown()
        servidor.server_close()
        thread.join(timeout=2)


def test_get_recupera_de_503(servidor_instavel) -> None:
    url, chamadas = servidor_instavel

    assert get_json(criar_sessao(), url) == {"ok": True}
    assert chamadas["GET"] == 2


def test_post_de_consulta_recupera_de_503_quando_habilitado(servidor_instavel) -> None:
    url, chamadas = servidor_instavel

    resposta = criar_sessao(retry_post=True).post(url, json={"consulta": True}, timeout=3)

    resposta.raise_for_status()
    assert chamadas["POST"] == 2
