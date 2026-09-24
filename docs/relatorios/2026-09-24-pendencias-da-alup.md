---
titulo: Pendências da Alup, item a item — 24/09/2026
documento: Pendências da contratante
referencia: REL-2026-09-24 · AlupData Fase 1
emitido_em: 24 de setembro de 2026
emitente: ness. Processos e Tecnologia Ltda.
destinatario: Alup — Leonardo Guiel Marques, com cópia para Saulo Rodrigues, Taina Ulhoa Mota e Mauricio Cardoso
contrato: CPS-01025/2026 — AlupData Fase 1: DataLake
marco: Ondas 0 a 4 — insumos da contratante
responsavel: Ricardo Esper
classificacao: Confidencial — uso restrito das partes
local_data: 24 de setembro de 2026
---

# Primeira carga concluída, e o que precisamos da Alup

Leonardo, boa tarde.

**A primeira carga real do AlupData aconteceu hoje às 9h34**: taxas de juros do
Banco Central, 6 registros carregados sem nenhuma rejeição. O ambiente de
desenvolvimento está completo, e a Onda 0 fica pronta para homologação após três
dias seguidos de carga com sucesso.

Abaixo está tudo o que depende da Alup. Cada item traz o que precisamos, o
formato, onde entregar e o prazo.

## Até amanhã, 25/09 — confirmação dos pedidos de acesso

Por favor, confirmem que **os pedidos internos de VPN e de credenciais das Ondas
2 e 3 já foram abertos** na Alup, com a previsão de entrega de cada um. As
entregas em si têm os prazos abaixo, amarrados ao início de cada onda.

## Credenciais — um único canal

Credenciais **não devem ser enviadas por e-mail, chat, GitHub ou qualquer outro
meio**. Elas são gravadas diretamente no cofre de segredos do projeto (Google
Secret Manager), por um grupo de vocês com permissão de **gravar, sem poder
ler**.

### 1. E-mail do grupo Google da Alup que vai gravar as credenciais — até 26/09

Respondam a este e-mail com o endereço do grupo. Em até 1 dia útil o grupo
recebe a permissão, e avisaremos.

Com o grupo ativo, cada credencial é gravada com o comando abaixo, trocando
apenas o nome do segredo e o arquivo. O arquivo deve ser apagado depois do
envio.

```
gcloud secrets versions add <nome-do-segredo> --data-file=<arquivo> --project=alupar-dev-alupdata
```

**Apoio:** Gabriel Paz (`gpaz@ness.com.br`) acompanha a gravação com vocês, tira
dúvidas e confirma a chegada de cada credencial.

### Onda 2 — APIs. Prazo: 12/10 (a onda começa em 19/10)

**2. BBCE** ([#23](https://github.com/nessenergy/Alupdatalake/issues/23))

- Segredo: `alupdata-bbce-credenciais`
- Formato: um arquivo JSON com exatamente estas cinco chaves:

```json
{"base_url": "…", "company_external_code": "…", "email": "…", "password": "…", "api_key": "…"}
```

**3. Hubspot** ([#24](https://github.com/nessenergy/Alupdatalake/issues/24))

- Segredo: `alupdata-hubspot-api-token`
- O que é: o token de um *private app* criado no Hubspot da Alup, **somente**
  com o escopo `crm.objects.deals.read`.

### Onda 3 — sistemas internos, somente leitura. Prazo: 09/11 (a onda começa em 16/11)

**4. Oracle FMB** ([#12](https://github.com/nessenergy/Alupdatalake/issues/12))

- Segredo: `alupdata-fmb-dsn`
- Formato, uma linha: `oracle://usuario:senha@host:1521/SERVICO`
- Além disso: a configuração da VPN e o contato técnico da TI responsável por ela.

**5. MySQL RDS da Comercialização** ([#14](https://github.com/nessenergy/Alupdatalake/issues/14))

- Segredo: `alupdata-comercializacao-dsn`
- Formato, uma linha: `mysql://usuario:senha@host:3306/base`
- Rede: vocês indicaram que não precisa de VPN. Se o banco restringir acesso por
  IP de origem, avisem, e informamos o endereço de saída do nosso ambiente.

**6. Portal Alup** ([#13](https://github.com/nessenergy/Alupdatalake/issues/13))

- MySQL: segredo `alupdata-portal-alup-dsn`, no formato
  `mysql://usuario:senha@host:3306/base`
- NoSQL e Storage: informem, respondendo na issue #13, **qual é o produto** de
  cada um (por exemplo, MongoDB, Amazon S3). A partir disso indicamos o formato
  da credencial.

**7. RM/TOTVS** ([#15](https://github.com/nessenergy/Alupdatalake/issues/15))

- Segredo: `alupdata-rm-dsn`
- Acesso ao banco: `sqlserver://usuario:senha@host:1433/base` ou `oracle://…`,
  conforme o banco.
- Acesso por API: respondam na issue #15 com a URL base e o método de
  autenticação, e indicamos o formato.

## Arquivos com dado da Alup — prazo: 01/10

Contêm dado da Alup, então **não vão por e-mail nem ao GitHub**. Devem ser
enviados ao bucket **`alupar-dev-alupdata-entrada`**, dentro do próprio projeto
Google Cloud da Alup:
<https://console.cloud.google.com/storage/browser/alupar-dev-alupdata-entrada?project=alupar-dev-alupdata>

Leonardo, Taina, Mauricio, Eduardo e Fernando já têm permissão para enviar. É só
abrir o link, entrar na pasta indicada e usar *Fazer upload*. Cada pasta tem um
arquivo `LEIA-ME.txt` com o que colocar nela.

**8. Exemplos reais das planilhas da proposta (G3)** ([#142](https://github.com/nessenergy/Alupdatalake/issues/142))

- Um exemplo preenchido de cada planilha, no formato em que ela é usada hoje
  (XLSX ou CSV), na pasta `planilhas/`.

**9. Sigla interna das usinas** ([#141](https://github.com/nessenergy/Alupdatalake/issues/141))

- Uma tabela com duas colunas, **sigla interna da Alup** e **CEG** (código da
  usina na ANEEL), na pasta `usinas/`.

## Respostas diretas — neste e-mail ou na issue indicada. Prazo: 01/10

**10. TempoOK** ([#174](https://github.com/nessenergy/Alupdatalake/issues/174), [#129](https://github.com/nessenergy/Alupdatalake/issues/129))

- A lista dos caminhos de arquivo do TempoOK que interessam a vocês. Hoje só
  conhecemos o da previsão de ENA.
- Com o fornecedor, a informação de onde estão os boletins posteriores a outubro
  de 2022.
- Na mesma conversa, peçam ao TempoOK **um token novo**, a ser gravado no
  segredo `alupdata-tempook-api-token` pelo canal acima. Depois disso o token
  atual será invalidado.

**11. Quem acessa o Portal**

- O e-mail de um grupo Google da Alup, ou o domínio (`alupar.com.br`), que deve
  entrar no Portal. Hoje ele está no ar e protegido, sem ninguém autorizado.

**12. Orçamento mensal de nuvem** ([#87](https://github.com/nessenergy/Alupdatalake/issues/87))

- O valor em US$ do alerta de orçamento de cada ambiente: desenvolvimento,
  homologação e produção. A referência de vocês foi de até US$ 20/mês até
  novembro e até US$ 400/mês depois.

## Ações no console do Google Cloud

**13. Exportação de faturamento para o BigQuery — o quanto antes**, por quem
administra a conta de faturamento

- No console: *Faturamento → Exportação de faturamento → BigQuery*.
- Ligar **custo padrão** e **custo detalhado**, os dois apontando para o dataset
  `faturamento` do projeto `alupar-dev-alupdata`.
- O histórico só é gravado a partir do dia em que a exportação é ligada.

**14. Papéis para `gptorres@ness.com.br` — até 01/10**, por quem administra o IAM

- Nos três projetos, os mesmos seis papéis das demais contas da ness., com a
  mesma condição de expiração: 28/02/2027 em `alupar-dev-alupdata`, e 01/03/2027
  em `alupar-hm-alupdata` e `prod-alupdata`.

## Governança — quando puderem

**15. Matriz RACI** ([#150](https://github.com/nessenergy/Alupdatalake/issues/150))

- Quem compõe o Comitê que aprova a passagem de fase, e se o Google fica como
  **consultado**, e não como **responsável**, na matriz RACI.

---

Confirmaremos o recebimento de cada item na issue correspondente, no dia em que
chegar. Se preferirem, podemos percorrer a lista na reunião de sexta.

Obrigado, e seguimos à disposição.

Atenciosamente,<br>
Ricardo Esper<br>
ness.
