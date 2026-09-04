# ADR 005 — Escopo do Portal MVP

**Status**: aceito · **Data**: 2026-08-26

## Contexto

O item 0.15 do plano — "Portal MVP com autenticação" — é o **único
componente de front-end de todo o contrato**, estimado em 8h. O contrato
exclui painéis e relatórios de BI (PowerBI, Tableau) de forma explícita, e abre
exatamente uma exceção: este Portal.

Oito horas para "um portal" é um convite ao mal-entendido. O risco R5 do plano
("escopo do Portal MVP cresce") não é hipotético: componente de interface atrai
pedido incremental — um filtro aqui, um gráfico ali, exportar para Excel — e
cada pedido isolado parece pequeno. Somados, viram um produto de BI que o
contrato explicitamente não comprou, consumindo horas de conector.

Esta ADR crava o escopo por escrito **antes** de existir código, que é a
mitigação que o próprio plano prescreve.

## Decisão — o que o Portal MVP é

Uma página web que prova, de ponta a ponta, que dado do DataLake chega a um
usuário autenticado:

1. **Login** com identidade Google restrita ao domínio da Alup.
2. **Uma view Gold** renderizada como tabela, com o dado real do BigQuery.
3. **Data da última ingestão** daquela view, lida de `bronze._execucoes`.

Isso é o critério de pronto do item 0.15 — "login funcionando; uma view Gold
visível" — e nada além disso.

## Decisão — o que o Portal MVP não é

Fora de escopo, e cada item aqui vira mudança de escopo formal se pedido:

| Não é | Onde isso vive |
|---|---|
| Painel com gráficos, filtros ou drill-down | ferramenta de BI (pendência A6) |
| Múltiplas views ou navegação entre telas | idem |
| Exportação para Excel/CSV/PDF | idem |
| Cadastro de usuário, perfis, permissão por linha | não previsto na Fase 1 |
| Edição de dado pela tela | o lake é read-only para o usuário final |
| Upload de planilha | é o motor S2 Data Intake (tarefa 4.1), não o Portal |
| Alerta, agendamento de e-mail, relatório recorrente | não previsto na Fase 1 |
| Responsivo/mobile, tema, identidade visual elaborada | não previsto na Fase 1 |

O Portal **não é o consumidor final dos dados**. Quem consome é a ferramenta de
BI que a Alup ainda vai definir (pendência A6). O Portal existe para provar o
caminho, não para substituí-la.

## Decisão — como é construído

- **Sem framework de front-end.** HTML servido pelo próprio backend Python, com
  a tabela renderizada no servidor. React/Next.js aqui significaria build,
  bundler, deploy separado e mais superfície para manter no handoff — para
  desenhar uma tabela.
- **Autenticação por Google Identity**, restrita ao domínio da Alup. Não
  escrevemos gestão de senha: senha própria em MVP é passivo de segurança sem
  contrapartida.
- **Mesmo repositório, mesma imagem** da CLI. Um artefato a menos para o time
  que vai operar.
- **Leitura direta do BigQuery**, sem cache nem banco intermediário. Uma view
  Gold por request, consultada com a mesma `Settings` do resto do projeto.

## Consequências

- Enquanto o ambiente GCP (pendência A3) não existir, o Portal roda contra um
  provedor de dados simulado, com a mesma interface do provedor BigQuery. Isso
  permite construir e testar a tela agora; a troca é de uma linha quando A3
  chegar.
- Se a Alup escolher uma ferramenta de BI que já entrega tela e autenticação
  (A6), o Portal continua fazendo sentido como prova de acesso e como página de
  status da ingestão — mas não deve crescer para competir com ela.
- Qualquer item da tabela "não é" que a Alup pedir entra como mudança de escopo,
  com estimativa própria. Registrar o pedido por escrito no dia em que ele
  chega, não quando o cronograma aperta.

---

## Adendo de 2026-09-04 — endurecimento, sem mudar o escopo

O Portal continua sendo exatamente o que esta ADR define. O que mudou é como
ele se comporta quando algo dá errado, e o que ele declara ao navegador.

**Cabeçalhos de segurança em toda resposta**, inclusive nas de erro e na recusa
por falta de identidade. A política de conteúdo é estrita porque pode ser:
o Portal **não tem uma linha de JavaScript** — as três visões são HTML e SVG
embutido. Isso permite `default-src 'none'` sem `script-src`, que não descreve
o estado atual, e sim impede que ele mude sem alguém perceber.

`style-src` precisa de `'unsafe-inline'`, porque a folha de estilo vai embutida
na página. Separá-la em arquivo estático renderia política mais estrita, mas
exigiria rota nova para servir estático — complexidade que a tela única não
paga.

**Falha fechada, com o motivo no log e não na tela.** Antes, uma exceção do
BigQuery subia até o handler padrão do Flask. Mensagem de erro do BigQuery
costuma trazer projeto, dataset e às vezes o SQL; agora ela passa pelo mesmo
sanitizador que o restante do projeto aplica nas fronteiras de log (cláusula
8.5), e o usuário vê uma página neutra.

Nada disso adiciona funcionalidade: não há tela nova, rota nova nem dado novo.
As exclusões de escopo da tabela acima seguem valendo integralmente.
