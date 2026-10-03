"""Conferência de cargas: consultas fixas, só leitura, sem rede (cliente falso)."""

import re
from pathlib import Path

import pytest
import yaml
from google.api_core.exceptions import NotFound
from scripts import conferir_cargas as cc

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOW = RAIZ / ".github" / "workflows" / "conferir-cargas.yml"
PROIBIDAS = ("INSERT", "UPDATE", "DELETE", "MERGE", "DROP", "CREATE", "ALTER")


def conjuntos():
    return cc.montar_conjuntos("proj", "bronze", "silver", "gold")


def todas_as_consultas() -> list[str]:
    return [item.sql for _, itens in conjuntos() for item in itens]


class ClienteFalso:
    """Devolve linhas fixas; levanta `NotFound` para as tabelas listadas em `ausentes`."""

    def __init__(self, linhas=None, ausentes=(), erro=None):
        self.linhas = linhas if linhas is not None else [{"linhas": 3}]
        self.ausentes = ausentes
        self.erro = erro
        self.consultas: list[str] = []

    def query(self, sql, job_config=None):
        self.consultas.append(sql)
        assert job_config is not None and job_config.use_query_cache is True
        if any(f".{nome}`" in sql for nome in self.ausentes):
            raise NotFound("Not found: Table proj:silver.x")
        if self.erro:
            raise self.erro
        return self

    def result(self):
        return iter(self.linhas)


def test_toda_consulta_e_leitura():
    consultas = todas_as_consultas()
    assert consultas
    for sql in consultas:
        assert re.match(r"\s*(SELECT|WITH)\b", sql, re.IGNORECASE), sql
        assert ";" not in sql, sql
        for palavra in PROIBIDAS:
            assert not re.search(rf"\b{palavra}\b", sql, re.IGNORECASE), (palavra, sql)
        cc.validar_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM `p.silver.x` WHERE TRUE",
        "INSERT INTO `p.silver.x` SELECT 1",
        "SELECT 1; DROP TABLE x",
        "SELECT 1;",
        "CREATE TABLE x AS SELECT 1",
        "WITH a AS (SELECT 1) DELETE FROM x WHERE TRUE",
        "SELECT 1 -- comentário",
        "  ",
    ],
)
def test_consulta_que_nao_e_leitura_e_recusada(sql):
    cliente = ClienteFalso()
    with pytest.raises(ValueError):
        cc.executar_consulta(cliente, sql)
    assert cliente.consultas == []


def test_tabela_ausente_vira_linha_ausente_e_o_resto_segue():
    cliente = ClienteFalso(ausentes=("ons_carga_programada",))
    secoes = cc.rodar(cliente, conjuntos())

    linhas = [linha for _, linhas_da_secao in secoes for linha in linhas_da_secao]
    ausentes = [linha for linha in linhas if linha.get("resultado") == "ausente"]
    assert [linha["item"] for linha in ausentes] == ["ons_carga_programada"]
    assert len(cliente.consultas) == len(todas_as_consultas())
    assert any(linha.get("linhas") == 3 for linha in linhas)


def test_consulta_que_falha_vira_erro_curto_sem_derrubar_as_demais():
    cliente = ClienteFalso(erro=RuntimeError("x" * 1000))
    secoes = cc.rodar(cliente, conjuntos())

    erros = [linha["resultado"] for _, linhas in secoes for linha in linhas]
    assert erros and all(e.startswith("erro: ") and len(e) < 300 for e in erros)


def test_markdown_tem_uma_secao_por_conjunto_e_escreve_no_resumo(tmp_path, monkeypatch, capsys):
    resumo = tmp_path / "resumo.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resumo))

    texto = cc.conferir(ClienteFalso(), conjuntos())

    titulos = [titulo for titulo, _ in conjuntos()]
    assert [linha for linha in texto.splitlines() if linha.startswith("## ")] == [f"## {t}" for t in titulos]
    assert "| item |" in texto
    assert resumo.read_text(encoding="utf-8") == texto + "\n"
    assert texto in capsys.readouterr().out


def test_sem_variavel_de_resumo_so_imprime(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)

    texto = cc.conferir(ClienteFalso(), conjuntos())

    assert texto in capsys.readouterr().out


def test_cada_silver_e_gold_citada_existe_em_definitions():
    citadas = set()
    for sql in todas_as_consultas():
        citadas.update(re.findall(r"`proj\.(bronze|silver|gold)\.(\w+)`", sql))
    assert {c for c in citadas if c[0] == "silver"} >= {("silver", "bcb_igpm"), ("silver", "ons_ear_bacia")}
    assert {c for c in citadas if c[0] == "gold"} >= {
        ("gold", "precipitacao_diaria_estacao"),
        ("gold", "precipitacao_diaria_bacia"),
    }
    for camada, nome in sorted(citadas):
        assert (RAIZ / "definitions" / camada / f"{nome}.sqlx").is_file(), f"{camada}.{nome} não existe"


def test_workflow_so_le_e_nao_interpola_entrada_em_run():
    texto = WORKFLOW.read_text(encoding="utf-8")
    wf = yaml.safe_load(texto)
    gatilho = wf.get("on") or wf[True]

    assert set(gatilho["workflow_dispatch"]["inputs"]) == {"environment"}
    assert gatilho["workflow_dispatch"]["inputs"]["environment"]["options"] == ["dev", "hml", "prod"]
    assert wf["permissions"] == {"contents": "read", "id-token": "write"}
    job = next(iter(wf["jobs"].values()))
    assert job["environment"] == "${{ inputs.environment }}"
    for passo in job["steps"]:
        assert "${{" not in passo.get("run", ""), passo
    assert any("scripts.conferir_cargas" in passo.get("run", "") for passo in job["steps"])
