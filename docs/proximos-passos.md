# Próximos passos — fila de execução

Documento **vivo**: é para riscar linha, não para arquivar. Atualizado em
**2026-09-25**.

Ele existe para responder uma pergunta que os outros três não respondem em uma
tela: **qual é a próxima ação, de quem é, e qual comando a executa.**

- [`status.md`](status.md) — onde estamos e o que trava o quê (fonte da verdade)
- [`plano-semanal.md`](plano-semanal.md) — o que sai em cada semana
- [`plano-execucao.md`](plano-execucao.md) — escopo e estimativa por onda
- [`acoes-humanas.md`](acoes-humanas.md) — **como** se executa o que exige uma pessoa: token, credencial, decisão e pedido à Alup
- **este arquivo** — a fila, com dono e comando
- [`planos/2026-09-24-fechamento-das-ondas.md`](planos/2026-09-24-fechamento-das-ondas.md) — as fases até o dossiê de cada onda, com datas e condições

Quando um item fecha, sai da fila ativa; os registros datados abaixo são
históricos. As ações externas da seção 2 ficam com a coordenação da ness.,
em acompanhamento com a Alup; sua execução não é presumida por esta revisão.

---

## 1. O que está travando tudo

**Nada externo trava o primeiro apply desde 23/09.** A Alup liberou o GCP nos
três ambientes e a cadeia passou a ser trabalho da ness.:

    bootstrap do dev → 1º apply → Onda 0 homologada

| # | Ação | Dono | Situação |
|---|---|---|---|
| ~~1.1~~ | ~~Gravar os IDs reais nos `.tfvars`~~ | ness. | **feito em 23/09**, nos seis arquivos de `infra/environments/` e `infra/bootstrap/environments/`. Os IDs ficam como a Alup criou — renomear é processo longo do lado dela e ID de projeto é imutável ([adendo da ADR 015](arquitetura/decisoes/015-fundacao-do-ambiente.md)) |
| ~~1.2~~ | ~~Conferir o que veio junto com a liberação~~ | ness. | **feito em 23/09** (A13 do status). Passou: faturamento, os seis papéis, `iam.allowedPolicyMemberDomains` e `iam.workloadIdentityPoolProviders` |
| ~~1.2a~~ | ~~Pedir à Alup a liberação de `us-east1`~~ | ness. | **resolvido por decisão em 23/09**, sem pedido: a política herdada admite só `us-central1`, e a [ADR 023](arquitetura/decisoes/023-regiao-us-central1.md) substituiu a 011. Pedir exceção custaria outra espera de prazo desconhecido; trocar a região, enquanto nada existe, é editar variável |
| ~~1.3~~ | ~~Bootstrap do `dev` e as variáveis no GitHub~~ | ness. | **feito em 23/09**: 38 recursos aplicados, state copiado para o bucket e as cinco variáveis gravadas no ambiente `dev` e nas do repositório. Ver N3 no [`status.md`](status.md) |
| ~~1.5~~ | ~~Primeiro `terraform apply` do `infra/` em `dev`~~ | ness. | **feito em 23/09**: 148 recursos, incluindo os 27 jobs agendados e o Portal no ar. Ver N5 no [`status.md`](status.md) |
| ~~1.6~~ | ~~Gravar o token do GitHub no secret `alupdata-dataform-git-token`~~ **feito em 24/09; Dataform de pé** — e apontar `DATAFORM_GIT_TOKEN_VERSAO` no ambiente `dev`, depois reexecutar o deploy | ness. (humano) | **é o que falta para o Dataform existir** — e sem Dataform não há Bronze, Silver nem Gold. O token é *fine-grained*, restrito a `nessenergy/Alupdatalake`, só *Contents: Read-only*. Passo a passo em [`acoes-humanas.md`](acoes-humanas.md) §1 e no `runbook/primeiro-deploy.md` §3 |
| ~~1.7~~ | ~~Bootstrap e `infra/` do `hml`~~ | ness. | **`hml` no ar em 25/09**: 174 recursos, Dataform em `SUCCEEDED`, janela de homologação das Ondas 0 e 1 aberta (#228). `prod` fica para depois do aceite das Ondas 0 e 1 |
| 1.4 | **Rotação do token do TempoOK** — a [ADR 020](arquitetura/decisoes/020-token-tempook-rotacao-na-producao.md) a define como a primeira ação depois de A3 | ness./TempoOK | **desbloqueada**: o Secret Manager do `dev` existe desde 23/09 |

> O atraso de A3 está registrado em
> [`relatorios/2026-09-04-a3-nao-entregue.md`](relatorios/2026-09-04-a3-nao-entregue.md),
> emitido no dia em que a situação se configurou. Condicionar A3 a G1 não
> interrompe a contagem da cláusula 3ª — o contrato conta o atraso do insumo,
> não o motivo.

---

## 2. Sua fila

| # | Ação | Como | Pronto quando |
|---|---|---|---|
| 2.2 | **Enviar o relatório de 04/09 à Alup** | `.md` e `.html` prontos em [`relatorios/`](relatorios/) | Registro na mão da contratante |
| 2.4 | **Enviar à Alup o registro de 09/09 sobre E1 e E2** | `.md` e `.html` prontos em [`relatorios/`](relatorios/) | Registro na mão da contratante |
| ~~2.5~~ | ~~Confirmar a entrega prevista de A3 e o responsável~~ | **A3 entregue em 23/09** e a [#55](https://github.com/nessenergy/Alupdatalake/issues/55) fechada. No mesmo dia a ness. comunicou à Alup, por e-mail, os IDs readequados, a adoção de `us-central1` e a conta `gptorres@` sem papel | — |
| 2.13 | **Acertar o valor do orçamento por ambiente** | o padrão do módulo de monitoramento é R$ 500/mês por ambiente e estoura o teto da E2 (US$ 20/mês até novembro, até US$ 400 depois). É o único item vivo da [#87](https://github.com/nessenergy/Alupdatalake/issues/87) | valor acordado e preenchido no `.tfvars`, antes de o alerta de custo subir |
| ~~2.6~~ | ~~**Obter a `billing_account`**~~ | teto e destinatário respondidos em 11/09: US$ 20/mês até novembro e até US$ 400/mês a partir de meados de novembro (E2); alertas para `alup.alertas@alupar.com.br` (E3) | **a conta apareceu na conferência de 23/09**, vinculada aos três projetos. Resta acertar o valor do orçamento por ambiente — [#87](https://github.com/nessenergy/Alupdatalake/issues/87) |
| 2.7 | **Combinar o canal das credenciais seguintes** (BBCE, Hubspot, Onda 3) | o pedido está redigido no [registro de 14/09](relatorios/2026-09-14-documentacao-de-apis-recebida.md) §5. **A rotação do token do TempoOK saiu desta linha** e ficou para a virada de produção ([ADR 020](arquitetura/decisoes/020-token-tempook-rotacao-na-producao.md)) — rotacionar antes de existir Secret Manager entregaria o valor novo pelo mesmo e-mail. **Em 21/09 dois gatilhos dessa ADR foram acionados** (o token alcança a previsão de ENA em dia): a ADR mandava rotacionar de imediato e, ao mesmo tempo, dizia que rotacionar sem Secret Manager renova a exposição. **Decidido em 21/09** (responsável da ADR): vale a seção 3, e a rotação passa a ser a **primeira ação depois de A3** — ver o adendo | a Alup grava cada credencial nova direto no Secret Manager, sem passar por e-mail |
| 2.8 | **Enviar à Alup o registro de 14/09** | `.md` e `.html` prontos em [`relatorios/`](relatorios/) | Registro na mão da contratante |
| 2.9 | **Perguntar à Alup onde estão os boletins recentes do TempoOK, e quais caminhos importam** (A10) — a pergunta mudou em 21/09: o mesmo token alcança a previsão de ENA em dia, então o acervo de 2022 deixou de ser o único fato | [#129](https://github.com/nessenergy/Alupdatalake/issues/129): o token funciona e o caminho está certo, mas nada posterior responde; três hipóteses no [registro de 14/09](relatorios/2026-09-14-documentacao-de-apis-recebida.md) §4.1 | acesso ao acervo recente, ou a informação de que o produto mudou. **Vale juntar com 2.7**: uma conversa só com o fornecedor resolve rotação e acervo |
| 2.11 | **Confirmar entrega dos exemplos de planilha** (Alup) | G3/[#142](https://github.com/nessenergy/Alupdatalake/issues/142), previsão de 18/09 sem confirmação | exemplos recebidos e suficientes para declarar templates e conferir cobertura das 13 fontes |
| 2.12 | **Obter acesso e host do BBCE e token do Hubspot** (Alup) | [#23](https://github.com/nessenergy/Alupdatalake/issues/23), [#24](https://github.com/nessenergy/Alupdatalake/issues/24); credenciais no Secret Manager | acesso liberado para execução dos conectores já implementados |
| 2.9b | **Receber da Alup a lista dos caminhos do TempoOK que interessam** | a Alup disse que vai indicá-los ("nós vamos pegar aqui o caminho dos arquivos que precisamos"); só o do ENA-PREVS é conhecido e só uma combinação de modelos. Estender `MODELOS` em `src/conectores/tempook_ena_prevs.py` é tudo que o conector precisa — [`tempook_ena_prevs.md`](dicionario-dados/tempook_ena_prevs.md). **Também pergunta se o token é estático ou renovável**: a função da Alup usa `get_tok_token()` | lista recebida, ou a informação de que basta o caminho já entregue |
| 2.10 | **Levar dois pontos da matriz RACI à Alup** — recebida em 15/09, [`raci.md`](raci.md) | na reunião de sexta e no relatório de fechamento da S3, não em peça separada: o documento não muda prazo nem marco. Os dois pontos são (a) **quem compõe o Comitê** que a matriz põe como accountable da passagem de fase, já que B4 dá isso a Taina, e (b) **rebaixar o Google de accountable a consultado** na arquitetura. O de-para Fase↔Onda e Core↔Gold já está resolvido do nosso lado (§5 do `raci.md`) e não precisa de resposta | Comitê definido ou B4 confirmado como rito válido; papel do Google acordado — [issue #150](https://github.com/nessenergy/Alupdatalake/issues/150) |

### Por que 2.5 e 2.6 têm pressa

São as duas metades de A3, o único elo que resta antes do primeiro apply. A
previsão é 18/09; a cláusula 3ª já conta atraso desde 08/09, e **passar de 5
dias úteis posterga o cronograma** — 14/09 foi o 5º dia, 15/09 o 6º e
18/09 o 9º dia útil, sem confirmação de entrega. O feriado de 07/09 foi excluído.

---

## 3. Decisões que dependem de você

| # | Decisão | Opções | Efeito |
|---|---|---|---|
| 3.1 | **Campo Semana** | (a) manter seleção `S1`–`S19`, gerenciada pelo script; (b) iteração com datas reais, criada à mão | Iteração não é criável por API. Em (b), o script deixa de gerenciar o campo |
| 3.2 | **Idioma do baralho** | português (atual) ou inglês | Só importa se a plateia do Google não for do Brasil |
| 3.3 | **Redação da exclusão de escopo no baralho de kickoff** | manter ou trocar por "modelos preditivos avançados" | Exclusão legítima da Fase 3; é preferência, não correção |
| 3.4 | **Paralelos restantes** | ~~dicionário de dados · endurecer o Portal MVP~~ — **mudou em 14/09**: com a CCEE destravada, a fila de trabalho útil sem GCP voltou a ser escopo faturável | Ver 3.7 |

Decisões já tomadas: **região** `us-central1` ([ADR 023](arquitetura/decisoes/023-regiao-us-central1.md), que
substituiu a 009) e **tom cordial** nos relatórios (convenção no [README](relatorios/README.md) do
diretório). Em 11/09, com as respostas da Alup: **três ambientes** e **bootstrap pela ness.**
([ADR 015](arquitetura/decisoes/015-fundacao-do-ambiente.md)), **Gold sem KPI nesta fase**
([ADR 012](arquitetura/decisoes/012-dataform.md)) e **contatos e empresas do Hubspot fora do escopo**.
Ainda em 11/09, diante do teto de E2: **orquestração da Onda 3 em Cloud Workflows, sem Composer**
([ADR 017](arquitetura/decisoes/017-orquestracao-sem-composer.md)).

---

## 4. Fila técnica da ness.

### Histórico: entregas de 14/09

| O quê | Branch/PR | Situação |
|---|---|---|
| Fila da ADR 021, ordens 1–5: `ccee_agente`, `ccee_exposicao_financeira`, `ccee_contabilizacao_perfil`, `ccee_geracao_usina`, `ccee_contrato_montante`, `ccee_varejista_consumidor`, `ccee_encargo_ess`, `ccee_energia_reserva`, `ccee_cvu_estrutural` | `worktree-fila-ccee` (sem número de PR ainda) | **9 entidades entregues em 14/09** — 7 componentes cada, contra a API real (`status.md` §1) |

### O que segue parado

| O quê | Bloqueado por |
|---|---|
| Conjuntos secundários ainda não implementados da ADR 021 (§2.1/§3) | demanda dos domínios registrada; ordem de execução e consumo do orçamento a priorizar — mesmo caminho de subclasse de `CceeCsvCkan` quando entrarem |

| # | Ação | Depende de |
|---|---|---|
| 4.2 | Endurecer o Portal MVP enquanto roda com provedor simulado | decisão 3.4 |
| 4.8 | **Próxima fonte pública sem insumo da Alup** — candidatas: térmicas do ONS (`cvu-usitermica`, `geracao-termica-despacho-2`), as entidades secundárias da ADR 021 ainda não implementadas; disponibilidade e constrained-off ONS já entregues | escolha de domínio, não de bloqueio: priorização pelos domínios e pelo orçamento, sem iniciar fonte por mera disponibilidade |
| 4.3 | Versão em inglês do baralho | decisão 3.2 |
| 4.5 | Emitir o relatório de situação da semana | fechamento da S3 (18/09), com evidência de bloqueios e sem homologação presumida |

### Histórico: entregas de 14/09, depois que os domínios fecharam

Nenhum destes estava na tabela acima: são consequência de os 8 domínios
passarem a existir, e cada um destravou o seguinte.

| Entrega | PR | O que destravou |
|---|---|---|
| Domínios corrigidos para os do **B1**, e a abrangência do dado escrita | ~~#139~~ (entrou pelo #138) | tudo abaixo |
| **Selic e CDI**, os dois itens que faltavam no domínio Econômico | [#143](https://github.com/nessenergy/Alupdatalake/pull/143) | fecha um dos oito domínios |
| **A7 em detalhe** no painel, e o aviso da sigla repetida | [#144](https://github.com/nessenergy/Alupdatalake/pull/144) | a linha do painel não dizia o tamanho do que está pendurado nela |
| **ADR 021** — 24 dos 204 conjuntos da CCEE, por demanda dos domínios | [#145](https://github.com/nessenergy/Alupdatalake/pull/145) | a ADR 018 tinha deixado essa fila em aberto à espera dos domínios |
| **Os dois calendários viram duas colunas**, com asserção que avisa | [#146](https://github.com/nessenergy/Alupdatalake/pull/146) | encerra a Lacuna 2, que a ADR 021 promoveu a bloqueio real |
| **Camada gratuita** declarada no modelo de custo | [#147](https://github.com/nessenergy/Alupdatalake/pull/147) | achado do 4.6 |

**Os cinco entraram na `main`** — a dependência de forma entre #143 e #146
(a coluna `periodo_apuracao_ccee` na Silver do `bcb_juros`) foi respeitada na
ordem de merge, como o teste exigia.

### Histórico: entregas de 15/09

Nenhum destes depende de insumo da Alup — é a fila que dá para andar sem A3.

| Entrega | PR | O que destravou |
|---|---|---|
| **Baralho do estado do desenvolvimento** em 15/09, no formato da casa | [#151](https://github.com/nessenergy/Alupdatalake/pull/151) | material de reunião sem montar nada à mão |
| **Runner em fatias** — de 9,6 GiB para 225 MiB de pico | [#152](https://github.com/nessenergy/Alupdatalake/pull/152) | tira o item "lote por fatia" desta fila e derruba a memória do job de 4 GiB para 1 GiB |
| **EAR e ENA diários do ONS** | [#153](https://github.com/nessenergy/Alupdatalake/pull/153) | fecha o domínio Mercado de Energia com a hidrologia que explica carga e preço |
| **Geração horária e capacidade instalada do ONS** | [#155](https://github.com/nessenergy/Alupdatalake/pull/155) | as usinas do SIN; e o achado de que o ONS publica o CEG |
| **CEG canônico e `gold.de_para_usina`** | [#156](https://github.com/nessenergy/Alupdatalake/pull/156) | encolhe a [#141](https://github.com/nessenergy/Alupdatalake/issues/141) de quatro colunas para uma |

O #156 nasceu de um bug que só apareceu quando as duas pontas existiram: a
ANEEL publica o último segmento do CEG com um dígito e o ONS com dois, e o JOIN
por `codigo_usina` devolvia **zero** de 2.047 usinas. Normalizado na ingestão,
casam 95,1% do cadastro de capacidade e 98,4% da geração horária.

### O que segue parado, e por quê

| # | Item | Depende de |
|---|---|---|
| 4.2 | Endurecer o Portal MVP | **despriorizado pela decisão 3.4**: com a CCEE destravada, a fila de trabalho útil sem GCP voltou a ser escopo facturável — e foi nela que o dia de 14/09 foi gasto |
| 4.3 | Versão em inglês do baralho | decisão **3.2**, que é sua |
| ~~4.4~~ | ~~Apagar branches já mescladas e arquivar os `backup/*` como tag~~ | **Destravou sozinho com o GitHub Enterprise, confirmado em 15/09**: `git push --delete` removeu as cinco branches já mescladas (`feat/bcb-selic-cdi`, `feat/lote-por-fatia`, `feat/ons-ear-ena`, `feat/ons-geracao`, `feat/de-para-usina`) sem 403, e os dois `backup/*` já estão como tag `arquivo/*`. Sobra `docs/raci-15-09`, cujo conteúdo entrou pelo squash do #151 mas que nunca teve PR próprio — deixada de pé até alguém confirmar que não está em uso |

### Uma pendência técnica do próprio repositório — encerrada em 14/09

O CI **não disparava em PR**, e o contorno era validar localmente antes de cada
push, deixando o merge acionar o CI pelo gatilho de `push`. Isso invertia a
ordem: o CI virava conferência posterior em vez de portão.

**Deixou de valer.** O PR [#130](https://github.com/nessenergy/Alupdatalake/pull/130)
disparou os **8 jobs**, todos verdes, antes do merge — inclusive a Auditoria de
Dependências, que não roda nesta estação porque o `pip-audit` quebra ao decodificar
o caminho com acento (`Área de Trabalho`). O portão preventivo da cláusula 8ª
passou a funcionar como previsto.

A causa provável é a mudança para GitHub Enterprise em 11/09, que também trouxe
a proteção da `main` (ADR 010, encerrada).

---

## 5. A fila aberta em 23/09 pela entrega de A3

Sequência, não lista — cada item depende do anterior. Detalhe em
[`runbook/primeiro-deploy.md`](runbook/primeiro-deploy.md).

0. **Gravar os IDs reais dos três projetos nos `.tfvars`** (item 1.1).
1. **Conferir os projetos e executar o bootstrap** em `infra/bootstrap/`: a
   Alup cria, vincula billing e concede os papéis da ADR 015; a ness. configura
   APIs, WIF, state e Artifact Registry. G1 já encerrou em 10/09.
2. **Rótulos de custo** já estão prontos (FinOps F0, implementado em 04/09) —
   conferir que entraram no `apply`, não depois dele.
3. `terraform apply` no ambiente `dev` — datasets, bucket, secrets, IAM.
4. Dataform executado pelo deploy logo após o apply — DDL do Bronze, views Silver e tabelas Gold (ADR 012).
5. Publicar a imagem e subir o Cloud Run Job + Scheduler.
6. **Três dias consecutivos com `status = SUCESSO`** em `bronze._execucoes`.
7. Validar o replay do raw contra objeto real no GCS.
8. Ligar o Portal MVP no BigQuery e publicar.

Só depois disso a Onda 0 pode ser declarada homologada — entrega técnica não é
homologação, e é o primeiro `apply` que revela IAM insuficiente, cota de API e
formato que o BigQuery recusa.

---

## 6. Prazos, em ordem de custo

Fonte: [`status.md` §6](status.md). Repetido aqui como calendário; a tabela lá
é a que vale.

| Prazo | Insumo | Situação |
|---|---|---|
| ~~sem data~~ | ~~G1 · resposta do Google~~ | **encerrada em 10/09**; as recomendações viraram ADRs |
| ~~04/09 — vencido~~ | A3 · projeto GCP | **atendida em 23/09**, com 12 dias úteis de atraso e os três ambientes de uma vez; S2 e S3 escorregaram |
| 11/09 — respondido | A4 Questionário, com A5 (data owners, B1), A6 (Power BI hoje; Looker Studio ou fronts internos na Fase 2, G1) e destinatário de alerta (E3). Segue aberto: A9 token Hubspot, com chamado a partir de 14/09 (C1) | Gold da Fase 1 sem KPI ([ADR 012](arquitetura/decisoes/012-dataform.md#gold-na-fase-1)); a execução real do Hubspot aguarda token |
| 18/09 | `billing_account` (E1, E2, em acerto com a QI Network) · exemplos de planilha (G3). **A2 encerrada em 14/09**: a orientação chegou, era filtro de `User-Agent`, e as 32h da Onda 1 destravaram no mesmo dia | sem confirmação de billing (#87) e planilhas (#142) em 18/09; sem conta, sem `apply` |
| 25/09 | A7 chamados de token e acesso, abertos a partir de 14/09 (C1); o MySQL RDS dispensa VPN (C8) · C7 RM/TOTVS. **A8 saiu daqui**: documentação recebida em 14/09 | **ociosidade de 4h/dia** — maior risco financeiro do contrato |

---

## Como manter isto vivo

Item que fecha sai da tabela; o que ele destravou aparece no `status.md`. Se uma
linha aqui sobrevive a duas semanas sem se mexer, ou ela não era próxima ação,
ou está bloqueada por algo que ainda não foi nomeado — nos dois casos, vale
reescrevê-la em vez de deixá-la envelhecer.
