"""Modelo de planilha do PRC (Preço de Referência Comparável, comercialização varejista).

Os valores das fixtures são ilustrativos: o modelo existe para a Alup preencher, e o que se
confere aqui é a forma, não um preço.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.planilha_prc import TEMPLATE_PRC, PlanilhaPrc, PrecoReferencia
from src.core.config import get_settings
from src.core.execucao import Janela
from src.core.planilha import TemplateInvalidoError, ler_tabela

MODELO = Path(__file__).resolve().parents[3] / "docs" / "modelos" / "modelo-prc.csv"
CABECALHO = ";".join(TEMPLATE_PRC.colunas)


@pytest.fixture(autouse=True)
def _dry_run() -> None:
    get_settings().dry_run = True


def _csv(tmp_path: Path, *linhas: str) -> Path:
    caminho = tmp_path / "prc.csv"
    caminho.write_text("\n".join([CABECALHO, *linhas]) + "\n", encoding="utf-8-sig")
    return caminho


def _linha(**campos: object) -> dict[str, object]:
    base = {
        "comercializadora": "Comercializadora Teste",
        "data_atualizacao": "2026-07-24",
        "submercado": "SE",
        "tipo_energia": "convencional",
        "ano": 2027,
        "prazo_meses": None,
        "preco_rs_mwh": "216.00",
        "indexador": "IPCA",
        "premissas": None,
    }
    return base | campos


def test_planilha_valida_chega_ao_schema_com_numero_brasileiro(tmp_path: Path) -> None:
    caminho = _csv(
        tmp_path,
        "Comercializadora Teste;24/07/2026;SE;convencional;2027;;216,00;IPCA;PIS/COFINS incluso; ICMS à parte",
    )
    [linha] = list(ler_tabela(caminho, TEMPLATE_PRC))
    registro = PrecoReferencia.model_validate(PlanilhaPrc().transformar(linha))

    assert registro.preco_rs_mwh == Decimal("216.00")
    assert registro.data_atualizacao == date(2026, 7, 24)
    assert registro.submercado == "SE"
    assert registro.ano == 2027


def test_arquivo_fora_do_template_e_rejeitado_inteiro(tmp_path: Path) -> None:
    caminho = tmp_path / "ruim.csv"
    caminho.write_text("Comercializadora;Preço\nX;1,00\n", encoding="utf-8-sig")

    with pytest.raises(TemplateInvalidoError, match="faltam"):
        list(ler_tabela(caminho, TEMPLATE_PRC))


def test_o_arquivo_modelo_bate_com_o_template_e_a_linha_de_exemplo_nao_carrega() -> None:
    linhas = list(ler_tabela(MODELO, TEMPLATE_PRC))

    assert linhas, "o modelo traz uma linha de exemplo"
    with pytest.raises(ValidationError, match="exemplo"):
        PrecoReferencia.model_validate(PlanilhaPrc().transformar(linhas[0]))


@pytest.mark.parametrize("submercado", ["SE/CO", "Sul", "XX", ""])
def test_submercado_so_aceita_a_sigla_de_um_submercado(submercado: str) -> None:
    with pytest.raises(ValidationError):
        PrecoReferencia.model_validate(_linha(submercado=submercado))


def test_tipo_de_energia_desconhecido_e_rejeitado() -> None:
    with pytest.raises(ValidationError):
        PrecoReferencia.model_validate(_linha(tipo_energia="mágica"))


def test_exige_ano_ou_prazo_em_meses_e_nunca_os_dois() -> None:
    PrecoReferencia.model_validate(_linha(ano=None, prazo_meses=36))
    with pytest.raises(ValidationError):
        PrecoReferencia.model_validate(_linha(ano=None, prazo_meses=None))
    with pytest.raises(ValidationError):
        PrecoReferencia.model_validate(_linha(ano=2027, prazo_meses=36))


@pytest.mark.parametrize("preco", ["0", "-10", "5000"])
def test_preco_fora_da_faixa_e_erro_de_digitacao(preco: str) -> None:
    with pytest.raises(ValidationError):
        PrecoReferencia.model_validate(_linha(preco_rs_mwh=preco))


def test_conector_percorre_o_runner_sem_rede(tmp_path: Path) -> None:
    conector = PlanilhaPrc()
    conector.caminho = _csv(
        tmp_path,
        "Comercializadora Teste;24/07/2026;SE;convencional;2027;;216,00;IPCA;",
        "Comercializadora Teste;24/07/2026;NE;incentivada_50;;36;251,00;IPCA;",
    )

    execucao = conector.ingerir(Janela.de_texto("2026-07-24", "2026-07-24"))

    # Em dry-run as linhas são validadas e não gravadas: o que vale é ninguém ter sido descartado.
    assert (execucao.linhas_extraidas, execucao.linhas_invalidas) == (2, 0)
