"""Leitor de pasta do Google Drive — o canal que leva as planilhas da Onda 4 ao motor S2.

A Alupar compartilha uma pasta com a conta de serviço do job; este módulo lista e baixa o que há nela. Só leitura
(`drive.readonly`) e com a identidade do próprio job (credenciais padrão do ambiente): não há credencial guardada, nem
no Secret Manager, nem no repositório. O que chega aqui é arquivo de uma pessoa, então nome e id são tratados como
entrada não confiável.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Any

import google.auth
import google.auth.transport.requests

from src.core.config import get_settings

if TYPE_CHECKING:
    from pathlib import Path

    import requests

API = "https://www.googleapis.com/drive/v3"
ESCOPO_LEITURA = "https://www.googleapis.com/auth/drive.readonly"
GOOGLE_SHEETS = "application/vnd.google-apps.spreadsheet"
EXPORTACAO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# O id vai dentro da consulta `q`: só o alfabeto que o Drive usa, para não abrir a consulta a injeção.
_ID_DRIVE = re.compile(r"[A-Za-z0-9_-]+")


class DriveInvalidoError(ValueError):
    """Entrada que não pode chegar à API do Drive."""


@dataclass(frozen=True)
class ArquivoDrive:
    id: str
    nome: str
    mime_type: str
    modificado_em: datetime


def token_de_leitura() -> str:
    """Token de acesso da conta de serviço do job, só com o escopo de leitura."""
    credenciais, _ = google.auth.default(scopes=[ESCOPO_LEITURA])
    credenciais.refresh(google.auth.transport.requests.Request())
    return str(credenciais.token)


def _cabecalho(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def listar_pasta(sessao: requests.Session, pasta_id: str, token: str) -> list[ArquivoDrive]:
    """Arquivos (fora da lixeira) de uma pasta, com paginação; inclui pastas de unidade compartilhada."""
    if not _ID_DRIVE.fullmatch(pasta_id):
        raise DriveInvalidoError("id da pasta inválido: o Drive usa só letras, números, hífen e sublinhado")
    arquivos: list[ArquivoDrive] = []
    pagina: str | None = None
    while True:
        params: dict[str, Any] = {
            "q": f"'{pasta_id}' in parents and trashed = false",
            "fields": "nextPageToken, files(id, name, mimeType, modifiedTime)",
            "pageSize": "100",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        if pagina:
            params["pageToken"] = pagina
        resposta = sessao.get(
            f"{API}/files", params=params, headers=_cabecalho(token), timeout=get_settings().http_timeout
        )
        resposta.raise_for_status()
        corpo = resposta.json()
        arquivos += [
            ArquivoDrive(
                id=item["id"],
                nome=item["name"],
                mime_type=item["mimeType"],
                modificado_em=datetime.fromisoformat(item["modifiedTime"].replace("Z", "+00:00")),
            )
            for item in corpo.get("files", [])
        ]
        pagina = corpo.get("nextPageToken")
        if not pagina:
            return arquivos


def _nome_seguro(nome: str) -> str:
    """Só o último componente do nome, nos dois estilos de separador; vazio ou `..` não é nome de arquivo."""
    base = PurePosixPath(PureWindowsPath(nome).name).name
    return base if base not in {"", ".", ".."} else "arquivo"


def baixar(sessao: requests.Session, arquivo: ArquivoDrive, destino: Path, token: str) -> Path:
    """Baixa o arquivo para `destino`; Google Sheets nativo vira xlsx. O arquivo só nasce se a API responder."""
    timeout = get_settings().http_timeout
    if arquivo.mime_type == GOOGLE_SHEETS:
        resposta = sessao.get(
            f"{API}/files/{arquivo.id}/export",
            params={"mimeType": EXPORTACAO_XLSX},
            headers=_cabecalho(token),
            timeout=timeout,
        )
        nome = f"{_nome_seguro(arquivo.nome)}.xlsx"
    else:
        resposta = sessao.get(
            f"{API}/files/{arquivo.id}",
            params={"alt": "media", "supportsAllDrives": "true"},
            headers=_cabecalho(token),
            timeout=timeout,
        )
        nome = _nome_seguro(arquivo.nome)
    resposta.raise_for_status()
    caminho = destino / nome
    caminho.write_bytes(resposta.content)
    return caminho
