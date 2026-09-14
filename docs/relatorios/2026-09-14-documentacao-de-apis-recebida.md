---
titulo: Registro de recebimento 14/09/2026 — documentação de APIs das fontes
documento: Registro de recebimento de insumo
referencia: REL-2026-09-14 · AlupData Fase 1
emitido_em: 14 de setembro de 2026
emitente: ness. Processos e Tecnologia Ltda.
destinatario: Alup
contrato: CPS-01025/2026 — AlupData Fase 1: DataLake
marco: Onda 1 · 20,69% · R$ 30.720,00
responsavel: Ricardo Esper
classificacao: Confidencial — uso restrito das partes
local_data: 14 de setembro de 2026
---

# Documentação de APIs das fontes — recebimento, efeito e uma recomendação de segurança

## 1. Objeto

Registro do recebimento, em **14/09/2026**, da documentação técnica das fontes
CCEE, BBCE e TempoOK, encaminhada pela Inteligência de Mercado da Alup.

O insumo atende integralmente a pendência **A2** e parcialmente a **A8**, e
tem efeito imediato sobre a Onda 1: **32h que estavam paradas desde 25/08
voltaram a andar no mesmo dia**. Este documento registra o que foi recebido, o
que isso destrava, o que permanece pendente e uma recomendação de segurança
sobre a forma de entrega de credenciais.

## 2. O que foi recebido

| Fonte | Conteúdo | Pendência atendida |
|---|---|---|
| **CCEE** | Cabeçalhos HTTP a enviar nas requisições; coleção Postman da API JSON; coleção Postman da API XML; indicação de que o restante vem dos dados abertos e de RPA | **A2 — integralmente** |
| **BBCE** | Coleção Postman documentando a API; informação de que um acesso somente leitura está sendo providenciado | **A8 — parte BBCE** |
| **TempoOK** | Exemplo de consulta em Python (não há documentação publicada) e o token de acesso | **A8 — parte TempoOK** |

### 2.1 Endereços recebidos

Transcritos aqui para que o registro seja autossuficiente — quem consultar este
documento no futuro não deve depender da mensagem original:

| Fonte | Documentação |
|---|---|
| CCEE — API JSON (Abertura de Mercado) | `documenter.getpostman.com/view/30322966/2sAXqqchhJ` |
| CCEE — API XML (Plataforma de Integração) | `documenter.getpostman.com/view/12351215/UzJJucpF` |
| **BBCE** | `documenter.getpostman.com/view/48979689/2sB3QJPWWr` |
| TempoOK | não há documentação publicada; o contrato foi derivado do exemplo e **verificado contra a API** (§4.1) |

A coleção do BBCE foi conferida e cobre autenticação, carteiras, produtos,
curva forward, negócios, ordens, contratos, boleta eletrônica, liquidação
financeira e RFQ. **É documentação suficiente para escrever o conector antes de
a credencial chegar** — que era exatamente o que a pendência A8 destravava.

## 3. Efeito sobre a Onda 1: a CCEE está destravada

A pendência A2 registrava que os domínios da CCEE respondiam **HTTP 403** a
requisições automatizadas, bloqueando as 32h previstas para a fonte
InfoMercado. A orientação recebida identificou a causa: **não era bloqueio de
IP nem exigência de credencial, e sim filtro de cliente não identificado**.

A ness. verificou a orientação contra a API real na mesma data, com o
resultado abaixo:

| Requisição | Antes | Com os cabeçalhos indicados |
|---|---|---|
| Catálogo de dados abertos da CCEE | 403 Forbidden | **200 OK — 204 conjuntos de dados** |
| Portal `www.ccee.org.br` | 403 Forbidden | **200 OK** |

**A pendência A2 está encerrada e nenhuma das quatro alternativas discutidas
(liberação de IP, credencial de agente, leitura por outro sistema ou
remanejamento das horas) se fez necessária.** A [issue #52](https://github.com/nessenergy/Alupdatalake/issues/52)
foi fechada, e a decisão está registrada na
[ADR 018](../arquitetura/decisoes/018-vias-de-acesso-a-ccee.md).

### 3.1 Uma distinção que vale registrar

As três documentações da CCEE que chegaram no mesmo e-mail descrevem
**produtos diferentes**, e a distinção muda o que a Onda 1 precisa esperar:

| Via | O que entrega | Credencial |
|---|---|---|
| **Dados abertos (InfoMercado)** | preço de liquidação das diferenças, consumo por submercado e por perfil, garantia física, contabilização, penalidades — 204 conjuntos | **nenhuma** |
| **API JSON — Abertura de Mercado** | operação de varejista e concessionária: migração de unidade consumidora, medições, contratos, recontabilização | credencial de agente |
| **API XML — Plataforma de Integração** | back office do agente: ativos, parcelas, contratos ACL/ACR, medidas, PLD | credencial de agente |

As duas últimas trazem **dado do agente Alupar**, não dado público de mercado.
Elas têm valor — cobrem medição e contratos, que o InfoMercado não cobre — mas
**nada na Onda 1 depende delas**. Ficam registradas como escopo candidato; se a
Alup quiser esse dado, é escopo novo, com pedido de credencial e decisão
própria.

O ponto prático: **a Onda 1 não deve esperar por essas credenciais.** Ela
segue pela via pública, que já funciona.

## 4. O que permanece pendente

| # | Pendência | Situação após este insumo |
|---|---|---|
| **A8** | Documentação de BBCE e TempoOK | **Atendida.** O BBCE está documentado em detalhe; o TempoOK não possui documentação publicada, e o exemplo recebido foi suficiente — o conector está escrito e o contrato de dados, verificado contra a API real (§4.1) |
| **A7** | Credencial de leitura do BBCE | **Em andamento** — a Alup informou que o acesso somente leitura está sendo providenciado. Permanece o prazo de 25/09 e o efeito de ociosidade da cláusula 3ª |
| **novo** | Acesso do TempoOK ao acervo recente | **Verificação junto ao fornecedor** — ver §4.1. Sem isso o conector, já pronto, não tem o que ingerir |
| — | Dados da CCEE sem API | A orientação indica RPA. A ness. **não recomenda** abrir essa frente antes de saber quais indicadores os domínios analíticos exigem (A4): automação de portal é o componente mais caro de manter, e boa parte do que se buscaria por RPA já está nos 204 conjuntos públicos |

### 4.1 TempoOK: o conector está pronto, mas o acervo alcançável para em 2022

O exemplo de consulta permitiu escrever o conector **e verificá-lo contra a API
real na mesma data**. O contrato de dados está confirmado: o caminho do arquivo
é derivável da data, a origem sinaliza ausência com HTTP 404, o boletim é
publicado em dia útil — não há boletim em fim de semana nem em feriado — e a
conexão dispensa a desativação de verificação de certificado que consta do
exemplo.

Há, porém, um ponto que **depende da Alup** e que a ness. não tem como
resolver:

> **Nenhum boletim posterior a 26/10/2022 responde.** Foram consultadas datas
> em dias úteis de novembro e dezembro de 2022 e ao longo de 2023, 2024, 2025 e
> 2026: todas retornam 404. Sete variações plausíveis do caminho para uma data
> recente também retornam 404.

O token é válido e o caminho está correto — boletins de março a outubro de 2022
são recuperados normalmente. O que não se alcança é o acervo recente. As
hipóteses são três:

1. o token é antigo e sua permissão cobre apenas o período contratado à época;
2. os boletins passaram a ser publicados em outra área do repositório do
   TempoOK;
3. o produto foi descontinuado ou renomeado.

**Solicitamos à Alup que verifique junto ao TempoOK qual das três se aplica.**
Enquanto isso, o conector está correto e ingere zero boletins, que é o
comportamento adequado a um acervo vazio — mas não é o que a Onda 2 precisa
entregar. Resolvido o acesso, o histórico é ingerido de uma vez, bastando
informar o período desejado.

Para dimensionamento: um boletim ocupa cerca de **9 MB**; um ano de dias úteis
fica na ordem de **2 GB** de armazenamento, dentro do teto de custo acordado.

## 5. Recomendação de segurança sobre a entrega de credenciais

O token do TempoOK foi entregue **em texto claro no corpo do e-mail**, com seis
destinatários em cópia. A ness. registra a recomendação, em cumprimento à
cláusula 8ª:

1. **Rotacionar o token do TempoOK na virada de produção** — e não antes.

   Um segredo que trafegou por e-mail permanece nas caixas postais, nos
   servidores de trânsito e em qualquer cópia local, e não há como auditar onde
   parou. A regra, portanto, é rotacionar. Mas **rotacioná-lo hoje reproduziria
   a mesma exposição**: sem o Secret Manager, que depende do insumo A3, o valor
   novo teria de ser entregue pelo mesmo e-mail — resultando em duas
   credenciais expostas em vez de uma.

   Rotacionar na virada de produção permite que a Alup grave o valor novo
   diretamente no cofre do projeto, sem que ele trafegue por e-mail em momento
   algum. É uma rotação só, e que de fato encerra a exposição.

   A espera é segura porque o alcance do token foi medido (§4.1): somente
   leitura, sem dado pessoal, e limitado a um acervo encerrado em 2022. A
   decisão está registrada com responsável nomeado e com gatilhos que antecipam
   a rotação — entre eles, **a própria Alup solicitá-la** ou o acervo recente
   passar a ser alcançável.

2. **Entregar as credenciais seguintes — a do BBCE inclusive — diretamente no
   Google Secret Manager do projeto**, sem passar por e-mail, mensagem ou
   planilha. Esta recomendação **não** foi adiada e vale a partir de A3. Os
   segredos já estão declarados em `infra/`, com nome definido e acesso
   restrito à conta de serviço da ingestão; o valor é gravado por quem o
   possui, com um comando, e nunca é visto por terceiros nem pela equipe da
   ness.

3. Enquanto o projeto GCP não existe (pendência **A3**), o token recebido é
   mantido **fora do repositório e fora de qualquer artefato versionado**, em
   cofre local com recusa programática de gravação dentro do repositório e de
   uso em ambiente de execução. Ele não consta deste documento nem de qualquer
   arquivo entregue.

Esta é uma recomendação de higiene, não um apontamento: a necessidade era
legítima e o canal, o disponível no momento. O que se propõe é que, existindo o
canal próprio a partir de A3, ele passe a ser o usado.

## 6. Situação do cronograma

Este insumo **não altera** a situação de A3, que segue sendo o item que
determina o cronograma. O ambiente GCP venceu em 04/09 e hoje completa o
**quinto dia útil de atraso**; a previsão informada pela Alup em 11/09 é 18/09.

O efeito prático do insumo de hoje é outro, e positivo: **a Onda 1 deixa de
depender da contratante.** Seu trabalho técnico prossegue integralmente em
paralelo à espera por A3 — sem, contudo, poder ser homologada antes da primeira
carga real, que depende do ambiente.

| Insumo | Situação em 14/09 |
|---|---|
| **A2** — decisão sobre a CCEE | **Encerrada** |
| **A8** — documentação de BBCE e TempoOK | **Atendida** |
| **A3** — ambiente GCP | Vencido em 04/09 · 5º dia útil de atraso · previsão de 18/09 |
| **A7** — credenciais e acessos | Em andamento · prazo 25/09 · ociosidade de 4h/dia se ultrapassado |
| **A9** — token do Hubspot | Pendente |

## 7. Agradecimento

A orientação sobre os cabeçalhos resolveu, em uma linha, uma pendência que
estava aberta havia vinte dias e que se supunha exigir liberação de IP ou
credencial. O registro fica também como reconhecimento: foi o insumo de maior
efeito por menor esforço recebido até aqui neste contrato.
