"""Cada cartão de indicador diz de onde vem o dado e quando o lake o carregou (02/10)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from src.portal.dados import Indicador, SaudeConector
from src.portal.indicadores import INDICADORES, ORIGEM, cartoes

BRONZE = Path(__file__).resolve().parents[2] / "definitions" / "bronze"


def _ind(nome: str, periodo: str = "2026-08") -> Indicador:
    return Indicador(periodo, nome, None, None, Decimal(1), "MWh", Decimal(2), "MWh", Decimal("0.5"), "fracao")


def _saude(conector: str, ultimo: datetime | None) -> SaudeConector:
    return SaudeConector(conector, "OK", ultimo, 5, 1440, 1.0, 0.0, 10, 1.0)


def test_toda_razao_do_catalogo_tem_origem_e_todo_conector_existe() -> None:
    assert set(ORIGEM) == {nome for nome, _, _ in INDICADORES}
    for _, conectores in ORIGEM.values():
        for conector in conectores:
            assert (BRONZE / f"{conector}.sqlx").exists(), conector


def test_cartao_mostra_fonte_mes_e_a_carga_mais_antiga_em_horario_de_brasilia() -> None:
    saude = [
        _saude("ons_restricao_coff_eolica", datetime(2026, 10, 2, 12, 0, tzinfo=UTC)),
        _saude("ons_restricao_coff_fotovoltaica", datetime(2026, 10, 1, 17, 30, tzinfo=UTC)),
    ]
    [cartao] = cartoes([_ind("taxa_corte_renovavel")], saude)
    assert "Fonte: ONS · restrição eólica e solar</span>" in cartao
    assert "dados até ago/2026 · carga em 01/10 14h" in cartao


def test_conector_sem_sucesso_nao_ganha_data_inventada() -> None:
    saude = [_saude("ons_disponibilidade_usina", None)]
    [cartao] = cartoes([_ind("disponibilidade")], saude)
    assert "sem carga registrada" in cartao


def test_sem_saude_o_cartao_so_diz_fonte_e_mes() -> None:
    [cartao] = cartoes([_ind("pld_real")])
    assert "Fonte: CCEE · PLD e IBGE · IPCA" in cartao
    assert "dados até ago/2026" in cartao
    assert "carga" not in cartao.split("ad-origem", 1)[1].split("</p>", 1)[0]
