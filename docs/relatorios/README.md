# Relatórios de situação

Relatório emitido para a contratante. Cada um é um retrato datado: o que estava
entregue, o que estava travado, quem precisava decidir o quê e até quando.
**Não são editados depois de emitidos** — corrigir um relatório antigo apaga o
registro de qual era a informação disponível naquela data, que é justamente o
que sustenta postergação, ociosidade ou suspensão numa medição.

Situação corrente e viva fica em [`../status.md`](../status.md); este diretório
é histórico.

| Data | Relatório | Marco em jogo | Questões abertas |
|---|---|---|---|
| 27/08/2026 | [Questões abertas e o que esperamos entregar](2026-08-27-situacao.md) · [versão HTML](2026-08-27-situacao.html) | Onda 0 · 15,52% | 11 · acompanhadas na [issue #57](https://github.com/nessenergy/Alupdatalake/issues/57) |
| 30/08/2026 | [Preparação local sem GCP](2026-08-30-preparacao-local-sem-gcp.md) | Prontidão técnica | GCP, Docker, Terraform e integrações reais ainda pendentes |
| 31/08/2026 | [Início da Onda 0](2026-08-31-inicio-onda-0.md) · [versão HTML](2026-08-31-inicio-onda-0.html) | Onda 0 · 15,52% · 11/09 | 7 · com [#67](https://github.com/nessenergy/Alupdatalake/issues/67) (região) e [#68](https://github.com/nessenergy/Alupdatalake/issues/68) (revisão na main) abertas hoje |
| 04/09/2026 | [Situação do ambiente GCP e do cronograma da Onda 0](2026-09-04-a3-nao-entregue.md) | Onda 0 · 15,52% · **postergada** | 1 · **G1** ([#77](https://github.com/nessenergy/Alupdatalake/issues/77)), resposta do Google, sem prazo acordado — precede A3 por decisão da Alup |
| 08/09/2026 | [Situação dos insumos pendentes e do cronograma da Onda 0](2026-09-08-s2-sem-ambiente.md) · [versão HTML](2026-09-08-s2-sem-ambiente.html) | Onda 0 · 15,52% · S2 integralmente postergada | 6 · A3, G1, A4, A9, A5/A6 e A2 · 1º dia útil de atraso de A3 |
| 09/09/2026 | [Esclarecimento sobre os itens E1 e E2 do Questionário de Gaps](2026-09-09-esclarecimento-e1-e2.md) · [versão HTML](2026-09-09-esclarecimento-e1-e2.html) | Onda 0 · 15,52% | 3 · E1 (data e responsável), E2 (`billing_account` e teto) e E3 (destinatários), todos do insumo A3 |
| 11/09/2026 | [Fechamento da S2 e decisões da revisão arquitetural com o Google](2026-09-11-fechamento-s2-revisao-google.md) · [versão HTML](2026-09-11-fechamento-s2-revisao-google.html) | Onda 0 · 15,52% · postergação a partir de 14/09 | 6 · A3 ([#55](https://github.com/nessenergy/Alupdatalake/issues/55)), A4, A9, A5, A6 e destinatários de alerta · G1 ([#77](https://github.com/nessenergy/Alupdatalake/issues/77)) resolvida em 10/09 |
| 14/09/2026 | [Documentação de APIs das fontes — recebimento, efeito e uma recomendação de segurança](2026-09-14-documentacao-de-apis-recebida.md) · [versão HTML](2026-09-14-documentacao-de-apis-recebida.html) | Onda 1 · 20,69% | 3 · **A2 encerrada** e **A8 atendida** · abertas: A3 (5º dia útil de atraso), A7 e A9 · recomendação de rotação do token do TempoOK |

## Convenções

- **Nome do arquivo**: `AAAA-MM-DD-assunto.md`, data de emissão.
- **Como gerar o HTML**: `make relatorio ARQ=docs/relatorios/AAAA-MM-DD-assunto.md`.
- **Identificação do documento**: o `.md` abre com um bloco `---` de
  metadados, que vira a ficha impressa abaixo do título e o fecho assinado no
  fim. Documento emitido à contratante precisa dizer, na própria folha, o que
  é, sob qual contrato, para quem, em que data e sob responsabilidade de quem.

  ```yaml
  ---
  titulo: Relatório de situação AAAA-MM-DD — AlupData Fase 1
  documento: Relatório de situação
  referencia: REL-AAAA-MM-DD · AlupData Fase 1
  emitido_em: DD de mês de AAAA
  emitente: ness. Processos e Tecnologia Ltda.
  destinatario: Alup
  contrato: CPS-01025/2026 — AlupData Fase 1: DataLake
  marco: Onda N · X% · R$ …
  responsavel: Nome de quem emite
  classificacao: Confidencial — uso restrito das partes
  local_data: DD de mês de AAAA
  ---
  ```

  Campo ausente não é impresso, e documento sem o bloco continua gerando como
  antes — a mudança é retrocompatível. `titulo` alimenta a aba do navegador e
  os metadados do PDF; sem ele, o gerador usa o `#` do documento.
- **Dois formatos**: o `.md` é a fonte e o que se lê no GitHub; o `.html` é a
  mesma coisa com a identidade ness. aplicada, para enviar à contratante ou
  imprimir em PDF. O HTML é autocontido — abre direto no navegador, sem
  servidor e sem dependência externa além da fonte Montserrat.
- **Toda questão aberta citada num relatório precisa existir como issue.** O
  relatório é a leitura; a issue é o controle. Se aparecer uma pendência nova
  ao escrever o relatório, abra a issue antes de emitir.
- **Sem dado de cliente.** Vale a mesma regra do resto do repositório: número
  de contrato e marco financeiro, sim; dado extraído de sistema da Alup, não.
- **Tom cordial.** O relatório é correspondência com a contratante, não peça de
  processo. Abre e fecha com cortesia, trata a outra parte como parceira e
  reconhece o que houver de razoável na posição dela. Isso **não** suaviza o
  registro: data, prazo vencido e efeito contratual entram com todas as letras,
  porque é para isso que o documento existe. O que muda é o registro da língua —
  "pedimos atenção" em vez de "fica registrado contra"; explicar por que o
  registro protege os dois lados em vez de apenas afirmá-lo. Um relatório que
  soa a cobrança consegue estar certo e ainda assim custar a relação que
  sustenta o contrato.
