"""Leitura progressiva e integridade do raw sem rede."""

import gzip
import io
import json
from contextlib import closing

import pytest
from google.cloud import storage
from src.core.storage import ler_raw

URI = "gs://lake-raw/teste/medicao/dt=2026-01-01/origem.json.gz"
LIMIT = 1024 * 1024


def _simular_download(monkeypatch, source, generation=42):
    opened = {}
    if isinstance(source, bytes):
        source = io.BytesIO(source)

    class Blob:
        def reload(self):
            self.generation = generation

        def download_as_bytes(self):
            raise AssertionError("download integral proibido")

        def open(self, mode, **kwargs):
            assert mode == "rb"
            opened.update(kwargs)
            return source

    class Client:
        def __init__(self, **kwargs):
            pass

        def bucket(self, name):
            return self

        def blob(self, name):
            return Blob()

    monkeypatch.setattr(storage, "Client", Client)
    return source, opened


def test_le_jsonl_e_fixa_geracao(monkeypatch):
    records = [{"id": "1"}, {"id": "2"}]
    source, opened = _simular_download(
        monkeypatch, gzip.compress(b"\n" + b"\n".join(json.dumps(r).encode() for r in records))
    )
    assert list(ler_raw(URI)) == records
    assert source.closed
    assert opened == {"chunk_size": LIMIT, "raw_download": True, "if_generation_match": 42}


@pytest.mark.parametrize(
    "body, message",
    [
        (b"nao-e-gzip", "gzip inválido"),
        (gzip.compress(b"{}")[:-3], "gzip inválido"),
        (gzip.compress(b"{}")[:-8] + b"\x00" * 8, "gzip inválido"),
        (gzip.compress(b"[1,2]"), "não é um objeto"),
        (gzip.compress(b"{invalido}"), "JSON inválido"),
        (gzip.compress(b'{"x":"\xff"}'), "UTF-8 inválido"),
        (gzip.compress(b" " * (LIMIT + 1)), "limite"),
    ],
)
def test_rejeita_formato_invalido_e_fecha(monkeypatch, body, message):
    source, _ = _simular_download(monkeypatch, body)
    with pytest.raises(ValueError, match=message):
        list(ler_raw(URI))
    assert source.closed


def test_sem_geracao_nao_abre(monkeypatch):
    _, opened = _simular_download(monkeypatch, gzip.compress(b"{}"), generation=None)
    with pytest.raises(ValueError, match="geração"):
        list(ler_raw(URI))
    assert not opened


def test_incremental_e_fecha_em_erro_do_consumidor(monkeypatch):
    source, _ = _simular_download(monkeypatch, gzip.compress(b"{}\ninvalido\n"))
    with pytest.raises(RuntimeError), closing(ler_raw(URI)) as records:
        assert next(records) == {}
        assert not source.closed
        raise RuntimeError("falha na carga")
    assert source.closed


def test_arquivo_maior_que_100_mib_em_linhas_pequenas(monkeypatch, tmp_path):
    path = tmp_path / "raw.gz"
    line = json.dumps({"valor": "x" * 1024}).encode() + b"\n"
    count = 101 * 1024
    with gzip.open(path, "wb") as stream:
        for _ in range(count):
            stream.write(line)
    source, _ = _simular_download(monkeypatch, path.open("rb"))
    assert sum(1 for _ in ler_raw(URI)) == count
    assert source.closed


def test_falha_de_rede_nao_vira_erro_de_formato(monkeypatch):
    class Broken(io.BytesIO):
        def read(self, *args):
            raise OSError("rede indisponível")

    source, _ = _simular_download(monkeypatch, Broken())
    with pytest.raises(OSError, match="rede indisponível"):
        list(ler_raw(URI))
    assert source.closed


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


@pytest.mark.parametrize("streaming", [False, True])
def test_escritores_respeitam_o_mesmo_limite_do_leitor(monkeypatch, streaming):
    from src.core.execucao import Execucao, Janela
    from src.core.storage import abrir_raw, gravar_raw

    monkeypatch.setenv("DRY_RUN", "false")
    captured = []

    class Destination(io.BytesIO):
        def close(self):
            captured.append(self.getvalue())
            super().close()

    class Blob:
        def open(self, mode, **kwargs):
            return Destination()

        def upload_from_string(self, body, **kwargs):
            captured.append(body)

    class Client:
        def __init__(self, **kwargs):
            pass

        def bucket(self, name):
            return self

        def blob(self, name):
            return Blob()

    monkeypatch.setattr(storage, "Client", Client)
    execution = Execucao(fonte="teste", entidade="medicao", janela=Janela.de_texto("2026-01-01", "2026-01-01"))
    # O limite inclui o delimitador de linha e conta bytes UTF-8, não caracteres.
    base = len((json.dumps({"value": ""}) + "\n").encode())
    row = {"value": "é" * ((LIMIT - base) // 2)}

    def write(record):
        if streaming:
            with abrir_raw(execution) as raw:
                raw.escrever(record)
        else:
            gravar_raw(execution, [record])

    write(row)
    _simular_download(monkeypatch, captured[-1])
    assert list(ler_raw(URI)) == [row]
    monkeypatch.setattr(storage, "Client", Client)
    with pytest.raises(ValueError, match="limite"):
        write({"value": row["value"] + "é"})
