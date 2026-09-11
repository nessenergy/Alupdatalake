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

Projects V2 só tem API GraphQL; não existe endpoint REST equivalente. O script
precisa de um **PAT clássico com escopo `project`** — o token do CI não serve,
porque é limitado ao repositório.

```bash
export GITHUB_TOKEN=<PAT clássico com escopo project>

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
lista como sem onda.

---

## Como isso vira o relatório semanal

Na sexta-feira, com o quadro filtrado por `Semana = S<n>`:

1. **Soma de Horas** por onda → quanto da onda foi consumido.
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

- **Horas** entra no fim do item, não no começo. Estimativa vai no plano; aqui
  é o realizado.
- **Horas previstas** é campo separado, transcrito do
  [`plano-execucao.md`](../plano-execucao.md). Os dois nunca se misturam: um é
  orçamento, o outro é medição.
- **Validado** só vira `Sim` com nome e data de quem validou registrados no
  item. "Alguém falou que estava ok" não é validação.
- **Atraso** é do item, não da pessoa. Um item bloqueado por insumo da Alup
  entra como `Sim` — é justamente o caso que o contrato quer ver registrado.

## Base do lançamento de horas realizadas

O contrato é por alocação de horas, e a medição se faz por item. A regra do
lançamento é uma só:

> **Hora contratada atribuída a entrega verificada.** Um item concluído recebe
> as horas que o `plano-execucao.md` lhe orçou, e só depois de conferido que a
> entrega existe de fato no repositório.

O que qualifica a hora, portanto, é a entrega — não a passagem do tempo. Item
sem entrega conferida não recebe hora, ainda que esteja marcado como concluído
no quadro.

A conferência não é a leitura do status no quadro — é a checagem dos artefatos.
Para fonte de dados, os **7 componentes** da cláusula 2ª, um a um: conector,
tabela Bronze, view Silver, view Gold, testes, agendamento e dicionário com
linhagem. Para item de infraestrutura ou documentação, o artefato
correspondente versionado.

**Lançamento de 08/09/2026** — 100h, sobre sete itens conferidos:

| Onda | Itens | Horas |
|---|---|---:|
| 0 — Fundação | Terraform (#2), CI/CD (#3), arquitetura Medallion (#7), conector BCB/PTAX (#21) | 40h |
| 1 — Mercado base | conectores ONS (#18), ANEEL (#19) e IBGE (#20) | 60h |

Os demais itens concluídos — região do ambiente (#67), revisão na `main` (#68)
e campos do quadro (#78) — **não receberam horas**: são decisões e
instrumentação, não constam do plano de execução e portanto não têm alocação
contratual a consumir.
