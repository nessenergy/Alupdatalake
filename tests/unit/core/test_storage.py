"""Leitura do raw arquivado, sem acesso real ao Cloud Storage."""

from __future__ import annotations

import gzip
import json

import pytest
from google.cloud import storage
from src.core.storage import MAX_RAW_BYTES, ler_raw

URI = "gs://lake-raw/teste/medicao/dt=2026-01-01/origem.json.gz"


def _simular_download(
    monkeypatch: pytest.MonkeyPatch,
    corpo: bytes,
    *,
    tamanho: int | None = -1,
) -> dict[str, int]:
    """Instala um GCS falso. Devolve um contador de downloads efetivamente feitos.

    `tamanho` é o que os metadados declaram; `-1` significa "o tamanho real do
    corpo". Passar um valor maior simula um objeto grande sem alocá-lo.
    """
    chamadas = {"download": 0}
    declarado = len(corpo) if tamanho == -1 else tamanho

    class BlobFalso:
        size: int | None = declarado

        def reload(self) -> None: ...

        def download_as_bytes(self) -> bytes:
            chamadas["download"] += 1
            return corpo

    class BucketFalso:
        def blob(self, _caminho: str) -> BlobFalso:
            return BlobFalso()

    class ClienteFalso:
        def __init__(self, **_kwargs) -> None: ...

        def bucket(self, _nome: str) -> BucketFalso:
            return BucketFalso()

    monkeypatch.setattr(storage, "Client", ClienteFalso)
    return chamadas


def test_ler_raw_descompacta_jsonl(monkeypatch: pytest.MonkeyPatch) -> None:
    registros = [{"id": "1", "valor": 10}, {"id": "2", "valor": 20}]
    jsonl = "\n".join(json.dumps(registro) for registro in registros).encode()
    _simular_download(monkeypatch, gzip.compress(jsonl))

    assert ler_raw(URI) == registros


def test_ler_raw_recusa_gzip_corrompido(monkeypatch: pytest.MonkeyPatch) -> None:
    _simular_download(monkeypatch, b"nao-e-gzip")

    with pytest.raises(ValueError, match="gzip inválido"):
        ler_raw(URI)


def test_ler_raw_recusa_linha_que_nao_e_objeto(monkeypatch: pytest.MonkeyPatch) -> None:
    _simular_download(monkeypatch, gzip.compress(b"[1, 2, 3]"))

    with pytest.raises(ValueError, match="não é um objeto"):
        ler_raw(URI)


def test_ler_raw_recusa_objeto_grande_sem_baixar(monkeypatch: pytest.MonkeyPatch) -> None:
    """A guarda de tamanho só serve se disparar antes do download.

    Conferir `len()` depois de `download_as_bytes()` não protege de nada: o
    estouro de memória que a guarda existe para evitar já teria acontecido.
    """
    chamadas = _simular_download(monkeypatch, gzip.compress(b"{}"), tamanho=MAX_RAW_BYTES + 1)

    with pytest.raises(ValueError, match="limite comprimido"):
        ler_raw(URI)

    assert chamadas["download"] == 0, "o objeto não pode ser baixado para só então ser recusado"


def test_ler_raw_recusa_bomba_de_descompressao(monkeypatch: pytest.MonkeyPatch) -> None:
    # Poucos KB comprimidos que viram mais que o teto ao descompactar.
    bomba = gzip.compress(b"\0" * (MAX_RAW_BYTES + 1))
    assert len(bomba) < MAX_RAW_BYTES, "a bomba precisa passar pela guarda do comprimido"
    _simular_download(monkeypatch, bomba)

    with pytest.raises(ValueError, match="limite descomprimido"):
        ler_raw(URI)


def test_ler_raw_recusa_objeto_sem_tamanho_declarado(monkeypatch: pytest.MonkeyPatch) -> None:
    _simular_download(monkeypatch, gzip.compress(b"{}"), tamanho=None)

    with pytest.raises(ValueError, match="sem tamanho declarado"):
        ler_raw(URI)


# ------------------------------------------------------- raw binário (ADR 019)
# O boletim do TempoOK é um PDF: o raw dessa fonte não cabe no JSONL, e o Bronze
# guarda um ponteiro em vez do conteúdo.


def test_caminho_de_arquivo_fica_ao_lado_do_raw_jsonl_com_a_extensao_da_origem():
    from src.core.execucao import Execucao, Janela
    from src.core.storage import caminho_arquivo

    execucao = Execucao(fonte="tempook", entidade="boletins", janela=Janela.de_texto("2026-03-31", "2026-03-31"))
    caminho = caminho_arquivo(execucao, "boletim_TOK_2026-03-31.pdf")

    assert caminho.startswith("tempook/boletins/dt=2026-03-31/")
    assert caminho.endswith("/boletim_TOK_2026-03-31.pdf")
    # o id da execução separa duas ingestões do mesmo dia, como no raw JSONL
    assert execucao.ingestao_id in caminho


def test_nome_de_arquivo_com_travessia_de_diretorio_e_recusado():
    """O nome vem da origem; `..` no caminho escreveria fora da partição."""
    from src.core.execucao import Execucao, Janela
    from src.core.storage import caminho_arquivo

    execucao = Execucao(fonte="tempook", entidade="boletins", janela=Janela.de_texto("2026-03-31", "2026-03-31"))

    for nome in ("../escapou.pdf", "sub/dir.pdf", "", "."):
        with pytest.raises(ValueError, match="nome de arquivo"):
            caminho_arquivo(execucao, nome)


def test_dry_run_nao_grava_arquivo_e_devolve_none(monkeypatch):
    from src.core.config import get_settings
    from src.core.execucao import Execucao, Janela
    from src.core.storage import gravar_arquivo

    get_settings.cache_clear()
    monkeypatch.setenv("DRY_RUN", "true")
    execucao = Execucao(fonte="tempook", entidade="boletins", janela=Janela.de_texto("2026-03-31", "2026-03-31"))

    assert gravar_arquivo(execucao, "b.pdf", b"%PDF-1.4", "application/pdf") is None

    get_settings.cache_clear()
