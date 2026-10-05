"""O runner separa "a origem não respondeu" de erro nosso, só pelo texto de `_execucoes.erro`."""

import pytest
import requests
from src.core.conector import PREFIXO_ORIGEM_INDISPONIVEL, descrever_erro


def _http_error(status: int) -> requests.HTTPError:
    resposta = requests.Response()
    resposta.status_code = status
    return requests.HTTPError(f"{status} Server Error", response=resposta)


@pytest.mark.parametrize(
    "exc",
    [
        requests.ConnectionError("dns"),
        requests.ConnectTimeout("timeout ao conectar"),
        requests.ReadTimeout("timeout ao ler"),
        ConnectionError("conexão derrubada"),
        TimeoutError("estourou"),
        _http_error(503),
    ],
)
def test_origem_que_nao_respondeu_ganha_o_prefixo(exc):
    assert descrever_erro(exc).startswith(PREFIXO_ORIGEM_INDISPONIVEL)
    assert type(exc).__name__ in descrever_erro(exc)


@pytest.mark.parametrize(
    "exc", [ValueError("layout novo"), _http_error(404), KeyError("coluna"), RuntimeError("nosso")]
)
def test_erro_nosso_ou_de_cliente_nao_ganha_o_prefixo(exc):
    assert not descrever_erro(exc).startswith(PREFIXO_ORIGEM_INDISPONIVEL)


def test_erro_embrulhado_por_outra_excecao_ainda_e_de_origem():
    try:
        try:
            raise requests.ConnectionError("dns")
        except requests.ConnectionError as causa:
            raise RuntimeError("falha ao baixar") from causa
    except RuntimeError as exc:
        assert descrever_erro(exc).startswith(PREFIXO_ORIGEM_INDISPONIVEL)


def test_texto_de_erro_continua_passando_pelo_sanitizador():
    exc = requests.ConnectionError("falhou em https://usuario:segredo@host/x")
    assert "segredo" not in descrever_erro(exc)
