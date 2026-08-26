"""Motor S2 Data Intake: template, leitura e os modos de falha de planilha.

O que se testa aqui é sobretudo o que uma pessoa faz com um arquivo — renomear
coluna, deixar linha em branco, pôr título acima do cabeçalho.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from src.core.planilha import (
    TemplateInvalidoError,
    TemplatePlanilha,
    decimal_br,
    ler_tabela,
    validar_cabecalho,
)

if TYPE_CHECKING:
    from pathlib import Path


TEMPLATE = TemplatePlanilha(
    colunas={"Data": "data_referencia", "Valor (R$)": "valor", "Obs": "observacao"},
    colunas_decimais=frozenset({"valor"}),
)


def _csv(tmp_path: Path, conteudo: str, nome: str = "planilha.csv") -> Path:
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8-sig")
    return caminho


def test_le_arquivo_no_template(tmp_path: Path) -> None:
    arquivo = _csv(tmp_path, "Data;Valor (R$);Obs\n2026-08-01;1.400,00;primeira\n")
    (linha,) = list(ler_tabela(arquivo, TEMPLATE))
    assert linha == {"data_referencia": "2026-08-01", "valor": Decimal("1400.00"), "observacao": "primeira"}


def test_coluna_faltando_rejeita_o_arquivo_inteiro(tmp_path: Path) -> None:
    arquivo = _csv(tmp_path, "Data;Obs\n2026-08-01;x\n")
    with pytest.raises(TemplateInvalidoError, match=r"faltam \['Valor \(R\$\)'\]"):
        list(ler_tabela(arquivo, TEMPLATE))


def test_coluna_renomeada_aponta_falta_e_sobra(tmp_path: Path) -> None:
    arquivo = _csv(tmp_path, "Data;Valor R$;Obs\n2026-08-01;10,00;x\n")
    with pytest.raises(TemplateInvalidoError) as erro:
        list(ler_tabela(arquivo, TEMPLATE))
    assert "faltam ['Valor (R$)']" in str(erro.value)
    assert "sobram ['Valor R$']" in str(erro.value)


def test_arquivo_vazio_nao_passa_silencioso(tmp_path: Path) -> None:
    with pytest.raises(TemplateInvalidoError, match="vazia"):
        list(ler_tabela(_csv(tmp_path, ""), TEMPLATE))


def test_linha_em_branco_no_meio_e_ignorada(tmp_path: Path) -> None:
    arquivo = _csv(tmp_path, "Data;Valor (R$);Obs\n2026-08-01;1,00;a\n;;\n2026-08-02;2,00;b\n\n")
    linhas = list(ler_tabela(arquivo, TEMPLATE))
    assert [linha["data_referencia"] for linha in linhas] == ["2026-08-01", "2026-08-02"]


def test_celula_vazia_vira_none_nao_string_vazia(tmp_path: Path) -> None:
    arquivo = _csv(tmp_path, "Data;Valor (R$);Obs\n2026-08-01;;\n")
    (linha,) = list(ler_tabela(arquivo, TEMPLATE))
    assert linha["valor"] is None
    assert linha["observacao"] is None


def test_titulo_acima_do_cabecalho(tmp_path: Path) -> None:
    template = TemplatePlanilha(colunas={"Data": "data_referencia"}, linha_cabecalho=3)
    arquivo = _csv(tmp_path, "Relatório mensal\n\nData\n2026-08-01\n")
    (linha,) = list(ler_tabela(arquivo, template))
    assert linha["data_referencia"] == "2026-08-01"


def test_le_xlsx_com_o_mesmo_template(tmp_path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    livro = openpyxl.Workbook()
    aba = livro.active
    aba.append(["Data", "Valor (R$)", "Obs"])
    aba.append(["2026-08-01", "1.400,00", "primeira"])
    aba.append([None, None, None])
    caminho = tmp_path / "planilha.xlsx"
    livro.save(caminho)

    (linha,) = list(ler_tabela(caminho, TEMPLATE))
    assert linha["valor"] == Decimal("1400.00")


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("1.400,00", Decimal("1400.00")),
        (",00", Decimal("0.00")),
        ("0,5", Decimal("0.5")),
        ("", None),
        (None, None),
        ("  12,3  ", Decimal("12.3")),
    ],
)
def test_decimal_brasileiro(entrada: str | None, esperado: Decimal | None) -> None:
    assert decimal_br(entrada) == esperado


def test_decimal_invalido_nao_vira_zero() -> None:
    with pytest.raises(ValueError, match="número inválido"):
        decimal_br("mil e quatrocentos")


def test_validar_cabecalho_ignora_espaco_e_coluna_vazia() -> None:
    validar_cabecalho([" Data ", "Valor (R$)", "Obs", "", None], TEMPLATE)  # type: ignore[list-item]
