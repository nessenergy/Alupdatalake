"""ConectorPlanilha: a planilha entra pelo mesmo runner das outras fontes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import BaseModel
from src.conectores.planilha import ConectorPlanilha
from src.core.config import get_settings
from src.core.execucao import Janela
from src.core.planilha import TemplateInvalidoError, TemplatePlanilha

if TYPE_CHECKING:
    from pathlib import Path


class Medicao(BaseModel):
    data_referencia: str
    energia_mwh: float


class MedicaoManual(ConectorPlanilha):
    fonte = "s2"
    entidade = "medicao_manual"
    schema = Medicao
    template = TemplatePlanilha(
        colunas={"Data": "data_referencia", "MWh": "energia_mwh"},
        colunas_decimais=frozenset({"energia_mwh"}),
    )


@pytest.fixture(autouse=True)
def _dry_run() -> None:
    get_settings().dry_run = True


def _planilha(tmp_path: Path, conteudo: str) -> Path:
    caminho = tmp_path / "medicao.csv"
    caminho.write_text(conteudo, encoding="utf-8-sig")
    return caminho


def test_ingestao_completa_de_planilha_valida(tmp_path: Path) -> None:
    conector = MedicaoManual()
    conector.caminho = _planilha(tmp_path, "Data;MWh\n2026-08-01;1.250,50\n2026-08-02;980,00\n")

    execucao = conector.ingerir(Janela.de_texto("2026-08-01", "2026-08-02"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 0


def test_linha_ruim_e_descartada_e_contada_sem_derrubar_o_arquivo(tmp_path: Path) -> None:
    conector = MedicaoManual()
    conector.caminho = _planilha(tmp_path, "Data;MWh\n2026-08-01;1.250,50\n2026-08-02;\n")

    execucao = conector.ingerir(Janela.de_texto("2026-08-01", "2026-08-02"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 1  # MWh vazio não vira zero


def test_arquivo_fora_do_template_derruba_a_execucao_como_erro(tmp_path: Path) -> None:
    conector = MedicaoManual()
    conector.caminho = _planilha(tmp_path, "Data;Energia\n2026-08-01;10\n")

    with pytest.raises(TemplateInvalidoError):
        conector.ingerir(Janela.de_texto("2026-08-01", "2026-08-02"))
