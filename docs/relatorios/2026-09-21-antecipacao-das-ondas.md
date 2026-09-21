---
titulo: Proposta 21/09/2026 — o que podemos antecipar e o que precisamos da Alup
documento: Proposta de antecipação de entregas
referencia: REL-2026-09-21 · AlupData Fase 1
emitido_em: 21 de setembro de 2026
emitente: ness. Processos e Tecnologia Ltda.
destinatario: Alup
contrato: CPS-01025/2026 — AlupData Fase 1: DataLake
marco: Ondas 0 a 4 — antecipação de entregas
responsavel: Ricardo Esper
classificacao: Confidencial — uso restrito das partes
local_data: 21 de setembro de 2026
---

# O que podemos antecipar, e o que precisamos da Alup para isso

## 1. Por que escrevemos

Boa parte do trabalho técnico das Ondas 1, 2, 3 e 4 ficou pronta antes do
calendário, porque adiantamos tudo que não dependia de insumo. Hoje o lake tem
**27 conectores**, dos quais **24 já foram verificados contra a origem real**,
com os sete componentes da cláusula 2ª cada.

Queremos aproveitar isso. A cláusula 1ª prevê que atividades, prioridades e
sequência podem ser redefinidas durante a execução, e o regime é de horas, não
de empreitada. Este documento propõe **fechar ondas antes das datas do
cronograma** e lista, em um só lugar, o que precisaríamos da Alup para isso.
Nada aqui muda escopo nem valor.

## 2. Onde estamos

| Onda | Calendário do contrato | Pronto do nosso lado | O que falta para fechar |
|---|---|---|---|
| **0 — Fundação** | até 11/09 | Framework, CI/CD, domínios, dimensões comuns, portal com autenticação (roda hoje com dados simulados) | Ambiente GCP para o primeiro `apply` e três dias de execução real |
| **1 — Mercado base** | 14/09 a 16/10 | **Escopo original entregue**, e além dele: CCEE, ONS e ANEEL com 20 conjuntos de dados, todos verificados contra a origem | O mesmo ambiente GCP — é só carga real e homologação |
| **2 — APIs com credencial** | 19/10 a 13/11 | Hubspot, BBCE e TempoOK com os sete componentes. O TempoOK já baixa um produto em dia (previsão de ENA) | Token do Hubspot e acesso do BBCE |
| **3 — Sistemas internos** | 16/11 a 18/12 | Caminho de banco pronto para Oracle, MySQL e SQL Server, testado sem rede | Credenciais e caminho de rede de cada sistema |
| **4 — Planilhas e handoff** | 21/12 a 08/01 | Motor de ingestão de planilhas pronto | As planilhas de exemplo, para declarar os templates |

**Nenhuma onda está homologada.** Homologar exige carga real em BigQuery e
aceitação da Alup, e as duas dependem do ambiente GCP. É por isso que ele
aparece no topo da seção 4.

## 3. O que podemos antecipar

### 3.1 Ondas 0 e 1, juntas, assim que o GCP existir

Não há trabalho de desenvolvimento pendente em nenhuma das duas. Do dia em que o
projeto `dev` estiver liberado, o caminho é: primeiro `apply`, publicação da
imagem, três dias consecutivos de execução com sucesso e a sessão de
homologação. **A Onda 1, cuja data é 16/10, pode ser homologada junto com a
Onda 0** — as duas passam pelo mesmo ambiente e pelas mesmas evidências.

### 3.2 A Onda 2 antes de ela começar

O calendário abre a Onda 2 em 19/10. Os três conectores já estão escritos contra
a documentação que a Alup enviou em 14/09, e o que falta é ligá-los à origem:

- **Hubspot** — só o token;
- **BBCE** — o acesso somente leitura, que a Alup informou em 14/09 estar sendo
  providenciado, e o endereço do serviço, que não consta da documentação;
- **TempoOK** — **já funciona.** A previsão de ENA, cujo caminho a Alup enviou
  em 18/09, responde para a data de hoje e está verificada. Falta só a Alup dizer
  quais outros arquivos interessam.

Com o token e o acesso em mãos, a Onda 2 pode ser entregue **em outubro, antes
de começar formalmente**.

### 3.3 Começar a Onda 3 pelo MySQL RDS

A Onda 3 é a maior do contrato (155h) e termina às vésperas do recesso. Começá-la
antes alivia o fim do ano, e há uma porta de entrada pronta: a Alup informou em
11/09 que o **MySQL RDS da Comercialização não precisa de VPN**. Com a
credencial somente leitura, podemos começar por ele **já em outubro**, sem
esperar o restante da Onda 3.

Do **Oracle FMB** já recebemos host, porta e schema em 11/09. Falta confirmar
se ele é alcançável sem VPN — se for, também pode começar cedo.

### 3.4 Os templates da Onda 4

O motor que ingere planilhas está pronto desde agosto. Com as planilhas de
exemplo da proposta, declaramos os templates e deixamos a Onda 4 com uma parte
já feita quando ela começar.

## 4. O que precisamos da Alup

Em ordem do que destrava mais. Cada item tem uma issue no repositório, onde o
andamento fica registrado.

| # | O que | Para quê | Onde acompanhar |
|---|---|---|---|
| 1 | **Projeto GCP `dev` liberado**, com os papéis concedidos às quatro contas enviadas em 16/09 | Homologar as Ondas 0 e 1. É o único item que destrava duas ondas de uma vez | [#55](https://github.com/nessenergy/Alupdatalake/issues/55) |
| 2 | **Conta de faturamento** vinculada ao projeto | O `apply` não completa sem ela | [#87](https://github.com/nessenergy/Alupdatalake/issues/87) |
| 3 | **Token do Hubspot** | Fechar o Hubspot na Onda 2 | [#24](https://github.com/nessenergy/Alupdatalake/issues/24) |
| 4 | **Acesso do BBCE** e o endereço do serviço | Fechar o BBCE na Onda 2 | [#23](https://github.com/nessenergy/Alupdatalake/issues/23) |
| 5 | **Credencial somente leitura do MySQL RDS** — e, se a liberação for por lista de IPs, nos avisar, para reservarmos um IP fixo de saída | Começar a Onda 3 sem VPN | [#14](https://github.com/nessenergy/Alupdatalake/issues/14) |
| 6 | **Oracle FMB**: confirmar se é alcançável sem VPN, e a credencial somente leitura | Antecipar a segunda fonte da Onda 3 | [#12](https://github.com/nessenergy/Alupdatalake/issues/12) |
| 7 | **Portal Alup**: credenciais do Aurora, DynamoDB e S3, e o caminho de rede | Onda 3 | [#13](https://github.com/nessenergy/Alupdatalake/issues/13) |
| 8 | **RM/TOTVS**: endpoints e credencial | Onda 3 | [#15](https://github.com/nessenergy/Alupdatalake/issues/15) |
| 9 | **Fuso da janela de leitura** dos sistemas internos (22h às 6h) — é horário de Brasília? | Agendar a Onda 3 dentro da janela certa | [#12](https://github.com/nessenergy/Alupdatalake/issues/12) |
| 10 | **Planilhas de exemplo da proposta** | Declarar os templates da Onda 4 | [#142](https://github.com/nessenergy/Alupdatalake/issues/142) |
| 11 | **Lista das siglas internas com o CEG ao lado** — pouco mais de vinte linhas | Ligar a geração por usina da CCEE aos ativos da Alup. O resto do de-para o lake já montou sozinho | [#141](https://github.com/nessenergy/Alupdatalake/issues/141) |
| 12 | **TempoOK**: quais arquivos interessam, onde estão os boletins recentes e se o token é fixo ou renovável | Ingerir o que importa, e nada além | [#174](https://github.com/nessenergy/Alupdatalake/issues/174) |
| 13 | **Matriz RACI**: quem compõe o Comitê e o papel do Google | Saber quem aceita cada homologação | [#150](https://github.com/nessenergy/Alupdatalake/issues/150) |

Os itens 1 e 2 são a mesma conversa. Os itens 4 a 8 são o pedido de acessos
com prazo em **25/09**, e o item 3 é o mais simples de todos: um token. Se
ajudar, podemos tratar os itens 3 a 9 numa reunião curta com o Leonardo, ponto
focal técnico da Alup: a maior parte é confirmação, não trabalho.

## 5. Como entregar as credenciais

Quando o projeto GCP existir, a forma mais segura para as duas partes é a Alup
gravar cada credencial **direto no Secret Manager**, sem passar por e-mail. Os
nomes já estão definidos e o acesso fica restrito à conta que executa a
ingestão — ninguém da ness. precisa ver o valor:

```
printf '%s' 'O-VALOR' | gcloud secrets versions add alupdata-hubspot-api-token --data-file=-
```

No mesmo dia, pedimos também a **rotação do token do TempoOK**, que chegou por
e-mail em 14/09 e desde 21/09 dá acesso a dado atual. O token novo segue o mesmo
caminho.

Se alguma credencial ficar pronta antes do GCP, combinamos um canal que não seja
e-mail.

## 6. Agradecimento

Chegamos até aqui porque cada insumo que a Alup enviou foi aproveitado no mesmo
dia: a orientação sobre a CCEE, a documentação de 14/09, a matriz RACI e o
caminho do TempoOK de 18/09. A proposta é seguir nesse ritmo — e, com o ambiente
liberado, transformar o que já está pronto em ondas homologadas.
