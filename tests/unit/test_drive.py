"""Leitor de pasta do Google Drive (canal das planilhas da Onda 4) — sem rede e sem credencial.

A Alupar ainda não criou a pasta (resposta de 27/10/2026: sai quando as planilhas estiverem prontas), então o contrato
com a API do Drive v3 está fixado aqui com respostas falsas. O que estes testes protegem:

- só leitura, pelo escopo `drive.readonly` e pela identidade do próprio job, sem credencial guardada;
- o id da pasta entra na consulta `q`, e por isso é validado antes (id malformado nunca chega à API);
- o nome do arquivo vem de fora e vira caminho em disco: sem escapar do diretório de destino;
- Google Sheets nativo é exportado para xlsx, que é o que o motor de planilha lê.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pytest
from src.core.drive import (
    ESCOPO_LEITURA,
    EXPORTACAO_XLSX,
    ArquivoDrive,
    DriveInvalidoError,
    baixar,
    listar_pasta,
)
from src.core.drive import (
    testar_drive as provar_drive,
)

if TYPE_CHECKING:
    from pathlib import Path

PASTA = "1AbC_dEf-GhI"
TOKEN = "token-de-teste"  # noqa: S105 - valor fictício de teste


class _Resposta:
    def __init__(self, corpo: Any = None, conteudo: bytes = b"", status: int = 200) -> None:
        self._corpo = corpo
        self.content = conteudo
        self.status_code = status

    def json(self) -> Any:
        return self._corpo

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AssertionError(f"status {self.status_code}")


class _Sessao:
    def __init__(self, respostas: list[_Resposta]) -> None:
        self._respostas = list(respostas)
        self.chamadas: list[dict[str, Any]] = []

    def get(self, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None, **k: Any):
        self.chamadas.append({"url": url, "params": params or {}, "headers": headers or {}, **k})
        return self._respostas.pop(0)


def _arquivo(id_: str, nome: str, mime: str = "text/csv") -> dict[str, str]:
    return {"id": id_, "name": nome, "mimeType": mime, "modifiedTime": "2026-10-27T13:00:00.000Z"}


def test_listar_pasta_devolve_os_arquivos_e_segue_a_paginacao() -> None:
    sessao = _Sessao(
        [
            _Resposta({"files": [_arquivo("a1", "prc.csv")], "nextPageToken": "p2"}),
            _Resposta({"files": [_arquivo("a2", "outra.csv")]}),
        ]
    )

    arquivos = listar_pasta(sessao, PASTA, TOKEN)

    assert [a.nome for a in arquivos] == ["prc.csv", "outra.csv"]
    assert arquivos[0] == ArquivoDrive("a1", "prc.csv", "text/csv", datetime(2026, 10, 27, 13, 0, tzinfo=UTC))
    assert sessao.chamadas[1]["params"]["pageToken"] == "p2"


def test_listar_pasta_so_le_a_pasta_pedida_e_ignora_lixeira() -> None:
    sessao = _Sessao([_Resposta({"files": []})])

    listar_pasta(sessao, PASTA, TOKEN)

    chamada = sessao.chamadas[0]
    assert f"'{PASTA}' in parents" in chamada["params"]["q"]
    assert "trashed = false" in chamada["params"]["q"]
    assert chamada["params"]["supportsAllDrives"] == "true"
    assert chamada["headers"]["Authorization"] == f"Bearer {TOKEN}"
    assert chamada["timeout"] is not None


@pytest.mark.parametrize("pasta", ["", "x' or '1'='1", "a b", "../etc", "pasta;drop"])
def test_id_de_pasta_malformado_nunca_chega_a_api(pasta: str) -> None:
    sessao = _Sessao([])

    with pytest.raises(DriveInvalidoError, match="id da pasta"):
        listar_pasta(sessao, pasta, TOKEN)

    assert sessao.chamadas == []


def test_baixar_arquivo_comum_grava_o_conteudo(tmp_path: Path) -> None:
    sessao = _Sessao([_Resposta(conteudo=b"a;b\n1;2\n")])

    caminho = baixar(sessao, ArquivoDrive("a1", "prc.csv", "text/csv", datetime.now(UTC)), tmp_path, TOKEN)

    assert caminho == tmp_path / "prc.csv"
    assert caminho.read_bytes() == b"a;b\n1;2\n"
    assert sessao.chamadas[0]["url"].endswith("/files/a1")
    assert sessao.chamadas[0]["params"]["alt"] == "media"


def test_google_sheets_e_exportado_para_xlsx(tmp_path: Path) -> None:
    sessao = _Sessao([_Resposta(conteudo=b"PK-xlsx")])
    planilha = ArquivoDrive("s1", "PRC outubro", "application/vnd.google-apps.spreadsheet", datetime.now(UTC))

    caminho = baixar(sessao, planilha, tmp_path, TOKEN)

    assert caminho.name == "PRC outubro.xlsx"
    assert sessao.chamadas[0]["url"].endswith("/files/s1/export")
    assert sessao.chamadas[0]["params"]["mimeType"] == EXPORTACAO_XLSX


@pytest.mark.parametrize("nome", ["../fora.csv", "..\\fora.csv", "/etc/passwd", "a/../../b.csv", "", ".."])
def test_nome_de_arquivo_nao_escapa_do_diretorio_de_destino(tmp_path: Path, nome: str) -> None:
    sessao = _Sessao([_Resposta(conteudo=b"x")])

    caminho = baixar(sessao, ArquivoDrive("a1", nome, "text/csv", datetime.now(UTC)), tmp_path, TOKEN)

    assert caminho.parent == tmp_path
    assert caminho.resolve().is_relative_to(tmp_path.resolve())


def test_o_escopo_e_so_de_leitura() -> None:
    assert ESCOPO_LEITURA == "https://www.googleapis.com/auth/drive.readonly"


def test_erro_da_api_nao_vira_arquivo_vazio(tmp_path: Path) -> None:
    sessao = _Sessao([_Resposta(status=404)])

    with pytest.raises(AssertionError):
        baixar(sessao, ArquivoDrive("a1", "prc.csv", "text/csv", datetime.now(UTC)), tmp_path, TOKEN)

    assert not (tmp_path / "prc.csv").exists()


class _SessaoQueFalha:
    def __init__(self, status: int) -> None:
        self.status = status

    def get(self, *args: Any, **kwargs: Any):
        import requests

        resposta = requests.Response()
        resposta.status_code = self.status
        raise requests.HTTPError(response=resposta)


def test_testar_drive_lista_nomes_sem_baixar_nada() -> None:
    sessao = _Sessao([_Resposta({"files": [_arquivo("a1", "GSF_template.xlsx"), _arquivo("a2", "outra.csv")]})])

    ok, mensagem = provar_drive(PASTA, sessao=sessao, token=TOKEN)

    assert ok
    assert "2 arquivo(s)" in mensagem
    assert "GSF_template.xlsx" in mensagem
    assert len(sessao.chamadas) == 1  # só a listagem; nenhum download


def test_testar_drive_sem_id_configurado_diz_qual_variavel_falta(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.core.drive.get_settings", lambda: type("S", (), {"drive_pasta_id": "", "http_timeout": 5})()
    )

    ok, mensagem = provar_drive(sessao=_Sessao([]), token=TOKEN)

    assert not ok
    assert "DRIVE_PASTA_ID" in mensagem


def test_testar_drive_pasta_vazia_nao_e_erro_mas_avisa() -> None:
    ok, mensagem = provar_drive(PASTA, sessao=_Sessao([_Resposta({"files": []})]), token=TOKEN)

    assert ok
    assert "0 arquivo(s)" in mensagem


@pytest.mark.parametrize(
    ("status", "dica"),
    [(404, "compartilhada"), (403, "API do Drive")],
)
def test_testar_drive_traduz_o_erro_da_api_na_causa_provavel(status: int, dica: str) -> None:
    ok, mensagem = provar_drive(PASTA, sessao=_SessaoQueFalha(status), token=TOKEN)

    assert not ok
    assert str(status) in mensagem
    assert dica in mensagem


def test_testar_drive_nome_com_quebra_de_linha_nao_forja_linha_de_log() -> None:
    sessao = _Sessao([_Resposta({"files": [_arquivo("a1", "x.csv\nok: falso")]})])

    _, mensagem = provar_drive(PASTA, sessao=sessao, token=TOKEN)

    assert mensagem.count("\n") == 1  # cabeçalho + uma linha de arquivo
