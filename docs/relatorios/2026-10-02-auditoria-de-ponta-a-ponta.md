# Auditoria de ponta a ponta — 02/10/2026

Contrato CPS-01025/2026 · AlupData Fase 1: DataLake · referência: `main` em `cdae310`.

Este documento confronta **o que o projeto declara** (documentos, painel, issues) com **o que existe de
verdade** (repositório e ambientes), contra o contrato e o cronograma. Cada número tem ao lado a forma como
foi conferido. Onde o declarado e o verificado divergem, a divergência está dita e tem dono.

Três frentes cruzadas:

1. **Declarado:** `docs/status.md`, `docs/proximos-passos.md`, `docs/acoes-humanas.md`, `painel/marcos.toml`,
   `painel/aditivo.toml`, o dossiê REL-2026-09-25-D e as issues abertas.
2. **Repositório:** código, testes, definições SQL, Terraform, CI.
3. **Ambientes:** BigQuery, Cloud Run, Scheduler, Monitoring e GitHub Actions de `dev` e `hml`; existência de `prod`.

Consultas feitas em 02/10/2026, entre 01h e 05h (horário de Brasília). O contrato é lido pelo
[`resumo-contrato.md`](../contrato/resumo-contrato.md): o texto integral das cláusulas não está no repositório.

## 1. Resumo

| Pergunta | Resposta |
|---|---|
| As Ondas 0 e 1 estão entregues? | **Sim, em aceite.** As 23 fontes carregam em `dev` e `hml`, com os sete componentes cada. Nenhuma onda está **aceita**: o pedido de aprovação por escrito seguiu a Eduardo Pires em 01/10 e não há resposta. |
| Quanto do projeto está pronto? | **343,8 de 580 h (59,3%)** pelo critério do painel. Só 208,6 h estão em aceite (Ondas 0 e 1); **0 h estão aceitas**. |
| O que está nos 59,3%? | Ondas 0 e 1 (208,6 h) e **135,2 h adiantadas** das Ondas 2, 3 e 4, que dependem da Alup. |
| Há dado incompleto? | **Havia, em duas fontes pesadas do ONS** (§6). **Corrigido no mesmo dia (02/10):** recarga em janelas de 3 meses e conferência mês a mês; `dev` e `hml` ficaram com 25 de 25 meses, idênticos. O ponto cego do monitoramento continua aberto. |
| Há algo vencido do lado da Alup? | Sim: **#258** (quem assina o aceite, prazo 29/09) e **#260** (32 h do item 2.1, prazo 30/09). A **#259** (confirmar a reunião de aceite) foi **fechada em 02/10**: a reunião ocorreu em 01/10 (§10). |
| O que trava a próxima onda? | Credenciais da Onda 2 (#262, contrato 19/10) e da Onda 3 (contrato 16/11), rede do FMB e planilhas (G3). Tudo externo. |
| Produção existe? | **Não.** O projeto `prod-alupdata` está ativo, mas sem a API do Cloud Run e sem infra aplicada. O bootstrap (item 1.9) espera o aceite. |

## 2. Cronograma e marcos

Fonte: `resumo-contrato.md` (cláusulas 3ª e 4ª) e `painel/marcos.toml`. As somas fecham: 580 h, R$ 148.480
(R$ 256 por hora), percentuais somando 100%.

| Onda | Janela contratual | Horas | % | Marco | Declarado | Verificado em 02/10 |
|---|---|---|---|---|---|---|
| 0 Fundação | 31/08–11/09 | 90 | 15,52% | R$ 23.040 | entregue em 25/09 | confirmado; ressalvas na §3 |
| 1 Mercado | 14/09–16/10 | 120 | 20,69% | R$ 30.720 | entregue em 25/09 | confirmado; ressalva de dado na §6 |
| 2 Credenciais | 19/10–13/11 | 110 | 18,97% | R$ 28.160 | aguarda Alup | confirmado |
| 3 Sistemas internos | 16/11–18/12 | 155 | 26,72% | R$ 39.680 | aguarda Alup | confirmado |
| 4 Planilhas e handoff | 21/12–08/01/2027 | 105 | 18,10% | R$ 26.880 | aguarda Alup | confirmado |

- **Onda 0 (prazo 11/09):** entregue em 25/09. O ambiente GCP (A3) venceu em 04/09 e chegou em 23/09,
  19 dias corridos depois; pela cláusula 3ª o prazo que depende do insumo se posterga, e o painel registra
  30/09. É registro de fato e de data: a decisão sobre o efeito contratual é da coordenação.
- **Onda 1 (prazo 16/10):** entregue em 25/09, 21 dias antes do fim da janela.
- **Pagamento (cláusula 6ª):** 10 dias após a aceitação formal da medição e a nota fiscal; faturamento dividido em
  6 coligadas. Os marcos 1 e 2 somam **R$ 53.760 (36,21%)**, ou R$ 8.960 por coligada. Hoje **R$ 0 está aceito**.
- **Datas externas que vêm aí:** 12/10 (feriado e data interna pedida para as credenciais), **16/10** (fim da janela
  da Onda 1), **19/10** (prazo contratual dos tokens da Onda 2), 09/11 (data pedida para a VPN) e **16/11** (prazo
  contratual das credenciais da Onda 3).

### Cálculo do progresso (painel)

`pct = 100 × Σ(horas do item × fração pronta) / 580`. Recalculado à mão do `marcos.toml` e conferido contra o
`dados.json` gerado pelo próprio painel (`scripts/painel.py`):

| Onda | Horas prontas | % da onda |
|---|---|---|
| 0 | 88,6 de 90 | 98,4% |
| 1 | 120 de 120 | 100% |
| 2 | 61,2 de 110 | 55,6% |
| 3 | 17,5 de 155 | 11,3% |
| 4 | 56,5 de 105 | 53,8% |
| **Total** | **343,8 de 580** | **59,3%** |

O painel mostra ritmo real de 12,3 h por dia útil contra 6,5 do plano, em 28 dias úteis. **O 59,3% mede
trabalho feito, não faturamento**, e quase 40% dele está em ondas que só avançam com insumo da Alup.

## 3. Onda a onda: o que está pronto e o que não está

### Onda 0 — Fundação (98,4%)

| Item | Fração | Verificação |
|---|---|---|
| 0.1–0.9, 0.10, 0.11, 0.13 | 100% | framework, CLI, Terraform, CI/CD, ADRs, runbooks, Questionário, domínios, dimensões: existem no repositório e rodam |
| 0.12 RACI | 75% | recebida em 15/09; dois pontos abertos (**#150**: composição do Comitê e papel do Google) |
| 0.14 Primeiro deploy | 100% | `bcb_cambio_ptax` com SUCESSO em **8 dias seguidos em `dev`** (24/09–01/10) e 7 em `hml` (25/09–01/10); meta de 3 |
| 0.15 Portal MVP | 95% | no ar em `dev` e `hml`; **falta o primeiro login efetivo da Alup**: o grupo `alup.alertas` tem 7 usuários nomeados (29/09), mas não há como verificar um login real |

### Onda 1 — Mercado (100%)

Conferência feita fonte a fonte, não por amostra. As 23 entidades das Ondas 0 e 1 do `marcos.toml`:

- **todas aparecem na saúde de `hml` e em situação OK**;
- **todas têm linhas na Bronze e na Silver, em `dev` e em `hml`**;
- as definições Bronze, Silver e Gold, o teste, o agendamento e o dicionário existem para as 44 fontes registradas (§4).

**Ressalva:** completude de histórico em `hml`, §6. O dossiê afirma carga **com sucesso** das 23 fontes, e isso
procede; ele não afirma 24 meses completos.

### Onda 2 — Credenciais (55,6%, aguarda a Alup)

| Item | Fração | Verificação |
|---|---|---|
| 2.1 CCEE agente credenciado | 0% | sem caminho definido; aguarda a posição da Alup (**#260**) |
| 2.2 BBCE | 80% | conector, Silver e Gold escritos; tabela Bronze **vazia** em `dev` e `hml`; falta o acesso (#23) |
| 2.3 Hubspot | 80% | idem; falta o token (#24) |
| 2.4 TempoOK | 80% | `tempook_ena_prevs` com 11 linhas na Silver em `dev`; **em `hml` o segredo está vazio** (a tela mostra "aguardando credencial"); `tempook_boletins` roda sem dado: o acervo alcançável termina em 26/10/2022 (**#129**) |
| 2.5 Gold de preço e posição | 70% | tabelas escritas; as de BBCE, Hubspot e TempoOK **estão vazias** (4 Gold em `hml`, 3 em `dev`) |

### Onda 3 — Sistemas internos (11,3%, aguarda a Alup)

- 3.5 Cloud Workflows (100%): **mecanismo escrito e validado em `infra/modules/orquestracao`, não implantado**.
  O recurso só sobe quando houver fonte interna, e `gcloud workflows list` não encontra nenhum em `dev` nem em `hml`.
  A fração de 100% vale para o mecanismo, não para um workflow em operação.
- 3.1 Oracle FMB (10%) e 3.3 MySQL RDS (10%): lado GCP da rede pronto em 25/09 (ADR 024). **O último teste de
  conexão falhou em 25/09**, como esperado: faltam a rota (G6), o FortiGate e o listener (L1–L5) e a credencial (N3).
  O pedido de rede foi enviado em 25/09.
- 3.2 Portal Alup, 3.4 RM/TOTVS e 3.6 Gold interna: 0%.

### Onda 4 — Planilhas e handoff (53,8%, aguarda a Alup)

| Item | Fração | Verificação |
|---|---|---|
| 4.1 Motor S2 Data Intake | 70% | motor pronto; faltam os templates, que dependem das planilhas (G3, **#142**) |
| 4.2 Fontes pendentes | 0% | depende das ondas anteriores |
| 4.3 Knowledge Catalog | 100% | glossário com **19 termos** (conferido em `glossario.tf`); **44 das 47 Gold anotadas**; as três ficam de fora por serem operacionais (`saude_ingestao`, `volumetria_lake`, `custo_consultas`) |
| 4.4 Gold consolidadas | 70% | `indicadores_mensais` em `dev` e `hml`; **cobertura desigual entre os dois** (§6); aceite da leitura da ADR 012 pendente |
| 4.5 Documentação final | 30% | 43 documentos de dicionário cobrem as 44 fontes (mais 2 técnicos); faltam o consolidado final e o glossário de entrega |
| 4.6 Handoff técnico | 20% | runbook de incidente escrito; falta o pacote de handoff |

## 4. Os sete componentes por fonte (cláusula 2ª)

"Fonte com 5 de 7 não é entrega parcial, é retrabalho na medição." Conferido por script contra o **registro de
conectores do código**: 44 conectores registrados.

| Componente | Presente |
|---|---|
| 1 Conector Python | 44/44 |
| 2 Tabela Bronze (`definitions/bronze`) | 44/44 |
| 3 View Silver (`definitions/silver`) | 44/44 |
| 4 Gold que lê a Silver da fonte | 44/44 |
| 5 Testes (arquivo de teste que importa o módulo do conector) | 44/44 |
| 6 Agendamento (`infra/modules/scheduler`) | 44/44 |
| 7 Dicionário com linhagem | 44/44 (`ons_restricao_coff_eolica` e `_fotovoltaica` compartilham `ons_restricao_coff.md`) |

A conferência dos componentes 4 e 5 é por presença de arquivo e referência, **não por qualidade do conteúdo**. A
qualidade dos testes aparece na cobertura (§7).

## 5. Ambientes

| | `dev` | `hml` | `prod` |
|---|---|---|---|
| Projeto GCP | ativo | ativo | ativo; **API do Cloud Run desabilitada: o Portal não existe** |
| Portal | **revisão 00038, commit `5ec8c58` (= main)** | **revisão 00018, commit `cdae310`** | não existe |
| Tabelas Bronze / Silver / Gold | 45 / 45 / 47 | 45 / 45 / 47 | não existe |
| Fontes com dado na Bronze | 41 de 44 | 40 de 44 | n/a |
| Gold com linhas | 43 de 47 | 42 de 47 | n/a |
| Jobs agendados | 41 habilitados | 40 habilitados | n/a |
| Políticas de alerta | 20 habilitadas, 1 canal de e-mail | 20 habilitadas, 2 canais de e-mail | n/a |
| Dataform | não reexecutado desde o deploy de 29–30/09: a Gold não tem a coluna `aguardando_credencial` | `SUCCEEDED` em 02/10 03h31 | n/a |

- **`dev` estava atrás da `main` e foi alinhado em 02/10:** o Portal de `dev` era de 29–30/09 e a `saude_ingestao` não
  tinha a coluna `aguardando_credencial`; as três fontes mensais do ONS apareciam como atrasadas pelo falso atraso já
  corrigido (PR #332). Deploy feito: Portal na revisão 00038 (`main`), Gold com a coluna nova. Em `dev` ficam fora de
  OK só `hubspot_negocios` (aguardando credencial) e `tempook_boletins` (atrasada: acervo termina em 2022).
- **Gold com linhas:** as 4 vazias em `hml` são as de BBCE, Hubspot e TempoOK (`curva_forward_vigente`,
  `funil_comercial`, `cobertura_boletins_tempook`, `cobertura_ena_prevs_tempook`). `custo_consultas` não pude ler
  (a minha conta não tem `INFORMATION_SCHEMA`); a conta de serviço do Portal lê.
- **Acesso:** `https://alupdata-portal-u6o7nifu6q-uc.a.run.app` exige login (redireciona ao Google). O cliente OAuth do
  IAP continua o de 29/09.

## 6. Completude do dado: o achado desta auditoria

> **Corrigido em 02/10, entre 08h e 10h.** As seções "O que foi encontrado" a "Impacto" descrevem o estado **antes** da
> correção; o resultado está em "Correção executada", ao fim desta seção.

A carga **com sucesso** das 23 fontes está comprovada. O histórico de **24 meses** das fontes pesadas do ONS não está
completo, e a tela de saúde não mostra isso, por um ponto cego do monitoramento.

### O que foi encontrado

Comparei a Silver de `hml` com a de `dev` para as 45 fontes. Três se afastam mais de 10%:

| Fonte | Silver `hml` | Silver `dev` | Situação |
|---|---|---|---|
| `ons_geracao_usina` | 4,87 M | 10,88 M | `hml` com **11 de 25 meses**; `dev` com 22 |
| `ons_restricao_coff_eolica` | 2,94 M | 4,90 M | `hml` com **14 de 25 meses**; `dev` com 22 |
| `ccee_geracao_usina` | 5,82 M | 2,96 M | `hml` com 2 meses; `dev` com 1 (a CCEE publica poucos meses) |

- **`hml`, `ons_geracao_usina`:** faltam jun/2025 a jul/2026 e há dois meses parciais (mai/2025 com 30% e ago/2026 com
  52%). A Bronze tem **13,1 M de linhas contra 10,9 M em `dev`** e, mesmo assim, a Silver é menor: os primeiros
  meses foram carregados **três vezes** e a Silver deduplica.
- **`hml`, `ons_restricao_coff_eolica`:** mesmo padrão, faltam set/2025 a jul/2026; Bronze com 2,7 vezes a Silver.
- **`dev`:** tem **lacunas próprias**: sem jun a ago/2025 em `ons_geracao_usina` e sem mar a mai/2025 em
  `ons_restricao_coff_eolica`.

### Causa

- **`hml`:** em 29/09 a recarga foi pedida em **uma janela só de 25 meses**
  (`ingerir ons_geracao_usina --de 2024-09-01 --ate 2026-09-29`). A execução do Cloud Run estourou o **tempo limite
  de 1800 s** (`The configured timeout was reached`) nas três tentativas permitidas, entre 22h37 de 29/09 e 00h22 de
  30/09. O mesmo ocorreu com a eólica, entre 20h53 e 22h37. Cada tentativa gravou um pedaço na Bronze e morreu antes
  de registrar a execução.
- **`dev`:** a recarga foi feita **em janelas de 3 meses** (certo), mas duas janelas ficaram de fora.

### Por que a tela não mostra

`bronze._execucoes` só recebe a linha **ao fim** da execução. Execução morta por tempo limite grava dado e **não deixa
registro**. A saúde de `ons_geracao_usina` em `hml` usa a execução de 25/09, bem-sucedida, e mostra OK. É um ponto
cego: "último sucesso recente" não prova que o histórico está inteiro.

### Impacto

- **Indicadores:** em `hml`, o `fator_capacidade` tem 11 meses (22 em `dev`) e a `taxa_corte_renovavel` tem 87 linhas
  (124 em `dev`). As tendências de fator de capacidade aparecem curtas na tela.
- **Marco de 29/09:** "carga de 24 meses em `hml`" era verdadeira para 42 das 44 fontes e parcial para duas. O
  `status.md` repetia "disponibilidade e fator de capacidade cobrem os 24 meses" em `dev`; o fator cobre **22**.
- **Aceite:** o dossiê das Ondas 0 e 1 não depende disso (afirma sucesso de carga). O pedido de aprovação do Portal
  mostra os indicadores de `hml`, então vale recarregar antes que alguém compare séries.

### Correção recomendada

1. Recarregar em `hml`, em janelas de 3 meses, `ons_geracao_usina` (jun/2025 a jul/2026, mais mai/2025 e ago/2026
   inteiros) e `ons_restricao_coff_eolica` (set/2025 a jul/2026, mais ago/2025 e ago/2026). Cerca de 9 minutos por
   janela. A Bronze é append-only e a Silver deduplica, então recarregar é seguro.
2. Em `dev`, as janelas jun–ago/2025 (geração) e mar–mai/2025 (eólica).
3. Rodar o Dataform e conferir os meses por fonte.
4. **Fechar o ponto cego:** execução do Cloud Run que falha ou estoura o tempo deve gerar alerta, e a saúde deve
   desconfiar de Bronze sem execução registrada. Hoje o limite de silêncio só enxerga o último sucesso.
5. Documentar no runbook que recarga longa se faz em janelas de até 3 meses.

### Correção executada (02/10)

Passos 1 a 3 feitos pelo workflow `Executar ingestão`, uma janela por vez (11 a 16 minutos cada, bem abaixo do limite
de 30):

| Ambiente | Fonte | Janelas | Resultado |
|---|---|---|---|
| `hml` | `ons_geracao_usina` | 6 (mai/2025 a ago/2026) | todas `success` |
| `hml` | `ons_restricao_coff_eolica` | 5 (ago/2025 a ago/2026) | todas `success` |
| `dev` | `ons_geracao_usina` | 1 (jun a ago/2025) | `success` |
| `dev` | `ons_restricao_coff_eolica` | 1 (mar a mai/2025) | `success` |

Em seguida o Dataform rodou nos dois ambientes (`SUCCEEDED`), com `terraform apply` **sem nenhuma mudança** (0 a
adicionar, 0 a alterar, 0 a destruir). Conferência no BigQuery:

| Fonte (Silver) | `hml` | `dev` |
|---|---|---|
| `ons_geracao_usina` | **25/25 meses**, 12.441.587 linhas | **25/25**, 12.441.587 |
| `ons_restricao_coff_eolica` | **25/25**, 5.583.456 | **25/25**, 5.583.456 |
| `ons_restricao_coff_fotovoltaica` | 25/25, 2.533.824 | 25/25, 2.513.664 |
| `ons_disponibilidade_usina` | 25/25, 4.196.981 | 25/25, 4.175.675 |

Indicadores, antes e depois da recarga:

| Indicador | `hml` antes | `hml` depois | `dev` antes | `dev` depois |
|---|---|---|---|---|
| fator de capacidade | 165 linhas, 11 meses | **375, 25 meses** | 330, 22 meses | **375, 25 meses** |
| taxa de corte renovável | 87 linhas | **133** | 124 | **133** |
| armazenamento, disponibilidade | 25 meses | 25 meses | 25 meses | 25 meses |
| PLD real | 3 meses | 3 meses | 3 meses | 3 meses |

`dev` e `hml` ficaram **iguais** nas fontes e nos indicadores. O PLD real tinha 3 meses nos dois: **a causa era o IPCA**, que só
tinha 3 meses (jun a ago/2026) e é o deflator do PLD real; o PLD em si começava em 28/05/2026. **Corrigido em 02/10:** `ccee_pld` e
`ibge_ipca` recarregados de 09/2024 em `dev` e `hml` e Dataform rodado; o PLD real passou a ter 24 meses (09/2024 a 08/2026) nos dois. As pequenas diferenças da fotovoltaica e da disponibilidade (0,1% a 0,8%) vêm de
cargas diárias em instantes diferentes.

**Continua aberto:** o ponto cego do passo 4 (execução que estoura o tempo ou deixa dado sem registro) e a nota de
runbook do passo 5.

## 7. Qualidade e segurança

| Verificação | Resultado | Como |
|---|---|---|
| Testes unitários | **1.542 passam**, 434 ignorados | `pytest tests/` |
| Cobertura | **95%** (4.164 instruções, 208 sem cobertura) | `--cov=src` |
| CI da `main` | todas as verificações verdes (CodeQL, SAST, segredos, lint, Terraform, Dataform, atribuição) | `gh pr checks`, execução de 02/10 |
| Auditoria de dependências | passa, depois da atualização de `urllib3` e `virtualenv` (#330) | `pip-audit --strict` na CI |

Dos 434 testes ignorados, **415 são casos parametrizados de regras SQL** que só valem para uma camada; os outros 19
dependem de token da Alup (TempoOK, BBCE, Hubspot) ou de contêineres de banco locais. O dossiê de 25/09 citava 1.085
testes e 94%: o crescimento acompanha o Aditivo 01 e o Portal.

## 8. Aditivo 01

Conferência de `painel/aditivo.toml` contra o documento do aditivo:

| Estado | Itens | Horas |
|---|---|---|
| Entregue | 17 (itens 1–11 e 20–25) | **83 h** |
| Pendente | 8 (B: 12–15; C: 16–17; D: 18–19) | **79 h** |
| Item 26 em revisão (fora do subtotal) | 1 | 6 h |

**Segunda verificação da evidência de linhas.** As contagens da §5 do documento do aditivo (de 29/09) conferem com a
Silver de hoje nas 17 fontes entregues: `dev` está de 0,1% a 0,5% acima, por cargas diárias posteriores, e **`hml` tem
exatamente as mesmas linhas de `dev`**. O Aditivo 01 está completo nos dois ambientes.

Subtotal dos itens 1–25: **162 h** (83 + 79). **O `status.md` e o `proximos-passos.md` diziam 57 h pendentes:
estava errado; são 79 h.** Corrigido. A forma de medição e o valor continuam em aberto: o aditivo diz "fora das 580 h",
e o enquadramento contratual é da coordenação com a Alup.

## 9. Portal e painéis

- **Portal (hml):** quatro telas na identidade da Alup; Indicadores como tela de abertura (`/`); modo telão
  (`?telao=1`, sem JavaScript); cache de 5 minutos nas leituras; carimbo com a hora real da leitura (ADR 025). O
  desenho foi conferido com as 41 fontes reais de `hml` em três alturas de janela.
- **Painel da ness. (`painel.alupdata.ness.com.br`):** atualizado nesta auditoria (§11). O que ele calcula sozinho
  (cargas, dias seguidos, pendências, teste de conexão) vem de `bronze._execucoes`, das issues
  `tipo/dependencia` e do Cloud Run; o que é editado à mão (`painel/marcos.toml`, `painel/aditivo.toml`) foi
  conferido item a item.
- **Aprovação do Portal:** o pedido foi **enviado** a Eduardo Pires em 02/10 (01h40), sem resposta até aqui.

## 10. Pendências por dono

### Alup

| Pendência | Prazo | Situação em 02/10 |
|---|---|---|
| **#258** quem assina o aceite das Ondas 0 e 1 | 29/09 | **vencida**; sem resposta registrada |
| **#259** confirmar a reunião de aceite | 29/09 | **fechada em 02/10**: a reunião ocorreu em 01/10 |
| **#260** posição sobre as 32 h do item 2.1 | 30/09 | **vencida** |
| **#262** credenciais da Onda 2 (Hubspot e BBCE) | 12/10 (contrato: 19/10) | aberta |
| **#12–#15** VPN e credenciais das fontes internas | 09/11 (contrato: 16/11) | abertas |
| Rede da Onda 3: rota (G6), FortiGate e listener (L1–L5), credencial (N3) | sem data | abertas; teste de conexão falhou em 25/09 |
| **#142** planilhas da proposta (G3) | 01/10, **movido por acordo** | Leonardo propôs (01/10) data perto da Onda 4 e a ness. aceitou; sem nova data. **Não está vencido.** |
| **#141** de-para de usina | 01/10 | **`usinas.csv` chegou** em 01/10 (14 usinas; Usinas, Nome do ativo, UC/CEG); falta confirmar o recebimento e ver o que cobre |
| **#129/#174** acervo e caminhos do TempoOK; **#150** RACI | sem data | abertas |
| **#87** orçamento e destinatários dos alertas | — | **orçamento respondido** ("manter o recomendado": US$ 20/mês até novembro, US$ 400 depois); falta o papel de Costs Manager para as contas de serviço (item 12) |
| Billing export (console) | — | **feito pela QI Network em 01/10** em `dev`: duas tabelas no dataset `faturamento`; histórico desde 01/10 |

### ness.

- ~~Recarga do histórico de `hml` e `dev`~~ e ~~deploy em `dev`~~: **feitos em 02/10** (§6).
- Aditivo B, C e D (79 h) e decisão sobre o item 26.
- Bootstrap de `prod` (item 1.9), depois do aceite.
- ~~Enviar o pedido de aprovação do Portal~~: **enviado em 02/10**.
- Confirmar na #141 o recebimento do `usinas.csv` e conferir o que ele cobre.
- Trocar o orçado do Portal de US$ 120 para a referência da Alup (US$ 20 até novembro).
- Fechar issues já cumpridas (lista na §11).
- **#188** mecanismo de alerta para fonte semanal e mensal, hoje sem alerta próprio.

## 11. Inconsistências encontradas e o que foi corrigido

**Corrigido nesta auditoria** (`painel/marcos.toml` e documentos):

1. Marco de 01/10 "Reunião de aceite" estava **previsto**; a reunião ocorreu. Passa a **feito**, com o pedido de
   aprovação enviado a Eduardo Pires no mesmo dia.
2. Marco de 29/09 afirmava "carga de 24 meses em hml" sem ressalva. Ganhou a ressalva das duas fontes parciais.
3. Item 4.3: "anotações das 26 Gold" passa a **44 das 47**.
4. Item 4.4: "24 meses em `dev`, `hml` pendente" passa a 25 meses nos dois, com o fator de capacidade em 22 e 11.
5. Item 4.5: "dicionário das 27 entidades" passa a **44 fontes**.
6. Item 3.5: nota de que o mecanismo existe e **não está implantado**.
7. Item 0.15: nota do redesenho de 02/10.
8. Dois marcos futuros do contrato entraram: 16/10 (fim da janela da Onda 1) e 19/10 (tokens da Onda 2).
9. `status.md` e `proximos-passos.md`: **57 h → 79 h** pendentes no Aditivo; cabeçalhos datados de 25/09 e 23/09
   atualizados; "ADRs 001–023" e "25 dicionários" atualizados; trechos superados sinalizados.

**Para decisão de quem coordena** (não alterei):

- **Quem assina o aceite:** `interlocutores.md` nomeia Taina Mota como aprovadora (B4). Em 29/09 o Leonardo
  respondeu que **Eduardo Pires é o membro do comitê aprovador de passagem de fase**, e os pedidos de aprovação foram
  dirigidos a ele. Falta a Alup confirmar que ele também assina o aceite (#258). Atualizar `interlocutores.md` então.
- **13 fontes × 27 × 44:** o contrato fala em 13 fontes; o repositório tem 44 conectores. A conciliação continua
  "pendente" no `status.md` desde 24/09 e depende da #142.
- **Aditivo e as 580 h:** `aditivo.toml` diz "fora das 580 h"; o documento do aditivo usa "28% das 580 h" como
  referência. Os dois dizem coisas compatíveis, mas o texto precisa de uma frase só.
- **Issues já cumpridas e ainda abertas** (sugestão de fechamento, com a evidência acima): #95 primeiro deploy real,
  #89 agendamento da Onda 1, #90 ajustes de framework, #17 conector CCEE InfoMercado (marcada "em revisão"), #6 Portal
  MVP, #36 Dataplex. Fechar issue é visível à Alup; deixei para o Ricardo.

## 12. Riscos, em ordem

1. **Ponto cego do monitoramento** (§6): carga parcial por tempo limite não deixa registro e a saúde mostra OK. O dado já foi corrigido; a causa de fundo não.
2. **Portal sem login efetivo da Alup** confirmado: o aceite do 0.15 e o pedido de aprovação do Portal dependem de
   alguém da Alup conseguir abrir.
3. **Aceite não assinado:** nenhuma onda está aceita; o faturamento não começa antes disso.
4. **Credenciais da Onda 2:** 12/10 interno e 19/10 contratual; se atrasarem, o dossiê de 23/10 também.
5. **Rede da Onda 3:** quatro pendências da Alup em cadeia, e o prazo contratual é 16/11.
6. **`dev` e `hml` evoluem por deploys separados:** divergiram por cinco dias e foram alinhados em 02/10; vale deployar os dois juntos.
7. **Dependência do token do TempoOK:** o segredo de `hml` está vazio por decisão (ADR 020).

## Anexo: como cada número foi obtido

- **Matriz dos 7 componentes:** script sobre `src.core.registry` (44 conectores), conferindo `definitions/bronze|silver`,
  referências `ref("silver", …)` nas Gold, arquivos de teste que importam o módulo, chaves de `infra/modules/scheduler`
  e `docs/dicionario-dados`.
- **Estado real:** consultas REST ao BigQuery de cada projeto (`bronze.__TABLES__`, contagem por view, `gold.saude_ingestao`,
  `bronze._execucoes`), `gcloud run services|jobs|executions`, `gcloud scheduler jobs list`, API de monitoramento,
  `gh run list` e `gh pr checks`.
- **Painel antes e depois:** `uv run python -m scripts.painel --saida dados.json`, com as credenciais do operador.
- **Testes:** `uv run pytest tests/ --cov=src`.
