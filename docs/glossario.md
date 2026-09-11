# Glossário

Para quem chega ao projeto sem vir do setor elétrico. As definições aqui são
**operacionais** — o suficiente para ler o código e as views sem travar. Para
definição regulatória precisa, a fonte é a ANEEL, a CCEE ou o ONS.

---

## Instituições

| Termo | O que é |
|---|---|
| **ANEEL** | Agência Nacional de Energia Elétrica. Regula o setor; mantém o cadastro de empreendimentos de geração (SIGA) e concede as outorgas. |
| **ONS** | Operador Nacional do Sistema Elétrico. Opera o SIN em tempo real; publica carga, geração e restrições. |
| **CCEE** | Câmara de Comercialização de Energia Elétrica. Contabiliza e liquida a energia comercializada; calcula o PLD; mantém o registro dos agentes. |
| **Agente CCEE** | Pessoa jurídica registrada na CCEE — gerador, comercializador, distribuidor ou consumidor livre. Cada coligada da Alup é um agente. |

## Sistema e mercado

| Termo | O que é |
|---|---|
| **SIN** | Sistema Interligado Nacional — a rede que conecta quase toda a geração e o consumo do país. |
| **Submercado** | Subdivisão do SIN para formação de preço: **SE/CO** (Sudeste/Centro-Oeste), **S** (Sul), **NE** (Nordeste), **N** (Norte). Existem porque a transmissão entre regiões tem limite: quando ele aperta, o preço descola entre submercados. No projeto é a dimensão comum `submercado`, com as siglas `SE`, `S`, `NE`, `N`. |
| **Carga de energia** | O consumo verificado, por submercado e período. É o que o conector ONS/carga ingere. |
| **PLD** | Preço de Liquidação das Diferenças. O preço da energia no mercado de curto prazo, por submercado e período, calculado pela CCEE. É a referência de quanto vale a energia que sobra ou falta em relação ao contratado. |
| **CMO** | Custo Marginal de Operação — quanto custa produzir o próximo MWh. Calculado pelo ONS; é a base do PLD. |
| **Mercado de curto prazo** | Onde se liquida a diferença entre o que foi contratado e o que foi de fato gerado ou consumido, ao PLD. |

## Geração

| Termo | O que é |
|---|---|
| **CEG** | Código Único de Empreendimento de Geração. Identificador da usina no cadastro da ANEEL — no projeto, a dimensão comum `codigo_usina`. |
| **Outorga** | A autorização ou concessão da ANEEL para gerar energia. **Potência outorgada** é o que foi autorizado; **potência fiscalizada** é o que a ANEEL verificou instalado. |
| **Garantia física** | Quanto de energia uma usina pode comercializar em contrato de longo prazo — não é a mesma coisa que sua potência instalada, e é o número que limita a venda. |
| **Fase da usina** | Onde o empreendimento está: `Operação`, `Construção`, `Construção não iniciada`. Diferencia parque existente de expansão. |
| **Tipos** | **UHE** hidrelétrica · **PCH** pequena central hidrelétrica · **CGH** central geradora hidrelétrica · **EOL** eólica · **UFV** solar fotovoltaica · **UTE** térmica. |

## Unidades

| Termo | O que é |
|---|---|
| **MW** | Potência instantânea. |
| **MWh** | Energia — potência × tempo. |
| **MWmed** | MW médio: a energia de um período dividida pelo tempo dele. 1 MWmed ao longo de um mês de 30 dias equivale a 720 MWh. O ONS publica carga em MWmed, e é a unidade das views de carga. |
| **kW** | Mil watts. O cadastro da ANEEL publica potência em kW; a Gold converte para MW dividindo por 1.000. |

---

## Do projeto

| Termo | O que é |
|---|---|
| **Medallion** | A arquitetura em três camadas: **Bronze** (dado bruto, fiel à origem), **Silver** (higienizado, tipado, deduplicado) e **Gold** (regra de negócio e KPI). |
| **Dimensões comuns** | As cinco colunas que toda view Silver expõe para permitir cruzar fontes: `data_referencia`, `submercado`, `codigo_usina`, `agente_ccee`, `periodo_apuracao`. Quando uma fonte não tem uma delas, a coluna vem `NULL` **com justificativa no dicionário** — nunca omitida. |
| **Janela** | O intervalo de datas de uma ingestão. Todo conector recebe uma; nenhum decide "hoje" sozinho. Reprocessar é passar outra janela. |
| **`_ingestao_id`** | Identificador de uma execução de ingestão. Aparece em toda linha do Bronze e em `bronze._execucoes`; é como se rastreia um lote. |
| **Append-only** | O Bronze só recebe inserção. Reprocessar insere de novo, e a Silver resolve com `QUALIFY ROW_NUMBER()`. Preserva o que a fonte devolveu em cada execução. |
| **dry-run** | Modo em que o conector extrai e valida sem gravar em GCS ou BigQuery. É como se testa contra a API real sem efeito colateral. |
| **Os 7 componentes** | O que toda fonte entrega (cláusula 2ª): conector, tabela Bronze, view Silver, view Gold, testes, agendamento e documentação com linhagem. |
| **Onda** | Bloco de entrega do contrato (0 a 4). Cada onda homologada é um marco de faturamento e abre 30 dias de garantia. |
| **Homologação** | O aceite formal de uma onda pela Alup. Dispara a medição e o pagamento. |
| **S2 Data Intake** | O motor de ingestão de planilhas (CSV/XLSX) previsto para a Onda 4. |
| **SSDLC** | Ciclo de desenvolvimento seguro — no projeto, os portões de Bandit, pip-audit, Gitleaks e Secret Manager (cláusula 8ª). |

> **Cuidado com "MCP".** No setor elétrico é *mercado de curto prazo*; em
> ferramental de agente é *Model Context Protocol*. O repositório usa a sigla
> por extenso nos dois casos, justamente para não confundir.
