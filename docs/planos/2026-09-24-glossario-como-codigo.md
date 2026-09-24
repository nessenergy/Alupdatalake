# Plano: glossário de negócio do Knowledge Catalog como código

**Objetivo:** declarar em `infra/modules/catalogo` os termos de `docs/glossario.md` como glossário de negócio do Knowledge Catalog (ADR 014, item 4.3, [issue #36](https://github.com/nessenergy/Alupdatalake/issues/36)), com teste que mantém o `.md` e o Terraform sincronizados.

**Arquitetura:** um `google_dataplex_glossary` por ambiente, com um `google_dataplex_glossary_term` por termo de negócio, agrupados por seção via label — sem recurso de categoria. `docs/glossario.md` continua sendo a única fonte de conteúdo; o Terraform não o lê em tempo de `apply` (ver "Confirmação do provider" e "Decisão de desenho" abaixo).

**Tecnologias:** Terraform 1.15, provider `hashicorp/google` (já em uso no módulo), pytest. Nenhuma dependência nova.

**Base de requisitos:** `docs/glossario.md`, ADR 014, `infra/modules/catalogo/main.tf` e `aspectos.tf`, `infra/main.tf` (bloco do módulo `catalogo` e `required_providers`), `tests/unit/test_catalogo.py`, tarefa 5.1 de `.superpowers/sdd/2026-09-24-fechamento-das-ondas/task-5.1-brief.md`. HEAD no início: `d6f8533`, branch `docs/plano-ondas`.

**Execução:** uma entrega, um PR. Este documento não autoriza `terraform apply` nem representa homologação.

## Confirmação do provider (passo obrigatório, antes de escrever o resto)

`infra/main.tf` fixa `hashicorp/google` em `~> 6.0`; `infra/.terraform.lock.hcl` trava a versão resolvida em `6.50.0`. Consultado o Context7 (`/hashicorp/terraform-provider-google`) e o CHANGELOG do provider (`raw.githubusercontent.com/hashicorp/terraform-provider-google/v6.37.0/CHANGELOG.md`, que acumula o histórico até essa tag) e o Terraform Registry (`registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dataplex_glossary`):

| Recurso | Provider | Adicionado em | PR |
|---|---|---|---|
| `google_dataplex_glossary` | `google` (não `google-beta`) | 6.36.0 (20/05/2025) | [#22794](https://github.com/hashicorp/terraform-provider-google/pull/22794) |
| `google_dataplex_glossary_term` | `google` | 6.37.0 | [#22835](https://github.com/hashicorp/terraform-provider-google/pull/22835) |
| `google_dataplex_glossary_category` | `google` | 6.37.0 | [#22835](https://github.com/hashicorp/terraform-provider-google/pull/22835) |

Os três existem no provider `google` padrão — não exigem `google-beta` — e a versão travada (`6.50.0`) é posterior a 6.37.0. **O recurso existe na faixa `~> 6.0` já em uso; o plano segue.**

Argumentos confirmados no Registry/Context7:

- `google_dataplex_glossary`: `glossary_id` (obrigatório na criação), `location` (obrigatório), `project`, `display_name`, `description`, `labels` (opcionais).
- `google_dataplex_glossary_term`: `parent` (obrigatório — `projects/{project}/locations/{location}/glossaries/{glossary_id}`), `location` (obrigatório), `glossary_id`, `term_id`, `display_name`, `description`, `labels`, `project` (opcionais).
- `google_dataplex_glossary_category`: mesmo formato de `parent`, mais `category_id`. Não usado neste plano — ver decisão abaixo.

## Decisão de desenho

**Local HCL literal, com teste de sincronização — não leitura do `.md`, nem `for_each` sobre variável.** As três opções do brief:

- *Leitura de `docs/glossario.md` em tempo de apply*: HCL não tem parser de Markdown; regex sobre texto de prosa em `templatefile`/`regexall` seria mais frágil do que o `.md` em si, e uma mudança de wording no documento quebraria o `apply` sem aviso claro. Descartado.
- *`for_each` sobre mapa em **variável***: moveria o conteúdo para `terraform.tfvars` ou para a chamada do módulo em `infra/main.tf`, sem ganho — ainda seria um mapa escrito à mão, só que num lugar mais distante do módulo que declara os recursos. Descartado.
- *Local HCL literal* (escolhido): um `locals.glossario_termos` dentro do próprio módulo, ao lado dos recursos que o consomem — mesmo padrão de `aspectos.tf` (enums e campos literais). A fonte da verdade continua sendo `docs/glossario.md`; o que garante que os dois não divirjam é `tests/unit/test_catalogo.py`, que extrai os termos do `.md` por seção e confere contra as chaves do `locals`. É o mesmo papel que os testes existentes já cumprem para zona↔camada e domínio↔aspecto — não introduz mecanismo novo.

**Só quatro das cinco seções do glossário viram termos do catálogo:** Instituições, Sistema e mercado, Geração, Unidades — 19 termos. A seção "Do projeto" (Medallion, Onda, Homologação, SSDLC, dry-run, `_ingestao_id` etc.) documenta o repositório e o contrato, não o dado; um termo desses no catálogo da Alup responderia a quem pergunta "o que é `submercado`" com "o que é uma Onda", o que não ajuda.

**Sem `google_dataplex_glossary_category`:** nem a ADR 014 nem o brief pedem hierarquia de categorias, e cada categoria seria mais um recurso para manter em sincronia com a mesma informação que a label `categoria` já carrega. Agrupamento por seção fica na label do termo. Menos recurso, mesmo resultado consultável.

**Ligação termo↔coluna:** nenhum dos três recursos expõe campo de vínculo a coluna/entrada do BigQuery — só `parent`, `location`, `glossary_id`/`term_id`/`category_id`, `display_name`, `description`, `labels`, `project`. A ADR 014 fala em "termos ligados às colunas que os usam"; esse vínculo não tem contraparte em `google_dataplex_glossary_term` neste provider. Fica registrado como lacuna, não implementado por invenção de campo inexistente — é trabalho de associação de entrada de metadado (`google_dataplex_entry` + *business context* ou anotação manual no console/API, fora do escopo deste `.tf`) para uma entrega futura, se a Alup pedir.

## Restrições globais

- Código (nomes de recurso, variável, chave de mapa) em inglês onde já é convenção do módulo (`glossary_id`, `term_id` são nomes de campo do provider, não traduzíveis); texto exibido (`display_name`, `description`, comentários, este documento) em português, como o resto de `infra/modules/catalogo`.
- Nada fora de `infra/`: o único arquivo novo é `infra/modules/catalogo/glossario.tf`. Teste em `tests/unit/`, documentação em `docs/`.
- TDD: o teste de sincronização é escrito e roda vermelho antes do `.tf` existir.
- Sem atribuição de IA em commit, branch, PR, comentário ou neste documento (regra 6). Branch `docs/plano-ondas` já em uso.
- Não executar `terraform apply`, não acessar o projeto GCP, não alterar horas/ondas/aceites.
- Bronze/Silver/Gold, credenciais e janelas não são tocados — este plano é só catálogo.

## Mapa de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `infra/modules/catalogo/glossario.tf` (novo) | `google_dataplex_glossary`, `locals.glossario_termos`, `google_dataplex_glossary_term` |
| `tests/unit/test_catalogo.py` | Testes de sincronização `.md` ↔ `.tf`, adicionados ao arquivo existente |
| `docs/arquitetura/decisoes/014-knowledge-catalog.md` | Adendo fechando a pendência do glossário registrada em 23/09 |
| `docs/status.md` | Registro do item concluído localmente, pendente de `apply` |

Nenhum arquivo em `infra/main.tf` muda: o módulo `catalogo` já recebe `project_id`, `region` e `environment`, que é tudo que `glossario.tf` usa.

## Tarefa única — Glossário de negócio como termos do Knowledge Catalog

**Interfaces:** módulo `catalogo` ganha um output `glossario`; nenhuma variável nova, nenhuma mudança em `main.tf` ou `aspectos.tf`.

- [ ] Acrescentar em `tests/unit/test_catalogo.py`, abaixo dos testes existentes de `aspectos.tf`, a leitura do novo arquivo e do glossário:

```python
import unicodedata

GLOSSARIO_MD = (RAIZ / "docs" / "glossario.md").read_text(encoding="utf-8")
GLOSSARIO_TF = (RAIZ / "infra" / "modules" / "catalogo" / "glossario.tf").read_text(encoding="utf-8")

SECOES_DE_NEGOCIO = ("Instituições", "Sistema e mercado", "Geração", "Unidades")


def _fatia_secao(titulo):
    """Texto de uma seção `## titulo` de docs/glossario.md, até o próximo `## `."""
    bloco = GLOSSARIO_MD.split(f"## {titulo}", 1)[1]
    return bloco.split("\n## ", 1)[0]


def _slug(texto):
    """Mesma regra usada nas chaves de `local.glossario_termos`: sem acento, minúsculo, `_` no espaço."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")
```

- [ ] Acrescentar os testes de sincronização, no mesmo arquivo:

```python
def test_todo_termo_de_negocio_do_glossario_vira_termo_do_catalogo():
    """Termo que existe em docs/glossario.md e falta aqui é busca que a Alup faz e não acha."""
    termos_no_md = {
        _slug(termo)
        for secao in SECOES_DE_NEGOCIO
        for termo in re.findall(r"^\| \*\*(.+?)\*\* \|", _fatia_secao(secao), re.MULTILINE)
    }
    chaves_no_tf = set(re.findall(r"^\s{4}([a-z][a-z0-9_]*) = \{", GLOSSARIO_TF, re.MULTILINE))

    assert termos_no_md, "nenhum termo encontrado nas quatro seções de negócio"
    assert termos_no_md == chaves_no_tf


def test_nenhum_termo_do_projeto_vaza_para_o_catalogo():
    """'Do projeto' é jargão de repositório e contrato, não vocabulário do dado."""
    termos_do_projeto = {
        _slug(termo)
        for termo in re.findall(r"^\| \*\*(.+?)\*\* \|", _fatia_secao("Do projeto"), re.MULTILINE)
    }
    chaves_no_tf = set(re.findall(r"^\s{4}([a-z][a-z0-9_]*) = \{", GLOSSARIO_TF, re.MULTILINE))

    assert not (termos_do_projeto & chaves_no_tf)


def test_cada_termo_tem_categoria_display_name_e_descricao():
    """Termo sem descrição no catálogo é pior que não ter termo: parece completo e não é."""
    chaves = re.findall(r"^\s{4}([a-z][a-z0-9_]*) = \{", GLOSSARIO_TF, re.MULTILINE)
    assert chaves
    for chave in chaves:
        entrada = re.search(rf"\n    {chave} = \{{(.*?)\n    \}}", GLOSSARIO_TF, re.DOTALL)
        assert entrada, chave
        corpo = entrada.group(1)
        assert "categoria" in corpo, chave
        assert "display_name" in corpo, chave
        assert "description" in corpo, chave


def test_o_glossario_e_os_termos_apontam_para_o_mesmo_glossary_id():
    """Termo com glossary_id diferente do glossário cria uma segunda árvore, órfã."""
    assert 'glossary_id  = "glossario-negocio"' in GLOSSARIO_TF or 'glossary_id = "glossario-negocio"' in GLOSSARIO_TF
    assert "glossary_id = google_dataplex_glossary.negocio.glossary_id" in GLOSSARIO_TF


def test_sem_recurso_de_categoria():
    """Decisão registrada no plano: agrupamento por label `categoria`, sem google_dataplex_glossary_category."""
    assert "google_dataplex_glossary_category" not in GLOSSARIO_TF
```

- [ ] Rodar `uv run pytest tests/unit/test_catalogo.py -q` e confirmar falha: `glossario.tf` ainda não existe (`FileNotFoundError` nas leituras de `GLOSSARIO_TF`).

- [ ] Criar `infra/modules/catalogo/glossario.tf`:

```hcl
# Glossário de negócio do Knowledge Catalog — ADR 014, issue #36, item 4.3 do
# plano de execução. `docs/glossario.md` é a fonte da verdade; ele não é lido
# em tempo de apply — HCL não tem parser de Markdown, e regex sobre prosa de
# terceiro seria mais frágil que manter os dois em sincronia por teste.
# `tests/unit/test_catalogo.py` extrai os termos do `.md` e confere que todos
# existem aqui, e que nenhum termo de fora das quatro seções de negócio vaza.
#
# Só entram Instituições, Sistema e mercado, Geração e Unidades. "Do projeto"
# documenta o repositório e o contrato (Onda, Homologação, SSDLC, dry-run),
# não o dado — um termo desses no catálogo confundiria quem procura o que uma
# coluna significa.
#
# Sem `google_dataplex_glossary_category`: a label `categoria` no termo
# agrupa por seção sem precisar de outro tipo de recurso para manter em
# sincronia. Nem a ADR nem o brief pedem hierarquia de categorias.

resource "google_dataplex_glossary" "negocio" {
  glossary_id  = "glossario-negocio"
  project      = var.project_id
  location     = var.region
  display_name = "Glossário de negócio — setor elétrico"
  description  = "Vocabulário operacional do setor elétrico para quem lê as views sem vir do setor. Fonte: docs/glossario.md."

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

locals {
  # Chave = term_id, mesma slugueira que test_catalogo.py aplica ao `.md`
  # (sem acento, minúsculo, espaço vira `_`). Termo novo no `.md`: acrescentar
  # aqui com a mesma regra, ou o teste de sincronização falha.
  glossario_termos = {
    aneel = {
      categoria    = "instituicoes"
      display_name = "ANEEL"
      description  = "Agência Nacional de Energia Elétrica. Regula o setor; mantém o cadastro de empreendimentos de geração (SIGA) e concede as outorgas."
    }
    ons = {
      categoria    = "instituicoes"
      display_name = "ONS"
      description  = "Operador Nacional do Sistema Elétrico. Opera o SIN em tempo real; publica carga, geração e restrições."
    }
    ccee = {
      categoria    = "instituicoes"
      display_name = "CCEE"
      description  = "Câmara de Comercialização de Energia Elétrica. Contabiliza e liquida a energia comercializada; calcula o PLD; mantém o registro dos agentes."
    }
    agente_ccee = {
      categoria    = "instituicoes"
      display_name = "Agente CCEE"
      description  = "Pessoa jurídica registrada na CCEE — gerador, comercializador, distribuidor ou consumidor livre. Cada coligada da Alup é um agente."
    }
    sin = {
      categoria    = "sistema_e_mercado"
      display_name = "SIN"
      description  = "Sistema Interligado Nacional — a rede que conecta quase toda a geração e o consumo do país."
    }
    submercado = {
      categoria    = "sistema_e_mercado"
      display_name = "Submercado"
      description  = "Subdivisão do SIN para formação de preço: SE/CO (Sudeste/Centro-Oeste), S (Sul), NE (Nordeste), N (Norte). Existem porque a transmissão entre regiões tem limite: quando ele aperta, o preço descola entre submercados. No projeto é a dimensão comum submercado, com as siglas SE, S, NE, N."
    }
    carga_de_energia = {
      categoria    = "sistema_e_mercado"
      display_name = "Carga de energia"
      description  = "O consumo verificado, por submercado e período. É o que o conector ONS/carga ingere."
    }
    pld = {
      categoria    = "sistema_e_mercado"
      display_name = "PLD"
      description  = "Preço de Liquidação das Diferenças. O preço da energia no mercado de curto prazo, por submercado e período, calculado pela CCEE. É a referência de quanto vale a energia que sobra ou falta em relação ao contratado."
    }
    cmo = {
      categoria    = "sistema_e_mercado"
      display_name = "CMO"
      description  = "Custo Marginal de Operação — quanto custa produzir o próximo MWh. Calculado pelo ONS; é a base do PLD."
    }
    mercado_de_curto_prazo = {
      categoria    = "sistema_e_mercado"
      display_name = "Mercado de curto prazo"
      description  = "Onde se liquida a diferença entre o que foi contratado e o que foi de fato gerado ou consumido, ao PLD."
    }
    ceg = {
      categoria    = "geracao"
      display_name = "CEG"
      description  = "Código Único de Empreendimento de Geração. Identificador da usina no cadastro da ANEEL — no projeto, a dimensão comum codigo_usina."
    }
    outorga = {
      categoria    = "geracao"
      display_name = "Outorga"
      description  = "A autorização ou concessão da ANEEL para gerar energia. Potência outorgada é o que foi autorizado; potência fiscalizada é o que a ANEEL verificou instalado."
    }
    garantia_fisica = {
      categoria    = "geracao"
      display_name = "Garantia física"
      description  = "Quanto de energia uma usina pode comercializar em contrato de longo prazo — não é a mesma coisa que sua potência instalada, e é o número que limita a venda."
    }
    fase_da_usina = {
      categoria    = "geracao"
      display_name = "Fase da usina"
      description  = "Onde o empreendimento está: Operação, Construção, Construção não iniciada. Diferencia parque existente de expansão."
    }
    tipos = {
      categoria    = "geracao"
      display_name = "Tipos"
      description  = "UHE hidrelétrica · PCH pequena central hidrelétrica · CGH central geradora hidrelétrica · EOL eólica · UFV solar fotovoltaica · UTE térmica."
    }
    mw = {
      categoria    = "unidades"
      display_name = "MW"
      description  = "Potência instantânea."
    }
    mwh = {
      categoria    = "unidades"
      display_name = "MWh"
      description  = "Energia — potência × tempo."
    }
    mwmed = {
      categoria    = "unidades"
      display_name = "MWmed"
      description  = "MW médio: a energia de um período dividida pelo tempo dele. 1 MWmed ao longo de um mês de 30 dias equivale a 720 MWh. O ONS publica carga em MWmed, e é a unidade das views de carga."
    }
    kw = {
      categoria    = "unidades"
      display_name = "kW"
      description  = "Mil watts. O cadastro da ANEEL publica potência em kW; a Gold converte para MW dividindo por 1.000."
    }
  }
}

resource "google_dataplex_glossary_term" "termo" {
  for_each = local.glossario_termos

  parent      = "projects/${var.project_id}/locations/${var.region}/glossaries/${google_dataplex_glossary.negocio.glossary_id}"
  glossary_id = google_dataplex_glossary.negocio.glossary_id
  project     = var.project_id
  location    = var.region
  term_id     = each.key

  display_name = each.value.display_name
  description  = each.value.description

  labels = {
    projeto   = "alupdata"
    ambiente  = var.environment
    categoria = each.value.categoria
  }
}

output "glossario" {
  description = "Glossário de negócio declarado e a contagem de termos"
  value = {
    glossary_id = google_dataplex_glossary.negocio.glossary_id
    termos      = length(local.glossario_termos)
  }
}
```

- [ ] Rodar `uv run pytest tests/unit/test_catalogo.py -q` e confirmar que os cinco testes novos, mais os já existentes do arquivo, passam.
- [ ] Rodar `terraform -chdir=infra fmt -recursive` para alinhar o `=` dos blocos (o teste de sincronização não depende de alinhamento, mas `fmt -check` sim) e então `terraform -chdir=infra fmt -check -recursive` para confirmar.
- [ ] Rodar `terraform -chdir=infra init -backend=false` (baixa o provider `6.50.0` já travado no lock, sem backend GCS) e, se o `init` concluir, `terraform -chdir=infra validate`. Se o ambiente não tiver acesso de rede para baixar o provider, registrar isso no lugar do resultado — não é bloqueio deste plano, é limitação do ambiente de execução local.
- [ ] Acrescentar o adendo em `docs/arquitetura/decisoes/014-knowledge-catalog.md`, logo após o "Adendo de 2026-09-23", registrando que o glossário de negócio passou a ser declarado em `infra/modules/catalogo/glossario.tf`, com as 19 entradas das quatro seções de vocabulário do setor elétrico, a decisão de não usar `google_dataplex_glossary_category`, e a lacuna do vínculo termo↔coluna (sem campo correspondente no provider). Referenciar a issue #36 como fechada por este item.
- [ ] Atualizar `docs/status.md`: mover o item do glossário de "pendente" para "declarado em código, validado localmente; `apply` pendente do ambiente da Alup" — mesma distinção usada no plano de 18/09 para os outros reparos.
- [ ] Validar a mensagem de commit antes de commitar: `python scripts/verifica_atribuicao.py <arquivo-da-mensagem>`.
- [ ] Commit: `feat(catalogo): glossario de negocio como termos do knowledge catalog`.

**Aceite local:** os cinco testes novos de `test_catalogo.py` passam; `terraform fmt -check` e, se possível no ambiente, `terraform validate` aprovam; ADR 014 e `docs/status.md` refletem o estado. **Aceite posterior em GCP:** `apply` cria o glossário e os 19 termos no Knowledge Catalog do projeto; a Alup consegue buscar um termo (ex. "PLD") e ver a descrição e a categoria. Pendente da liberação do ambiente pela Alup — este plano não autoriza `apply`.

## Referências técnicas consultadas

- [google_dataplex_glossary — Terraform Registry, provider hashicorp/google](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dataplex_glossary)
- [google_dataplex_glossary_term — Terraform Registry](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dataplex_glossary_term)
- [google_dataplex_glossary_category — Terraform Registry](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dataplex_glossary_category)
- CHANGELOG do provider (`terraform-provider-google`, tag `v6.37.0`): `google_dataplex_glossary` adicionado em 6.36.0 ([PR #22794](https://github.com/hashicorp/terraform-provider-google/pull/22794), mesclado em 20/05/2025); `google_dataplex_glossary_term` e `google_dataplex_glossary_category` adicionados em 6.37.0 ([PR #22835](https://github.com/hashicorp/terraform-provider-google/pull/22835)).
- `infra/.terraform.lock.hcl`: versão resolvida do provider `google` no repositório é `6.50.0`, acima da versão mínima que introduz os três recursos.
- Consulta via Context7 (`/hashicorp/terraform-provider-google`) confirmou os argumentos de `parent`, `location`, `glossary_id`/`term_id`/`category_id`, `display_name`, `description`, `labels`, `project` e `deletion_policy` para `google_dataplex_glossary_term` e `google_dataplex_glossary_category`.
