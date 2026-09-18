# Plano de atualização global do acompanhamento

**Objetivo:** alinhar documentação viva, issues e Project 2 às evidências disponíveis, distinguindo implementação, validação em ambiente e homologação.

**Abordagem:** atualizar os registros existentes e reutilizar `scripts/quadro.py` e `scripts/quadro.toml`. A conferência editorial complementa a sincronização mecânica; não será criado um novo sistema de acompanhamento.

**Ferramentas:** Markdown, GitHub Projects, GitHub CLI, Python e configuração TOML existentes.

**Base de requisitos:** solicitação de atualização global após a conferência de 18/09/2026; `AGENTS.md`, `docs/status.md`, `docs/proximos-passos.md`, `docs/runbook/acompanhamento-semanal.md` e ADRs 011–021. Este plano consolida o escopo; não existe especificação separada.

**Execução:** realizar as tarefas em ordem, conferindo o resultado de cada uma antes da seguinte. Este documento planeja a atualização; sua criação não publica alterações no GitHub.

## Restrições globais

- Manter 580h, cinco ondas e a linha de base contratual. Previsão revisada não substitui prazo original nem prova entrega.
- Não marcar homologação, `Validado = Sim`, horas efetivamente gastas ou liberação de acesso sem evidência.
- Não preencher `Horas` copiando `Horas previstas`. Conferir a origem dos sete lançamentos existentes antes de usá-los na medição.
- Preservar relatórios datados, comentários históricos e ADRs substituídos. Corrigir a leitura atual nos documentos vivos e nas descrições das issues.
- Manter credenciais no Secret Manager. Não copiar tokens de e-mails, logs ou arquivos para os artefatos da atualização.
- Respeitar a regra 6 de `AGENTS.md` em arquivos, commits, branch e textos publicados.
- Não enviar mensagens à Alup nem publicar comentários por consequência implícita de um comando. Qualquer comentário preparado deve ter conteúdo e destino revisados e autorização explícita de publicação.
- Não provisionar GCP, executar ingestões ou modificar recursos de infraestrutura dentro desta atualização do acompanhamento.
- Não converter as 26 entidades implementadas em 26 fontes contratuais: o contrato mantém seus 13 conectores; a relação precisa estar documentada.
- Código, se uma falha concreta exigir mudança, segue TDD. Correções editoriais não precisam de testes novos.

## Mapa dos artefatos

| Artefato | Responsabilidade na atualização |
|---|---|
| `docs/status.md` | Estado consolidado, evidências, ondas e dependências atuais |
| `docs/proximos-passos.md` | Próxima ação executável, responsável e condição de conclusão |
| `docs/plano-semanal.md` | Fechamento da S3 e distinção entre plano original e execução |
| `docs/plano-execucao.md` | Referências técnicas vigentes, preservando escopo e orçamento |
| `README.md`, `AGENTS.md` | Resumos de entrada coerentes com o estado consolidado |
| `docs/dicionario-dados/README.md` | Índice e cobertura das entidades implementadas |
| `docs/runbook/acompanhamento-semanal.md` | Semântica de status, horas e limitações da sincronização |
| `scripts/quadro.toml` | Mapeamento dos itens, donos e vencimentos comprovados |
| `scripts/quadro.py`, `.github/workflows/quadro.yml` | Inspeção e validação; sem alteração de comportamento prevista |
| `docs/relatorios/2026-09-18-reconciliacao-acompanhamento.md` | Evidências, diferenças antes/depois e pendências não confirmadas |
| `docs/relatorios/README.md` | Índice do novo relatório |
| Project 2 e descrições das issues | Visão operacional alinhada aos artefatos acima |

## Tarefa 1 — Fixar a referência e conferir mudanças desde a leitura

**Arquivos:** criar `docs/relatorios/2026-09-18-reconciliacao-acompanhamento.md`; ler os documentos do mapa.

**Entrada:** repositório e GitHub atuais. **Saída:** tabela de evidências que sustenta todas as decisões seguintes.

- [x] Conferir `git status --short`, branch atual e SHA de `main` remoto. Preservar `.claude/settings.json`, que já estava não rastreado.
- [x] Ler ADRs 011, 012, 015, 017, 018, 019 e 021 e a skill de homologação do projeto antes de classificar conclusões.
- [x] Consultar o Project completo, issues abertas, comentários das dependências e PRs mesclados desde 14/09. Comandos de leitura:

```powershell
gh project item-list 2 --owner nessenergy --limit 200 --format json
gh issue list --repo nessenergy/Alupdatalake --state open --limit 200 --json number,title,updatedAt
gh pr list --repo nessenergy/Alupdatalake --state merged --search 'merged:>=2026-09-14' --limit 100 --json number,title,mergedAt,url
gh run list --repo nessenergy/Alupdatalake --limit 20 --json databaseId,name,conclusion,createdAt,url
```

- [x] Registrar no relatório: data de consulta, SHA, URL de evidência, estado técnico, pendência, responsável, prazo original e previsão atual. Separar fato confirmado de ausência de confirmação.
- [x] Conferir especialmente #55, #87 e #142: previsão de GCP, faturamento e planilhas para 18/09. Se não houver confirmação, registrar exatamente isso; não presumir recebimento nem nova data.
- [x] Usar como referência inicial da auditoria: 69 itens, 30 `Done`, 1 `In Progress`, 38 `Todo`, sete campos `Horas` preenchidos. Recalcular na execução, pois os números podem mudar.

**Aceite:** cada conclusão tem evidência; informações externas ainda desconhecidas aparecem como pendências, sem impedir as correções já comprovadas.

## Tarefa 2 — Consolidar a documentação viva

**Arquivos:** modificar `docs/status.md`, `docs/proximos-passos.md`, `docs/plano-semanal.md`, `docs/plano-execucao.md`, `README.md`, `AGENTS.md` e, se houver omissões, `docs/dicionario-dados/README.md`.

**Entrada:** tabela da tarefa 1. **Saída:** uma narrativa coerente do estágio atual.

- [x] Em `docs/status.md`, encerrar G1 pela revisão de 10/09 e retirar a resposta do Google da cadeia atual de bloqueios. Preservar sua participação histórica no atraso.
- [x] Corrigir N1: BBCE já foi implementado no PR #131; falta acesso, incluindo host. Templates de planilha dependem de G3/#142, não do questionário A4 já respondido.
- [x] Atualizar caminhos antigos `sql/` e `make deploy-views` para os artefatos e comandos Dataform realmente existentes. Conferir contagens de dicionários e entidades por arquivos/registro, distinguindo bases compartilhadas de conectores concretos.
- [x] Datar os números de testes e cobertura com a execução que os produziu, ou retirar números antigos do resumo. Não apresentar 257 testes e 92% como medição atual sem evidência de execução correspondente.
- [x] Manter as estimativas de prontidão por onda com método e ressalva de ausência de homologação; não derivar progresso de quantidade de cartões ou de PRs.
- [x] Em `docs/proximos-passos.md`, retirar ações concluídas da fila ativa; substituir frases relativas como “hoje, 15/09” por datas explícitas. Vincular GCP, billing, planilhas, acervo e credenciais às issues correspondentes.
- [x] Em `docs/plano-semanal.md`, acrescentar fechamento da S3 com realizado, bloqueios e próximos passos condicionais. Identificar S1/S2 como registros históricos; não reescrever o passado para parecer que as decisões posteriores já existiam.
- [x] Em `README.md` e `docs/plano-execucao.md`, apresentar Dataform e Cloud Workflows conforme ADRs 012 e 017. No mapa de diretórios, `dags/` não deve sugerir uma implementação ativa de Composer.
- [x] Em `AGENTS.md`, substituir o retrato de 04/09 por resumo datado, apontando `docs/status.md` para detalhes voláteis; incluir as ADRs posteriores ausentes no índice.
- [x] Conferir a divisão de A3: Alup cria projetos, vincula faturamento e concede papéis; ness. executa bootstrap conforme ADR 015. Não copiar listas de IAM de comentários conflitantes.
- [x] Revisar o diff e preparar commit `docs: alinha o acompanhamento ao estado de 18 de setembro` quando a execução estiver autorizada.

**Aceite:** os documentos vivos concordam sobre G1, BBCE, TempoOK, GCP e planilhas; cronograma original e fatos históricos continuam identificáveis.

## Tarefa 3 — Preparar a reconciliação das issues e do Project

**Artefatos:** descrições de issues e campos do Project; registrar proposta antes/depois no relatório da tarefa 1. Modificar `scripts/quadro.toml` somente para refletir itens e prazos comprovados.

**Entrada:** documentação reconciliada. **Saída:** relação concreta de alterações publicáveis, com evidência e critério de conclusão.

| Itens | Alteração proposta |
|---|---|
| #17 — CCEE | Descrever as entidades entregues e a verificação nas origens. Usar `In Progress` enquanto o critério da issue incluir carga real; só concluir se todo o critério técnico estiver atendido e a validação residual estiver explicitamente rastreada. |
| #22 — CCEE credenciado | Reconciliar com ADR 018 e #17: identificar eventual escopo residual. Só encerrar por substituição se toda a cobertura estiver demonstrada; ausência de credencial não justifica manter uma dependência já eliminada. |
| #23, #24, #25 | Mostrar implementação existente, usar `In Progress` e manter abertas enquanto os critérios exigirem execução real. Relacionar BBCE ao acesso/host, Hubspot ao token e TempoOK à #129. |
| #34 | Registrar motor pronto e templates/validação ainda pendentes; `In Progress`, dependência #142 e #16. |
| #55 | Consolidar descrição com três ambientes, `us-east1`, bootstrap pela ness. e orquestração da ADR 017. Retirar estimativas antigas baseadas em Composer da visão atual; apontar fonte datada de custo em vez de inventar orçamento novo. |
| #55 — IAM | Conciliar o comentário de 16/09 com a lista de papéis de bootstrap da ADR 015. A descrição atual deve indicar a referência normativa correta e registrar que a comunicação anterior precisa de conferência. |
| #87, #142 | Distinguir destinatários já recebidos de billing pendente; registrar prazo de 18/09 no texto. Manter datas de linha de base dos campos do Project conforme sua semântica. |
| #27, #29, #31, #32 | Atualizar perguntas já respondidas pelo questionário e manter apenas lacunas reais; fontes não implementadas continuam `Todo`, com dependências #12–#15. |
| #6, #89–#95 | Conferir código já entregue contra os critérios de cada issue; separar configuração implementada de operação pendente no GCP. |
| #73, #111, #113, #150 | Conferir pendências documentais e de governança; só fechar com evidência de cobertura integral. |

- [x] Revisar também os demais itens abertos, sem limitar a atualização aos exemplos da tabela.
- [x] Comparar PRs desde 14/09 com os 69 cartões para detectar entregas ONS/CCEE ausentes. Vincular PRs às issues de escopo existentes; adicionar cartão apenas quando houver entrega distinta sem representação, evitando contar issue e PR como esforço duplicado.
- [x] Preservar `Validado`, `Correções`, horas e atrasos históricos registrados. Não trocar próximo responsável por mera inferência do autor do código.
- [x] Verificar especialmente BCB/#21: o mapa o classifica na Onda 0, enquanto há referências à Onda 1. Conciliar com o plano contratual antes de qualquer reclassificação.
- [x] Conferir os sete lançamentos de horas com registros de trabalho. Sem comprovação, registrar “origem do lançamento a conferir”, preservando os valores até conciliação.
- [x] Preparar corpos completos das issues com estado em data explícita, evidência, trabalho restante e critério de conclusão. Preservar seções válidas da descrição anterior.
- [x] Revisar a proposta de alterações antes de qualquer escrita externa. Não publicar comentários novos nesta etapa.

**Aceite:** nenhum cartão afirma “não iniciado” quando existe implementação; nenhum cartão ganha conclusão ou aceite apenas por existir código.

## Tarefa 4 — Explicitar o que a sincronização faz e o que depende de configuração

**Arquivos:** modificar `docs/runbook/acompanhamento-semanal.md`; conferir `scripts/quadro.toml`, `scripts/quadro.py`, `.github/workflows/quadro.yml` e `tests/unit/test_quadro.py`.

**Entrada:** proposta da tarefa 3 e execução da automação de 17/09. **Saída:** operação manual reproduzível e pendência de ativação automática claramente registrada.

- [x] Documentar que “workflow verde” não comprova sincronização: verificar se o passo de aplicação executou ou foi pulado. Referência inicial: execução `35240311826`, que pulou os passos após a guarda de configuração.
- [x] Documentar que zero mudanças na simulação significa conformidade com o mapa e o estado de fechamento das issues; não comprova coerência entre código, descrições e critérios de aceite.
- [x] Manter a autenticação existente por App/WIF/Secret Manager. Enquanto indisponível, usar a sessão autenticada local para conferência e atualização autorizada; não criar segredo alternativo para contornar A3.
- [x] Retirar do runbook a afirmação atual de organização Free, confrontando-a com a migração Enterprise registrada. Preservar a configuração de variáveis efetivamente usada pelo workflow, sem migrar ambientes nesta tarefa.
- [x] Conferir vencimentos e mapa após as decisões editoriais; rodar:

```powershell
python -m scripts.quadro --hoje 2026-09-18
uv run pytest tests/unit/test_quadro.py -q
```

- [x] Resultado esperado: simulação lista somente diferenças justificadas; testes existentes passam. Não executar `--aplicar` automaticamente: o comando também pode publicar comentários de atraso.
- [x] Registrar ativação automática como pendência se faltarem variáveis, App ou Secret Manager. Não declarar automação operacional sem observar o passo de sincronização efetivamente executado.

**Aceite:** procedimento e estado real estão documentados; nenhuma mudança de lógica ou dependência nova é necessária para corrigir as divergências editoriais identificadas.

## Tarefa 5 — Verificar e preparar publicação

**Arquivos:** todos os alterados; atualizar `docs/relatorios/README.md` e finalizar o relatório da tarefa 1.

**Entrada:** documentos, mapa e proposta de alterações externas. **Saída:** pacote revisável e validado.

- [x] Registrar no relatório diferenças antes/depois, referências das entregas, ausência ou presença de confirmação de GCP/planilhas e lista de pendências remanescentes.
- [x] Executar `git diff --check`; conferir links locais modificados e a terminologia das camadas, ambientes e ondas.
- [x] Executar a verificação de atribuição sobre os arquivos e textos preparados, passando caminhos explícitos a `python scripts/verifica_atribuicao.py`.
- [x] Rodar `make all` antes do PR, conforme `AGENTS.md`. Se houver falha, registrar causa e resolver o que pertence à atualização; não declarar verificação concluída sem saída de sucesso.
- [x] Preparar branch `docs/atualizacao-global-acompanhamento`, commits em português e PR com problema, mudanças e validação. Manter qualquer trabalho local preexistente fora do commit.
- [x] Conferir o GitHub novamente antes de aplicar o pacote externo para não sobrescrever alterações concorrentes. Preparar as descrições completas em arquivos e usar `--body-file` quando a execução das edições estiver autorizada.
- [x] Alterações de descrições/campos e fechamento de issues seguem o escopo autorizado na execução. Mensagens novas, envio a terceiros, merge e provisionamento não decorrem da aprovação deste plano.

**Aceite:** diff local e proposta externa podem ser revisados em conjunto; nenhum dado desconhecido foi preenchido por estimativa.

## Tarefa 6 — Aplicar o pacote autorizado e conferir a leitura final

**Artefatos:** Project 2, issues e relatório final.

**Entrada:** pacote da tarefa 5 e autorização de execução correspondente. **Saída:** acompanhamento coerente ou pendências explicitamente delimitadas.

- [x] Aplicar somente as descrições e os campos revisados; atualizar mapa versionado para os cartões adicionados. Não recriar o quadro.
- [x] Reconsultar os itens e as issues alteradas; comparar com a tabela antes/depois. Confirmar estados, responsáveis, datas e preservação dos valores humanos.
- [x] Rodar novamente a simulação do quadro. Se a atualização ocorrer em outra data, usar a data real e recalcular os vencimentos; não reaplicar 18/09 como se ainda fosse hoje.
- [x] Conferir que não há duplicação de horas entre PRs e issues nem uso de `Done` como sinônimo de homologação.
- [x] Entregar relatório curto: estágio técnico por onda, operação real comprovada, bloqueios com donos/prazos, alterações efetuadas e o que segue sem confirmação.

**Aceite final:** documentação viva e GitHub contam a mesma história; a automação tem estado verificável; horas e homologações permanecem sustentadas por evidência. A atualização editorial pode concluir com A3 ainda pendente, desde que isso esteja explícito e não seja confundido com ativação da automação ou entrega do ambiente.

## Execução em 18/09/2026

As seis tarefas foram executadas na branch `docs/atualizacao-global-acompanhamento`.
Evidências e resultado em [reconciliação do acompanhamento](../relatorios/2026-09-18-reconciliacao-acompanhamento.md).

- 41 descrições de issues, dois títulos, 16 estados do quadro, um responsável e a apresentação do Project atualizados e relidos.
- 69 cartões preservados: 30 concluídos, 17 em andamento, 22 a fazer. Sem comentários ou fechamentos novos.
- Horas, validações, semanas, ondas, datas, atrasos e histórico preservados; as 100h existentes continuam com origem a conciliar na #73.
- Verificações do alvo `make all` executadas diretamente porque `make` não está disponível no Windows. Auditoria repetida com `PYTHONUTF8=1` após erro local de codificação: aprovada.
- Regras do quadro: 13 testes aprovados; simulação final sem diferenças. A automação continua pendente de configuração.
- Revisão independente corrigiu referências à CCEE credenciada, prazo vigente de billing e tabela de ADRs antes da publicação.
- Alterações versionadas preparadas para PR; a incorporação à `main` e a conclusão da #113 dependem de merge posterior. Não houve provisionamento nem homologação.

A execução manteve o escopo do plano: o ambiente ausente não impediu corrigir os registros comprovadamente desatualizados. Datas futuras e entregas externas não foram presumidas.