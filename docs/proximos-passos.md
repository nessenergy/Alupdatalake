# Próximos passos — fila de execução

Documento **vivo**: é para riscar linha, não para arquivar. Atualizado em
**2026-09-15**.

Ele existe para responder uma pergunta que os outros três não respondem em uma
tela: **qual é a próxima ação, de quem é, e qual comando a executa.**

- [`status.md`](status.md) — onde estamos e o que trava o quê (fonte da verdade)
- [`plano-semanal.md`](plano-semanal.md) — o que sai em cada semana
- [`plano-execucao.md`](plano-execucao.md) — escopo e estimativa por onda
- **este arquivo** — a fila, com dono e comando

Quando um item aqui fecha, ele sai daqui e o efeito aparece no `status.md`.

---

## 1. O que está travando tudo

A cadeia hoje é **em série**, e encurtou: com a revisão do Google feita em
10/09, sobrou um elo antes do primeiro apply.

    A3 (ambiente GCP) → 1º apply → Onda 0 homologada

| # | Ação | Dono | Situação |
|---|---|---|---|
| ~~1.1~~ | ~~**Obter uma data para a resposta do Google**~~ — [issue #77](https://github.com/nessenergy/Alupdatalake/issues/77) | Alup / Google | **Encerrada: a revisão aconteceu em 10/09** e as recomendações viraram as ADRs 012, 013, 015 e 017. Esta linha sobreviveu por descuido à atualização de 11/09 — G1 deixou de ser gargalo, e o que precede o resto passou a ser A3 sozinho |
| 1.2 | **Projeto GCP `dev`** (A3) | Alup | **vencido em 04/09**; hoje, 15/09, é o **6º dia útil de atraso — passou dos 5 dias úteis da cláusula 3ª**. Previsão da Alup: 18/09. Quem cria (E1) e de quem é a `billing_account` (E2) foi esclarecido em 09/09: ambos são da Alup. **Com G1 encerrada, é o único elo antes do primeiro apply** |
| 1.3 | Variáveis `GCP_WIF_PROVIDER` e `GCP_DEPLOY_SA` (A1) | ness./Alup | dependem de A3. **Branch protection resolvida em 11/09**: a organização passou ao GitHub Enterprise e a `main` exige PR e seis verificações (ADR 010, encerrada) |

> O atraso de A3 está registrado em
> [`relatorios/2026-09-04-a3-nao-entregue.md`](relatorios/2026-09-04-a3-nao-entregue.md),
> emitido no dia em que a situação se configurou. Condicionar A3 a G1 não
> interrompe a contagem da cláusula 3ª — o contrato conta o atraso do insumo,
> não o motivo.

---

## 2. Sua fila

| # | Ação | Como | Pronto quando |
|---|---|---|---|
| ~~2.1~~ | ~~Cobrar a data do Google~~ | — | **Encerrada: a revisão aconteceu em 10/09** e virou as ADRs 012, 013, 015 e 017 |
| 2.2 | **Enviar o relatório de 04/09 à Alup** | `.md` e `.html` prontos em [`relatorios/`](relatorios/) | Registro na mão da contratante |
| 2.3 | ~~Decidir a região com a Alup~~ | resposta à pergunta E7 do questionário | **Decidido em 10/09**: `us-east1` ([ADR 011](arquitetura/decisoes/011-regiao-us-east1.md)) |
| 2.4 | **Enviar à Alup o registro de 09/09 sobre E1 e E2** | `.md` e `.html` prontos em [`relatorios/`](relatorios/) | Registro na mão da contratante |
| 2.5 | **Obter a data e o nome do responsável por A3** | em 11/09 a Alup deu previsão de 18/09, com o faturamento em acerto com a QI Network; o nome não veio — [issue #55](https://github.com/nessenergy/Alupdatalake/issues/55) | E1 respondido com data e nome |
| 2.6 | **Obter a `billing_account`** | teto e destinatário respondidos em 11/09: US$ 20/mês até novembro e até US$ 400/mês a partir de meados de novembro (E2); alertas para `alup.alertas@alupar.com.br` (E3). Falta a conta — [issue #87](https://github.com/nessenergy/Alupdatalake/issues/87) | conta vinculada, prevista para 18/09 |
| 2.7 | **Combinar o canal das credenciais seguintes** (BBCE, Hubspot, Onda 3) | o pedido está redigido no [registro de 14/09](relatorios/2026-09-14-documentacao-de-apis-recebida.md) §5. **A rotação do token do TempoOK saiu desta linha**: fica para a virada de produção ([ADR 020](arquitetura/decisoes/020-token-tempook-rotacao-na-producao.md)) — rotacionar antes de existir Secret Manager entregaria o valor novo pelo mesmo e-mail | a Alup grava cada credencial nova direto no Secret Manager, sem passar por e-mail |
| 2.8 | **Enviar à Alup o registro de 14/09** | `.md` e `.html` prontos em [`relatorios/`](relatorios/) | Registro na mão da contratante |
| 2.9 | **Perguntar ao TempoOK por que o acervo para em 26/10/2022** (A10) | o token funciona e o caminho está certo, mas nada posterior responde; três hipóteses no [registro de 14/09](relatorios/2026-09-14-documentacao-de-apis-recebida.md) §4.1 | acesso ao acervo recente, ou a informação de que o produto mudou. **Vale juntar com 2.7**: uma conversa só com o fornecedor resolve rotação e acervo |
| 2.10 | **Levar dois pontos da matriz RACI à Alup** — recebida em 15/09, [`raci.md`](raci.md) | na reunião de sexta e no relatório de fechamento da S3, não em peça separada: o documento não muda prazo nem marco. Os dois pontos são (a) **quem compõe o Comitê** que a matriz põe como accountable da passagem de fase, já que B4 dá isso a Taina, e (b) **rebaixar o Google de accountable a consultado** na arquitetura. O de-para Fase↔Onda e Core↔Gold já está resolvido do nosso lado (§5 do `raci.md`) e não precisa de resposta | Comitê definido ou B4 confirmado como rito válido; papel do Google acordado — [issue #150](https://github.com/nessenergy/Alupdatalake/issues/150) |

### Por que 2.5 e 2.6 têm pressa

São as duas metades de A3, o único elo que resta antes do primeiro apply. A
previsão é 18/09; a cláusula 3ª já conta atraso desde 08/09, e **passar de 5
dias úteis posterga o cronograma** — marca ultrapassada em 14/09; 15/09 é o 6º
dia útil de atraso.

---

## 3. Decisões que dependem de você

| # | Decisão | Opções | Efeito |
|---|---|---|---|
| 3.1 | **Campo Semana** | (a) manter seleção `S1`–`S19`, gerenciada pelo script; (b) iteração com datas reais, criada à mão | Iteração não é criável por API. Em (b), o script deixa de gerenciar o campo |
| 3.2 | **Idioma do baralho** | português (atual) ou inglês | Só importa se a plateia do Google não for do Brasil |
| 3.3 | **Redação da exclusão de escopo no baralho de kickoff** | manter ou trocar por "modelos preditivos avançados" | Exclusão legítima da Fase 3; é preferência, não correção |
| 3.4 | **Paralelos restantes** | ~~dicionário de dados · endurecer o Portal MVP~~ — **mudou em 14/09**: com a CCEE destravada, a fila de trabalho útil sem GCP voltou a ser escopo faturável | Ver 3.7 |
| 3.7 | ~~**Próxima entidade da CCEE**~~ — **resolvida em 14/09** | Entregue `ccee_perfil`, a partir de **`lista_perfil_v1`** e não de `lista_perfil`, que a CCEE descontinuou na CO 562/25 — apontar para a antiga traria cadastro congelado em 2025 | **As cinco dimensões comuns passaram a ter fonte.** A próxima escolha (`consumo_horario_submercado` ou outra dos 204 conjuntos) fica para depois de A4 |
| 3.5 | **Branch protection** | ~~GitHub Team pago por usuário, ou assumir o risco por escrito~~ — **resolvido em 11/09** | A organização passou ao GitHub Enterprise; a `main` exige PR e seis verificações, com force push e exclusão bloqueados (ADR 010, encerrada) |
| 3.6 | **Teto de US$ 400/mês a partir de meados de novembro** (E2) | ~~pedir revisão do teto à Alup, ou redimensionar a orquestração gerenciada da Onda 3~~ — **resolvido em 11/09** | Redimensionada: a Onda 3 passa a Cloud Workflows em vez de Composer ([ADR 017](arquitetura/decisoes/017-orquestracao-sem-composer.md)). Sem ambiente ligado 24×7, a estimativa volta para dentro do teto e não foi preciso pedir dinheiro à contratante |

Decisões já tomadas: **região** `us-east1` ([ADR 011](arquitetura/decisoes/011-regiao-us-east1.md), que
substituiu a 009) e **tom cordial** nos relatórios (convenção no [README](relatorios/README.md) do
diretório). Em 11/09, com as respostas da Alup: **três ambientes** e **bootstrap pela ness.**
([ADR 015](arquitetura/decisoes/015-fundacao-do-ambiente.md)), **Gold sem KPI nesta fase**
([ADR 012](arquitetura/decisoes/012-dataform.md)) e **contatos e empresas do Hubspot fora do escopo**.
Ainda em 11/09, diante do teto de E2: **orquestração da Onda 3 em Cloud Workflows, sem Composer**
([ADR 017](arquitetura/decisoes/017-orquestracao-sem-composer.md)).

---

## 4. Minha fila

### O que entrou na fila em 14/09

| O quê | Branch/PR | Situação |
|---|---|---|
| Fila da ADR 021, ordens 1–5: `ccee_agente`, `ccee_exposicao_financeira`, `ccee_contabilizacao_perfil`, `ccee_geracao_usina`, `ccee_contrato_montante`, `ccee_varejista_consumidor`, `ccee_encargo_ess`, `ccee_energia_reserva`, `ccee_cvu_estrutural` | `worktree-fila-ccee` (sem número de PR ainda) | **9 entidades entregues em 14/09** — 7 componentes cada, contra a API real (`status.md` §1) |

### O que segue parado

| O quê | Bloqueado por |
|---|---|
| ~~EAR e ENA do ONS~~ | **entregues em 15/09** ([#153](https://github.com/nessenergy/Alupdatalake/pull/153)) |
| As 19 entidades secundárias da ADR 021 (§2.1/§3 da ADR) | fila priorizada, sem demanda de domínio ainda — mesmo caminho de subclasse de `CceeCsvCkan` quando entrarem |
| ~~Lote por fatia no runner~~ | **entregue em 15/09** ([#152](https://github.com/nessenergy/Alupdatalake/pull/152)). A memória deixou de ser premissa: medida contra a fonte real, caiu de **9.859 MiB** para **225 MiB** de pico, e o Terraform baixou de 4 GiB para 1 GiB. A janela de 40 dias do `ccee_geracao_usina` continua, por outro motivo — cobre o mês fechado sem abrir um quarto recurso mensal |

| # | Ação | Depende de |
|---|---|---|
| ~~4.1~~ | ~~Conector do BBCE~~ — **entregue em 14/09**: `bbce_curva_forward`, 7 componentes, 17 testes. Falta só o acesso (A7, [#23](https://github.com/nessenergy/Alupdatalake/issues/23)) — inclusive o **host**, que não consta da documentação | — |
| 4.2 | Endurecer o Portal MVP enquanto roda com provedor simulado | decisão 3.4 |
| 4.8 | **Próxima fonte pública sem insumo da Alup** — candidatas: térmicas do ONS (`cvu-usitermica`, `geracao-termica-despacho-2`), `disponibilidade_usina`, ou as 19 entidades secundárias da ADR 021 | escolha de domínio, não de bloqueio: as três destravam Geração e Operacional pelo lado público |
| 4.3 | Versão em inglês do baralho | decisão 3.2 |
| 4.4 | Apagar `docs/fluxo-execucao` e o branch de trabalho, já mesclados; arquivar os dois `backup/*` como tag | permissão — daqui o `git push --delete` e a API respondem 403 |
| 4.5 | Emitir o relatório de situação da semana | fechamento da S2 (11/09) |
| ~~4.6~~ | ~~Conferir as tarifas-premissa de `us-east1`~~ — **concluído em 14/09** ([#112](https://github.com/nessenergy/Alupdatalake/pull/112) e [#147](https://github.com/nessenergy/Alupdatalake/pull/147)): armazenamento corrigido de 0,020 para 0,023 (a página cota por GiB·hora), e o preço por TiB de `us-east1` **segue sem confirmação** — o seletor de região roda no navegador. Dois caminhos independentes chegaram ao mesmo impedimento. No caminho apareceu o que faltava: **a camada gratuita de 1 TB/mês não estava no modelo**, e o lake inteiro cabe nela | — |
| ~~4.7~~ | ~~Asserções de faixa por fonte (`rowConditions`, ex.: `cotacao_compra > 0`, `submercado IN ('N','NE','S','SE')`) e alerta de falha do workflow do Dataform; hoje o portão (`uniqueKey`/`nonNull`) repete o `QUALIFY` da Silver e os `NOT NULL` do Bronze (ADR 012)~~ — **concluído em 14/09** ([#110](https://github.com/nessenergy/Alupdatalake/pull/110)) | — |

### O que entrou na fila em 14/09, depois que os domínios fecharam

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

### O que entrou na fila em 15/09

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

## 5. Depois que G1 e A3 destravarem

Sequência, não lista — cada item depende do anterior. Detalhe em
[`runbook/primeiro-deploy.md`](runbook/primeiro-deploy.md).

1. **Recomendações do Google viram ADR** — novo ou revisão de existente. É o
   que justifica ter esperado.
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
| **04/09 — vencido** | A3 · projeto GCP | atraso registrado; S2 e S3 escorregam |
| 11/09 — respondido | A4 Questionário, com A5 (data owners, B1), A6 (Power BI hoje; Looker Studio ou fronts internos na Fase 2, G1) e destinatário de alerta (E3). Segue aberto: A9 token Hubspot, com chamado a partir de 14/09 (C1) | Gold da Fase 1 sem KPI ([ADR 012](arquitetura/decisoes/012-dataform.md#gold-na-fase-1)); o conector Hubspot segue parado |
| 18/09 | `billing_account` (E1, E2, em acerto com a QI Network) · exemplos de planilha (G3). **A2 encerrada em 14/09**: a orientação chegou, era filtro de `User-Agent`, e as 32h da Onda 1 destravaram no mesmo dia | sem conta, sem `apply` |
| 25/09 | A7 chamados de token e acesso, abertos a partir de 14/09 (C1); o MySQL RDS dispensa VPN (C8) · C7 RM/TOTVS. **A8 saiu daqui**: documentação recebida em 14/09 | **ociosidade de 4h/dia** — maior risco financeiro do contrato |

---

## Como manter isto vivo

Item que fecha sai da tabela; o que ele destravou aparece no `status.md`. Se uma
linha aqui sobrevive a duas semanas sem se mexer, ou ela não era próxima ação,
ou está bloqueada por algo que ainda não foi nomeado — nos dois casos, vale
reescrevê-la em vez de deixá-la envelhecer.
