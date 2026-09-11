"""Conector Hubspot: transformação, paginação e o filtro de janela.

Sem rede e sem token — o teste que fala com a API real vive em
`tests/integration/` e é pulado enquanto a credencial não chega.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.hubspot_negocios import PROPRIEDADES, HubspotNegocios, Negocio, _epoch_ms
from src.core.execucao import Janela

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "hubspot_negocios.json").read_text(encoding="utf-8"))


@pytest.fixture
def conector(monkeypatch: pytest.MonkeyPatch) -> HubspotNegocios:
    monkeypatch.setattr("src.conectores.hubspot_negocios.ler_secret", lambda *_: "valor-simulado")
    return HubspotNegocios()


def test_transformar_negocio_completo(conector: HubspotNegocios) -> None:
    linha = Negocio.model_validate(conector.transformar(FIXTURE["results"][0]))
    assert linha.negocio_id == "1001"
    assert linha.nome == "PPA Cliente Exemplo 2027"
    assert linha.valor == Decimal("1250000.00")
    assert linha.data_fechamento == date(2026, 11, 30)


def test_dono_do_negocio_nao_e_tratado(conector: HubspotNegocios) -> None:
    """RIPD, item g: nenhuma Gold usa o dono do negócio, então ele não é lido.

    A fixture ainda traz `hubspot_owner_id`: mesmo que a API o devolva, o
    conector não o repassa.
    """
    assert "hubspot_owner_id" not in PROPRIEDADES
    assert "proprietario_id" not in conector.transformar(FIXTURE["results"][0])
    assert "proprietario_id" not in Negocio.model_fields


def test_campos_vazios_viram_nulo_nao_string_vazia(conector: HubspotNegocios) -> None:
    linha = Negocio.model_validate(conector.transformar(FIXTURE["results"][1]))
    assert linha.valor is None
    assert linha.data_fechamento is None
    assert linha.nome == "(sem nome)"  # dealname nulo não pode quebrar a carga


def test_estagio_vazio_e_registro_invalido(conector: HubspotNegocios) -> None:
    with pytest.raises(ValueError, match="obrigatório"):
        Negocio.model_validate(conector.transformar(FIXTURE["results"][2]))


def test_paginacao_segue_o_cursor_e_para_sem_ele(conector: HubspotNegocios, monkeypatch: pytest.MonkeyPatch) -> None:
    paginas = [
        {"results": [FIXTURE["results"][0]], "paging": {"next": {"after": "abc"}}},
        {"results": [FIXTURE["results"][1]], "paging": {}},
    ]
    corpos: list[dict] = []

    class RespostaFalsa:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def raise_for_status(self) -> None: ...

        def json(self) -> dict:
            return self._payload

    def post_falso(_url: str, *, json: dict, headers: dict, timeout: float) -> RespostaFalsa:  # noqa: A002
        corpos.append(dict(json))
        assert headers["Authorization"] == "Bearer valor-simulado"
        assert timeout > 0
        return RespostaFalsa(paginas[len(corpos) - 1])

    monkeypatch.setattr(conector._sessao, "post", post_falso)
    registros = list(conector.extrair(Janela.de_texto("2026-08-20", "2026-08-22")))

    assert [r["id"] for r in registros] == ["1001", "1002"]
    assert "after" not in corpos[0]
    assert corpos[1]["after"] == "abc"


def test_janela_vira_intervalo_em_milissegundos() -> None:
    inicio = _epoch_ms(date(2026, 8, 20))
    fim = _epoch_ms(date(2026, 8, 20), fim_do_dia=True)
    assert inicio == "1787184000000"  # 2026-08-20T00:00:00Z
    assert int(fim) - int(inicio) == 86_399_999  # o dia inteiro, sem invadir o seguinte


def test_hubspot_habilita_retry_do_post(monkeypatch: pytest.MonkeyPatch) -> None:
    opcoes: dict = {}

    def sessao_falsa(**kwargs):
        opcoes.update(kwargs)
        return object()

    monkeypatch.setattr("src.conectores.hubspot_negocios.criar_sessao", sessao_falsa)

    HubspotNegocios()

    assert opcoes == {"retry_post": True}
