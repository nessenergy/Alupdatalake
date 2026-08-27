# Aditivo proposto — FinOps do DataLake

**Status**: proposta técnica · **Data**: 2026-08-27 · **Não contratado**

Este documento levanta escopo e esforço de um painel de FinOps — custo real da
plataforma, atribuído por conector — que **não existe hoje** e **não está no
contrato**. Serve de base para uma conversa comercial; não é compromisso.

Documento irmão: [ADR 007](../arquitetura/decisoes/007-painel-de-saude-como-entrega.md),
que trata do painel de saúde já construído. São coisas diferentes: aquele já
está pronto e discute-se como classificá-lo; este ainda não foi escrito.

---

## 1. O que existe hoje, e por que não é FinOps

Três peças já entregues tocam o assunto e nenhuma responde "quanto custa":

| Peça | O que faz | O que não faz |
|---|---|---|
| `google_billing_budget` (`infra/modules/monitoramento/custo.tf`) | avisa em 50%, 90% do gasto e 100% da projeção | não mostra nada; e **não é criado** enquanto a Alup não fornecer o `billing_account` (pendência A3) |
| `gold.volumetria_lake` | linhas, execuções e segundos por conector/dia | conta **linhas, não reais** — volume é proxy ruim de custo: uma consulta mal escrita custa mais que um milhão de linhas carregadas |
| Painel do Cloud Monitoring | saúde da plataforma | métrica de execução, não de gasto |

**Nenhum dado de custo entra no lake hoje.** O gasto do projeto só é
observável abrindo o console de faturamento — que é exatamente o trabalho
manual que a franquia de sustentação não deveria pagar.

Vale registrar a assimetria que dá urgência ao tema: pela cláusula 5ª o custo
de infra GCP **é da Alup**, e a regra 4 do projeto (particionar e clusterizar
sempre) existe por causa disso. Ou seja, o contrato já reconhece que esse custo
importa e que é responsabilidade da ness. não inflá-lo — mas não entrega à Alup
nenhum instrumento para **verificar** isso. É essa lacuna que o aditivo fecha.

---

## 2. A decisão de arquitetura que separa o aditivo em duas camadas

Há duas fontes possíveis de dado de custo, com dependências muito diferentes:

**`INFORMATION_SCHEMA` — dentro do BigQuery, sem depender de ninguém.**
`JOBS_BY_PROJECT` traz bytes faturados por consulta, por usuário e por job;
`TABLE_STORAGE` traz bytes armazenados por tabela. Dá para calcular custo de
consulta e de armazenamento com granularidade **maior** que a do faturamento, e
sem pedir nada à Alup além do projeto GCP que já é a pendência A3. Custa uma
multiplicação por um preço unitário parametrizado.

**Billing export — a fonte oficial do dinheiro, e a que tem dependência.**
É o único lugar que traz o gasto de *todos* os serviços (Cloud Run, GCS,
Artifact Registry, Composer) e o valor que de fato aparece na fatura, com
descontos e créditos aplicados. Em compensação depende de alguém com papel de
administrador de faturamento da Alup ligar o export.

> ⚠ **Verificar antes de fechar preço**: até onde apuramos, ligar o export de
> faturamento para o BigQuery é configuração da **conta de faturamento**, feita
> no console, sem recurso Terraform equivalente. Se confirmado, isso tem duas
> consequências: vira pendência da Alup (como A3), e é a **primeira exceção
> legítima à regra 5** do projeto ("recurso GCP que não está em `infra/` não
> existe") — o dataset de destino e o IAM ficam no Terraform, mas o interruptor
> do export, não. Isso precisa ser dito na proposta, não descoberto depois.

Daí a proposta ter **duas camadas**, contratáveis em separado:

| Camada | Fonte | Depende de | Responde |
|---|---|---|---|
| **A — Custo do BigQuery** | `INFORMATION_SCHEMA` | só do ambiente GCP (A3), que já é pendência | "qual conector, qual view e qual consulta consomem o orçamento?" |
| **B — Custo da plataforma** | billing export | A3 **+** administrador de faturamento ligar o export | "quanto custou o mês, por serviço, contra o previsto?" |

A camada A entrega valor sozinha e é a que tem melhor relação esforço/retorno.
A camada B é a que fecha a conta com a fatura — e é a que a Alup vai querer
quando o Composer entrar.

---

## 3. Por que agora: o salto do Composer

O custo hoje é irrelevante — Ondas 0 a 2 estimadas em **US$ 5–15/mês**. A Onda 3
traz o Cloud Composer, que cobra por ambiente ligado 24×7, e a conta salta para
**~US$ 450/mês** (issue #55, `infra/modules/composer/README.md`). É um fator de
30×.

Construir FinOps *depois* do salto significa descobrir a curva pela fatura.
Construir *antes* significa ter a linha de base com que comparar — e essa é a
única janela em que a linha de base ainda é barata de coletar.

O risco R4 do plano ("volume do ONS estoura o custo de BigQuery") é o mesmo
argumento por outro caminho: o plano manda "decidir profundidade de histórico
**antes** de carregar", e hoje não existe instrumento que meça o efeito dessa
decisão depois de tomada.

---

## 4. Escopo — camada A: custo do BigQuery

| # | Item | Est. | Entregável |
|---|---|---|---|
| F1 | **Rotular os jobs** de carga com `fonte` e `entidade` | 6h | `LoadJobConfig(labels=...)` em `src/core/bigquery.py` + testes. Sem isso não há atribuição por conector: hoje o `LoadJobConfig` não leva `labels` |
| F2 | View `gold.custo_consulta` a partir de `JOBS_BY_PROJECT` | 8h | Bytes faturados, custo estimado, por dia/usuário/label; view versionada em `sql/gold/` |
| F3 | View `gold.custo_armazenamento` a partir de `TABLE_STORAGE` | 6h | Bytes ativos e de longo prazo por dataset e tabela, com custo estimado |
| F4 | View `gold.custo_por_conector` | 8h | Junta F2/F3 com `bronze._execucoes`: custo de ingestão e de armazenamento por fonte, e **custo por mil linhas** — que é o número que denuncia conector ineficiente |
| F5 | Tela `/custo` no Portal | 12h | Mesmo padrão do `/lake`: SVG do servidor, sem bundler, tabela equivalente para acessibilidade |
| F6 | Testes, dicionário de dados e ADR | 8h | Inclui a exceção nova em `tests/unit/test_sql.py` — ver §6 |
| | **Subtotal camada A** | **48h** | |

**Preço unitário não vai no código.** O valor por TiB varre e por GiB
armazenado entra como parâmetro de deploy, não como literal no SQL: preço do
Google muda, e view com preço fixo mente em silêncio. O número exato precisa ser
confirmado na tabela vigente no momento da implementação, e a view expõe **bytes
e custo estimado lado a lado**, para que o bytes continue verdadeiro se o preço
envelhecer.

## 5. Escopo — camada B: custo da plataforma

| # | Item | Est. | Entregável |
|---|---|---|---|
| F7 | Dataset de billing export, IAM e documentação do que a Alup precisa ligar | 6h | Terraform do que é terraformável + runbook do passo manual |
| F8 | View `gold.custo_plataforma` por serviço/dia | 10h | Gasto por serviço (BigQuery, Cloud Run, GCS, Composer), reconciliável com a fatura |
| F9 | Projeção e comparação com o orçamento | 8h | Gasto corrente vs. `orcamento_mensal_brl`, projeção de fim de mês, e a linha de base pré-Composer |
| F10 | Alerta de anomalia de custo | 8h | Desvio contra a mediana móvel, não só percentual de teto — pega o salto de um conector antes de ele virar fatura |
| F11 | Testes e documentação | 6h | |
| | **Subtotal camada B** | **38h** | |

---

## 6. Impacto no que já existe

Três pontos concretos, que é o que distingue esta estimativa de um chute:

1. **`tests/unit/test_sql.py` precisa de exceção nova.** O teste
   `test_view_referencia_a_camada_anterior` exige que toda view Gold leia da
   Silver, e já abre **uma** exceção — a view de monitoramento que lê
   `bronze._execucoes`. As views de FinOps não leem nem Silver nem Bronze: leem
   `INFORMATION_SCHEMA` e o dataset de billing. A exceção tem de ser explícita e
   estreita, com a mesma regra de não-mistura que vale hoje (view de custo não
   junta dinheiro com dado de negócio).
2. **`src/core/bigquery.py` ganha labels.** Mudança pequena e de baixo risco,
   mas toca o caminho de carga de todos os conectores — logo, roda contra as 4
   fontes verificadas antes de entrar.
3. **O Portal ganha uma terceira rota.** A ADR 005 lista "painel com gráficos e
   filtros" como fora de escopo do Portal MVP; a ADR 006 abriu o `/lake` com o
   argumento de que monitoramento não é BI. `/custo` precisa do mesmo tipo de
   justificativa escrita, ou a ADR 005 vira letra morta por acúmulo de exceções
   — que é exatamente o risco R5 que ela existe para conter.

---

## 7. Resumo para a conversa comercial

| Cenário | Esforço | Valor a R$ 256/h | O que a Alup precisa fornecer |
|---|---|---|---|
| **Só camada A** | 48h | R$ 12.288 | nada além do ambiente GCP (A3), que já é pendência |
| **A + B** | 86h | R$ 22.016 | A3 + administrador de faturamento ligar o export |
| Só camada B | não recomendado | — | entrega o total sem conseguir atribuir a ninguém |

**Recomendação: fechar a camada A e deixar a B com preço travado por opção.**
A camada A não cria dependência nova — e dependência nova, neste contrato, é o
maior risco documentado (§7 do plano: atraso de insumo dispara ociosidade de
4h/dia). Entregar A primeiro também produz a linha de base antes do Composer,
que é o argumento de oportunidade da §3.

**Este aditivo não deve ser vendido como pré-requisito de nada.** A Fase 1
entrega sem ele. É melhoria de governança de custo, que o contrato coloca do
lado da Alup — e é justamente por ser dela que faz sentido oferecer o
instrumento, em vez de assumir o custo de operá-lo à mão pela franquia.

## 8. O que ainda não foi verificado

Honestidade sobre os limites desta estimativa:

- **O export de faturamento via Terraform** — §2. É o item que mais pode mover
  a camada B, para mais ou para menos.
- **Nada disso rodou contra um BigQuery real**, porque o projeto GCP não existe
  (A3). `INFORMATION_SCHEMA` tem particularidades por região e retenção de
  histórico (a de `JOBS` é limitada) que só aparecem na primeira consulta real.
  A mesma ressalva da §5.1 do `status.md` vale aqui.
- **As horas seguem a granularidade do plano** (blocos redondos), e a camada A
  é mais confiável que a B — F1 a F4 são trabalho conhecido sobre código que já
  existe; F7 a F10 dependem de um formato de dado que ainda não vimos.
