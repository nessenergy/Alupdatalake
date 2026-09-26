# Runbook — incidentes

O que fazer quando um alerta do AlupData chega. Escrito para quem opera a
plataforma depois do handoff (item 4.6): cada alerta abaixo existe em
`infra/modules/monitoramento/` e chega com o nome exato da primeira coluna.

A regra que orienta tudo: **Bronze é append-only e a deduplicação vive na
Silver** (`QUALIFY ROW_NUMBER()`). Reprocessar uma janela que já carregou não
duplica dado na Silver nem na Gold, então, na dúvida, reprocessar é seguro.

## 1. Qual alerta chegou

| Alerta | O que significa | Primeiro passo |
|---|---|---|
| `AlupData <amb> — ingestão falhou` | um Cloud Run Job de ingestão terminou com tarefa falhada | §2, depois §3 pela mensagem de erro |
| `AlupData <amb> — <fonte> sem sucesso há Nh` | **silêncio**: nenhuma execução bem-sucedida da fonte dentro da cadência. Pega job que nem disparou, que o alerta de falha não vê | conferir o Cloud Scheduler do job (§2.3); se disparou e falhou, é o caso anterior |
| `AlupData <amb> — registros inválidos em alta` | mais de 100 registros descartados pela validação em uma hora | §3.2: quase sempre a origem mudou o formato |
| `AlupData <amb> — carga zerada por registro inválido` | a execução extraiu registros e não carregou nenhum | §3.2, com urgência: a origem mudou e **todo** o dado está sendo descartado |
| `AlupData <amb> — Dataform falhou (asserção ou execução)` | a transformação Bronze → Silver → Gold falhou, ou uma asserção de qualidade reprovou | §3.4 |
| `AlupData <amb> — orçamento mensal` | o gasto do mês passou de 50% ou 90% do orçamento, ou a projeção do mês chegou a 100%. Existe quando o valor do orçamento estiver acertado ([#87](https://github.com/nessenergy/Alupdatalake/issues/87)) | §3.5 |

## 2. Diagnóstico comum

### 2.1 O registro da execução

Toda ingestão grava uma linha em `bronze._execucoes`, com sucesso ou falha. É
o registro durável: não expira, ao contrário do log.

```sql
SELECT ingestao_id, fonte, entidade, modo, status, janela_inicio, janela_fim,
       linhas_carregadas, iniciada_em, erro
FROM bronze._execucoes
WHERE fonte = '<fonte>'
ORDER BY iniciada_em DESC
LIMIT 10
```

Ela responde três perguntas: quando foi o último `SUCESSO`, qual janela
falhou e com que mensagem.

### 2.2 O log daquela execução

No Cloud Logging, com o `ingestao_id` da linha acima:

```
jsonPayload.ingestao_id="<id>"
```

Mais consultas prontas em [`observabilidade.md`](observabilidade.md).

### 2.3 O agendamento

No console, **Cloud Scheduler**: o job `ingestao-<conector>`, com hífen no lugar do sublinhado (`ingestao-bcb-cambio-ptax`), mostra a
última execução e o resultado. Pausado ou sem execução recente explica o
alerta de silêncio sem erro nenhum no log.

## 3. Causas típicas e o que fazer

### 3.1 Origem fora do ar ou lenta

**Sinal:** erro HTTP 5xx, *timeout* ou conexão recusada no log, em execuções
que antes passavam.

**Ação:** em geral, nenhuma. O agendamento usa janela móvel
(`ultimos_dias` em `infra/modules/scheduler/main.tf`: 3 ou 5 dias no BCB, 30
no ONS), então a próxima execução bem-sucedida cobre o dia perdido. Se a
queda passar da janela, reprocessar o intervalo (§4.1).

### 3.2 A origem mudou o formato

**Sinal:** alerta de inválidos ou de carga zerada; no log, `registro inválido
descartado` com o campo que falhou.

**Ação:**
1. Não mudar a validação para "aceitar qualquer coisa". O descarte é o que
   impediu dado errado de chegar à Gold.
2. Ajustar o schema Pydantic do conector, com teste antes (TDD), e publicar
   pelo fluxo normal de PR e deploy ([`deploy.md`](deploy.md)).
3. Reprocessar **a partir do raw arquivado** (§4.2). O arquivo original já está
   no GCS; não é preciso pedir de novo à origem.

### 3.3 Credencial expirada ou revogada

**Sinal:** HTTP 401 ou 403, ou erro de autenticação no banco.

**Ação:** gravar uma **nova versão** do segredo no Secret Manager, pelo
procedimento de [`credenciais.md`](credenciais.md). A credencial nunca vai por
e-mail, chat, issue ou log. O job lê a versão mais recente na próxima execução.

### 3.4 Dataform falhou

**Sinal:** o alerta do Dataform. No console, **Dataform → repositório →
Workflow executions**, a execução com erro mostra a ação que falhou.

**Ação:**
- **Asserção reprovada** (duplicata, nulo em chave, valor fora de domínio): o
  dado da Bronze está lá, e o problema está na regra ou na origem. Ler a
  asserção antes de relaxá-la.
- **Erro de SQL ou de permissão:** corrigir por PR. A próxima execução diária
  recompõe Silver e Gold a partir da Bronze.

### 3.5 Custo acima do previsto

**Sinal:** alerta de orçamento.

**Ação:** no BigQuery, **Histórico de jobs** ordenado por bytes processados.
O suspeito usual é consulta sem filtro na coluna de partição, que varre a
tabela inteira. Toda tabela Bronze é particionada e clusterizada para que o
filtro por data resolva isso.

## 4. Reprocessar

Pessoa não executa job direto (ADR 015). O disparo manual é pelo workflow
**Executar ingestão** do GitHub, que registra quem disparou, qual conector e
com que janela.

### 4.1 Uma janela, direto da origem

Workflow **Executar ingestão**, com `environment`, `conector` (como
`ons_carga`; a lista sai de `alupdata listar`), `de` e `ate`.

### 4.2 Replay de um raw já arquivado

Mesmo workflow, com `uri` apontando para o objeto `gs://` do raw e a **janela
original** em `de` e `ate`. A execução fica com `modo = REPLAY` em
`bronze._execucoes`. É o caminho depois de uma correção de schema (§3.2).

### 4.3 Conferir

Nova linha em `bronze._execucoes` com `SUCESSO` e, depois da próxima execução
do Dataform, as linhas na Silver sem duplicata.

## 5. Registrar

Todo incidente que exigiu ação vira issue com a etiqueta `tipo/bug`, com o
`ingestao_id`, a janela afetada, a causa e o que foi feito. Incidente cuja
causa é dependência da Alup ou de terceiro leva `tipo/dependencia`, e o prazo
vai numa linha `Prazo: AAAA-MM-DD`, que o painel do projeto lê.
