# Plano de fechamento das ondas, com o GCP liberado

> **Para quem executa:** siga as fases em ordem. Dentro de cada fase, as
> tarefas marcadas *paralela* podem andar juntas. Os passos usam checkbox
> (`- [ ]`) para acompanhamento. Tarefa com código novo abre plano próprio,
> nomeado na própria tarefa, **quando a fase começar**. Antes disso a
> especificação dela não existe.

**Objetivo:** levar as cinco ondas a dossiê de homologação no menor prazo que
o insumo da Alup permite. A Onda 0, vencida, fecha primeiro. As seguintes
fecham antes da data contratual sempre que o insumo chegar a tempo.

**Arquitetura:** nada muda na arquitetura. O `dev` está provisionado desde
23/09 e o Dataform subiu em 24/09. O que falta é **operação com evidência**:
carga real, replay, Portal com dado, uma janela de homologação em `hml` e o
dossiê de cada onda. Código novo aparece só onde a fase exige: glossário do
catálogo, templates de planilha e as fontes internas.

**Ferramentas:** `gcloud`, `bq`, o workflow `Deploy GCP` (GitHub Actions), a
CLI `alupdata` dentro dos Cloud Run Jobs, o Terraform 1.15 e a skill
`homologacao-onda`.

**Base:** [`contrato/resumo-contrato.md`](../contrato/resumo-contrato.md)
(cronograma e marcos), [`plano-execucao.md`](../plano-execucao.md) (escopo
por onda), [`status.md`](../status.md) e
[`acoes-humanas.md`](../acoes-humanas.md). Nenhuma especificação separada:
os critérios de aceite são os da skill `homologacao-onda`.

## Restrições globais

- As seis regras do [`AGENTS.md`](../../AGENTS.md) valem para todas as
  tarefas: 7 componentes por fonte, credencial só no Secret Manager, ingestão
  por janela, Bronze append-only, nada fora de `infra/` e nenhuma atribuição
  de IA no que se publica.
- **Homologação é aceite da Alup.** Este plano entrega dossiê e pede aceite.
  Nenhuma onda é declarada homologada por nós.
- Prazo de insumo, atraso e efeito contratual são **registrados com data**.
  Postergação, ociosidade e cobrança ficam com a coordenação da ness.
- Acesso de pessoas só por grupo (R01): `group:` ou `domain:`, nunca `user:`.
- `hml` fica com `agendamentos_ativos = false` fora da janela de
  homologação, por causa do teto de custo da E2 (US$ 20/mês até novembro).
- Mensagem à Alup, e-mail ou comentário em issue é ação externa. Quem executa
  confirma com a coordenação antes de enviar.
- Branch por assunto (`docs/…`, `feat/…`, `chore/…`), PR para `main` e
  worktree em `C:/Users/resper/worktrees/`.

---

## 1. Onde estamos em 24/09

| Onda | Prazo contratual | Situação técnica | O que falta para o dossiê |
|---|---|---|---|
| **0 — Fundação** | **11/09 — vencida** | tudo entregue; `dev` provisionado (159 recursos), Dataform de pé, Portal publicado atrás do IAP | 3 dias seguidos de `SUCESSO`, replay contra o GCS real, Portal mostrando uma Gold real |
| **1 — Mercado base** | 16/10 | as 23 fontes públicas escritas e testadas contra as APIs reais em dry-run; Gold do domínio de mercado escrita | carga real de cada uma, Gold com linha, aplicação em `hml` |
| **2 — APIs credenciadas** | 13/11 | os 4 conectores escritos; TempoOK ENA com token no Secret Manager | credencial do Hubspot e do BBCE, acervo do TempoOK e a decisão sobre o item 2.1 |
| **3 — Sistemas internos** | 18/12 | caminho de banco (ADR 008) e orquestração (Workflows) prontos | VPN e credenciais read-only das quatro fontes (A7) |
| **4 — Planilhas e handoff** | 08/01/2027 (22/01 com recesso) | motor S2 Data Intake pronto; lake, zonas e *aspect types* do catálogo aplicados | exemplos de planilha (G3), glossário, anotações e handoff |

**A Onda 0 é a única em atraso**, e o atraso tem causa registrada: A3 venceu
em 04/09 e foi atendida em 23/09, 12 dias úteis depois. A cláusula 3ª
posterga o cronograma. A nova data formal fica com a coordenação. Aqui só
se registra quando a ness. consegue entregar.

## 2. Cronograma proposto

| Onda | Dossiê entregue à Alup | Prazo contratual | Diferença | Condição |
|---|---|---|---|---|
| 0 | **30/09** | 11/09 (postergado por A3) | — | nenhuma além da carga |
| 1 | **07/10** | 16/10 | **6 dias úteis antes** | a janela de `hml` aberta em 30/09 |
| 2 | **23/10** | 13/11 | **14 dias úteis antes** | Hubspot e BBCE no Secret Manager até **12/10** |
| 3 | chegada da última credencial **+ 5 semanas** | 18/12 | até cerca de 3 semanas e meia antes | com tudo em 19/10, dossiê em **23/11** |
| 4 | dossiê da Onda 3 **+ 1 semana** | 08/01/2027 | até 6 semanas antes | planilhas no bucket até **01/10**; o resto adiantado nas fases 4 e 5 |

As datas das Ondas 2 a 4 **são condicionais**, e a condição é o insumo da
coluna da direita. Se o insumo atrasa, a data do dossiê anda junto; atraso da
Alup só se registra depois do prazo contratual (19/10 Onda 2, 16/11 Onda 3,
21/12 Onda 4).

## 3. Mapa de arquivos

| Arquivo | Muda em | Para quê |
|---|---|---|
| `infra/environments/dev.tfvars` | Fase 1 | `portal_acesso` com o grupo da ness., para validar o Portal com dado real |
| `infra/environments/hml.tfvars` | Fases 2 e 3 | `agendamentos_ativos` na janela de homologação e os grupos da Alup |
| `docs/relatorios/2026-09-30-dossie-onda-0.md` (+ `.html`) | Fase 1 | dossiê da Onda 0 |
| `docs/relatorios/2026-10-07-dossie-onda-1.md` (+ `.html`) | Fase 3 | dossiê da Onda 1 |
| `docs/status.md`, `docs/proximos-passos.md`, `docs/plano-semanal.md` | ao fim de cada fase | registrar o que fechou |
| `docs/planos/2026-09-24-glossario-como-codigo.md` | Fase 5 | plano próprio do glossário |
| `docs/planos/<data>-templates-de-planilha.md` | Fase 5 | plano próprio dos templates |
| `docs/planos/<data>-fonte-<nome>.md` | Fase 6 | um plano por fonte interna |

---

## Fase 0 — Conferir a primeira carga (25/09)

### Tarefa 0.1: Reautenticar e ler o `_execucoes`

**Dono:** ness. (humano para o login, qualquer um para a leitura)

- [ ] **Passo 1: Reautenticar o `gcloud` na conta da ness.** O token local
  expirou em 24/09.

```bash
gcloud auth login resper@ness.com.br
gcloud auth application-default login --account=resper@ness.com.br
```

- [ ] **Passo 2: Ler as execuções desde 24/09**

```bash
bq --project_id=alupar-dev-alupdata query --use_legacy_sql=false --format=pretty '
SELECT fonte, entidade, modo, status,
       DATE(iniciada_em, "America/Sao_Paulo") AS dia,
       linhas_carregadas, erro
FROM bronze._execucoes
WHERE DATE(iniciada_em, "America/Sao_Paulo") >= "2026-09-24"
ORDER BY iniciada_em'
```

Esperado: `bcb/cambio_ptax`, `bcb/juros`, `ons/carga`, `ons/ear`, `ons/ena`
e `tempook/ena_prevs` com `SUCESSO` em 25/09; `tempook/boletins` com
`SUCESSO` e 0 linha (acervo, A10); `hubspot` e `bbce` com `ERRO` de
credencial ausente, que é esperado.

- [ ] **Passo 3: Conferir o Dataform das 11h**

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://dataform.googleapis.com/v1/projects/alupar-dev-alupdata/locations/us-central1/repositories/alupdata/workflowInvocations?pageSize=5" \
  | grep -E '"(name|state|createTime)"'
```

Esperado: a invocação de 25/09 da *workflow config* `diario` com estado
`SUCCEEDED`. Qualquer ação reprovada vira tarefa de correção com teste
antes da Fase 1, com o mesmo padrão do
[#208](https://github.com/nessenergy/Alupdatalake/pull/208).

- [ ] **Passo 4: Registrar em `status.md`** a data e o resultado da primeira
  carga agendada, com o ID de uma execução por fonte.

---

## Fase 1 — Fechar a Onda 0 (25/09 → 30/09)

### Tarefa 1.1: Três dias seguidos de `SUCESSO` *(corre sozinha)*

**Critério do plano 0.14:** 3 dias consecutivos com `status = SUCESSO` em
`bronze._execucoes`. Os jobs diários do BCB já estão agendados.

- [ ] **Passo 1: Em 28/09, rodar a consulta de continuidade**

```bash
bq --project_id=alupar-dev-alupdata query --use_legacy_sql=false --format=pretty '
SELECT fonte, entidade, DATE(iniciada_em, "America/Sao_Paulo") AS dia,
       LOGICAL_AND(status = "SUCESSO") AS dia_limpo,
       SUM(linhas_carregadas) AS linhas
FROM bronze._execucoes
WHERE modo = "FONTE" AND fonte = "bcb"
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3'
```

Esperado: `dia_limpo = true` em três dias seguidos para `cambio_ptax` e
`juros`. Fim de semana conta: o BCB não publica, a janela de 3 e 5 dias
cobre a sexta, e a execução termina `SUCESSO`. Se algum dia falhar, a
contagem recomeça no dia seguinte e a data do dossiê anda junto.

- [ ] **Passo 2: Guardar a saída** para o dossiê (Tarefa 1.4).

### Tarefa 1.2: Replay contra o GCS real *(paralela)*

**Critério:** reprocessamento demonstrado em uma fonte, sem nova chamada à
origem (N4).

- [ ] **Passo 1: Achar um objeto raw de uma execução `SUCESSO`**

```bash
gcloud storage ls "gs://alupar-dev-alupdata-raw/bcb/cambio_ptax/" --recursive | head
```

- [ ] **Passo 2: Executar o replay pelo workflow `Executar ingestão`.** Pessoa
  não executa Cloud Run Job; o workflow roda com a SA de deploy. Troque
  `<objeto>` pelo URI do passo 1, e `<de>`/`<ate>` pela janela original dessa
  execução, que está em `_execucoes`.

```bash
gh workflow run "Executar ingestão" -f environment=dev -f conector=bcb_cambio_ptax \
  -f uri=<objeto> -f de=<de> -f ate=<ate>
```

- [ ] **Passo 3: Conferir a linha de replay**

```bash
bq --project_id=alupar-dev-alupdata query --use_legacy_sql=false --format=pretty '
SELECT ingestao_id, modo, origem_ingestao_id, status, linhas_carregadas
FROM bronze._execucoes WHERE modo = "REPLAY" ORDER BY iniciada_em DESC LIMIT 1'
```

Esperado: `modo = REPLAY`, `origem_ingestao_id` igual ao `ingestao_id` da
execução que gerou o objeto raw (é o nome do arquivo) e `status = SUCESSO`.
Na Silver, o total de linhas da janela não muda, porque a deduplicação
absorve a recarga.

### Tarefa 1.3: Portal mostrando uma Gold real *(paralela)*

**Critério do plano 0.15:** login funcionando e uma tabela Gold visível.
Hoje ninguém passa pelo IAP, porque `portal_acesso` está vazio. Para validar
em `dev` entra o grupo da ness. que já opera o ambiente. O grupo da Alup
entra em `hml` (Tarefa 2.1).

- [ ] **Passo 1: Acrescentar o grupo em `infra/environments/dev.tfvars`**,
  logo abaixo de `leitura_projeto`:

```hcl
# Validação do Portal com dado real (Onda 0). O grupo da Alup entra em hml.
portal_acesso = ["group:operacao-datalake@ness.com.br"]
```

- [ ] **Passo 2: Validar e testar**

```bash
terraform -chdir=infra fmt -check -recursive
uv run pytest tests/unit/test_infra.py -q
```

Esperado: formato limpo e os testes passando. A validação da variável já
recusa `user:`.

- [ ] **Passo 3: Commit, PR e, depois do merge, deploy em `dev`.** O
  módulo `infra` sozinho exige `image_sha`; `all` reconstrói a imagem do
  mesmo commit e dispensa o parâmetro.

```bash
git add infra/environments/dev.tfvars
git commit -m "feat(infra): o grupo de operacao passa pelo IAP do Portal em dev"
gh workflow run "Deploy GCP" -f environment=dev -f module=all
```

- [ ] **Passo 4: Abrir o Portal, entrar com a conta da ness. e capturar a
  tela de `juros_mensal`**, com data e URL visíveis. A captura vai para o
  dossiê.

### Tarefa 1.4: Dossiê da Onda 0

**Depende de:** 1.1, 1.2 e 1.3. **Entrega:** 30/09.

- [ ] **Passo 1: Carregar a skill `homologacao-onda`** e preencher o
  checklist "Uma onda está pronta quando" com uma evidência por linha:

| Linha do checklist | Evidência |
|---|---|
| 7 componentes (BCB, fonte de referência) | caminhos dos arquivos no repositório |
| Portões de segurança | execução do CI na `main` do dia, com o link |
| Recursos em `infra/` e aplicados | saída de `terraform plan` sem mudança em `dev` |
| Dicionário e linhagem | `docs/dicionario-dados/bcb_cambio_ptax.md` |
| Reprocessamento | saída da Tarefa 1.2 |
| 3 dias de `SUCESSO` | saída da Tarefa 1.1 |
| Portal com login e Gold | captura da Tarefa 1.3 |
| 8 domínios e dimensões comuns | `docs/arquitetura/dominios-analiticos.md`, `visao-geral.md` |
| RACI e data owners | `docs/raci.md`, `docs/interlocutores.md` |
| `make all` verde | saída de `make all` na `main` do dia |
| Agendamento executando | captura do Cloud Scheduler do `dev` com a última execução dos jobs do BCB |

- [ ] **Passo 2: Escrever `docs/relatorios/2026-09-30-dossie-onda-0.md`** no
  formato dos outros relatórios e gerar o HTML:

```bash
uv run --with markdown python scripts/gerar_documento.py docs/relatorios/2026-09-30-dossie-onda-0.md --html
```

- [ ] **Passo 3: Indexar em `docs/relatorios/README.md`, commit e PR.**
- [ ] **Passo 4: Entregar à Alup e pedir o aceite.** Ação externa, feita pela
  coordenação.

---

## Fase 2 — Abrir a janela de homologação em `hml` (30/09)

Uma janela só para as Ondas 0 e 1 custa menos que duas. Os jobs agendados em
`hml` custam cerca de US$ 3/mês, dentro do teto da E2.

### Tarefa 2.1: Aplicar o `infra/` em `hml`

**Depende de:** os grupos da Alup (Leonardo). Se não chegarem até 29/09, a
janela abre sem `portal_acesso` e a validação do Portal com a Alup acontece
por tela compartilhada, com registro no dossiê.

- [ ] **Passo 1: Editar `infra/environments/hml.tfvars`**

```hcl
agendamentos_ativos = true # janela de homologação das Ondas 0 e 1, aberta em 30/09

grupo_consumidores = "<grupo-consumidores>@<dominio-da-alup>"
grupo_operacao     = "<grupo-operacao>@<dominio-da-alup>"
portal_acesso      = ["group:<grupo-consumidores>@<dominio-da-alup>"]
```

Os `<…>` são os e-mails que a Alup informar. Sem eles, as três linhas de
grupo ficam comentadas, como hoje.

- [ ] **Passo 2: Validar, commit e PR**

```bash
terraform -chdir=infra fmt -check -recursive
uv run pytest tests/unit/test_infra.py -q
git add infra/environments/hml.tfvars
git commit -m "feat(infra): abre a janela de homologacao das Ondas 0 e 1 em hml"
```

- [ ] **Passo 3: Gravar o token do Dataform em `hml`**, pelo mesmo caminho
  de `acoes-humanas.md` §1, no projeto `alupar-hm-alupdata`, e apontar
  `DATAFORM_GIT_TOKEN_VERSAO=1` no ambiente `hml` do GitHub.
- [ ] **Passo 4: Deploy `all` em `hml`**

```bash
gh workflow run "Deploy GCP" -f environment=hml -f module=all
```

Esperado: o `apply` cria o mesmo conjunto do `dev` e o Dataform termina
`SUCCEEDED`. O `apply` do `dev` revelou quatro defeitos, então este pode
revelar algum específico de `hml`. Nesse caso, a correção vem com teste antes
de repetir.

- [ ] **Passo 5: Ligar o `INFORMATION_SCHEMA.TABLE_STORAGE` em `hml`**, passo
  de *Owner* ([`acoes-humanas.md`](../acoes-humanas.md) §1b).

---

## Fase 3 — Fechar a Onda 1 (25/09 → 07/10)

### Tarefa 3.1: Carga real das 23 fontes públicas em `dev` *(começa em 25/09)*

As fontes mensais só rodariam sozinhas entre 05 e 12/10, e as semanais em
28 e 29/09. Executar cada job uma vez, com os argumentos do agendamento,
antecipa a carga sem mudar a janela. A regra 3 continua valendo: a janela
vem de `--ultimos-dias`.

- [ ] **Passo 1: Disparar os 23 jobs**

```bash
for c in bcb_cambio_ptax bcb_juros ibge_ipca aneel_siga \
         ons_carga ons_ear ons_ena ons_capacidade ons_geracao_usina \
         ons_disponibilidade_usina ons_restricao_coff_eolica ons_restricao_coff_fotovoltaica \
         ccee_pld ccee_perfil ccee_agente ccee_exposicao_financeira ccee_contabilizacao_perfil \
         ccee_geracao_usina ccee_contrato_montante ccee_varejista_consumidor \
         ccee_encargo_ess ccee_energia_reserva ccee_cvu_estrutural; do
  gh workflow run "Executar ingestão" -f environment=dev -f conector="$c"
done
```

- [ ] **Passo 2: Esperar e ler o resultado**

```bash
bq --project_id=alupar-dev-alupdata query --use_legacy_sql=false --format=pretty '
SELECT fonte, entidade, status, linhas_extraidas, linhas_invalidas,
       linhas_carregadas, ROUND(duracao_segundos) AS s, erro
FROM bronze._execucoes
WHERE DATE(iniciada_em, "America/Sao_Paulo") = CURRENT_DATE("America/Sao_Paulo")
  AND fonte NOT IN ("hubspot", "bbce", "tempook")
QUALIFY ROW_NUMBER() OVER (PARTITION BY fonte, entidade ORDER BY iniciada_em DESC) = 1
ORDER BY status, fonte, entidade'
```

Esperado: 23 linhas com `SUCESSO` e `linhas_invalidas` perto dos números do
dry-run registrados em `status.md` §1. Uma fonte com `ERRO` vira correção com
teste de regressão, uma por PR. O primeiro contato com o BigQuery é onde o
formato recusado aparece: foi o que aconteceu no #208.

- [ ] **Passo 3: Rodar o Dataform** para a Silver e a Gold refletirem a
  carga, sem esperar as 11h do dia seguinte. O deploy `all` roda o `apply`,
  que não muda nada, e em seguida o Dataform, com a SA e o repositório certos:

```bash
gh workflow run "Deploy GCP" -f environment=dev -f module=all
```

### Tarefa 3.2: Toda Gold do domínio de mercado com linha

- [ ] **Passo 1: Contar as linhas de cada Gold**

```bash
for t in agentes_ccee agentes_por_classe_mensal armazenamento_e_afluencia_mensal \
         cambio_mensal capacidade_instalada_vigente_usina carga_mensal_submercado \
         consumo_varejista_mensal_uf cvu_estrutural_vigente_usina de_para_usina \
         disponibilidade_mensal_usina encargos_setoriais_mensal exposicao_mercado_mensal \
         geracao_mensal_usina geracao_mensal_usina_ons inflacao_mensal juros_mensal \
         mercado_mensal_submercado parque_gerador pld_mensal_submercado \
         posicao_contratual_mensal_perfil restricao_coff_mensal_usina \
         resultado_contabilizacao_mensal_perfil; do
  printf '%s ' "$t"
  bq --project_id=alupar-dev-alupdata query --use_legacy_sql=false --format=csv \
    "SELECT COUNT(*) FROM gold.$t" | tail -1
done
```

Esperado: nenhuma Gold com zero linha. Uma Gold vazia com Silver cheia é
defeito de SQL e ganha teste em `tests/unit/test_sql.py`. Uma Gold vazia
porque a Silver também está vazia volta para a Tarefa 3.1.

- [ ] **Passo 2: Conferir o de-para de usina contra o que foi medido em
  15/09** (95,1% do cadastro de capacidade casando com a ANEEL). Uma queda
  grande indica mudança na origem, não no código.

### Tarefa 3.3: Repetir a carga em `hml` e colher a evidência

**Depende de:** Fase 2.

- [ ] **Passo 1:** o laço da Tarefa 3.1 com `-f environment=hml`.
- [ ] **Passo 2: Rodar o Dataform em `hml`** para a Silver e a Gold
  refletirem a carga.

```bash
gh workflow run "Deploy GCP" -f environment=hml -f module=all
```

- [ ] **Passo 3:** as consultas das Tarefas 3.1 e 3.2 em `hml`.
- [ ] **Passo 4: Replay de uma fonte da onda em `hml`** (`ons_carga`), com o
  mesmo procedimento da Tarefa 1.2.
- [ ] **Passo 5: Captura do Cloud Scheduler de `hml`** com os 27 jobs e a
  próxima execução de cada um.

### Tarefa 3.4: Dossiê da Onda 1

**Entrega:** 07/10.

- [ ] **Passo 1:** checklist da skill `homologacao-onda`, uma linha por
  fonte: 7 componentes, carga em `hml` (ID da execução), linhas carregadas,
  Gold correspondente e dicionário.
- [ ] **Passo 2: Declarar o que ficou de fora**, com motivo. O item 1.1
  (CCEE) entrega 11 entidades da fila de 24 da ADR 021. As restantes são fila
  por demanda, não pendência da onda.
- [ ] **Passo 3:** `docs/relatorios/2026-10-07-dossie-onda-1.md`, o HTML, o
  índice, commit e PR.
- [ ] **Passo 4: Entregar e pedir o aceite.** Ação externa, feita pela
  coordenação.
- [ ] **Passo 5: Fechar a janela** depois do aceite das duas ondas:
  `agendamentos_ativos = false` em `hml.tfvars`, PR e deploy `all` em `hml`.

---

## Fase 4 — Onda 2, conforme cada credencial chega (25/09 → 23/10)

Cada fonte fecha sozinha, na ordem em que o insumo chega. A onda fecha
quando a última fecha, ou quando uma decisão tira alguma dela do escopo.

### Tarefa 4.1: TempoOK — rotação do token e carga *(pode começar já)*

- [ ] **Passo 1: Rotacionar o token** ([ADR 020](../arquitetura/decisoes/020-token-tempook-rotacao-na-producao.md),
  [`acoes-humanas.md`](../acoes-humanas.md) §2). Pedir ao fornecedor um
  token novo, gravar como versão nova de `alupdata-tempook-api-token` e
  confirmar que o antigo deixou de autenticar.
- [ ] **Passo 2:** executar `ingestao-tempook-ena-prevs` em `dev` e ler o
  `_execucoes`. Esperado: `SUCESSO` com até 5 arquivos (o acervo tem buracos
  aos sábados).
- [ ] **Passo 3: Boletins.** Sem acervo recente (A10,
  [#129](https://github.com/nessenergy/Alupdatalake/issues/129)), o conector
  roda e carrega zero. O dossiê declara isso como pendência da origem, com
  data, e não como falha do conector.

### Tarefa 4.2: Hubspot — ligar e ajustar (~4h restantes)

**Depende de:** o token no secret `alupdata-hubspot-api-token` (A9), gravado
pelo grupo da Alup no canal combinado.

- [ ] **Passo 1:** executar `ingestao-hubspot-negocios` em `dev`.
- [ ] **Passo 2: Rodar o teste de integração que hoje é `skipif`**

```bash
ALUPDATA_INTEGRACAO_HUBSPOT=1 uv run pytest tests/integration -k hubspot -v
```

- [ ] **Passo 3:** conferir cada item da lista "Não verificado" de
  `docs/dicionario-dados/hubspot_negocios.md` contra a API real. Divergência
  entra com teste; item confirmado sai da lista.

### Tarefa 4.3: BBCE — ligar e ajustar

**Depende de:** o acesso e o **host** (A7,
[#23](https://github.com/nessenergy/Alupdatalake/issues/23)). O host não
consta da documentação pública.

- [ ] **Passo 1:** executar `ingestao-bbce-curva-forward` em `dev`.
- [ ] **Passo 2: Rodar o teste de integração que hoje é `skipif`**

```bash
ALUPDATA_INTEGRACAO_BBCE=1 uv run pytest tests/integration -k bbce -v
```

- [ ] **Passo 3:** conferir cada item da seção "O que não foi possível
  verificar sem credencial" de `docs/dicionario-dados/bbce_curva_forward.md`
  contra a API real. Divergência entra com teste; item confirmado sai da
  lista.

### Tarefa 4.4: Decidir o item 2.1 (CCEE agente credenciado, 32h)

A [ADR 018](../arquitetura/decisoes/018-vias-de-acesso-a-ccee.md) registrou
que medição e contratos da CCEE por API credenciada **são escopo novo**, com
ADR própria. As 32h do item 2.1 precisam de destino antes do dossiê da Onda
2. As opções são pedir a credencial de agente e escrever a ADR, ou realocar
as horas, que o regime da cláusula 1ª permite, para a fila da ADR 021 já
entregue. **A decisão é da coordenação com a Alup** (decisão D2, seção 9).

### Tarefa 4.5: Dossiê da Onda 2

**Entrega:** 23/10, se Hubspot e BBCE chegarem até 12/10.

- [ ] A janela de `hml` reabre com o mesmo procedimento das Tarefas 2.1 e
  3.3, restrita às 4 fontes da onda. Depois: checklist, dossiê, aceite e
  fechamento da janela.

---

## Fase 5 — Adiantar a Onda 4 (28/09 em diante, em paralelo)

Três frentes da Onda 4 não esperam a Onda 3. Adiantá-las é o que permite
fechar a Onda 4 uma semana depois da 3, em vez de três.

### Tarefa 5.1: Glossário como código *(plano próprio)*

- [x] Escrever [`docs/planos/2026-09-24-glossario-como-codigo.md`](2026-09-24-glossario-como-codigo.md):
  os termos de `docs/glossario.md` declarados em `infra/modules/catalogo`
  como glossário do Knowledge Catalog, com teste em
  `tests/unit/test_catalogo.py`.

### Tarefa 5.2: Anotações do catálogo *(depois da Fase 3)*

- [ ] Preencher os *aspects* `origem` e `dominio-analitico` das tabelas
  carregadas. O plano próprio nasce quando as tabelas tiverem linha, porque o
  conteúdo da anotação é a linhagem real, não a prevista.

### Tarefa 5.3: Templates de planilha *(plano próprio, depois de 01/10)*

- [ ] Quando os exemplos chegarem ao bucket `alupar-dev-alupdata-entrada`,
  escrever `docs/planos/<data>-templates-de-planilha.md`, com um template por
  planilha no motor S2 Data Intake.
- [ ] Antes do template, **conferir cada planilha contra as 13 fontes da
  proposta** (A12). O que estiver fora dela é aditivo e vai para a
  coordenação antes de virar código.

### Tarefa 5.4: Documentação final contínua

- [ ] A cada fonte que fecha, o dicionário e a linhagem ficam no estado de
  entrega. Assim o item 4.5 (10h) vira revisão, não redação.

---

## Fase 6 — Onda 3, quando o acesso chegar

**Depende de:** A7. Os pedidos vencem em 25/09, e a mensagem de 24/09 pede
as credenciais até 09/11.

### Tarefa 6.1: Registrar A7 em 26/09

- [ ] Em 26/09, registrar em `status.md` se a Alup confirmou os pedidos
  abertos, com número de chamado e responsável. Sem confirmação, a
  coordenação decide o registro formal. Este plano não cobra.

### Tarefa 6.2: Uma fonte por plano

- [ ] Para cada fonte cuja credencial chegar (Oracle FMB, Portal Alup, MySQL
  RDS, RM/TOTVS), escrever `docs/planos/<data>-fonte-<nome>.md` com o
  procedimento do `plano-execucao.md` §8: `make novo-conector`, schema
  Pydantic, TDD, `extrair()` sobre `src/core/banco.py` e os 7 componentes.
- [ ] Acrescentar o conector a `cadeia_onda3` em `infra/environments/<amb>.tfvars`.
  A orquestração passa a existir a partir da primeira fonte.
- [ ] A rede (VPN) é recurso em `infra/`, nunca no console. O MySQL RDS
  dispensa VPN (C8) e é a primeira candidata.

---

## Fase 7 — Virada de produção

**Quando:** depois do aceite das Ondas 0 e 1. Subir `prod` cedo faz o
histórico começar a acumular onde vai ser consumido.

- [ ] **Pré-requisitos:** o valor do orçamento por ambiente
  ([#87](https://github.com/nessenergy/Alupdatalake/issues/87)) e a região
  confirmada. A política herdada admite só `us-central1`, e depois do
  primeiro `apply` de `prod` mudar a região é migração de dado.
- [ ] Bootstrap de `prod`, com o procedimento de `runbook/primeiro-deploy.md`
  §0 e o workspace `prod`.
- [ ] Deploy `all` em `prod`, TABLE_STORAGE e tokens gravados pelos grupos.
- [ ] Carga inicial das fontes homologadas, com o laço da Tarefa 3.1 apontado
  para `prod-alupdata`.

---

## 8. Ações humanas, por data

| Até | Ação | Quem |
|---|---|---|
| 25/09 | Reautenticar o `gcloud` na conta da ness. | Ricardo |
| 25/09 | Enviar a mensagem das pendências (`relatorios/2026-09-24-pendencias-da-alup.html`) | Ricardo |
| 26/09 | Registrar se A7 foi confirmada | Ricardo |
| 29/09 | Grupos da Alup para `hml` (consumidores, operação, IAP) | Alup (Leonardo) |
| 30/09 | Token do Dataform em `hml` e TABLE_STORAGE em `hml` | ness., com papel de *Owner* |
| 30/09 | Entregar o dossiê da Onda 0 e pedir aceite | coordenação da ness. |
| 01/10 | Exemplos de planilha no bucket de entrada | Alup |
| 07/10 | Entregar o dossiê da Onda 1 e pedir aceite | coordenação da ness. |
| 12/10 | Token do Hubspot e acesso/host do BBCE no Secret Manager | Alup |
| quando der | Rotação do token do TempoOK | ness., com o fornecedor |
| 09/11 | VPN e credenciais das quatro fontes internas | Alup |

## 9. Decisões que o plano não toma

| # | Decisão | Recomendação | Trava |
|---|---|---|---|
| D1 | **Profundidade do histórico** (risco R4, o custo é da Alup) | homologar com a janela do agendamento e fazer carga retroativa só por pedido de domínio, com janela explícita | nada; a carga retroativa é opcional |
| D2 | **Destino das 32h do item 2.1** | **antecipada em 24/09**: pedir a posição da Alup em 30/09, junto do dossiê da Onda 0 | dossiê da Onda 2 |
| D3 | **Aviso de fonte semanal ou mensal parada** ([#188](https://github.com/nessenergy/Alupdatalake/issues/188)) | **decidida em 24/09: opção (a)**, vigia diário sobre `gold.saude_ingestao`; implementação até o dossiê da Onda 2 | nada até a Fase 7 |
| D4 | **Valor do orçamento** ([#87](https://github.com/nessenergy/Alupdatalake/issues/87)) | acertar com o Saulo junto do pedido de grupos | Fase 7 |
| D5 | **Data formal da Onda 0 postergada** | coordenação da ness., com o registro de A3 | nada técnico |

## 10. Fora deste plano

A higiene de IAM do `dev` (os papéis duplicados sem condição e o *Owner*
avulso), o design system do Portal
([#177](https://github.com/nessenergy/Alupdatalake/issues/177)) e a versão
em inglês do baralho. Nenhum deles muda data de onda.
