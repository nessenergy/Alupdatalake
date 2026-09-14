"""Conector TempoOK — boletins diários em PDF (Onda 2, exige token).

Fonte: `https://storage.tempook.com/tokstorage/download_post/`
Documentação: **não existe publicada.** O contrato abaixo foi derivado do
exemplo de consulta fornecido pela Alup em 14/09/2026.

Escrito **sem token**, como o `hubspot_negocios` foi escrito sem credencial e
pelo mesmo motivo: a credencial é pendência da Alup (A7). O que não pôde ser
verificado está no fim de `docs/dicionario-dados/tempook_boletins.md`.

O que esta fonte tem de diferente das outras doze (ADR 019):

- **não é API de dados, é endpoint de download.** Não há listagem nem filtro:
  pede-se um caminho, recebe-se um arquivo;
- **o caminho é derivável da data** — é isso que torna a fonte ingerível por
  janela (regra 3) sem endpoint de listagem;
- **o Bronze guarda o catálogo, não o conteúdo.** O PDF vai inteiro para o
  bucket raw e o Bronze aponta para ele. Extrair os números do boletim é
  escopo futuro, e depende de A4 para saber quais números importam.

O exemplo fornecido usa `verify=False`. **Este conector não reproduz isso**: o
token viaja na conexão, e desligar a verificação de certificado a expõe a
interceptação (ADR 019, item 3).
"""

from __future__ import annotations

import hashlib
import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

from src.core.conector import Conector
from src.core.config import get_settings
from src.core.http import criar_sessao
from src.core.registry import registrar
from src.core.secrets import ler_secret
from src.core.storage import gravar_arquivo

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

URL = "https://storage.tempook.com/tokstorage/download_post/"

# Template do caminho na origem, derivado do único exemplo conhecido:
#   Comercializadora/Boletins/Diario/2022-03/boletim_TOK_2022-03-31.pdf
PASTA = "Comercializadora/Boletins/Diario"
NOME = "boletim_TOK_{dia}.pdf"

# Assinatura de PDF. Endpoint de download que devolve 200 com página de erro é
# comum; sem esta conferência o lake arquivaria HTML de erro como se fosse
# boletim (ADR 019, item 4).
ASSINATURA_PDF = b"%PDF-"

CONTENT_TYPE = "application/pdf"


def caminho_do_dia(dia: date) -> str:
    """Caminho do boletim daquele dia na origem."""
    return f"{PASTA}/{dia:%Y-%m}/{NOME.format(dia=dia.isoformat())}"


class Boletim(BaseModel):
    """Um boletim diário arquivado: onde está, de quando é, e o que é.

    Catálogo, não conteúdo. O `sha256` é o que permite saber depois que a
    origem republicou um boletim corrigido sem ter de reabrir o PDF.
    """

    data_referencia: date
    caminho_origem: str
    nome_arquivo: str
    uri_arquivo: str | None = Field(default=None, description="gs://… ; nulo em dry-run")
    tamanho_bytes: int = Field(gt=0)
    sha256: str
    content_type: str

    @field_validator("sha256")
    @classmethod
    def _hash_valido(cls, valor: str) -> str:
        if len(valor) != 64 or not all(c in "0123456789abcdef" for c in valor):
            raise ValueError(f"sha256 malformado: {valor!r}")
        return valor


@registrar
class TempookBoletins(Conector):
    """Um boletim por dia da janela. Dia sem boletim é aviso, não falha."""

    fonte = "tempook"
    entidade = "boletins"
    schema = Boletim
    schema_versao = "1"
    max_dias_por_requisicao = None  # um GET por dia; a janela não precisa ser partida

    def __init__(self) -> None:
        # O endpoint é POST, mas apenas lê: repetir depois de 429/5xx não cria
        # nem altera nada na origem.
        self._sessao = criar_sessao(retry_post=True)

    def _baixar(self, caminho: str) -> bytes | None:
        """Conteúdo do boletim, ou `None` quando a origem não devolve um PDF."""
        cfg = get_settings()
        resposta = self._sessao.post(
            URL,
            data={"t": ler_secret(self.fonte, "api-token"), "p": caminho},
            timeout=cfg.http_timeout,
            allow_redirects=True,
        )
        if resposta.status_code == 404:
            return None
        resposta.raise_for_status()

        conteudo = resposta.content
        if not conteudo.startswith(ASSINATURA_PDF):
            # 200 com corpo que não é PDF: dia sem boletim, ou página de erro.
            # Nos dois casos não é dado, e arquivar seria pior que pular.
            logger.warning(
                "TempoOK: resposta de %s não é PDF (%d bytes, content-type %s); tratado como ausente",
                caminho,
                len(conteudo),
                resposta.headers.get("Content-Type"),
            )
            return None
        return conteudo

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        dia = janela.inicio
        while dia <= janela.fim:
            caminho = caminho_do_dia(dia)
            conteudo = self._baixar(caminho)
            if conteudo is None:
                logger.info("TempoOK: sem boletim em %s", dia.isoformat())
                dia += timedelta(days=1)
                continue

            nome = caminho.rsplit("/", 1)[-1]
            uri = gravar_arquivo(self._execucao, nome, conteudo, CONTENT_TYPE) if self._execucao else None

            yield {
                "data_referencia": dia.isoformat(),
                "caminho_origem": caminho,
                "nome_arquivo": nome,
                "uri_arquivo": uri,
                "tamanho_bytes": len(conteudo),
                "sha256": hashlib.sha256(conteudo).hexdigest(),
                "content_type": CONTENT_TYPE,
            }
            dia += timedelta(days=1)
