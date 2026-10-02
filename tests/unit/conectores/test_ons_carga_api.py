"""Conectores ONS de carga por API (programada e verificada): sem rede, com fixture de resposta real."""

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_carga_api import AREAS_CARGA
from src.conectores.ons_carga_programada import CargaProgramada, OnsCargaProgramada
from src.conectores.ons_carga_verificada import CargaVerificada, OnsCargaVerificada
from src.core.execucao import Janela
from src.core.registry import listar

FIXTURES = Path(__file__).parents[2] / "fixtures"


class _Resposta:
    def __init__(self, corpo, status=200):
        self._corpo = corpo
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._corpo


class _Sessao:
    """Devolve as linhas da fixture da área pedida e guarda as chamadas."""

    def __init__(self, fixture):
        self.fixture = fixture
        self.chamadas = []

    def get(self, url, params=None, timeout=None):
        self.chamadas.append((url, params, timeout))
        return _Resposta(self.fixture.get(params["cod_areacarga"], []))


def _conector(monkeypatch, classe, arquivo):
    monkeypatch.setattr("src.conectores.ons_carga_api.criar_sessao", lambda: None)
    conector = classe()
    conector._sessao = _Sessao(json.loads((FIXTURES / arquivo).read_text(encoding="utf-8")))
    return conector


@pytest.fixture
def verificada(monkeypatch):
    return _conector(monkeypatch, OnsCargaVerificada, "ons_carga_verificada_2026.json")


@pytest.fixture
def programada(monkeypatch):
    return _conector(monkeypatch, OnsCargaProgramada, "ons_carga_programada_2026.json")


JANELA = Janela.de_texto("2026-09-20", "2026-09-30")


def test_a_api_e_publica_e_cada_area_e_uma_chamada_com_a_janela_inclusiva(verificada):
    list(verificada.extrair(JANELA))

    chamadas = verificada._sessao.chamadas
    assert [p["cod_areacarga"] for _, p, _ in chamadas] == list(AREAS_CARGA)
    assert all(url == "https://apicarga.ons.org.br/prd/cargaverificada" for url, _, _ in chamadas)
    assert all(p["dat_inicio"] == "2026-09-20" and p["dat_fim"] == "2026-09-30" for _, p, _ in chamadas)
    assert all(set(p) == {"dat_inicio", "dat_fim", "cod_areacarga"} for _, p, _ in chamadas)  # sem token


def test_programada_usa_o_outro_endpoint(programada):
    list(programada.extrair(JANELA))
    assert programada._sessao.chamadas[0][0] == "https://apicarga.ons.org.br/prd/cargaprogramada"


def test_janela_respeita_o_limite_de_tres_meses_da_api():
    assert OnsCargaVerificada.max_dias_por_requisicao <= 31
    assert OnsCargaProgramada.max_dias_por_requisicao <= 31


def test_catalogo_de_areas_e_o_do_swagger_do_ons():
    assert len(AREAS_CARGA) == 33
    assert {"SECO", "S", "NE", "N", "RS", "PESE"} <= set(AREAS_CARGA)
    assert "SIN" not in AREAS_CARGA  # a API devolve zero para SIN e SE; não estão no catálogo oficial
    assert "SE" not in AREAS_CARGA


def test_verificada_traduz_as_colunas(verificada):
    brutos = [b for b in verificada.extrair(JANELA) if b["cod_areacarga"] == "N"]
    primeiro = CargaVerificada.model_validate(verificada.transformar(brutos[0]))

    assert primeiro.area_carga == "N"
    assert primeiro.data_referencia == date(2026, 9, 20)
    assert primeiro.instante_utc == datetime(2026, 9, 20, 3, 30, tzinfo=UTC)
    assert primeiro.carga_global_mwmed == Decimal("10038.321")
    assert primeiro.carga_global_sem_mmgd_mwmed == Decimal("10036.081")
    assert primeiro.carga_mmgd_mwmed == Decimal("2.24")
    assert primeiro.carga_supervisionada_mwmed == Decimal("9966.96")
    assert primeiro.carga_nao_supervisionada_mwmed == Decimal("69.1208")
    assert primeiro.consistencia_mwmed == 0
    assert primeiro.atualizado_em == datetime(2026, 9, 30, 3, 21, 44, 320000, tzinfo=UTC)


def test_programada_traduz_as_colunas(programada):
    bruto = next(b for b in programada.extrair(JANELA) if b["cod_areacarga"] == "SECO")
    registro = CargaProgramada.model_validate(programada.transformar(bruto))

    assert registro.area_carga == "SECO"
    assert registro.carga_programada_mwmed == Decimal("40086.77")


def test_ultima_meia_hora_do_dia_cai_no_dia_seguinte_em_utc_mas_mantem_a_data_de_referencia(programada):
    bruto = next(b for b in programada.extrair(JANELA) if b["cod_areacarga"] == "NE")
    registro = CargaProgramada.model_validate(programada.transformar(bruto))

    assert registro.data_referencia == date(2026, 9, 30)
    assert registro.instante_utc == datetime(2026, 10, 1, 3, 0, tzinfo=UTC)


def test_valor_negativo_e_aceito_porque_a_origem_publica(verificada):
    """Carga líquida e supervisionada ficam negativas onde a MMGD passa da carga (MT, 07/09/2026)."""
    bruto = next(b for b in verificada.extrair(JANELA) if b["cod_areacarga"] == "MT")
    registro = CargaVerificada.model_validate(verificada.transformar(bruto))

    assert registro.carga_global_sem_mmgd_mwmed == Decimal("-238.70529")
    assert registro.carga_supervisionada_mwmed == Decimal("-703.7008")


def test_notacao_cientifica_da_origem_e_lida(verificada):
    bruto = {
        "cod_areacarga": "PI",
        "din_atualizacao": "2025-06-26T08:37:42.709Z",
        "dat_referencia": "2025-03-01",
        "din_referenciautc": "2025-03-01T03:30:00.000Z",
        "val_cargaglobal": 1,
        "val_cargaglobalcons": 1,
        "val_cargaglobalsmmgd": 1,
        "val_cargasupervisionada": 1,
        "val_carganaosupervisionada": 0,
        "val_cargammgd": 0,
        "val_consistencia": -6.1035156e-05,
    }
    registro = CargaVerificada.model_validate(verificada.transformar(bruto))
    assert registro.consistencia_mwmed < 0


def test_area_fora_do_catalogo_e_rejeitada(programada):
    bruto = {
        "cod_areacarga": "SIN",
        "dat_referencia": "2026-09-20",
        "din_referenciautc": "2026-09-20T03:30:00.000Z",
        "val_cargaglobalprogramada": 0,
    }
    with pytest.raises(ValidationError):
        CargaProgramada.model_validate(programada.transformar(bruto))


def test_resposta_que_nao_e_lista_falha_com_erro_claro(verificada):
    verificada._sessao.fixture = {"N": {"message": "Forbidden"}}
    with pytest.raises(RuntimeError, match="resposta inesperada"):
        list(verificada.extrair(JANELA))


def test_http_de_erro_nao_vira_dado_vazio(verificada):
    verificada._sessao.get = lambda *a, **k: _Resposta({}, status=403)
    with pytest.raises(RuntimeError, match="HTTP 403"):
        list(verificada.extrair(JANELA))


def test_rotulos_nao_colidem_com_ons_carga():
    rotulos = listar()
    assert {"ons_carga", "ons_carga_programada", "ons_carga_verificada"} <= set(rotulos)
