"""Conector CCEE/consumo horário por perfil de agente (item 26) — gzip mensal, uma linha por carga e hora, sem rede.

O que estes testes protegem:

- o recurso é mensal (`_AAAAMM`) e gzip, e a janela escolhe quantos meses baixar;
- `PERIODO_COMERCIALIZACAO` (1..744) vira `data_referencia` e `data_hora`, e período
  fora do mês é linha inválida (contada), nunca queda da execução;
- medida vazia é nula, não zero;
- a guarda de recarga: a Bronze é append-only e cada mês pesa ~11 GiB, então mês
  já carregado (mesma `versao_publicacao`) não é relido.
"""

from __future__ import annotations

import gzip
import io
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from src.conectores.ccee_consumo_horario_perfil_agente import (
    CceeConsumoHorarioPerfilAgente,
    ConsumoHorarioPerfilAgente,
)
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_consumo_horario_perfil_agente_202607.csv"
MODULO = "src.conectores.ccee_consumo_horario_perfil_agente"


def _pacote(*sufixos: str, last_modified: str | None = "2026-09-01T10:00:00") -> dict:
    return {
        "resources": [
            {
                "name": f"consumo_horario_perfil_agente_{s}",
                "url": "u",
                "format": "GZIP",
                "last_modified": last_modified,
            }
            for s in sufixos
        ]
    }


def _settings(dry_run=False, reler=False):
    return lambda: SimpleNamespace(
        dry_run=dry_run,
        reler_meses_carregados=reler,
        gcp_project_id="p",
        bq_dataset_bronze="bronze",
        tabela_bronze=lambda fonte, entidade: f"p.bronze.{fonte}_{entidade}",
    )


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    monkeypatch.setattr(f"{MODULO}.get_settings", _settings(dry_run=True))  # sem guarda: não toca o BigQuery
    conector = CceeConsumoHorarioPerfilAgente()
    monkeypatch.setattr(conector, "_pacote", lambda: _pacote("202607"))
    abertos: list[str] = []
    monkeypatch.setattr(
        conector, "_abrir", lambda s: abertos.append(s) or io.BytesIO(gzip.compress(FIXTURE.read_bytes()))
    )
    conector.abertos = abertos
    return conector


def _validos(conector, de="2026-07-01", ate="2026-07-31"):
    return [
        ConsumoHorarioPerfilAgente.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto(de, ate))
        if b["PERIODO_COMERCIALIZACAO"] != "745"
    ]


def _bruto(**mudancas) -> dict:
    linhas = FIXTURE.read_text(encoding="utf-8").splitlines()
    bruto = dict(zip(linhas[0].split(";"), linhas[1].split(";"), strict=True))
    return bruto | {"_versao_publicacao": "2026-09-01", "_sufixo": "202607"} | mudancas


def test_recurso_e_mensal_sem_credencial():
    assert CceeConsumoHorarioPerfilAgente.recurso_por == "mes"
    assert CceeConsumoHorarioPerfilAgente.dataset == "consumo_horario_perfil_agente"


def test_extrai_so_o_mes_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))

    assert len(registros) == 4  # a linha de 202608 fica de fora
    assert conector.abertos == ["202607"]


def test_transformar_deriva_data_hora_do_periodo(conector):
    primeiro, segundo, *_ = _validos(conector)

    assert primeiro.data_referencia == date(2026, 7, 1)
    assert primeiro.data_hora == datetime(2026, 7, 1, 0, 0)
    assert segundo.periodo_comercializacao == 25
    assert segundo.data_referencia == date(2026, 7, 2)  # período 25 = hora 0 do dia 2
    assert segundo.data_hora == datetime(2026, 7, 2, 0, 0)


def test_transformar_tipa_as_colunas(conector):
    r = _validos(conector)[0]

    assert r.codigo_carga == 9001
    assert r.nome_carga == "CARGA FICTICIA ALFA"
    assert r.data_migracao == date(2024, 3, 15)
    assert r.classe_perfil_agente == "Consumidor Livre"
    assert r.cnpj_carga == "00000000000191"
    assert r.submercado == "SE"  # SUDESTE por extenso vira sigla
    assert r.codigo_perfil_agente_distribuidora == 7001
    assert r.capacidade_carga == Decimal("1.5")
    assert r.consumo_carga_acl == Decimal("0.812")
    assert r.consumo_carga_ponto_conexao == Decimal("0.81")
    assert r.periodo_apuracao_ccee == "2026-07"
    assert r.versao_publicacao == date(2026, 9, 1)


def test_medida_vazia_e_nula_e_zero_continua_zero(conector):
    beta = _validos(conector)[2]

    assert beta.consumo_carga_acl == Decimal("0")
    assert beta.consumo_carga_ajustado is None
    assert beta.consumo_carga_ponto_conexao is None
    assert beta.capacidade_carga is None
    assert beta.codigo_perfil_agente_distribuidora is None
    assert beta.data_migracao is None


def test_periodo_fora_do_mes_e_linha_invalida_sem_derrubar_a_execucao(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-07-01", "2026-07-31"))

    assert execucao.linhas_extraidas == 4
    assert execucao.linhas_invalidas == 1  # período 745; julho tem 744 horas
    assert execucao.status == "SUCESSO"


def test_periodo_nao_numerico_e_invalido(conector):
    with pytest.raises(ValueError, match="periodo_comercializacao"):
        ConsumoHorarioPerfilAgente.model_validate(conector.transformar(_bruto(PERIODO_COMERCIALIZACAO="abc")))


def test_submercado_desconhecido_e_invalido(conector):
    with pytest.raises(ValueError, match="submercado"):
        ConsumoHorarioPerfilAgente.model_validate(conector.transformar(_bruto(SUBMERCADO="LUA")))


# ------------------------------------------------------- guarda de recarga


def _com_guarda(conector, monkeypatch, carregados, *, last_modified="2026-09-01T10:00:00", **cfg):
    """`carregados`: o que a Bronze já tem, como {(AAAAMM, versao_ou_None)}. Registra as consultas."""
    monkeypatch.setattr(conector, "_pacote", lambda: _pacote("202605", "202606", "202607", last_modified=last_modified))
    monkeypatch.setattr(f"{MODULO}.get_settings", _settings(**cfg))
    consultas: list[tuple] = []

    def consulta(inicio, fim, versao):
        consultas.append((inicio, fim, versao))
        return (inicio.strftime("%Y%m"), versao) in carregados

    monkeypatch.setattr(conector, "_bronze_tem_carga_concluida", consulta)
    conector.consultas = consultas
    return conector


JANELA_3_MESES = Janela.de_texto("2026-05-01", "2026-07-31")


def test_mes_ja_carregado_na_mesma_versao_nao_e_relido(conector, monkeypatch):
    _com_guarda(conector, monkeypatch, {("202606", date(2026, 9, 1))})

    assert conector._sufixos(JANELA_3_MESES) == ["202605", "202607"]
    assert (date(2026, 6, 1), date(2026, 6, 30), date(2026, 9, 1)) in conector.consultas


def test_mes_republicado_com_outra_versao_e_relido(conector, monkeypatch):
    _com_guarda(conector, monkeypatch, {("202606", date(2026, 8, 1))})  # a Bronze tem a versão antiga

    assert conector._sufixos(JANELA_3_MESES) == ["202605", "202606", "202607"]


def test_sem_last_modified_a_guarda_vale_pelo_mes(conector, monkeypatch):
    """Sem versão na origem, `versao_publicacao` seria a data da carga: nunca bateria e o mês seria relido."""
    _com_guarda(conector, monkeypatch, {("202606", None)}, last_modified=None)

    assert conector._sufixos(JANELA_3_MESES) == ["202605", "202607"]


def test_mes_nao_publicado_segue_para_a_base_ignorar(conector, monkeypatch):
    _com_guarda(conector, monkeypatch, set())
    janela = Janela.de_texto("2026-05-01", "2026-09-30")

    assert conector._sufixos(janela)[-1] == "202609"  # a base loga e ignora; a guarda não decide por ele


def test_dry_run_e_releitura_explicita_nao_consultam_a_bronze(conector, monkeypatch):
    _com_guarda(conector, monkeypatch, {("202606", date(2026, 9, 1))}, dry_run=True)
    assert conector._sufixos(JANELA_3_MESES) == ["202605", "202606", "202607"]

    _com_guarda(conector, monkeypatch, {("202606", date(2026, 9, 1))}, reler=True)
    assert conector._sufixos(JANELA_3_MESES) == ["202605", "202606", "202607"]
    assert conector.consultas == []


def test_consulta_da_bronze_filtra_particao_tem_teto_e_so_conta_execucao_concluida(conector, monkeypatch):
    capturado = {}

    class _Job:
        def result(self):
            return [object()]

    class _Cliente:
        def query(self, sql, job_config):
            capturado["sql"], capturado["cfg"] = sql, job_config
            return _Job()

    monkeypatch.setattr(f"{MODULO}.cliente", lambda: _Cliente())

    assert conector._bronze_tem_carga_concluida(date(2026, 6, 1), date(2026, 6, 30), date(2026, 9, 1)) is True
    sql = capturado["sql"]
    assert "data_referencia BETWEEN @inicio AND @fim" in sql  # require_partition_filter
    assert "e.status = 'SUCESSO'" in sql  # carga que morreu no meio não conta como carregada
    assert "versao_publicacao = @versao" in sql
    assert capturado["cfg"].maximum_bytes_billed  # teto de custo (regra 4)
