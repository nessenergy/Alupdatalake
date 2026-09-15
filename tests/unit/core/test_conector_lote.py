"""O runner ingere em fatias: memória limitada, e a carga começa antes do fim da extração.

O que estes testes protegem, e que a primeira versão do runner não fazia:

- `extrair()` é consumido **preguiçosamente**. Antes, o runner fazia
  `brutos.extend(...)` de tudo antes de gravar qualquer coisa — com a geração
  horária da CCEE isso são ~3 milhões de dicionários por mês, e o Cloud Run Job
  morria de memória antes da primeira linha chegar ao Bronze;
- a carga acontece **por fatia**, e os contadores somam entre as fatias em vez
  de serem sobrescritos pela última;
- o raw recebe todos os registros, na ordem da origem, mesmo fatiado.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from pydantic import BaseModel
from src.core.conector import Conector
from src.core.execucao import Janela


class Registro(BaseModel):
    data_referencia: date
    valor: Decimal


class ConectorFatiado(Conector):
    """Emite `total` registros, anotando quantos já saíram quando cada carga ocorre."""

    fonte = "teste"
    entidade = "fatia"
    schema = Registro
    tamanho_do_lote = 2

    def __init__(self, total: int = 5, invalidos: frozenset[int] = frozenset()) -> None:
        self.total = total
        self.invalidos = invalidos
        self.emitidos = 0

    def extrair(self, janela: Janela):
        del janela
        for i in range(self.total):
            self.emitidos += 1
            yield {"dia": "2026-01-01", "valor": "vazio" if i in self.invalidos else str(i)}

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {"data_referencia": bruto["dia"], "valor": bruto["valor"]}


@pytest.fixture
def espiao(monkeypatch):
    """Registra cada chamada de carga e cada registro gravado no raw."""
    cargas: list[int] = []
    emitidos_na_carga: list[int] = []
    raw: list[dict[str, Any]] = []
    conector: dict[str, ConectorFatiado] = {}

    def carregar(_execucao, linhas):
        cargas.append(len(linhas))
        emitidos_na_carga.append(conector["c"].emitidos)
        return len(linhas)

    class RawFalso:
        uri = "gs://bucket/teste/fatia/dt=2026-01-01/abc.json.gz"

        def escrever(self, registro):
            raw.append(registro)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr("src.core.conector.carregar_bronze", carregar)
    monkeypatch.setattr("src.core.conector.abrir_raw", lambda _e: RawFalso())
    monkeypatch.setattr("src.core.conector.registrar_execucao", lambda _e: None)
    monkeypatch.setattr("src.core.conector.emitir_linhagem", lambda *_a, **_k: None)
    return {"cargas": cargas, "emitidos": emitidos_na_carga, "raw": raw, "conector": conector}


def test_carrega_em_fatias_em_vez_de_um_lote_unico(espiao):
    c = ConectorFatiado(total=5)
    espiao["conector"]["c"] = c

    execucao = c.ingerir(Janela.de_texto("2026-01-01", "2026-01-01"))

    assert espiao["cargas"] == [2, 2, 1], "5 registros com lote de 2 são três cargas"
    assert execucao.linhas_carregadas == 5, "o contador soma as fatias, não guarda só a última"
    assert execucao.linhas_extraidas == 5


def test_a_primeira_carga_acontece_antes_do_fim_da_extracao(espiao):
    """É esta a propriedade que limita a memória — sem ela, fatiar não adianta."""
    c = ConectorFatiado(total=5)
    espiao["conector"]["c"] = c

    c.ingerir(Janela.de_texto("2026-01-01", "2026-01-01"))

    assert espiao["emitidos"][0] == 2, "a primeira carga viu só os 2 primeiros registros emitidos"
    assert espiao["emitidos"][-1] == 5


def test_raw_recebe_todos_os_registros_na_ordem(espiao):
    c = ConectorFatiado(total=5)
    espiao["conector"]["c"] = c

    c.ingerir(Janela.de_texto("2026-01-01", "2026-01-01"))

    assert len(espiao["raw"]) == 5
    assert [r["valor"] for r in espiao["raw"]] == ["0", "1", "2", "3", "4"]


def test_invalidos_sao_contados_em_todas_as_fatias(espiao):
    c = ConectorFatiado(total=5, invalidos=frozenset({0, 3}))
    espiao["conector"]["c"] = c

    execucao = c.ingerir(Janela.de_texto("2026-01-01", "2026-01-01"))

    assert execucao.linhas_extraidas == 5
    assert execucao.linhas_invalidas == 2, "um inválido na primeira fatia e outro na segunda"
    assert execucao.linhas_carregadas == 3
    assert execucao.status == "SUCESSO"


def test_lote_maior_que_o_volume_faz_uma_carga_so(espiao):
    c = ConectorFatiado(total=3)
    c.tamanho_do_lote = 500
    espiao["conector"]["c"] = c

    execucao = c.ingerir(Janela.de_texto("2026-01-01", "2026-01-01"))

    assert espiao["cargas"] == [3]
    assert execucao.linhas_carregadas == 3


def test_janela_sem_registro_nao_carrega_nada(espiao):
    c = ConectorFatiado(total=0)
    espiao["conector"]["c"] = c

    execucao = c.ingerir(Janela.de_texto("2026-01-01", "2026-01-01"))

    assert espiao["cargas"] == []
    assert execucao.linhas_extraidas == 0
    assert execucao.status == "SUCESSO"


def test_o_tamanho_do_lote_e_configuravel_por_conector():
    """A geração horária da CCEE precisa de fatia menor que a de uma série diária."""
    assert Conector.tamanho_do_lote > 0
    assert ConectorFatiado.tamanho_do_lote == 2
