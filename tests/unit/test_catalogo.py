"""Knowledge Catalog: lake, zonas e ativos sobre o que já existe (ADR 014).

O catálogo é metadado — não copia dado e não deveria custar. O que custa é a
varredura de descoberta, cobrada por unidade de processamento, e o teto da E2
é de US$ 20/mês até novembro. Estes testes prendem as duas coisas que um apply
distraído desfaria: a descoberta desligada e a correspondência entre zona e
camada da arquitetura.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MODULO = (RAIZ / "infra" / "modules" / "catalogo" / "main.tf").read_text(encoding="utf-8")


def test_descoberta_nasce_desligada():
    """Varredura ligada paga para adivinhar o esquema que o Dataform declara."""
    variavel = MODULO.split('variable "descoberta_ativa"')[1].split("}")[0]
    assert "default     = false" in variavel

    blocos = re.findall(r"discovery_spec \{\s*enabled = ([^\s}]+)", MODULO)
    assert blocos, "nenhum discovery_spec encontrado"
    assert set(blocos) == {"var.descoberta_ativa"}, "descoberta fora da variável escapa do controle de custo"


def test_uma_zona_por_camada_medallion():
    """Zona que não corresponde a camada deixa o catálogo contando outra história."""
    zonas = dict(re.findall(r"(bronze|silver|gold)\s*=\s*\{ tipo = \"(RAW|CURATED)\"", MODULO))

    assert zonas == {"bronze": "RAW", "silver": "CURATED", "gold": "CURATED"}


def test_o_nome_da_zona_nao_colide_com_dataset_nosso():
    """A zona cria um dataset com o próprio ID, e `bronze` e `gold` já são nossos.

    Sem o prefixo, o apply reprova com "Zone ID 'bronze' ... is already taken"
    — e só no fim, depois de já ter criado o lake.
    """
    assert 'name         = "camada-${each.key}"' in MODULO


def test_ativos_apontam_para_o_que_o_infra_ja_declara():
    """Ativo é ponteiro. Nome inventado aqui vira ativo em erro no console."""
    assert 'type = "BIGQUERY_DATASET"' in MODULO
    assert 'type = "STORAGE_BUCKET"' in MODULO
    assert "var.datasets_por_camada" in MODULO
    assert "var.dataset_qualidade" in MODULO
    assert "var.bucket_raw" in MODULO

    principal = (RAIZ / "infra" / "main.tf").read_text(encoding="utf-8")
    bloco = principal.split('module "catalogo"')[1].split("}")[0]
    assert "module.bigquery.dataset_ids" in bloco
    assert "module.storage.bucket_raw" in bloco


def test_o_agente_do_dataplex_recebe_acesso():
    """Sem o agente, o ativo nasce em erro e ninguém repara até abrir o console."""
    assert "google_project_service_identity" in MODULO
    assert "roles/dataplex.serviceAgent" in MODULO


ASPECTOS = (RAIZ / "infra" / "modules" / "catalogo" / "aspectos.tf").read_text(encoding="utf-8")


def test_o_aspecto_que_separa_texto_curado_de_gerado():
    """A ADR 014 ativou a IA do catálogo com uma condição: marcar o que ela escreve.

    Sem a marca, sugestão do serviço vira documentação com a mesma autoridade
    do que uma pessoa revisou.
    """
    assert '"curada"' in ASPECTOS or '"curada"' in ASPECTOS.replace("'", '"')
    assert "automatica" in ASPECTOS
    assert "revisada_em" in ASPECTOS


def test_os_oito_dominios_do_b1_estao_no_aspecto():
    """Domínio que falta aqui é dado que o catálogo não sabe de quem é."""
    for dominio in (
        "mercado_de_energia",
        "geracao_e_operacional",
        "meteorologia",
        "comercial_e_contratos",
        "crm_e_marketing",
        "risco_e_compliance",
        "economico",
        "planejamento",
    ):
        assert dominio in ASPECTOS, f"domínio {dominio} fora do aspect type"
