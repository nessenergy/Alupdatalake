# ADR 018 — As três vias de acesso à CCEE, e qual delas atende a Onda 1

**Status**: aceito · **Data**: 2026-09-14 · **Encerra** a pendência A2 e a
[issue #52](https://github.com/nessenergy/Alupdatalake/issues/52) ·
**Complementa** as ADRs [003](003-framework-de-conectores.md) e
[008](008-acesso-a-bancos-relacionais.md)

## Contexto

A Onda 1 previa 32h para a fonte **CCEE InfoMercado**, bloqueadas desde
2026-08-25: `www.ccee.org.br` e `dadosabertos.ccee.org.br` respondiam **HTTP
403** a qualquer requisição automatizada, inclusive à página de documentação
(plano de execução §3.1). A pendência A2 pedia à Alup que decidisse entre
liberar IP, fornecer credencial de agente, ler de outro sistema ou remanejar as
horas.

Em 11/09 a Alup respondeu (item C4 do Questionário de Gaps) que o InfoMercado é
público, que nenhuma dessas vias era necessária e que **o 403 se resolve
ajustando a requisição**. A orientação do ajuste ficou pendente.

Em **14/09** o e-mail de Leonardo Guiel Marques (Inteligência de Mercado)
entregou a orientação e, junto com ela, duas coleções Postman da CCEE. As três
fontes que chegaram no mesmo e-mail **não são a mesma coisa**, e tratá-las como
se fossem levaria a Onda 1 a esperar por credencial que ela não precisa.

## O que o 403 era

Não era bloqueio de IP, nem exigência de credencial: era filtro de
`User-Agent`. A CCEE recusa cliente que não se identifica.

Verificado em 14/09, contra a API real:

| Requisição | Resultado |
|---|---|
| `GET https://dadosabertos.ccee.org.br/api/3/action/package_list` sem cabeçalhos | **403 Forbidden** |
| a mesma requisição com o `User-Agent` indicado pela Alup | **200 OK**, 204 datasets |
| `GET https://www.ccee.org.br/` sem cabeçalhos | **403 Forbidden** |
| a mesma requisição com o `User-Agent` | **200 OK** |

O cabeçalho que a Alup indicou identifica o coletor e dá um contato:

```
User-Agent: Alupar-DataCollector/1.0 (+https://alupar.com.br; contato: comercializacao@alupar.com.br)
```

## Decisão

### 1. O cabeçalho de identificação é do framework, não do conector da CCEE

`src/core/http.py` passa a enviar o `User-Agent` em **toda** requisição de
**todos** os conectores.

Poderia ter ficado no conector da CCEE, que é quem sofre o 403. Ficou no
núcleo por duas razões:

- **Identificar-se é a conduta correta com qualquer origem**, não um contorno
  para uma origem específica. Um coletor anônimo é indistinguível de um
  raspador abusivo, e quem opera o portal do ONS, da ANEEL ou do IBGE tem o
  mesmo direito de saber quem está consumindo e a quem recorrer.
- **Qualquer outra fonte pública pode ligar o mesmo filtro amanhã.** Corrigir
  em um ponto vale para as treze fontes; corrigir no conector da CCEE deixa as
  outras doze esperando o mesmo incidente.

O valor é constante no código — identifica a Alupar e aponta um endereço de
contato público. Não é credencial e não entra no Secret Manager.

### 2. A Onda 1 usa a via de dados abertos (CKAN), sem credencial

A CCEE publica em `dadosabertos.ccee.org.br` uma instância **CKAN** com **204
datasets**, entre eles PLD horário, médio e final, consumo por submercado e por
perfil de agente, garantia física, contabilização e penalidades. Cada dataset
expõe **um CSV por ano**, endereçado por um recurso estável.

É o mesmo formato do ONS (ADR 003, conector `ons_carga`): CSV anual remoto,
recortado pela janela na extração. O conector da CCEE **reusa esse caminho**,
sem framework novo.

A descoberta dos recursos é feita pela própria API CKAN
(`package_show`), não por URL escrita à mão: a CCEE republica arquivo, e o
endereço do recurso muda.

### 3. As duas coleções Postman **não** atendem a Onda 1

Elas vieram no mesmo e-mail e descrevem produtos diferentes do InfoMercado.
Registrar isso agora evita que a Onda 1 espere por uma credencial que ela não
precisa:

| Coleção | O que é | Autenticação | Serve à Onda 1? |
|---|---|---|---|
| [Abertura de Mercado](https://documenter.getpostman.com/view/30322966/2sAXqqchhJ) (`api-abm.ccee.org.br`) | operação de varejista e concessionária: migração de unidade consumidora, medições, contratos CCV, resposta da demanda, recontabilização | OAuth 2.0 (`/sso/oauth/token`) — **exige credencial de agente** | **não** |
| [Plataforma de Integração](https://documenter.getpostman.com/view/12351215/UzJJucpF) (`servicos.ccee.org.br`, SOAP/XML) | back office do agente: ativos, parcelas, contratos ACL/ACR, medidas, DRI, **PLD** | certificado/credencial de agente | **não** |

Ambas são **dado do agente**, restrito à Alupar, não dado público de mercado.
Têm valor — a Plataforma de Integração cobre medição e contratos, que o
InfoMercado não cobre — mas dependem de credencial que a Alup ainda não pediu.
Ficam registradas como **escopo candidato**, fora da Onda 1, e a decisão de
entrar depende de A7.

O PLD aparece nas duas vias. A Onda 1 lê o da via pública: mesmo dado, sem
credencial e sem dependência.

### 4. A primeira entidade é o PLD horário por submercado

Dos 204 datasets, `pld_horario_submercado` entra primeiro porque é o preço que
o resto do lake cruza, e porque preenche a dimensão `submercado`, que já existe
pelo ONS. As demais entram por demanda dos domínios analíticos (A4), uma
entidade por vez, cada uma com os 7 componentes.

**A dimensão `agente_ccee` continua sem fonte nesta ADR.** Quem a preenche é
`lista_perfil` / `lista_agente_associado`, também públicos e alcançáveis pela
mesma via — é a próxima entidade natural, não um bloqueio.

## Consequências

- A pendência **A2 está encerrada**; a issue #52 fecha com esta ADR. As 32h da
  Onda 1 voltam a andar sem insumo da contratante.
- `src/core/http.py` ganha cabeçalho padrão, com teste. Nenhum conector existente
  muda de comportamento além de passar a se identificar.
- Nasce o conector `ccee_pld`, com os 7 componentes.
- O InfoMercado **sai** da tabela de fontes bloqueadas do `status.md` §5: ele
  era o caso de "documentação inalcançável", e não é mais.
- As duas APIs credenciadas ficam registradas aqui. Se a Alup quiser medição ou
  contratos da CCEE, é escopo novo, com credencial pedida em A7 — e ADR própria.
- O filtro é da CCEE e pode mudar. Se o 403 voltar com o cabeçalho, a
  investigação começa pelo que a origem passou a exigir, não pelo conector.
