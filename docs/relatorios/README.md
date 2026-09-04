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
| 04/09/2026 | [Registro de atraso — A3 não entregue](2026-09-04-a3-nao-entregue.md) | Onda 0 · 15,52% · **postergada** | 1 · **G1**, resposta do Google, sem prazo acordado — bloqueia A3 por decisão da Alup |

## Convenções

- **Nome do arquivo**: `AAAA-MM-DD-assunto.md`, data de emissão.
- **Como gerar o HTML**: `make relatorio ARQ=docs/relatorios/AAAA-MM-DD-assunto.md`.
- **Dois formatos**: o `.md` é a fonte e o que se lê no GitHub; o `.html` é a
  mesma coisa com a identidade ness. aplicada, para enviar à contratante ou
  imprimir em PDF. O HTML é autocontido — abre direto no navegador, sem
  servidor e sem dependência externa além da fonte Montserrat.
- **Toda questão aberta citada num relatório precisa existir como issue.** O
  relatório é a leitura; a issue é o controle. Se aparecer uma pendência nova
  ao escrever o relatório, abra a issue antes de emitir.
- **Sem dado de cliente.** Vale a mesma regra do resto do repositório: número
  de contrato e marco financeiro, sim; dado extraído de sistema da Alup, não.
