"""A sessão HTTP compartilhada: sem timeout, uma fonte lenta pendura o job."""

import pytest
import requests
from src.core.http import criar_sessao, get_json


def test_sessao_tem_retry_configurado_para_5xx_e_429():
    retry = criar_sessao().get_adapter("https://exemplo").max_retries

    assert retry.total == 3
    assert 429 in retry.status_forcelist
    assert 503 in retry.status_forcelist


def test_retry_so_em_metodos_idempotentes_por_padrao():
    permitidos = criar_sessao().get_adapter("https://exemplo").max_retries.allowed_methods

    assert "GET" in permitidos
    assert "POST" not in permitidos  # repetir POST duplicaria efeito


def test_post_pode_ser_habilitado_para_consulta_idempotente():
    permitidos = criar_sessao(retry_post=True).get_adapter("https://exemplo").max_retries.allowed_methods

    assert "POST" in permitidos


def test_get_json_sempre_passa_timeout(monkeypatch):
    capturado = {}

    class RespostaFalsa:
        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": True}

    class SessaoFalsa:
        def get(self, url, params=None, timeout=None):
            capturado.update(url=url, params=params, timeout=timeout)
            return RespostaFalsa()

    assert get_json(SessaoFalsa(), "https://exemplo/api", params={"a": 1}) == {"ok": True}
    assert capturado["timeout"] == 30.0
    assert capturado["params"] == {"a": 1}


def test_get_json_propaga_erro_http():
    class SessaoQueFalha:
        def get(self, *_a, **_k):
            resposta = requests.Response()
            resposta.status_code = 500
            return resposta

    with pytest.raises(requests.HTTPError):
        get_json(SessaoQueFalha(), "https://exemplo/api")
