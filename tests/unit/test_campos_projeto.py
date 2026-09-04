"""Contrato dos campos de acompanhamento semanal do GitHub Projects.

O script fala com uma API que não temos como exercitar no CI, então o que se
testa aqui é o que dá para errar em silêncio: tipo inválido, opção faltando,
e a idempotência — campo existente não pode ser recriado.
"""

from __future__ import annotations

import pytest
from scripts import campos_projeto as cp

# Projects V2 não tem booleano nem checkbox; e ITERATION não é criável por API.
TIPOS_CRIAVEIS = {"TEXT", "NUMBER", "DATE", "SINGLE_SELECT"}
ESPERADOS = {"Horas", "Semana", "Validado", "Correções", "Atraso"}


def test_os_cinco_campos_pedidos_estao_declarados():
    assert {campo["nome"] for campo in cp.CAMPOS} == ESPERADOS


def test_todo_tipo_e_criavel_por_api():
    for campo in cp.CAMPOS:
        assert campo["tipo"] in TIPOS_CRIAVEIS, campo["nome"]


def test_horas_e_numerico():
    horas = next(c for c in cp.CAMPOS if c["nome"] == "Horas")
    assert horas["tipo"] == "NUMBER"


@pytest.mark.parametrize("nome", ["Validado", "Correções", "Atraso"])
def test_indicadores_sao_sim_ou_nao(nome):
    campo = next(c for c in cp.CAMPOS if c["nome"] == nome)
    assert campo["tipo"] == "SINGLE_SELECT"
    assert [o["name"] for o in campo["opcoes"]] == ["Sim", "Não"]


def test_semana_cobre_as_19_semanas_do_contrato():
    semana = next(c for c in cp.CAMPOS if c["nome"] == "Semana")
    assert [o["name"] for o in semana["opcoes"]] == [f"S{n}" for n in range(1, 20)]


def test_toda_selecao_tem_opcoes_e_nenhum_outro_tipo_tem():
    for campo in cp.CAMPOS:
        if campo["tipo"] == "SINGLE_SELECT":
            assert campo.get("opcoes"), campo["nome"]
        else:
            assert "opcoes" not in campo, campo["nome"]


def test_todo_campo_declara_por_que_existe():
    # O "porque" vai para o log e para o runbook; campo sem justificativa vira
    # coluna que ninguém preenche.
    for campo in cp.CAMPOS:
        assert campo["porque"].strip()


def test_projeto_de_aceita_org_ou_usuario():
    assert cp.projeto_de({"organization": {"projectV2": {"id": "A"}}, "user": None}, "projectV2") == {"id": "A"}
    assert cp.projeto_de({"organization": None, "user": {"projectV2": {"id": "B"}}}, "projectV2") == {"id": "B"}
    assert cp.projeto_de({"organization": None, "user": None}, "projectV2") is None


def test_campo_existente_nao_e_recriado(monkeypatch, caplog):
    """Idempotência: com os cinco campos já lá, nenhuma mutação é enviada."""
    chamadas = []

    def falso_consultar(query, variaveis):
        chamadas.append(query)
        if "createProjectV2Field" in query:
            raise AssertionError("não deveria criar campo que já existe")
        return {
            "organization": {
                "projectV2": {
                    "id": "P_1",
                    "title": "AlupData",
                    "fields": {"nodes": [{"name": nome} for nome in ESPERADOS]},
                }
            },
            "user": None,
        }

    monkeypatch.setattr(cp, "consultar", falso_consultar)
    assert cp.aplicar("nessenergy", 1, dry_run=False) == 0
    assert len(chamadas) == 1  # só a consulta, nenhuma mutação


def test_projeto_inexistente_falha_sem_criar_nada(monkeypatch):
    monkeypatch.setattr(cp, "consultar", lambda *_: {"organization": None, "user": None})
    assert cp.aplicar("nessenergy", 99, dry_run=False) == 1
