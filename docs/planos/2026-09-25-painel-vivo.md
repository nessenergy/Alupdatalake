# Painel vivo do projeto

Registrado em **25/09/2026**. Em 26/09 foram feitas as Tarefas 1 a 4; a 5 e a 6 dependem de concessão e de console.

**Objetivo:** um painel de acompanhamento do AlupData que se atualiza sozinho,
com pouco texto e dado real: marcos, cargas por onda, pendências com a Alup e
a rede da Onda 3.

**Onde fica:** no GCP da ness., no projeto `ness-painel-projetos`, e não no
projeto da Alupar. O painel é alimentado pela ness., e pôr contas da ness. no
IAP do Portal mudaria a segurança de um produto da Alup. Nada deste plano cria
recurso nos projetos da Alupar, nem dá a conta dela permissão no projeto da
ness.

## Já existe (25/09)

- Projeto `ness-painel-projetos`, com faturamento vinculado.
- Repositório de imagens `paineis` (Artifact Registry, `us-central1`) e a
  imagem estática `painel-alupdata:20260925`, a primeira versão do painel.
- Cloud Run `painel-alupdata`, com IAP ligado e o agente do IAP como único
  invocador. **Ainda sem ninguém na lista de acesso.**

## Fontes de dados

| Bloco | Fonte | Atualização |
|---|---|---|
| Cargas por onda | `bronze._execucoes` de `dev` e `hml`: último estado por entidade, linhas, horário, e os últimos 7 dias | automática |
| Dias seguidos de carga | calculado das mesmas execuções | automática |
| Pendências com a Alup | issues abertas com a etiqueta `tipo/dependencia` (a convenção `[ALUP]` que o repositório já usa): prazo, dias em aberto, atraso | automática |
| Rede da Onda 3 | última execução do `teste-conexao-fmb` (passou, ou a mensagem de onde parou) mais o checklist G, L e N | automática + arquivo |
| Marcos e ondas | `painel/marcos.toml` no repositório: janelas, datas e estado de cada marco | editado quando um marco muda |

Sai do ambiente da Alupar só **metadado de execução** (contagens, status e
horários), nunca linha de dado.

## Tarefas

### Tarefa 1 — Issues das pendências (feita em 26/09)

- A etiqueta já existia: `tipo/dependencia`, com o prefixo `[ALUP]` no título.
- Abertas em 26/09 as que faltavam (#258 a #262), e a #12 recebeu a situação da rede com prazo.
- Origem das que faltavam: dos pedidos da [pauta de 25/09](../relatorios/2026-09-25-alinhamento.md) §4: quem
  assina o aceite, confirmação da reunião, as 32h do item 2.1, grupos do
  Portal, e rede local e credencial do FMB. **O cliente lê o GitHub:** texto no
  tom da pauta, com prazo no corpo (`Prazo: AAAA-MM-DD`).

### Tarefa 2 — `painel/marcos.toml` (feita em 26/09)

Ondas (janela do contrato, horas, marco percentual), marcos com data e estado,
e o checklist da rede (G1 a G6, L1 a L6, N1 a N4, conforme
[`runbook/rede-onda3.md`](../runbook/rede-onda3.md)). Um teste valida o esquema.

### Tarefa 3 — Gerador do `dados.json` (feita em 26/09)

`scripts/painel.py`, que junta as quatro fontes num JSON com
`gerado_em`. Testes com as fontes simuladas: entidade sem execução, execução
com erro, dias seguidos interrompidos, issue sem prazo, teste de conexão que
nunca rodou. O gerador nunca escreve credencial nem linha de dado no JSON.

### Tarefa 4 — Página (feita em 26/09: `painel/index.html`)

A página atual, lendo `dados.json` do mesmo endereço, com "atualizado há X
min" e estado vazio explícito quando um bloco falha. Marca ness.
(Montserrat, ciano como único acento) e menos texto interpretativo.

### Tarefa 5 — Entrega automática

- Bucket no `ness-painel-projetos`, montado no Cloud Run (volume do Cloud
  Storage), de onde o nginx serve o `dados.json`.
- Workflow **Painel**, de hora em hora e depois de cada deploy e de cada
  *Executar ingestão*. Lê com a conta de deploy de `dev` e `hml` e grava no
  bucket com uma identidade própria do GitHub no projeto da ness. (pool de WIF
  restrito a este repositório, papel só de escrita no bucket).
- **Concessão de permissão:** o pool, o papel no bucket e o papel de leitura
  de issues são concessões e passam pelo Ricardo.

### Tarefa 6 — Acesso (Ricardo, no console)

1. **Cliente OAuth "Externo"** no `ness-painel-projetos` (Google Auth
   Platform → Público: Externo; Clientes → aplicativo da Web, com o URI de
   redirecionamento `https://iap.googleapis.com/v1/oauth/clientIds/<ID>:handleRedirect`),
   aplicado nas configurações do IAP. Sem ele, só contas da ness. entram. O
   segredo do cliente é digitado no console, nunca em chat ou repositório.
2. **Lista de acesso do IAP**: papel *Usuário do app da Web protegido pelo
   IAP* para a equipe da ness. e para os envolvidos da Alupar
   ([`interlocutores.md`](../interlocutores.md)). Se a TI da Alupar bloquear
   aplicativos de terceiros, o administrador deles marca o cliente como
   confiável.

## Custo

Cloud Run com escala a zero, IAP sem cobrança, imagem e logs dentro das faixas
gratuitas: próximo de zero por mês, no faturamento da ness.

## Estimativa

Cerca de 2h30 de desenvolvimento (Tarefas 1 a 5) e 25 minutos de console
(Tarefa 6 e as concessões da Tarefa 5).
