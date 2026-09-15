"""Gravação do dado bruto no Cloud Storage, antes de qualquer parsing.

Se o parser tiver bug, reprocessa-se do GCS sem bater de novo na fonte —
algumas APIs do projeto têm rate limit ou retenção curta.
"""

from __future__ import annotations

import gzip
import io
import json
import logging
import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from src.core.config import get_settings

if TYPE_CHECKING:
    from src.core.execucao import Execucao

logger = logging.getLogger(__name__)

_CAMINHO_RAW = re.compile(
    r"^(?P<fonte>[a-z0-9_-]+)/(?P<entidade>[a-z0-9_-]+)/dt=(?P<data>\d{4}-\d{2}-\d{2})/"
    r"(?P<ingestao_id>[A-Za-z0-9_-]+)\.json\.gz$"
)
MAX_RAW_BYTES = 100 * 1024 * 1024


@dataclass(frozen=True)
class RawInfo:
    bucket: str
    caminho: str
    fonte: str
    entidade: str
    data_referencia: date
    ingestao_id: str


def identificar_raw(uri: str) -> RawInfo:
    """Valida o layout canônico e identifica a origem de um objeto raw."""
    parsed = urlparse(uri)
    caminho = parsed.path.lstrip("/")
    match = _CAMINHO_RAW.fullmatch(caminho)
    if parsed.scheme != "gs" or not parsed.netloc or not match:
        raise ValueError("URI de raw inválida; use gs://bucket/fonte/entidade/dt=AAAA-MM-DD/id.json.gz")
    grupos = match.groupdict()
    try:
        data_referencia = date.fromisoformat(grupos["data"])
    except ValueError as exc:
        raise ValueError("URI de raw contém data inválida") from exc
    return RawInfo(
        bucket=parsed.netloc,
        caminho=caminho,
        fonte=grupos["fonte"],
        entidade=grupos["entidade"],
        data_referencia=data_referencia,
        ingestao_id=grupos["ingestao_id"],
    )


def ler_raw(uri: str) -> list[dict[str, Any]]:
    """Lê JSONL gzip do GCS para replay, sem consultar novamente a fonte."""
    info = identificar_raw(uri)
    from google.cloud import storage

    cliente = storage.Client(project=get_settings().gcp_project_id)
    blob = cliente.bucket(info.bucket).blob(info.caminho)

    # O tamanho é conferido pelos metadados, antes de baixar: medir depois do
    # download não protege de nada — o estouro de memória já teria acontecido.
    blob.reload()
    if blob.size is None:
        raise ValueError("raw sem tamanho declarado no GCS")
    if blob.size > MAX_RAW_BYTES:
        raise ValueError(f"raw excede o limite comprimido de {MAX_RAW_BYTES} bytes")

    corpo_comprimido = blob.download_as_bytes()
    # Leitura com teto em vez de `gzip.decompress`: gzip descompacta na razão de
    # ~1000:1, então 100 MB comprimidos cabem na memória mas viram dezenas de GB.
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(corpo_comprimido)) as fluxo:
            corpo = fluxo.read(MAX_RAW_BYTES + 1)
    except (OSError, EOFError) as exc:
        raise ValueError("raw gzip inválido") from exc
    if len(corpo) > MAX_RAW_BYTES:
        raise ValueError(f"raw excede o limite descomprimido de {MAX_RAW_BYTES} bytes")

    registros: list[dict[str, Any]] = []
    for numero, linha in enumerate(corpo.decode("utf-8").splitlines(), start=1):
        if not linha.strip():
            continue
        registro = json.loads(linha)
        if not isinstance(registro, dict):
            raise ValueError(f"linha {numero} do raw não é um objeto JSON")
        registros.append(registro)
    return registros


def caminho_raw(execucao: Execucao) -> str:
    """Objeto de destino no bucket raw, particionado por data de referência."""
    dt = execucao.janela.inicio.isoformat()
    return f"{execucao.fonte}/{execucao.entidade}/dt={dt}/{execucao.ingestao_id}.json.gz"


_NOME_ARQUIVO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,200}$")


def caminho_arquivo(execucao: Execucao, nome: str) -> str:
    """Objeto de um raw que não é JSONL, ao lado do raw da mesma execução.

    Fonte que entrega arquivo em vez de registros — o boletim em PDF do TempoOK
    (ADR 019) — guarda o arquivo aqui e um ponteiro no Bronze.
    """
    if not _NOME_ARQUIVO.fullmatch(nome) or ".." in nome:
        raise ValueError(f"nome de arquivo inválido: {nome!r}")
    dt = execucao.janela.inicio.isoformat()
    return f"{execucao.fonte}/{execucao.entidade}/dt={dt}/{execucao.ingestao_id}/{nome}"


def gravar_arquivo(execucao: Execucao, nome: str, conteudo: bytes, content_type: str) -> str | None:
    """Grava um arquivo da origem como veio, sem parsing. Devolve o URI gs://."""
    cfg = get_settings()
    caminho = caminho_arquivo(execucao, nome)
    uri = f"gs://{cfg.bucket_raw}/{caminho}"

    if cfg.dry_run:
        logger.info("dry-run: %d bytes não gravados em %s", len(conteudo), uri)
        return None

    from google.cloud import storage  # import tardio: teste unitário não precisa do SDK

    blob = storage.Client(project=cfg.gcp_project_id).bucket(cfg.bucket_raw).blob(caminho)
    blob.upload_from_string(conteudo, content_type=content_type)
    logger.info("arquivo gravado: %s (%d bytes)", uri, len(conteudo))
    return uri


def gravar_raw(execucao: Execucao, registros: list[dict[str, Any]]) -> str | None:
    """Grava os registros brutos como JSONL comprimido. Devolve o URI gs://."""
    cfg = get_settings()
    caminho = caminho_raw(execucao)
    uri = f"gs://{cfg.bucket_raw}/{caminho}"

    if cfg.dry_run:
        logger.info("dry-run: %d registros não gravados em %s", len(registros), uri)
        return None

    from google.cloud import storage  # import tardio: teste unitário não precisa do SDK

    corpo = "\n".join(json.dumps(r, ensure_ascii=False, default=str) for r in registros)
    blob = storage.Client(project=cfg.gcp_project_id).bucket(cfg.bucket_raw).blob(caminho)
    blob.content_encoding = "gzip"
    blob.upload_from_string(gzip.compress(corpo.encode("utf-8")), content_type="application/json")
    logger.info("raw gravado: %s (%d registros)", uri, len(registros))
    return uri


class _RawEmFluxo:
    """Escreve o raw registro a registro, sem montar o arquivo inteiro em memória.

    O `gravar_raw` acima serve a quem já tem a lista na mão — o replay e as
    fontes pequenas. Para a geração horária da CCEE, que são ~3 milhões de
    registros por mês, montar a string inteira e só então comprimir custa
    alguns gigabytes de pico: a versão em fluxo comprime conforme escreve.

    O objeto final é idêntico ao do `gravar_raw`: um JSONL comprimido, no
    mesmo caminho canônico, um por execução. O replay continua funcionando
    sem saber qual dos dois o gravou.
    """

    def __init__(self, execucao: Execucao) -> None:
        cfg = get_settings()
        self._caminho = caminho_raw(execucao)
        self.uri = f"gs://{cfg.bucket_raw}/{self._caminho}"
        self._dry_run = cfg.dry_run
        self._registros = 0
        self._destino: Any = None
        self._gzip: Any = None

    def __enter__(self) -> _RawEmFluxo:
        if self._dry_run:
            return self
        from google.cloud import storage  # import tardio: teste unitário não precisa do SDK

        cfg = get_settings()
        blob = storage.Client(project=cfg.gcp_project_id).bucket(cfg.bucket_raw).blob(self._caminho)
        blob.content_encoding = "gzip"
        self._destino = blob.open("wb", content_type="application/json")
        self._gzip = gzip.GzipFile(fileobj=self._destino, mode="wb")
        return self

    def escrever(self, registro: dict[str, Any]) -> None:
        self._registros += 1
        if self._dry_run:
            return
        linha = json.dumps(registro, ensure_ascii=False, default=str) + "\n"
        self._gzip.write(linha.encode("utf-8"))

    def __exit__(self, exc_tipo: Any, exc: Any, tb: Any) -> bool:
        if self._dry_run:
            logger.info("dry-run: %d registros não gravados em %s", self._registros, self.uri)
            return False
        # Fecha nos dois caminhos: com erro, o objeto parcial fica no GCS e a
        # execução vai para ERRO — é o que permite ver até onde a origem
        # respondeu antes de falhar.
        try:
            self._gzip.close()
        finally:
            self._destino.close()
        logger.info("raw gravado: %s (%d registros)", self.uri, self._registros)
        return False


def abrir_raw(execucao: Execucao) -> _RawEmFluxo:
    """Gravador de raw em fluxo, para usar como gerenciador de contexto."""
    return _RawEmFluxo(execucao)
