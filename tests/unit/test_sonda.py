"""Sondas de rede: dizem se um endereço público responde do ambiente onde o job roda. Sem rede."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from src.cli import main
from src.core.sonda import PREVIEW, SONDAS, ResultadoSonda, gravar_resultado, sondar

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "sondar-rede.yml"


class RespostaFalsa:
    def __init__(self, status: int, corpo: bytes, tipo: str = "text/xml") -> None:
        self.status_code = status
        self.content = corpo
        self.headers = {"Content-Type": tipo}


class SessaoFalsa:
    def __init__(self, respostas: dict[str, object]) -> None:
        self.respostas = respostas
        self.chamadas: list[str] = []

    def get(self, url: str, timeout: float):  # noqa: ARG002
        self.chamadas.append(url)
        resposta = self.respostas[url]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def _todas(status: int = 200) -> SessaoFalsa:
    return SessaoFalsa({url: RespostaFalsa(status, b"<ok/>") for urls in SONDAS.values() for url in urls})


def test_sonda_registra_status_tamanho_tipo_e_amostra() -> None:
    [primeiro, *_] = sondar("cptec", _todas(403))

    assert isinstance(primeiro, ResultadoSonda)
    assert (primeiro.status, primeiro.bytes, primeiro.tipo, primeiro.amostra) == (403, 5, "text/xml", "<ok/>")
    assert primeiro.erro is None


def test_endereco_que_levanta_vira_erro_e_nao_derruba_os_outros() -> None:
    urls = SONDAS["cptec"]
    sessao = SessaoFalsa({urls[0]: ConnectionError("dns"), urls[1]: RespostaFalsa(200, b"ok")})

    resultados = sondar("cptec", sessao)

    assert [r.status for r in resultados] == [None, 200]
    assert "ConnectionError" in (resultados[0].erro or "")
    assert sessao.chamadas == list(urls)


def test_amostra_e_truncada_e_sem_quebra_de_linha() -> None:
    url = SONDAS["open_meteo"][0]
    sessao = SessaoFalsa({url: RespostaFalsa(200, ("a\n" * 500).encode())})

    [resultado] = sondar("open_meteo", sessao)

    assert len(resultado.amostra) <= PREVIEW
    assert "\n" not in resultado.amostra


def test_so_conhece_as_sondas_da_lista() -> None:
    with pytest.raises(KeyError):
        sondar("qualquer_coisa", _todas())


def test_enderecos_sao_constantes_sem_marcador_de_substituicao() -> None:
    for urls in SONDAS.values():
        for url in urls:
            assert url.startswith(("http://", "https://"))
            assert "{" not in url
            assert " " not in url


def test_cli_imprime_uma_linha_json_por_endereco_e_devolve_zero(monkeypatch, capsys) -> None:
    monkeypatch.setattr("src.core.sonda.criar_sessao", lambda: _todas(403))
    monkeypatch.setattr("src.cli.gravar_resultado", lambda nome, resultados: None)

    codigo = main(["sondar", "cptec"])

    saida = [json.loads(linha) for linha in capsys.readouterr().out.splitlines() if linha.startswith("{")]
    assert codigo == 0  # a sonda nunca falha o job: nada de alerta de ingestão por diagnóstico
    assert [linha["status"] for linha in saida if "status" in linha] == [403] * len(SONDAS["cptec"])
    assert {linha["sonda"] for linha in saida} == {"cptec"}


def test_cli_recusa_sonda_fora_da_lista() -> None:
    with pytest.raises(SystemExit):
        main(["sondar", "http://exemplo.com"])


def test_workflow_so_oferece_as_sondas_da_lista_e_nao_interpola_entrada_em_run() -> None:
    fluxo = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    entradas = fluxo[True]["workflow_dispatch"]["inputs"]  # PyYAML lê `on` como True

    assert set(entradas) == {"environment", "sonda"}
    assert set(entradas["sonda"]["options"]) == set(SONDAS)
    for passo in fluxo["jobs"]["sondar"]["steps"]:
        assert "${{ inputs." not in passo.get("run", "")


def test_gravar_resultado_falha_em_silencio_sem_credencial(monkeypatch) -> None:
    def explode(*args, **kwargs):
        raise RuntimeError("sem credencial")

    monkeypatch.setattr("google.cloud.storage.Client", explode)

    assert gravar_resultado("cptec", []) is None
