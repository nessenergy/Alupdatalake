"""Fluxo da Onda 3: ingerir as fontes internas, depois transformar (ADR 017).

O fluxo é YAML gerado por `templatefile`, e YAML quebrado só aparece no
`gcloud workflows deploy` — tarde, e com a cadeia já configurada. Estes testes
cobram a estrutura: que o documento seja YAML válido depois de renderizado, que
os passos existam e que o encadeamento de `next` aponte para passo que existe.

O que eles **não** provam é semântica de Cloud Workflows — conector, sintaxe de
expressão, comportamento de `parallel`. Isso só o primeiro deploy com cadeia
real responde, e a cadeia depende de VPN e credencial (A7).
"""

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML acompanha o Dataform; sem ele, o teste não se aplica")

RAIZ = Path(__file__).resolve().parents[2]
MODULO = RAIZ / "infra" / "modules" / "orquestracao"

VALORES = {
    "projeto": "alupar-dev-alupdata",
    "regiao": "us-central1",
    "jobs": '["ingestao-fmb-contrato", "ingestao-rm-centro-custo"]',
    "repositorio": "projects/alupar-dev-alupdata/locations/us-central1/repositories/alupdata",
    "service_account_dataform": "alupdata-dataform@alupar-dev-alupdata.iam.gserviceaccount.com",
    "timeout_ingestao": "1800",
}


def renderizar() -> str:
    """Emula `templatefile`: `$${x}` vira `${x}`; `${x}` vira o valor."""
    texto = (MODULO / "onda3.yaml.tftpl").read_text(encoding="utf-8")
    marca = "\x00"
    texto = texto.replace("$${", marca)
    texto = re.sub(r"\$\{(\w+)\}", lambda m: VALORES[m.group(1)], texto)
    texto = re.sub(r"\$\{jsonencode\((\w+)\)\}", lambda m: VALORES[m.group(1)], texto)
    return texto.replace(marca, "${")


def passos() -> dict[str, dict]:
    documento = yaml.safe_load(renderizar())
    return {nome: corpo for passo in documento["main"]["steps"] for nome, corpo in passo.items()}


def test_o_fluxo_e_yaml_valido_depois_de_renderizado():
    assert passos(), "o fluxo não produziu passo algum"


def test_ingere_antes_de_transformar():
    """A ordem é a razão de o fluxo existir.

    Dataform rodando sobre carga incompleta produz Gold errada em silêncio.
    """
    nomes = list(passos())
    assert nomes.index("ingestoes") < nomes.index("compilar") < nomes.index("invocar")


def test_espera_o_dataform_terminar():
    """Sem o laço, o fluxo dá sucesso no instante em que pede a execução."""
    fluxo = passos()
    assert fluxo["pausa"]["call"] == "sys.sleep"
    condicoes = fluxo["decidir"]["switch"]
    assert any(c["next"] == "execucao_reprovada" for c in condicoes)
    assert fluxo["decidir"]["next"] == "pausa", "sem voltar para a pausa, o laço não existe"
    assert "raise" in fluxo["execucao_reprovada"]


def test_todo_next_aponta_para_passo_que_existe():
    """`next` para passo inexistente é erro de implantação, não de execução."""
    fluxo = passos()
    conhecidos = set(fluxo) | {"end", "continue", "break"}

    for nome, corpo in fluxo.items():
        alvos = [corpo["next"]] if isinstance(corpo, dict) and "next" in corpo else []
        for condicao in (corpo.get("switch") or []) if isinstance(corpo, dict) else []:
            alvos += [condicao["next"]] if "next" in condicao else []
        for alvo in alvos:
            assert alvo in conhecidos, f"passo `{nome}` aponta para `{alvo}`, que não existe"


def test_nada_sobe_enquanto_a_cadeia_estiver_vazia():
    """Fonte interna depende de VPN e credencial; até lá, custo zero."""
    codigo = (MODULO / "main.tf").read_text(encoding="utf-8")
    assert 'length(var.cadeia) > 0 && var.repositorio_dataform != "" ? 1 : 0' in codigo
    for recurso in re.findall(r'resource "(google_\w+)" "(\w+)" \{\n((?:.|\n)*?)\n\}', codigo):
        corpo = recurso[2]
        assert "count" in corpo or "for_each" in corpo, f"{recurso[1]} sobe mesmo sem cadeia"
