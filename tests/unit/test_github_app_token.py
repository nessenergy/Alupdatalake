"""Token de instalação de GitHub App: JWT RS256 e troca por token de acesso. Sem rede."""

from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from scripts.github_app_token import jwt_do_app, token_de_instalacao


@pytest.fixture(scope="module")
def chave() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _pem(chave: rsa.RSAPrivateKey) -> bytes:
    return chave.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )


def _decodificar(parte: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(parte + "=" * (-len(parte) % 4)))


def test_jwt_tem_a_forma_e_a_assinatura_que_o_github_exige(chave) -> None:
    jwt = jwt_do_app("Iv-teste", _pem(chave), agora=1_000_000)

    cabecalho, corpo, assinatura = jwt.split(".")
    assert _decodificar(cabecalho) == {"alg": "RS256", "typ": "JWT"}
    assert _decodificar(corpo) == {"iat": 999_940, "exp": 1_000_540, "iss": "Iv-teste"}
    bruta = base64.urlsafe_b64decode(assinatura + "=" * (-len(assinatura) % 4))
    chave.public_key().verify(bruta, f"{cabecalho}.{corpo}".encode(), padding.PKCS1v15(), hashes.SHA256())


class _Resposta:
    def __init__(self, corpo: dict) -> None:
        self._corpo = corpo

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._corpo


class _Sessao:
    def __init__(self) -> None:
        self.chamadas: list[tuple[str, str, dict]] = []

    def get(self, url: str, **kw) -> _Resposta:
        self.chamadas.append(("GET", url, kw))
        return _Resposta({"id": 42})

    def post(self, url: str, **kw) -> _Resposta:
        self.chamadas.append(("POST", url, kw))
        return _Resposta({"token": "ghs_abc"})


def test_troca_o_jwt_por_token_com_so_as_permissoes_pedidas(chave) -> None:
    sessao = _Sessao()

    obtido = token_de_instalacao("Iv-teste", _pem(chave), "nessenergy", {"contents": "read"}, sessao=sessao)

    assert obtido == "ghs_abc"
    (_, url_get, _), (_, url_post, kw_post) = sessao.chamadas
    assert url_get == "https://api.github.com/orgs/nessenergy/installation"
    assert url_post == "https://api.github.com/app/installations/42/access_tokens"
    assert kw_post["json"] == {"permissions": {"contents": "read"}}
    assert kw_post["headers"]["Authorization"].startswith("Bearer ")


def test_permissao_sem_igual_da_mensagem_clara_e_sai_com_2(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.github_app_token import main

    with pytest.raises(SystemExit) as saida:
        main(["--dono", "x", "--permissao", "contents"])
    assert saida.value.code == 2
    assert "nome=nivel" in capsys.readouterr().err
