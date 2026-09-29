"""Gerador da tela do Aditivo 01 (painel/aditivo.html).

Fonte única, sem E/S: `painel/aditivo.toml`, hand-editado junto com
docs/contrato/aditivo-01-conjuntos-publicos.md.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from scripts import painel_aditivo
from scripts.painel_aditivo import BRASILIA

RAIZ = Path(__file__).resolve().parents[2]


def test_aditivo_toml_do_repositorio_e_valido():
    dados = painel_aditivo.carregar(RAIZ / "painel" / "aditivo.toml")
    numeros = sorted(i["numero"] for g in dados["grupo"] for i in g["item"])
    assert numeros == list(range(1, 27)), "os 26 itens do aditivo, em sequência"


def test_item_entregue_sem_pr_e_recusado(tmp_path):
    texto = """
    titulo = "t"
    pedido_em = 2026-09-28
    issue = 1
    documento = "d"
    [[grupo]]
    codigo = "A"
    nome = "n"
    [[grupo.item]]
    numero = 1
    titulo = "x"
    horas = 4
    estado = "entregue"
    entregue_em = 2026-09-28
    """
    arquivo = tmp_path / "aditivo.toml"
    arquivo.write_text(texto, encoding="utf-8")
    with pytest.raises(ValueError, match="entregue exige"):
        painel_aditivo.carregar(arquivo)


def test_item_revisao_sem_nota_e_recusado(tmp_path):
    texto = """
    titulo = "t"
    pedido_em = 2026-09-28
    issue = 1
    documento = "d"
    [[grupo]]
    codigo = "A"
    nome = "n"
    [[grupo.item]]
    numero = 1
    titulo = "x"
    horas = 4
    estado = "revisao"
    """
    arquivo = tmp_path / "aditivo.toml"
    arquivo.write_text(texto, encoding="utf-8")
    with pytest.raises(ValueError, match="revisao exige nota"):
        painel_aditivo.carregar(arquivo)


def test_numero_repetido_e_recusado(tmp_path):
    texto = """
    titulo = "t"
    pedido_em = 2026-09-28
    issue = 1
    documento = "d"
    [[grupo]]
    codigo = "A"
    nome = "n"
    [[grupo.item]]
    numero = 1
    titulo = "x"
    horas = 4
    estado = "pendente"
    [[grupo.item]]
    numero = 1
    titulo = "y"
    horas = 4
    estado = "pendente"
    """
    arquivo = tmp_path / "aditivo.toml"
    arquivo.write_text(texto, encoding="utf-8")
    with pytest.raises(ValueError, match="número repetido"):
        painel_aditivo.carregar(arquivo)


def test_montar_exclui_revisao_do_subtotal():
    dados = {
        "titulo": "t",
        "pedido_em": __import__("datetime").date(2026, 9, 28),
        "issue": 294,
        "documento": "d",
        "grupo": [
            {
                "codigo": "A",
                "nome": "n",
                "item": [
                    {
                        "numero": 1,
                        "titulo": "a",
                        "horas": 6,
                        "estado": "entregue",
                        "entregue_em": "2026-09-28",
                        "prs": [1],
                    },
                    {"numero": 2, "titulo": "b", "horas": 5, "estado": "pendente"},
                    {"numero": 3, "titulo": "c", "horas": 6, "estado": "revisao", "nota": "grande demais"},
                ],
            }
        ],
    }

    saida = painel_aditivo.montar(dados, datetime(2026, 9, 29, tzinfo=BRASILIA))

    assert saida["subtotal"] == {"estimado": 11, "apontado": 6, "itens_total": 2, "itens_entregues": 1}
    assert len(saida["grupos"][0]["item"]) == 3, "o item em revisão continua na lista, só sai do subtotal"
