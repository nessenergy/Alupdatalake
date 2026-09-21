"""Base dos conectores do TempoOK que arquivam um arquivo por dia (Onda 2, exige token).

Fonte: `https://storage.tempook.com/tokstorage/download_post/`
Documentação: **não existe publicada.** O contrato vem dos exemplos de consulta
fornecidos pela Alup — o boletim em 14/09/2026 e o ENA-PREVS em 18/09/2026.

Dois produtos usam o mesmo endpoint e a mesma mecânica (ADR 019):

- **não é API de dados, é endpoint de download.** Não há listagem nem filtro:
  pede-se um caminho, recebe-se um arquivo;
- **o caminho é derivável da data** — é isso que torna a fonte ingerível por
  janela (regra 3) sem endpoint de listagem;
- **o Bronze guarda o catálogo, não o conteúdo.** O arquivo vai inteiro para o
  bucket raw e o Bronze aponta para ele. Extrair os números é escopo futuro, e
  depende de a Alup dizer quais números importam.

Por isso a mecânica vive aqui e cada produto é uma subclasse que declara só o
caminho, a assinatura do arquivo e o tipo de conteúdo — o mesmo desenho do
`CceeCsvCkan` e do `OnsRestricaoCoff`.

Os exemplos fornecidos usam `verify=False`. **Nenhum conector deste módulo
reproduz isso**: o token viaja na conexão, e desligar a verificação de
certificado a expõe a interceptação (ADR 019, item 3). Conferido em 21/09 contra
a origem real: a verificação passa sem ajuste.
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
from src.core.secrets import ler_secret
from src.core.storage import gravar_arquivo

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

URL = "https://storage.tempook.com/tokstorage/download_post/"


class ArquivoTempook(BaseModel):
    """Um arquivo diário arquivado: onde está, de quando é, e o que é.

    Catálogo, não conteúdo. O `sha256` é o que permite saber depois que a
    origem republicou um arquivo corrigido sem ter de reabri-lo.
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


class TempookArquivos(Conector):
    """Um arquivo por dia da janela. Dia sem arquivo é aviso, não falha.

    A subclasse declara `entidade`, `schema`, `assinatura`, `content_type` e
    implementa `caminho_do_dia`. Se o produto tiver mais de um caminho por dia,
    `caminhos_do_dia` é o gancho.
    """

    fonte = "tempook"
    schema_versao = "1"
    max_dias_por_requisicao = None  # um POST por dia; a janela não precisa ser partida

    assinatura: bytes  # primeiros bytes que o arquivo tem de ter
    content_type: str

    def __init__(self) -> None:
        # O endpoint é POST, mas apenas lê: repetir depois de 429/5xx não cria
        # nem altera nada na origem.
        self._sessao = criar_sessao(retry_post=True)

    def caminho_do_dia(self, dia: date) -> str:
        raise NotImplementedError

    def caminhos_do_dia(self, dia: date) -> list[str]:
        return [self.caminho_do_dia(dia)]

    def _registro(self, dia: date, caminho: str, nome: str, conteudo: bytes, uri: str | None) -> dict[str, Any]:
        """O registro do catálogo; a subclasse acrescenta o que for só dela."""
        return {
            "data_referencia": dia.isoformat(),
            "caminho_origem": caminho,
            "nome_arquivo": nome,
            "uri_arquivo": uri,
            "tamanho_bytes": len(conteudo),
            "sha256": hashlib.sha256(conteudo).hexdigest(),
            "content_type": self.content_type,
        }

    def _baixar(self, caminho: str) -> bytes | None:
        """Conteúdo do arquivo, ou `None` quando a origem não devolve o que se espera."""
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
        if not conteudo.startswith(self.assinatura):
            # 200 com corpo que não é o arquivo: dia sem dado, ou página de erro.
            # Nos dois casos não é dado, e arquivar seria pior que pular.
            logger.warning(
                "TempoOK: %s sem a assinatura esperada (%d bytes, content-type %s); tratado como ausente",
                caminho,
                len(conteudo),
                resposta.headers.get("Content-Type"),
            )
            return None
        return conteudo

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        dia = janela.inicio
        while dia <= janela.fim:
            for caminho in self.caminhos_do_dia(dia):
                conteudo = self._baixar(caminho)
                if conteudo is None:
                    logger.info("TempoOK %s: sem arquivo em %s (%s)", self.entidade, dia.isoformat(), caminho)
                    continue

                nome = caminho.rsplit("/", 1)[-1]
                uri = gravar_arquivo(self._execucao, nome, conteudo, self.content_type) if self._execucao else None
                yield self._registro(dia, caminho, nome, conteudo, uri)
            dia += timedelta(days=1)
