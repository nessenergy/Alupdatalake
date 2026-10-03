"""INMET — precipitação horária por estação, lida do zip anual do portal. Sem rede."""

from __future__ import annotations

import io
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.inmet_precipitacao import InmetPrecipitacao, LayoutInesperadoError, PrecipitacaoHoraria
from src.core.config import get_settings
from src.core.execucao import Janela

FIXTURE = (Path(__file__).parents[2] / "fixtures" / "inmet_A701_2025.csv").read_bytes()
NOME = "2025/INMET_SE_SP_A701_SAO PAULO - MIRANTE_01-01-2025_A_31-12-2025.CSV"


@pytest.fixture(autouse=True)
def _dry_run() -> None:
    get_settings().dry_run = True


def _zip(*arquivos: tuple[str, bytes]) -> bytes:
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w") as z:
        z.writestr("2025/", b"")  # o zip real traz a pasta como primeiro item
        for nome, conteudo in arquivos:
            z.writestr(nome, conteudo)
    return memoria.getvalue()


def _conector(monkeypatch: pytest.MonkeyPatch, por_ano: dict[int, bytes | None]) -> tuple[InmetPrecipitacao, list[int]]:
    monkeypatch.setattr("src.conectores.inmet_precipitacao.criar_sessao", lambda: None)
    conector = InmetPrecipitacao()
    baixados: list[int] = []

    def baixar(ano: int):
        baixados.append(ano)
        conteudo = por_ano.get(ano)
        return None if conteudo is None else io.BytesIO(conteudo)

    monkeypatch.setattr(conector, "_baixar_zip", baixar)
    return conector, baixados


def _linhas(conector: InmetPrecipitacao, ini: str, fim: str) -> list[PrecipitacaoHoraria]:
    janela = Janela.de_texto(ini, fim)
    return [PrecipitacaoHoraria.model_validate(conector.transformar(b)) for b in conector.extrair(janela)]


def _registro(**campos: object) -> dict[str, object]:
    base = {
        "estacao": "A001",
        "nome_estacao": "X",
        "regiao": "CO",
        "uf": "DF",
        "latitude": "-15,78",
        "longitude": "-47,92",
        "altitude_m": None,
        "data_referencia": "2025-01-01",
        "hora_utc": 0,
        "precipitacao_mm": "0",
    }
    return {**base, **campos}


def test_le_metadados_da_estacao_e_a_precipitacao_horaria(monkeypatch) -> None:
    conector, _ = _conector(monkeypatch, {2025: _zip((NOME, FIXTURE))})
    primeira = _linhas(conector, "2025-01-01", "2025-01-01")[0]

    assert (primeira.estacao, primeira.regiao, primeira.uf) == ("A701", "SE", "SP")
    assert primeira.nome_estacao == "SAO PAULO - MIRANTE"
    assert primeira.latitude == Decimal("-23.4962888")  # a origem escreve com vírgula
    assert primeira.data_referencia == date(2025, 1, 1)
    assert primeira.hora_utc == 0
    assert primeira.precipitacao_mm == Decimal("0")


def test_hora_sem_medicao_vira_nulo_e_nunca_zero(monkeypatch) -> None:
    """47 horas de A701 em 2025 vêm vazias: chuva zero inventada contaminaria o acumulado."""
    conector, _ = _conector(monkeypatch, {2025: _zip((NOME, FIXTURE))})
    registros = _linhas(conector, "2025-01-01", "2025-12-31")

    assert any(r.precipitacao_mm is None for r in registros)


def test_sentinela_9999_vira_nulo() -> None:
    registro = PrecipitacaoHoraria.model_validate(_registro(altitude_m="1160", precipitacao_mm="-9999"))

    assert registro.precipitacao_mm is None


@pytest.mark.parametrize("mm", ["-1", "501"])
def test_precipitacao_fora_da_faixa_e_erro_de_origem(mm: str) -> None:
    with pytest.raises(ValueError):
        PrecipitacaoHoraria.model_validate(_registro(precipitacao_mm=mm))


def test_janela_recorta_as_horas_pedidas(monkeypatch) -> None:
    conector, _ = _conector(monkeypatch, {2025: _zip((NOME, FIXTURE))})

    assert {r.data_referencia for r in _linhas(conector, "2025-01-01", "2025-01-01")} == {date(2025, 1, 1)}


def test_janela_que_cruza_o_ano_baixa_os_dois_zips(monkeypatch) -> None:
    ano_novo = FIXTURE.replace(b"2025/01/01", b"2026/01/01")
    conector, baixados = _conector(
        monkeypatch,
        {2025: _zip((NOME, FIXTURE)), 2026: _zip((NOME.replace("2025", "2026"), ano_novo))},
    )
    registros = _linhas(conector, "2025-01-01", "2026-01-01")

    assert baixados == [2025, 2026]
    assert {r.data_referencia.year for r in registros} == {2025, 2026}


def test_ano_ainda_nao_publicado_e_aviso_nao_erro(monkeypatch) -> None:
    conector, _ = _conector(monkeypatch, {2025: _zip((NOME, FIXTURE)), 2026: None})

    assert _linhas(conector, "2025-01-01", "2026-12-31")  # o 2026 devolveu 404; o 2025 vale


def test_zip_sem_nenhum_csv_falha_alto(monkeypatch) -> None:
    conector, _ = _conector(monkeypatch, {2025: _zip()})

    with pytest.raises(LayoutInesperadoError, match="nenhum CSV"):
        list(conector.extrair(Janela.de_texto("2025-01-01", "2025-01-02")))


def test_ciclo_completo_no_runner_sem_rede(monkeypatch) -> None:
    conector, _ = _conector(monkeypatch, {2025: _zip((NOME, FIXTURE))})
    execucao = conector.ingerir(Janela.de_texto("2025-01-01", "2025-01-01"))

    assert execucao.linhas_extraidas > 0
    assert execucao.linhas_invalidas == 0
