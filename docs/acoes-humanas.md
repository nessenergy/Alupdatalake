# Ações que dependem de gente

Atualizado em **2026-09-23**.

Este documento responde uma pergunta só: **o que uma pessoa precisa fazer, e
como exatamente se faz.** Ele não repete o que já está automatizado nem o que
um agente consegue executar sozinho — se está aqui, é porque exige uma conta
de pessoa, uma credencial criada à mão, uma decisão ou uma conversa com a
contratante.

- [`proximos-passos.md`](proximos-passos.md) — a fila: **o que** vem depois, de quem é
- **este arquivo** — **como** se executa cada item que é de pessoa
- [`status.md`](status.md) — onde estamos e o que trava o quê

Cada item traz quem faz, o passo a passo, como saber que deu certo e o que
destrava. Os comandos foram executados ou conferidos em 23/09, no ambiente
`dev`; onde o comando ainda não pôde ser rodado, está dito.

> **Sobre permissão.** A Alup concedeu à ness. os seis papéis de bootstrap da
> [ADR 015](arquitetura/decisoes/015-fundacao-do-ambiente.md) — nenhum deles dá
> Secret Manager, BigQuery ou Cloud Run. Vários comandos abaixo podem
> responder `PERMISSION_DENIED` por isso; cada item diz o que fazer quando
> responder.

---

## 0. ~~Reativar o GitHub Actions~~ — resolvido em 24/09

Parou por cota às 03h e voltou no fim da manhã, com a cobrança regularizada.
Se voltar a acontecer, o sintoma é o job que não inicia, com a anotação de
pagamento recusado ou limite de gasto atingido: *Settings → Billing & plans*
da organização `nessenergy`, depois `gh run rerun <id> --failed`.

---

## 1. Destravar o Dataform — sem isto não há dado nenhum

**Quem**: ness. (líder técnico ou quem tiver acesso ao Secret Manager do `dev`)
· **Bloqueia**: Bronze, Silver, Gold, homologação da Onda 0 · **Issue**:
[#95](https://github.com/nessenergy/Alupdatalake/issues/95)

O `infra/` está aplicado em `dev`, mas o repositório Dataform não existe: ele
depende de um token do GitHub gravado no secret `alupdata-dataform-git-token`,
que o Terraform cria **vazio** de propósito — segredo não entra em código.
Enquanto o token não existir, nenhuma tabela é criada e as ingestões agendadas
falham por tabela ausente.

### 1.1 Criar o token

Em [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new):

| Campo | Valor |
|---|---|
| Token name | `alupdata-dataform-dev` |
| Resource owner | **`nessenergy`** — não a conta pessoal |
| Expiration | a definir; anote a data, porque no vencimento o Dataform para |
| Repository access | *Only select repositories* → `nessenergy/Alupdatalake` |
| Permissions → Repository | **Contents: Read-only** e nada mais (*Metadata: Read-only* entra sozinho) |

A organização está no GitHub Enterprise: o token pode ficar **pendente de
aprovação** de um owner antes de funcionar.

### 1.2 Gravar no Secret Manager

Nunca cole o token em chat, issue, e-mail ou arquivo do repositório. O caminho
do projeto é o cofre local mais o script que já existe — ele não imprime o
valor em momento algum:

```powershell
# 1. acrescente ao cofre local (fora do repositório), usando o nome do secret como chave:
#    alupdata-dataform-git-token=<token>
notepad $env:USERPROFILE\.alupdata\segredos.env

# 2. simule, confira o que ele faria, e só então grave
$env:ALUPDATA_SECRETS_LOCAIS=1
uv run python -m scripts.migrar_segredos --projeto alupar-dev-alupdata
uv run python -m scripts.migrar_segredos --projeto alupar-dev-alupdata --aplicar
```

Alternativa direta, sem cofre:

```powershell
[IO.File]::WriteAllText("$env:TEMP\tok.txt", "<token>")
gcloud secrets versions add alupdata-dataform-git-token --data-file="$env:TEMP\tok.txt" --project=alupar-dev-alupdata
Remove-Item "$env:TEMP\tok.txt"
```

O `WriteAllText` existe para não gravar a quebra de linha que o `echo` do
PowerShell acrescentaria — token com `\n` no fim é recusado pelo GitHub e o
erro aparece longe daqui.

**Vai responder `PERMISSION_DENIED`**, e respondeu em 24/09: nenhuma conta da
ness. tem papel no Secret Manager. Não é falta de concessão da Alup — é uma
lacuna nossa. A ADR 015 diz que gravar este token "entra no `infra/` por
variável, como o acesso de pessoas", e a variável nunca tinha sido escrita.
Agora existe: `gravacao_segredos`, que dá `roles/secretmanager.secretVersionAdder`
— **grava versão sem poder ler** — só a grupo, nunca a pessoa (R01).

1. Criar no Google Workspace da ness. um grupo para quem opera o AlupData — por
   exemplo `alupdata-operacao@ness.com.br` — com as pessoas que gravam
   credencial. **Criado em 24/09: `operacao-datalake@ness.com.br`.**
2. Preencher no `infra/environments/dev.tfvars`:
   `gravacao_segredos = ["group:operacao-datalake@ness.com.br"]`, por PR — **feito no #204**.
3. Depois do deploy, gravar o token com os comandos acima.

O mesmo papel destrava o `migrar_segredos`, que grava as credenciais das
fontes e esbarraria no mesmo erro.

Evite as saídas rápidas: o convite de *Owner* pendente no `dev` dá acesso
muito além do necessário, e pedir a outra pessoa que rode o comando faz o token
trocar de mãos.

**O token de `dev` vence em 25/09/2027.** Na véspera, criar outro pelo mesmo
caminho e gravar como versão nova; o Dataform passa a usá-la quando
`DATAFORM_GIT_TOKEN_VERSAO` apontar para ela.

### 1.3 Apontar a versão e reexecutar o deploy

```powershell
gh variable set DATAFORM_GIT_TOKEN_VERSAO --env dev --body 1
gh workflow run deploy.yml -f environment=dev -f module=all
```

**Deu certo quando**: o passo do Dataform no workflow termina verde, e
`terraform output repositorio_dataform` deixa de ser vazio. Depois disso as
tabelas Bronze existem e as ingestões agendadas param de falhar.

---

## 1b. Ligar o `TABLE_STORAGE` no projeto — registro

**Feito em `dev` em 24/09, entre 09h45 e 11h**, à mão, por quem já era *Owner*
do projeto (Thiago). A invocação do Dataform das 09h45 ainda reprovou
`gold.custo_consultas` com a mensagem de `TABLE_STORAGE` desligado; a das 11h
(a *workflow config* `diario`) passou inteira, 141 ações, zero falhas.

Regra do projeto (25/09): nenhuma ação operacional no GCP depende de pessoa
de fora da equipe ness. — e o único *Owner* de `hml` é externo. O deploy
passa a ligar o `TABLE_STORAGE` sozinho, com a SA de deploy (passo "Ligar o
TABLE_STORAGE do projeto" em `.github/workflows/deploy.yml`, depois do
`terraform apply`), que precisa do papel `bigquery.config.update` — concedido
no bootstrap (`infra/bootstrap/main.tf`, ADR 015, adendo de 25/09).

O que resta é de pessoa: o Ricardo reaplicar o bootstrap com o papel novo em
`dev` (que já tem o efeito, mas não o papel formal) e em `hml`. Sem isso, o
passo do deploy responde `PERMISSION_DENIED` nesses ambientes.

**Deu certo quando**: o próximo deploy termina com o Dataform em `SUCCEEDED`.
O histórico de armazenamento leva cerca de um dia para aparecer no painel de
custo.

---

## 2. Rotacionar o token do TempoOK

**Quem**: ness., junto ao fornecedor · **Bloqueia**: nada hoje; é dívida de
segurança com prazo · **Referência**:
[ADR 020](arquitetura/decisoes/020-token-tempook-rotacao-na-producao.md)

O token chegou por e-mail em 14/09 e a ADR 020 fixou a rotação como **a
primeira ação depois de A3**. A condição que faltava — Secret Manager
existindo — foi atendida em 23/09.

1. Pedir ao TempoOK a emissão de um token novo e a invalidação do atual.
2. Combinar que a entrega seja feita **direto no Secret Manager**, e não por
   e-mail. Se não for possível, gravar o valor recebido imediatamente e apagar
   a mensagem de origem.
3. Gravar como versão nova do secret `alupdata-tempook-api-token`, pelo mesmo
   caminho do item 1.2.

**Deu certo quando**: o conector `tempook_ena_prevs` roda com a versão nova e o
token antigo deixa de autenticar.

---

## 2b. Gravar a chave do App do quadro

**Quem**: alguém do grupo `operacao-datalake@ness.com.br` que administre o App
na organização · **Bloqueia**: a sincronização automática do quadro (achado O5
da avaliação de 24/09) · **Referência**:
[`runbook/acompanhamento-semanal.md`](runbook/acompanhamento-semanal.md), passo 3

O App existe e a variável `QUADRO_APP_CLIENT_ID` está preenchida; falta só a
chave privada. Desde 25/09 o workflow avisa e termina com sucesso enquanto ela
não existe, em vez de falhar todo dia.

1. No GitHub: *nessenergy → Settings → Developer settings → GitHub Apps →* o
   App do quadro *→ Private keys → Generate a private key*. O navegador baixa
   um `.pem`.
2. No console do Google Cloud, projeto `alupar-dev-alupdata`: *Segurança →
   Secret Manager →* `alupdata-github-quadro-app-key` *→ Nova versão →
   Fazer upload de arquivo*, escolher o `.pem` e *Adicionar nova versão*.
3. Apagar o `.pem` do disco e da lixeira.
4. No GitHub: *Actions → Quadro — sincronização automática → Run workflow*,
   com **simular** marcado.

**Deu certo quando**: nessa execução o passo que roda `scripts.quadro` aparece
executado, e não pulado, e o log lista o que mudaria no quadro. A partir daí o
agendamento das 08h grava sozinho.

---

## 3. Pedidos à Alup que continuam abertos

Nenhum destes é comando: é conversa, com prazo e efeito contratual. A cobrança
formal e as questões financeiras ficam com a coordenação — este documento
registra o que pedir e por quê.

| # | O que pedir | Quem, na Alup | Por que trava |
|---|---|---|---|
| [#87](https://github.com/nessenergy/Alupdatalake/issues/87) | **Valor do orçamento por ambiente** | Saulo (TI) | O padrão do módulo é R$ 500/mês e estoura o teto da E2 (US$ 20/mês até novembro, US$ 400 depois). Sem o valor, o alerta de custo não sobe |
| — | ~~**Papéis para `gptorres@ness.com.br`** nos três projetos~~ — **congelado em 24/09 por decisão do Ricardo**: segue registrado no pedido de 24/09 (item 14 do relatório), mas sem cobrança ativa | Saulo (TI) | As outras três contas da ness. receberam; essa não. Não bloqueia trabalho técnico hoje |
| — | **Grupos que passam pelo IAP do Portal** (R01 do RIPD) | Leonardo (PO) | O Portal está publicado e só a Alup pode entrar: o IAP com cliente OAuth gerenciado pelo Google [admite apenas contas da organização](https://docs.cloud.google.com/iap/docs/managed-oauth-client), e contas `@ness.com.br` são recusadas (25/09). **É o que permite demonstrar o Portal no aceite das Ondas 0 e 1** |
| — | **Ligar o billing export no console**, apontando para o dataset `faturamento` do `dev` | Alup, com papel na conta de faturamento | Dataset regional só recebe dado **a partir do dia em que o export é ligado**: cada dia de espera é histórico que não volta ([ADR 007](arquitetura/decisoes/007-portal-de-custo.md)) |
| [#24](https://github.com/nessenergy/Alupdatalake/issues/24) · [#23](https://github.com/nessenergy/Alupdatalake/issues/23) | **Token do Hubspot** e **acesso/host do BBCE** | Leonardo (ponto focal) | Conectores escritos e parados; Onda 2 não executa |
| [#12](https://github.com/nessenergy/Alupdatalake/issues/12) · [#13](https://github.com/nessenergy/Alupdatalake/issues/13) · [#14](https://github.com/nessenergy/Alupdatalake/issues/14) · [#15](https://github.com/nessenergy/Alupdatalake/issues/15) | **VPN e credenciais read-only**: Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS | Leonardo, com Mauricio de substituto | Onda 3 inteira, 155h. **Vence em 25/09** e é o único item que dispara ociosidade de 4h/dia |
| [#142](https://github.com/nessenergy/Alupdatalake/issues/142) | **Exemplos reais das planilhas** (G3) | Taina / donos de dado | Sem eles não dá para declarar template nem conferir o escopo das 13 fontes contra a proposta |
| [#141](https://github.com/nessenergy/Alupdatalake/issues/141) | **De-para de usina: a sigla interna** | dono do domínio de Geração | Três quartos do de-para já saem do dado público; falta a coluna que só a Alup tem |
| [#174](https://github.com/nessenergy/Alupdatalake/issues/174) · [#129](https://github.com/nessenergy/Alupdatalake/issues/129) | **Caminhos do TempoOK que importam** e onde está o acervo recente de boletins | Leonardo, com o fornecedor | O token alcança a previsão de ENA em dia; o resto do produto é adivinhação sem a lista |
| [#150](https://github.com/nessenergy/Alupdatalake/issues/150) | **Dois pontos da matriz RACI**: quem compõe o Comitê e o papel do Google | Leonardo | Governança da passagem de fase |

**Como pedir**: pelo canal que a Alup usa para o projeto — Google Chat para o
operacional, e-mail quando o registro precisa ficar. O que muda prazo ou
escopo entra também como comentário na issue correspondente, porque é lá que o
acompanhamento vive.

---

## 4. Decisões pendentes — não é execução, é escolha

| # | Decisão | Opções | Minha recomendação |
|---|---|---|---|
| [#188](https://github.com/nessenergy/Alupdatalake/issues/188) | Como avisar que uma **fonte semanal ou mensal parou** | (a) vigia diário lendo `gold.saude_ingestao`; (b) asserção no Dataform; (c) métrica customizada no lugar da métrica de log | **(a)** — mantém o aviso no mesmo lugar dos outros e não confunde frescor com qualidade de dado |
| [#177](https://github.com/nessenergy/Alupdatalake/issues/177) | Quando aplicar o **design system da Alup** no Portal | depende de a ness. fechar o sistema de design e de a Alup validar | pedir à Alup o logo em SVG e a licença da Basic Sans junto, para não travar duas vezes |
| — | **Região `us-central1`** | a Alup pode preferir `us-east1` e alterar a política | vale **até o primeiro apply de `prod`**; depois, mudar região é migração de dado |

---

## 5. Ordem, se for para fazer uma coisa de cada vez

1. **Token do Dataform** (item 1) — é o único que trava trabalho técnico hoje.
2. **VPN e credenciais da Onda 3** (item 3) — vence em 25/09 e é o único com
   cláusula financeira associada.
3. **Grupos do IAP e billing export** (item 3) — o export perde histórico a
   cada dia de espera.
4. **Rotação do TempoOK** (item 2) — dívida de segurança com condição já
   atendida.
5. **Decisões do item 4** — nenhuma bloqueia código hoje.
