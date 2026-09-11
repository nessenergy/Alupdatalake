"""Regras do quadro de acompanhamento (Project 2) — sem rede."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest
from scripts import quadro
from scripts.verifica_atribuicao import infracoes

if TYPE_CHECKING:
    from pathlib import Path

FERIADOS = frozenset({date(2026, 9, 7)})
CFG = quadro.Config(
    dono="org",
    numero=2,
    inicio_s1=date(2026, 8, 31),
    onda_de={1: "Onda 0", 8: "Onda 0", 106: "Onda 0"},
    alup=frozenset({8}),
    vencimentos={1: date(2026, 9, 4), 8: date(2026, 9, 11)},
    feriados=FERIADOS,
)


def _item(numero: int = 8, tipo: str = "Issue", concluido_em: date | None = None, **valores: str) -> quadro.Item:
    return quadro.Item(
        id="item", conteudo_id="conteudo", numero=numero, tipo=tipo, concluido_em=concluido_em, valores=valores
    )


# ----------------------------------------------------------------- calendário


def test_semana_conta_a_partir_da_s1_e_limita_as_pontas() -> None:
    assert quadro.semana(date(2026, 8, 27), CFG.inicio_s1) == "S1"  # concluído antes da S1
    assert quadro.semana(date(2026, 9, 4), CFG.inicio_s1) == "S1"
    assert quadro.semana(date(2026, 9, 8), CFG.inicio_s1) == "S2"
    assert quadro.semana(date(2027, 6, 1), CFG.inicio_s1) == "S19"


def test_atraso_comeca_no_primeiro_dia_util_apos_o_vencimento() -> None:
    # sexta 11/09 → segunda 14/09
    assert quadro.primeiro_dia_util_de_atraso(date(2026, 9, 11), FERIADOS) == date(2026, 9, 14)
    # sexta 04/09 → terça 08/09, porque 07/09 é feriado nacional
    assert quadro.primeiro_dia_util_de_atraso(date(2026, 9, 4), FERIADOS) == date(2026, 9, 8)


# -------------------------------------------------------- valores desejados


def test_insumo_aberto_entra_em_atraso_so_no_primeiro_dia_util_seguinte() -> None:
    assert quadro.desejado(_item(8), CFG, date(2026, 9, 11))["Atraso"] == "Não"  # dia do vencimento
    assert quadro.desejado(_item(8), CFG, date(2026, 9, 12))["Atraso"] == "Não"  # sábado
    assert quadro.desejado(_item(8), CFG, date(2026, 9, 14))["Atraso"] == "Sim"


def test_item_concluido_vira_done_com_semana_e_sem_atraso() -> None:
    alvo = quadro.desejado(_item(8, concluido_em=date(2026, 9, 10)), CFG, date(2026, 9, 20))
    assert alvo["Status"] == "Done"
    assert alvo["Semana"] == "S2"
    assert alvo["Atraso"] == "Não"
    assert alvo["Correções"] == "Não"
    assert alvo["Validado"] == "Não"


def test_item_aberto_nao_tem_status_nem_semana_decididos_pelo_comando() -> None:
    alvo = quadro.desejado(_item(1), CFG, date(2026, 9, 11))
    assert "Status" not in alvo
    assert "Semana" not in alvo


def test_responsavel_e_onda_vem_do_mapa() -> None:
    assert quadro.desejado(_item(8), CFG, date(2026, 9, 11))["Responsável"] == "Alup"
    assert quadro.desejado(_item(1), CFG, date(2026, 9, 11))["Responsável"] == "ness."
    assert quadro.desejado(_item(1), CFG, date(2026, 9, 11))["Onda"] == "Onda 0"
    assert "Onda" not in quadro.desejado(_item(999), CFG, date(2026, 9, 11))


def test_pull_request_nao_recebe_atraso() -> None:
    assert "Atraso" not in quadro.desejado(_item(106, tipo="PullRequest"), CFG, date(2026, 9, 14))


# ----------------------------------------------------------------- mudanças


def test_mudancas_traz_so_o_que_difere() -> None:
    item = _item(8, Onda="Onda 0", Responsável="Alup", Atraso="Não")
    alvo = quadro.desejado(item, CFG, date(2026, 9, 14))
    assert quadro.mudancas(item, alvo) == {"Atraso": "Sim"}


def test_nunca_desfaz_decisao_humana() -> None:
    item = _item(8, concluido_em=date(2026, 9, 10), Atraso="Sim", Validado="Sim", Correções="Sim", Semana="S3")
    alvo = quadro.desejado(item, CFG, date(2026, 9, 20))
    mudou = quadro.mudancas(item, alvo)
    for campo in ("Atraso", "Validado", "Correções", "Semana"):
        assert campo not in mudou, campo
    assert mudou["Status"] == "Done"


def test_rodar_de_novo_nao_muda_nada() -> None:
    item = _item(8, Onda="Onda 0", Responsável="Alup", Atraso="Não")
    alvo = quadro.desejado(item, CFG, date(2026, 9, 14))
    aplicado = quadro.Item(**{**item.__dict__, "valores": {**item.valores, **quadro.mudancas(item, alvo)}})
    assert quadro.mudancas(aplicado, quadro.desejado(aplicado, CFG, date(2026, 9, 14))) == {}


# -------------------------------------------------------------- comentário


def test_comentario_de_atraso_cita_as_datas_e_passa_na_regra_6() -> None:
    texto = quadro.comentario_de_atraso(date(2026, 9, 11), date(2026, 9, 14), FERIADOS)
    assert "11/09/2026" in texto
    assert "14/09/2026" in texto
    assert "cláusula 3ª" in texto
    assert infracoes(texto) == []


# -------------------------------------------------------------- configuração


def test_configuracao_do_repositorio_carrega() -> None:
    cfg = quadro.carregar_config()
    assert cfg.dono == "nessenergy"
    assert cfg.numero == 2
    assert cfg.inicio_s1 == date(2026, 8, 31)
    assert date(2026, 9, 7) in cfg.feriados
    # todo insumo da Alup com vencimento está classificado numa onda
    assert all(n in cfg.onda_de for n in cfg.vencimentos)
    assert 55 in cfg.alup and cfg.vencimentos[55] == date(2026, 9, 4)


def test_configuracao_recusa_issue_em_duas_ondas(tmp_path: Path) -> None:
    arquivo = tmp_path / "quadro.toml"
    arquivo.write_text(
        'dono = "org"\nnumero = 2\ninicio_s1 = 2026-08-31\nalup = []\nferiados = []\n'
        '[ondas]\n"Onda 0" = [1]\n"Onda 1" = [1]\n[vencimentos]\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="#1"):
        quadro.carregar_config(arquivo)
