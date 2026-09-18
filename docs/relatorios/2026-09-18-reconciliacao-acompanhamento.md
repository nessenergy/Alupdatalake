# Reconciliação do acompanhamento — 18/09/2026

Registro de conferência documental e operacional da ness. para o AlupData,
contrato CPS-01025/2026. A atualização aproxima a leitura do quadro das
entregas comprovadas, preservando o histórico e as pendências da Alup.
Não constitui homologação de onda nem comprovação de horas trabalhadas.

## Referência conferida

- Código: `main` em `2d0f7c6fc6bd569a9944645d3b7b45785b593121`, de 16/09.
- [Project 2](https://github.com/orgs/nessenergy/projects/2): 69 cartões antes
  da reconciliação — 30 `Done`, 1 `In Progress` e 38 `Todo`.
- 39 issues abertas revisadas, mais as entregas técnicas fechadas que ainda
  exibiam checklists ou caminhos antigos.
- Sete registros de `Horas`, totalizando 100h: #2 (10h), #3 (10h), #7 (10h),
  #18 (28h), #19 (20h), #20 (12h) e #21 (10h). O runbook antigo orientava
  copiar estimativas para esse campo. A origem deve ser conciliada antes da
  medição; os valores foram preservados e não representam 100h comprovadas.

## Estágio técnico e evidências

| Frente | Evidência | Estado e próximo passo |
|---|---|---|
| Fundação | `src/core/`, `infra/`, Dataform, CI/CD e portal | Implementação avançada; primeiro ambiente e validação ponta a ponta dependem de #55/#95 |
| CCEE pública | [PR #130](https://github.com/nessenergy/Alupdatalake/pull/130), [PR #149](https://github.com/nessenergy/Alupdatalake/pull/149), ADRs 018/021 | PLD, perfil e nove entidades adicionais implementados; carga real pendente em #17 |
| ONS | [#153](https://github.com/nessenergy/Alupdatalake/pull/153), [#155](https://github.com/nessenergy/Alupdatalake/pull/155), [#158](https://github.com/nessenergy/Alupdatalake/pull/158), [#159](https://github.com/nessenergy/Alupdatalake/pull/159) | Sete entidades adicionais além de carga; evidências vinculadas à #18, sem duplicar horas |
| BBCE | [PR #131](https://github.com/nessenergy/Alupdatalake/pull/131) | Sete componentes implementados; host e acesso pendentes, #23/#11 |
| Hubspot | `src/conectores/hubspot_negocios.py` e dicionário | Implementado; token e execução real pendentes, #24/#11 |
| TempoOK | ADR 019 e #129 | Contrato verificado com a origem; acervo recente ainda sem confirmação, #25/#129 |
| Planilhas | `src/core/planilha.py`, `src/conectores/planilha.py` | Motor implementado; templates e validação com arquivos reais pendentes, #34/#142 |
| Sistemas internos | ADR 008 e respostas C5–C9 | Caminho relacional pronto, fontes ainda não implementadas; #27/#29/#31/#32 |

São 26 entidades implementadas: 23 com extrações em dry-run registradas nas
origens, TempoOK com contrato verificado e duas APIs ainda sem acesso. Isso
não altera os 13 conectores contratuais nem comprova ingestão em BigQuery.
Nenhuma onda tem homologação registrada nas evidências consultadas.

As estimativas de prontidão do `docs/status.md` permanecem estimativas:
Onda 0 ~82%; Onda 1 com implementação do escopo original; Onda 2 ~50%
escrito; Onda 3 sem fonte implementada; Onda 4 ~29%. Horas e homologação
não podem ser calculadas a partir da contagem de cartões ou de entidades.

## Dependências em 18/09

| Referência | Responsável pela próxima ação | Prazo e fato confirmado |
|---|---|---|
| [#55 — GCP/A3](https://github.com/nessenergy/Alupdatalake/issues/55) | Alup | Prazo original 04/09; previsão 18/09. Liberação em processo informada em 16/09, sem confirmação de entrega nos registros consultados em 18/09 |
| [#87 — faturamento](https://github.com/nessenergy/Alupdatalake/issues/87) | Alup | Data acordada 18/09. Destinatários e teto respondidos em 11/09; vinculação da conta sem confirmação |
| [#142 — planilhas](https://github.com/nessenergy/Alupdatalake/issues/142) | Alup | Exemplos prometidos para 18/09; recebimento sem confirmação |
| [#11 — acessos](https://github.com/nessenergy/Alupdatalake/issues/11) | Alup | Hubspot desde 11/09; demais pedidos da Onda 2 e sistemas internos acompanhados para 25/09. CCEE pública não depende de token |
| [#129 — TempoOK](https://github.com/nessenergy/Alupdatalake/issues/129) | Alup | Acervo acessível medido até 26/10/2022; resolver acesso recente, acompanhado para 25/09 |
| [#141 — usinas](https://github.com/nessenergy/Alupdatalake/issues/141) | Alup | Sigla interna e identificação das parcelas CCEE ainda dependem de correspondência; sem prazo pactuado |
| [#150 — RACI](https://github.com/nessenergy/Alupdatalake/issues/150) | ness., para conciliar com a Alup | Composição do Comitê e papel do Google; sem prazo pactuado |
| [#111 — minutas](https://github.com/nessenergy/Alupdatalake/issues/111) | Alup | Minutas técnicas entregues em 11/09; revisão e aprovação da controladora ainda pendentes |

G1 está encerrada pela reunião de 10/09 ([#77](https://github.com/nessenergy/Alupdatalake/issues/77)).
A cadeia atual começa em A3. Em 18/09, se a entrega permanecer pendente,
são nove dias úteis desde 08/09, usando o calendário versionado. A previsão
de 18/09 não apaga o vencimento de A3 em 04/09. Billing e planilhas vencem
em 18/09 e não devem ser marcados atrasados antes do primeiro dia útil seguinte.

## Correções de leitura

- Descrições atuais devem separar o que foi implementado do que aguarda
  ambiente, credencial, arquivo real ou aceite; `Todo` não descreve uma
  implementação já existente com validação pendente.
- A #22 permanece distinta da #17: APIs de agente JSON/XML não se confundem
  com os dados públicos. Sua demanda e cobertura precisam ser definidas;
  não foi encerrada como duplicata nem considerada bloqueio da Onda 1.
- A #21 permanece na Onda 0: conector de referência do item 0.3. A verificação
  operacional de três dias pertence ao primeiro deploy/#95.
- A #55 passa a apontar a ADR 015 para os seis papéis de bootstrap em contas
  nominais. A lista de papéis no comentário de 16/09 diverge dessa decisão;
  preservar o comentário não significa tratá-lo como instrução vigente.
- Os resumos passam a usar três ambientes, `us-east1`, Dataform e Cloud
  Workflows. Relatórios antigos e decisões históricas não são reescritos.
- A orientação de copiar estimativas para horas realizadas é removida do
  procedimento atual. A pendência de conciliação é vinculada à #73.

## Sincronização e verificações

A [execução de 17/09](https://github.com/nessenergy/Alupdatalake/actions/runs/35240311826)
terminou com sucesso, mas pulou os passos de sincronização por falta de
configuração de WIF/conta de deploy ou App. Seu resultado verde não prova
atualização do quadro. A ativação depende do ambiente/#55 e da configuração
do App descrita no runbook; não houve provisionamento nesta atualização.

Também não basta a simulação retornar zero mudanças: o script compara campos
com o mapa e o fechamento das issues; não lê a implementação para arbitrar
se uma descrição está desatualizada.

Verificações locais em 18/09, no mesmo código-base:

- Ruff: análise e formatação aprovadas, 123 arquivos.
- Pytest: 956 testes aprovados, 264 ignorados, cobertura total de 93%.
  Integrações ignoradas não comprovam acesso às fontes nem operação no GCP.
- Quadro: 13 testes aprovados.
- Bandit com o nível usado em `make all`: nenhuma ocorrência média ou alta.
- pip-audit: nenhuma vulnerabilidade conhecida na repetição com UTF-8.
- Links locais alterados conferidos; nenhuma nova infração de atribuição.
  As ocorrências da própria regra 6 em `AGENTS.md` são preexistentes.

O executável `make` não está disponível nesta estação. Seus comandos de
lint, testes, Bandit e auditoria foram executados diretamente. A primeira
tentativa de `pip-audit` encontrou erro de decodificação no caminho Windows;
a repetição usa `PYTHONUTF8=1`, sem alterar dependências ou código do projeto.

## Fechamento da atualização

A aplicação foi relida pela API em 18/09 e comparada com a referência anterior:

| Item | Antes | Depois |
|---|---|---|
| Cartões | 69 | 69, sem duplicação de issue e PR |
| Status | 30 `Done`, 1 `In Progress`, 38 `Todo` | 30 `Done`, 17 `In Progress`, 22 `Todo` |
| Descrições de issues | Textos antigos ou incompletos em 41 itens | 41 corpos atualizados; títulos de #38 e #57 ajustados |
| Responsável de #111 | ness. | Alup, pela aprovação pendente das minutas já entregues |
| Horas e validações | Sete lançamentos de horas; nenhum aceite novo comprovado | Valores, validações, correções, atrasos, semanas, ondas e datas preservados |
| Histórico | Comentários e estados de abertura/fechamento existentes | Preservados integralmente; nenhum comentário ou fechamento novo |
| Apresentação do Project | Sem distinção suficiente entre estimativa e realizado | Semântica de status, horas e limitações da automação explícitas |
| Simulação com o mapa revisado | Alteração do responsável de #111 a aplicar | Zero mudanças após a aplicação e releitura |

Passaram de `Todo` a `In Progress`: #1, #6, #11, #17, #23, #24, #25,
#34, #55, #57, #73, #87, #89, #90, #111 e #113. As descrições explicam
se o trabalho restante é técnico, validação ou insumo externo. Isso não
significa atividade técnica contínua em todas essas frentes.

As 39 issues abertas foram revisadas; #95 e #129 já estavam corretas e
foram mantidas. As quatro entregas fechadas #18–#21 receberam descrições e
checklists coerentes com seus artefatos, preservando o encerramento técnico.
PRs de novas entidades foram vinculados às issues existentes; não foi
criado cartão adicional nem lançado esforço duplicado.

A documentação versionada segue em branch de atualização e PR para `main`.
A #113 permanece aberta até a incorporação e conferência dessa documentação.
O relatório é registro da revisão; seu preparo não comprova envio à Alup.

A liberação do ambiente, as horas efetivamente gastas e a homologação
continuam exigindo evidência própria. A prioridade operacional é confirmar
A3, billing e planilhas; depois executar bootstrap, implantação, cargas e
replay para reunir as evidências da primeira homologação.
