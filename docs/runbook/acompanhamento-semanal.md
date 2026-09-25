# Acompanhamento semanal — campos do GitHub Projects

O objetivo destes cinco campos é que **uma semana sem reunião ainda produza um
relatório**. Sem eles, o quadro diz o que está em andamento, mas não diz quanto
custou, em que semana, se a Alup conferiu, se foi retrabalho, nem o que passou
do prazo — exatamente as cinco coisas que a medição e a cláusula 3ª pedem.

Configuração versionada em `scripts/campos_projeto.py`. Semântica, aqui.

---

## Os cinco campos

| Campo | Tipo | O que registra | Por que existe |
|---|---|---|---|
| **Horas** | Número | Horas gastas no item | O contrato é por regime de horas (580h em 5 ondas). É o insumo da medição por onda e o único jeito de ver uma onda estourando antes de ela estourar. |
| **Semana** | Seleção `S1`–`S19` | Período de desenvolvimento | Nomenclatura já usada em `plano-execucao.md` e `plano-semanal.md`. Agrupar o quadro por semana dá o relatório semanal quase pronto. |
| **Validado** | Seleção `Sim`/`Não` | Se alguém da Alup conferiu o que está em Done | **Entrega técnica não é homologação.** Done é da ness.; validado é da Alup. Sem separar os dois, uma onda parece fechada e não está. |
| **Correções** | Seleção `Sim`/`Não` | Se o item é retrabalho sobre algo já entregue | Separa entrega nova de refação na contagem de horas. Retrabalho somado como progresso esconde tanto erro nosso quanto mudança de requisito. |
| **Atraso** | Seleção `Sim`/`Não` | Se a tarefa passou do prazo | A cláusula 3ª só sustenta postergação, ociosidade ou suspensão se o atraso estiver **registrado no dia em que começou**, não quando vira problema. |

### Duas restrições da plataforma, para não haver surpresa

- **Projects V2 não tem campo booleano nem checkbox.** Os três indicadores são
  seleção de duas opções (`Sim`/`Não`). É o equivalente mais próximo, e tem a
  vantagem de permitir filtro e agrupamento no quadro.
- **Campo de iteração não é criável por API** — só pela interface. Se um dia a
  Semana passar a precisar de datas reais em vez de `S1`–`S19`, esse campo tem
  de ser criado à mão e o script deixa de gerenciá-lo.

---

## Como aplicar

O script usa a API GraphQL do Projects V2. Na operação local, reutilize a
sessão autenticada do `gh`, com acesso ao Project, sem criar segredo alternativo
para contornar A3. Na automação, preserve o App com WIF e Secret Manager
descrito abaixo; o token padrão do CI é limitado ao repositório.

```bash
export GITHUB_TOKEN=$(gh auth token)

# 1. descobrir o número do projeto
uv run python -m scripts.campos_projeto --owner nessenergy --listar

# 2. conferir o que seria criado, sem criar
uv run python -m scripts.campos_projeto --owner nessenergy --numero <n> --dry-run

# 3. aplicar
make campos-projeto owner=nessenergy numero=<n>
```

O script é **idempotente**: campo que já existe é deixado como está. Ele nunca
apaga nem renomeia — rodar de novo depois de acrescentar um campo novo à lista
cria só o que falta.

---

## Sincronização semanal

O que se deduz do repositório não é preenchido à mão. `scripts/quadro.py` lê o
quadro e acerta, a partir do mapa em `scripts/quadro.toml`:

| Campo | Regra |
|---|---|
| Onda | a onda do item no mapa; item fora do mapa é listado, não classificado |
| Responsável | Alup para os itens listados em `alup`; ness. para os demais |
| Status | Done quando a issue é fechada ou o PR é mesclado; item aberto não é tocado |
| Semana | a semana da data de conclusão (S1 a S19, contadas de 31/08), só se estiver vazia |
| Atraso | Sim a partir do primeiro dia útil após o vencimento registrado em `vencimentos`, com um comentário datado na issue; Não enquanto não vence |
| Correções e Validado | Não, só se estiverem vazios, no item concluído |

O comando **nunca** mexe em Horas e **nunca** desfaz Validado = Sim, Correções
= Sim ou Atraso = Sim: são decisões humanas. Os feriados nacionais ficam no
mesmo arquivo, porque a cláusula 3ª conta dia útil.

```bash
export GITHUB_TOKEN=$(gh auth token)   # PAT com escopo `project`
make quadro            # simula: mostra o que mudaria e os comentários que seriam postados
make quadro-aplicar    # grava e posta os comentários de atraso novos
```

Por padrão ele só simula, porque cada gravação e cada comentário ficam visíveis
para a Alup. Issue nova no quadro entra no `quadro.toml`; sem isso, o comando a
lista como sem onda. **Zero mudanças na simulação comprova apenas conformidade
com o mapa e o estado de fechamento consultado.** Não confere implementação,
descrições, critérios de aceite ou homologação. Issue aberta com código pronto
pode exigir `In Progress` após revisão editorial; o script não decide isso.

Para reproduzir a conferência datada, sem escrita externa:

```powershell
python -m scripts.quadro --hoje 2026-09-18
uv run pytest tests/unit/test_quadro.py -q
```

`--aplicar` também publica comentários de atraso. Antes de usá-lo, revise
conteúdo e destino e obtenha autorização explícita para essas mensagens;
a autorização para editar campos ou descrições não a substitui.

### Sincronização automática

O workflow `.github/workflows/quadro.yml` roda o mesmo comando, com `--aplicar`,
em três situações:

| Gatilho | Quando |
|---|---|
| `workflow_run` | ao fim de cada execução do **Deploy GCP**, só se ela terminou com sucesso |
| `schedule` | dias úteis às 08h de Brasília (`0 11 * * 1-5`, em UTC) |
| `workflow_dispatch` | à mão, na aba Actions; a opção **simular** roda sem gravar |

Nunca rodam duas sincronizações ao mesmo tempo: a que chega depois espera.

O token é de um **GitHub App**, não de um PAT: não depende da conta de uma
pessoa e expira em uma hora. A chave privada do App fica no Secret Manager
(regra 2), no secret `alupdata-github-quadro-app-key` declarado em
`infra/modules/secrets`. Só a service account de deploy, que o GitHub assume
via WIF, pode lê-la. O workflow autentica no GCP como o deploy, com as
variáveis do repositório, lê a chave, mascara cada linha e gera o token de
instalação com
`actions/create-github-app-token`.

**Enquanto o projeto GCP (A3) e o App não existirem**, o job registra um aviso
e termina com sucesso. Ele começa a sincronizar sozinho quando as três
variáveis abaixo estiverem preenchidas e a chave estiver gravada. **Com as
variáveis preenchidas e o secret ainda sem versão**, o passo que lê a chave
registra o mesmo tipo de aviso e os passos seguintes ficam pulados (desde
25/09; antes disso o job falhava todo dia). Qualquer outro erro de leitura
continua falhando. Não é preciso
mudar nenhum arquivo. **Workflow verde não comprova sincronização:** confira
se o passo que executa `scripts.quadro` rodou ou foi pulado. Na
[execução de 17/09/2026, nº 35240311826](https://github.com/nessenergy/Alupdatalake/actions/runs/35240311826),
a guarda encerrou sem configuração suficiente e os passos seguintes ficaram
`skipped`. Em 18/09, a ativação permanece pendente de configuração e de uma
execução efetiva observada; a conferência manual usa a sessão local existente.

**Configuração, uma vez (fora do repositório):**

1. **Criar o App na organização**: *nessenergy → Settings → Developer settings
   → GitHub Apps → New GitHub App*. Webhook desligado. Permissões mínimas:
   - *Organization → Projects*: **Read and write**;
   - *Repository → Issues*: **Read and write** (comentário de atraso);
   - *Repository → Pull requests*: **Read-only**. O quadro tem PRs e o
     repositório é privado: sem essa permissão, o `mergedAt` não aparece;
   - *Repository → Metadata*: **Read-only** (obrigatória, já vem marcada).

   Em *Where can this GitHub App be installed?*, **Only on this account**.
2. **Instalar o App**: na página do App, *Install App → nessenergy → Only
   select repositories → Alupdatalake*.
3. **Gerar a chave privada**: na página do App, *Private keys → Generate a
   private key*. O `.pem` baixado é gravado no Secret Manager e depois apagado
   do disco:

   ```bash
   gcloud secrets versions add alupdata-github-quadro-app-key \
     --project=<projeto> --data-file=chave.pem
   rm chave.pem
   ```

   O secret só existe depois do primeiro `terraform apply`. Para trocar a chave,
   gere uma nova, grave-a como nova versão e revogue a antiga no App: o workflow
   sempre lê `latest`.
4. **Variáveis no GitHub**:
   - `QUADRO_APP_CLIENT_ID`, variável do repositório com o *Client ID* do App.
     Não é segredo. O `create-github-app-token` v3 recomenda o Client ID no
     lugar do App ID, que está em desuso.
   - `GCP_WIF_PROVIDER` e `GCP_DEPLOY_SA` como variáveis **do repositório**,
     com os valores do projeto `dev` ([`deploy.md`](deploy.md)). A organização
     passou ao GitHub Enterprise em 11/09 (ADR 010). Este workflow continua
     sem `environment:` e lê variáveis do repositório; a revisão documental
     não muda essa configuração. O comentário sobre Free no YAML é histórico.

`make quadro` e `make quadro-aplicar` continuam valendo para rodar à mão, com o
token de quem roda.

---

## Como isso vira o relatório semanal

Na sexta-feira, com o quadro filtrado por `Semana = S<n>`:

1. **Soma de Horas** por onda → consumo apontado, pelo critério da seção
   "Critério de apontamento" abaixo.
2. **Itens em Done com `Validado = Não`** → a fila de homologação. É o que
   precisa de alguém da Alup, e o que trava o fechamento da onda.
3. **Itens com `Correções = Sim`** → quanto da semana foi refação. Se cresce
   duas semanas seguidas, o problema não é execução: é requisito ou premissa.
4. **Itens com `Atraso = Sim`** → entram no registro de atraso, com a data em
   que o atraso começou. Sem essa data, a cláusula 3ª não se sustenta na
   medição.

O relatório emitido para a contratante vive em `docs/relatorios/`; estes quatro
recortes são o esqueleto dele nas semanas sem reunião.

---

## Convenção de preenchimento

- **Horas** entra no fim do item, não no começo: só item `Done` recebe
  apontamento, pelo critério da seção seguinte.
- **Horas previstas** é campo separado, transcrito do
  [`plano-execucao.md`](../plano-execucao.md): é o orçamento da proposta, e
  não muda com o apontamento.
- **Validado** só vira `Sim` com nome e data de quem validou registrados no
  item. "Alguém falou que estava ok" não é validação.
- **Atraso** é do item, não da pessoa. Um item bloqueado por insumo da Alup
  entra como `Sim` — é justamente o caso que o contrato quer ver registrado.

## Critério de apontamento

**Definido pela coordenação da ness. em 24/09/2026.** Cada item concluído
(`Done`) recebe em `Horas` as **horas previstas na proposta, acrescidas de 3%**
(`Horas = Horas previstas × 1,03`, com duas casas). Item sem horas previstas
não recebe apontamento próprio: seu esforço está dentro de um item com peso.
Item em andamento ou a fazer não recebe apontamento.

Aplicado em 24/09 aos 14 itens `Done` com horas previstas: **162h previstas,
166,86h apontadas**. Os valores de 08/09 (abaixo) foram substituídos pelo
mesmo critério.

Apontamento não é homologação: a medição da onda continua dependendo do
aceite da Alup (`Validado = Sim`).

### Registro histórico de 08/09/2026 — substituído em 24/09

Foram lançadas **100h em sete itens**, usando a regra então documentada de
atribuir o orçamento à entrega verificada. A consulta de 18/09 preserva os
valores, mas **não os considera horas realizadas comprovadas** até conciliar
sua origem com registros de trabalho. Em 24/09 esses itens foram reapontados
pelo critério acima.

| Onda no lançamento | Itens | Horas registradas, não comprovadas |
|---|---|---:|
| 0 — Fundação | Terraform (#2), CI/CD (#3), arquitetura Medallion (#7), conector BCB/PTAX (#21) | 40h |
| 1 — Mercado base | conectores ONS (#18), ANEEL (#19) e IBGE (#20) | 60h |

BCB/PTAX consta na Onda 0 como conector de referência (plano, item 0.3);
a fonte também é listada no escopo da Onda 1 sem horas adicionais. Não
reclassificar o lançamento nem contar o esforço duas vezes por essa diferença.

O registro de 08/09 informa que região (#67), revisão na `main` (#68) e
campos do quadro (#78) não receberam horas. A ausência de orçamento próprio
não permite inferir ausência de trabalho realizado. A conciliação deve manter
histórico de qualquer correção, sem sobrescrever valores por estimativa.
