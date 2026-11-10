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


def test_conferencia_mostra_o_erro_da_ultima_execucao_com_falha():
    """A conta de deploy não lê o Cloud Logging, mas lê `_execucoes.erro`: a causa de uma falha aparece aqui."""
    consultas = {item.rotulo: item.sql for _, itens in conjuntos() for item in itens}
    sql = consultas["ultimo_erro"]
    cc.validar_sql(sql)
    assert "erro IS NOT NULL" in sql
    assert "INTERVAL 3 DAY" in sql
    assert "`proj.bronze._execucoes`" in sql
    assert "SUBSTR(erro, 1, 200)" in sql


def test_conferencia_nomeia_as_fontes_fora_do_ok():
    """A contagem por situação não diz qual fonte falha: este item lista o conector."""
    consultas = {item.rotulo: item.sql for _, itens in conjuntos() for item in itens}
    sql = consultas["saude_fora_do_ok"]
    cc.validar_sql(sql)
    assert "`proj.gold.saude_ingestao`" in sql
    assert "situacao != 'OK'" in sql
    assert "conector" in sql


def test_texto_de_erro_vindo_do_bigquery_passa_pelo_sanitizador():
    """O erro gravado pela ingestão vai para o resumo do GitHub: nada que pareça credencial pode sair."""
    cliente = ClienteFalso(linhas=[{"conector": "x", "erro": "falhou com Bearer abc123segredo e mais texto"}])
    secoes = cc.rodar(cliente, [("Erros", [cc.Item("ultimo_erro", "SELECT 1")])])
    texto = str(secoes)
    assert "abc123segredo" not in texto
    assert "[REDACTED]" in texto


def test_conferencia_mostra_os_negocios_do_hubspot_em_quarentena_sem_vazar_valor():
    itens = {item.rotulo: item.sql for _, lista in conjuntos() for item in lista}

    contagem = itens["hubspot_negocios_fora_da_regra"]
    assert "hubspot_negocios_quarentena" in contagem
    assert "valor_negativo" in contagem
    assert "fechamento_antes_da_criacao" in contagem

    lista = itens["hubspot_negocios_reprovados"]
    assert "hubspot_negocios_quarentena" in lista
    assert "negocio_id" in lista and "LIMIT 50" in lista
    colunas_escolhidas = lista.split(" FROM ")[0]
    for dado_do_cliente in ("valor,", "nome", "email", "proprietario"):
        assert dado_do_cliente not in colunas_escolhidas


def test_silver_e_quarentena_do_hubspot_dividem_a_mesma_regra():
    """O que a Silver recusa tem de ser exatamente o que a quarentena mostra, senão negócio some sem rastro."""
    silver = (RAIZ / "definitions" / "silver" / "hubspot_negocios.sqlx").read_text(encoding="utf-8")
    quarentena = (RAIZ / "definitions" / "qualidade" / "hubspot_negocios_quarentena.sqlx").read_text(encoding="utf-8")

    for regra in ("valor IS NULL OR valor >= 0", "data_fechamento IS NULL OR data_fechamento >= DATE(criado_em)"):
        assert silver.count(regra) == 2, "a regra vale na asserção e no filtro da Silver"
        assert regra in quarentena
    assert "valor_negativo" in quarentena and "fechamento_antes_da_criacao" in quarentena
    assert "uniqueKey" not in quarentena, "a quarentena espera ter linhas; só a Silver carrega asserções"


# Silvers que a conferência por contagem de linhas não cobre. Elas são acompanhadas pela `gold.saude_ingestao`
# (frescor e erro por fonte), e o teste abaixo obriga a decidir sobre toda Silver nova: entra em `SILVER` ou entra aqui.
EXCECOES_DA_CONFERENCIA = frozenset(
    {
        "aneel_siga",
        "bcb_cambio_ptax",
        "bcb_juros",
        "ccee_agente",
        "ccee_consumo_classe_agente",
        "ccee_contabilizacao_perfil",
        "ccee_contabilizacao_perfil_historico",
        "ccee_contrato_montante",
        "ccee_cvu_conjuntural",
        "ccee_cvu_conjuntural_revisado",
        "ccee_cvu_estrutural",
        "ccee_cvu_merchant",
        "ccee_encargo_ess",
        "ccee_energia_reserva",
        "ccee_energia_reserva_consumo_referencia",
        "ccee_exposicao_financeira",
        "ccee_geracao_usina",
        "ccee_perfil",
        "ccee_pi_medida",
        "ccee_pi_ponto_medicao",
        "ccee_pld",
        "ccee_reserva_encargo",
        "ccee_varejista_consumidor",
        "hubspot_negocios",
        "ibge_ipca",
        "ons_balanco_energia",
        "ons_capacidade",
        "ons_carga",
        "ons_cmo_semi_horario",
        "ons_cvu_termica",
        "ons_disponibilidade_usina",
        "ons_ear",
        "ons_ear_bacia",
        "ons_ear_reservatorio",
        "ons_ena",
        "ons_ena_bacia",
        "ons_ena_reservatorio",
        "ons_geracao_exportacao",
        "ons_geracao_usina",
        "ons_intercambio_internacional",
        "ons_intercambio_nacional",
        "ons_restricao_coff_eolica",
        "ons_restricao_coff_fotovoltaica",
        "ons_volume_espera",
    }
)


def test_toda_silver_esta_na_conferencia_ou_na_lista_de_excecoes():
    """Fonte nova sem entrada na conferência passaria despercebida; a exceção tem de ser escrita."""
    silvers = {p.stem for p in (RAIZ / "definitions" / "silver").glob("*.sqlx")}
    assert silvers - set(cc.SILVER) - EXCECOES_DA_CONFERENCIA == set()
    assert not EXCECOES_DA_CONFERENCIA & set(cc.SILVER), "fonte na lista e na exceção ao mesmo tempo"
    assert silvers >= EXCECOES_DA_CONFERENCIA, "exceção de Silver que não existe mais"


def test_bbce_entra_com_silver_gold_e_log_de_execucoes():
    sql = " ".join(i.sql for _, itens in cc.montar_conjuntos("p", "bronze", "silver", "gold") for i in itens)
    assert "`p.silver.bbce_curva_forward`" in sql
    assert "`p.gold.curva_forward_vigente`" in sql
    assert "'bbce_curva_forward'" in sql
