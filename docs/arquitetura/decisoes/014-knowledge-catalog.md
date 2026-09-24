# ADR 014 — Knowledge Catalog: governança, linhagem e recursos de IA do produto

**Status**: aceito · **Data**: 2026-09-10

## Adendo de 2026-09-23 — lake, zonas e ativos declarados

`infra/modules/catalogo` declara o lake `alupdata`, as três zonas — Bronze
crua, Silver e Gold curadas — e um ativo por dataset, mais o bucket raw na
zona Bronze. O agente de serviço do Dataplex recebe `dataplex.serviceAgent`
no projeto, sem o que o ativo nasce em estado de erro.

**A descoberta nasce desligada.** Ela é cobrada por unidade de processamento,
e o esquema das tabelas vem do Dataform (ADR 012), que é fonte melhor do que
inferência: ligá-la pagaria para adivinhar o que já está declarado. É uma
variável, `descoberta_ativa`, para o dia em que houver motivo.

Os ***aspect types*** entraram em seguida, no mesmo dia: `origem` — com
`curada`, `automatica` e a data da última revisão humana, que é a condição
desta ADR para ativar a IA generativa — e `dominio-analitico`, com os oito
domínios do B1 e o responsável. Eles são **estrutura**, não conteúdo: dizem
que campos uma anotação pode ter, e por isso não dependem de carga.

Continua fora, na [issue #36](https://github.com/nessenergy/Alupdatalake/issues/36),
o **glossário de negócio** a partir de `docs/glossario.md`, e o preenchimento
das anotações — os dois são conteúdo, e conteúdo antes da primeira carga seria
descrição de tabela vazia.

## Contexto

A Onda 4 do contrato prevê a "configuração do Google Cloud Dataplex (Knowledge
Catalog) com mapeamento lógico de Lakes, Zonas de dados (Bronze/Silver/Gold) e
Ativos, ativação de linhagem automática e criação de Tag Templates".

Dois fatos do produto mudaram o vocabulário desde que o texto foi escrito:

- em **10/04/2026** o Dataplex Universal Catalog passou a se chamar
  **Knowledge Catalog**. API, comandos `gcloud dataplex`, bibliotecas e nomes de
  IAM não mudaram;
- o **Data Catalog foi descontinuado em 01/06/2026**. *Tag templates* eram
  recurso dele; no Knowledge Catalog a mesma função se chama *aspect types*.

Além disso, o produto passou a oferecer recursos de IA generativa com o modelo
Gemini, do próprio Google — o que exige posição explícita, dada a regra 6.

## Decisão

### Escopo da Onda 4, como no contrato

- **Lake, zonas e ativos**: um lake do projeto, zonas Bronze, Silver e Gold, e
  os datasets e o bucket raw como ativos.
- **"Tag Templates" do contrato = *aspect types*.** É o mesmo recurso com o nome
  atual; a homologação lê o termo contratual por essa equivalência.
- **Glossário de negócio** a partir de [`docs/glossario.md`](../../glossario.md),
  com os termos ligados às colunas que os usam.

### Linhagem desde o primeiro `apply`, não só na Onda 4

A API de linhagem é habilitada no primeiro `apply`, para que o histórico se
acumule desde a primeira carga: BigQuery e Dataform registram sozinhos
(ADR 012), o trecho origem → Bronze vem do executor via OpenLineage (ADR 013) e,
na Onda 3, o Airflow também reporta linhagem. O custo, se houver, aparece na
fatura; no painel de custo (ADR 007) só depois do billing export (camada F2),
porque o painel hoje lê apenas o log do BigQuery.

### Qualidade: uma regra, um lugar

As *assertions* do Dataform são o portão que barra dado ruim (ADR 012). O
Knowledge Catalog faz *profiling* — sem regra — para dar visibilidade. *Scans*
de qualidade do catálogo não duplicam as *assertions*.

### Configuração como código

Lake, zonas, ativos, *aspect types* e glossário são declarados em `infra/`
onde o provider do Terraform cobre; o que ele não cobrir vai para script
versionado em `scripts/`. Nada pelo console (regra 5).

### Recursos de IA generativa: ativados, sob o aviso abaixo

Descrição de ativo passa a carregar o *aspect* `origem`, com valor `curada` ou
`automatica`, para que a separação fique visível a quem consulta o catálogo.

> ### Aviso — recursos de IA generativa do Knowledge Catalog
>
> **Natureza.** O Knowledge Catalog é um serviço do Google Cloud. Ele fica na
> organização da Alupar, é faturado à Alup pela conta de faturamento do projeto
> e é operado pela Alup. Alguns recursos dele usam o modelo Gemini, do próprio
> Google: sugestão de descrições de tabelas e colunas, identificação de relações
> entre ativos, consultas SQL de exemplo, busca semântica e acesso de agentes
> via MCP.
>
> **Uso no produto, não na execução do contrato.** Esses recursos fazem parte
> da plataforma entregue à Alup e são usados por ela. A ness. desenvolve a
> plataforma e não os utiliza. Nenhum entregável do contrato CPS-01025/2026 é
> produzido com eles: código, SQL, conectores, linhagem, glossário, dicionário
> de dados e documentação são de autoria da equipe da ness.
>
> **Conteúdo gerado automaticamente.** Descrição ou consulta sugerida pelo
> serviço fica marcada no catálogo como `origem = automatica`. Ela não é
> homologada, não entra na medição das ondas e não substitui a documentação do
> componente 07. Só passa a ser oficial depois que o dono de dados do domínio,
> conforme a RACI, revisa e aprova.
>
> **Tratamento de dados.** Para gerar sugestões, o serviço processa metadados:
> esquemas, logs de consulta e modelos semânticos. O processamento acontece
> dentro do Google Cloud, na região do ambiente (ADR 023), sob os termos de
> serviço do Google Cloud contratados pela Alupar. A ness. não controla esse
> processamento nem responde por ele.
>
> **Reversibilidade.** Os recursos de IA podem ser desativados a qualquer
> momento, sem efeito sobre catálogo, linhagem, glossário e regras de qualidade
> de dado.
>
> **Registro.** Ativação decidida pelo arquiteto da solução, Ricardo Esper
> (ness.), após a reunião de revisão arquitetural com o Google, e registrada em
> 10/09/2026.

## Alternativas avaliadas

- ***Google Cloud Data Agent Kit*** — avaliado e não adotado. É ferramenta de
  desenvolvimento assistido por IA, em Preview (termos Pre-GA), e cairia do
  lado "execução do contrato" da distinção feita no aviso acima. Não é peça da
  plataforma nem cobre nenhum dos 7 componentes. Pode ser reavaliado pela
  equipe da Alup depois do handoff, quando sair do Preview, como escolha de
  ferramental dela.

## Consequências

- A regra 6 do `AGENTS.md` passa a registrar a exceção: IA no produto, operada
  pela Alup, é aceita; IA na execução do contrato continua proibida.
- O item 4.3 do plano de execução (Dataplex: catálogo e linhagem, 20h) passa a
  se chamar Knowledge Catalog, sem mudança de escopo ou de esforço.
- **Antes de ativar os recursos de IA**, confirmar que estão disponíveis em
  `us-central1`: a página de localizações do produto não informa (ADR 023).
- Operação do catálogo e decisão de manter ou desligar os recursos de IA depois
  do handoff são da Alup.

## Adendo de 2026-09-11 — retenção da linhagem

A documentação do Google informa que toda informação de linhagem fica retida
por 30 dias. Ligar a API no primeiro `apply` não acumula histórico além
disso — garante que a linhagem exista desde a primeira carga e se renove a
cada execução. A aresta origem → Bronze de uma fonte fica visível enquanto
ela rodar ao menos uma vez a cada 30 dias, e fontes mensais ou esporádicas (o
IPCA, por exemplo) podem ficar sem ela no intervalo. O dicionário de dados
(componente 07) continua sendo o registro permanente da linhagem.
