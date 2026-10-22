"""Token de instalação de um GitHub App, para o CI ler o repositório privado, as issues e os PRs.

A chave privada vem do Secret Manager pelo Cloud Build (`availableSecrets`), na variável de ambiente `CHAVE_APP`; o
`client_id` vem de `CLIENT_ID_APP`. O token vale uma hora e sai só em stdout, nunca em log nem em arquivo.

    python -m scripts.github_app_token --dono nessenergy --permissao contents=read --permissao issues=read
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import time

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

API = "https://api.github.com"
TIMEOUT = 30


def _b64(dados: bytes) -> bytes:
    return base64.urlsafe_b64encode(dados).rstrip(b"=")


def jwt_do_app(client_id: str, chave_pem: bytes, agora: int | None = None) -> str:
    agora = int(time.time()) if agora is None else agora
    cabecalho = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    corpo = _b64(json.dumps({"iat": agora - 60, "exp": agora + 540, "iss": client_id}).encode())
    chave = serialization.load_pem_private_key(chave_pem, password=None)
    assinatura = chave.sign(cabecalho + b"." + corpo, padding.PKCS1v15(), hashes.SHA256())  # type: ignore[union-attr]
    return (cabecalho + b"." + corpo + b"." + _b64(assinatura)).decode()


def token_de_instalacao(
    client_id: str,
    chave_pem: bytes,
    dono: str,
    permissoes: dict[str, str],
    sessao: requests.Session | None = None,
) -> str:
    sessao = sessao or requests.Session()
    cabecalhos = {
        "Authorization": f"Bearer {jwt_do_app(client_id, chave_pem)}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    instalacao = sessao.get(f"{API}/orgs/{dono}/installation", headers=cabecalhos, timeout=TIMEOUT)
    instalacao.raise_for_status()
    resposta = sessao.post(
        f"{API}/app/installations/{instalacao.json()['id']}/access_tokens",
        headers=cabecalhos,
        json={"permissions": permissoes},
        timeout=TIMEOUT,
    )
    resposta.raise_for_status()
    return resposta.json()["token"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dono", required=True)
    parser.add_argument("--permissao", action="append", required=True, help="nome=nivel, ex.: contents=read")
    args = parser.parse_args(argv)
    permissoes = dict(item.split("=", 1) for item in args.permissao)
    print(token_de_instalacao(os.environ["CLIENT_ID_APP"], os.environ["CHAVE_APP"].encode(), args.dono, permissoes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
