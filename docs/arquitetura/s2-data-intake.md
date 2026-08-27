# S2 Data Intake — motor de ingestão de planilhas

Tarefa 4.1 do plano (Onda 4, 30h). Este documento é o desenho; a implementação
vive em `src/core/planilha.py` e `src/conectores/planilha.py`.

## Por que este componente é diferente dos outros

Todas as outras fontes do AlupData são máquinas falando com máquinas: uma API
devolve o que o contrato dela promete, e quando muda, muda para todo mundo de
uma vez. A planilha é a única fonte **editada por uma pessoa**. Ela chega com
coluna renomeada, linha em branco no meio, número com vírgula, aba extra,
cabeçalho na terceira linha porque alguém pôs um título em cima.

Disso vem a única regra que importa aqui:

> Arquivo fora do template é **rejeitado inteiro**, com erro que diz qual
> coluna falta e qual sobra. Nunca carregado parcialmente.

Planilha "quase certa" carregada em silêncio é o modo de falha clássico deste
tipo de componente: ninguém percebe até o número aparecer errado num relatório,
semanas depois, e aí não se sabe mais quais linhas vieram de onde.

## Onde ele encaixa

O motor **não é um conector novo** — é uma base de conector. O runner de
`src/core/conector.py` continua fazendo raw no GCS, validação Pydantic, colunas
técnicas, carga no Bronze e log de execução. O que o motor acrescenta é um
`extrair()` que lê arquivo em vez de falar HTTP.

```
planilha (GCS ou disco)
  → ler_tabela()        csv/xlsx → dicionários por linha
  → validar_cabecalho() rejeita arquivo fora do template, antes de qualquer linha
  → transformar()       renomeia coluna, converte número BR
  → runner existente    valida com Pydantic, grava, carrega, registra
```

## O template

Template é **código**, não arquivo de configuração. Um `TemplatePlanilha` é uma
dataclass declarativa; o schema Pydantic da fonte continua sendo quem define
tipo e regra de negócio.

```python
TemplatePlanilha(
    colunas={"Data": "data_referencia", "Valor (R$)": "valor"},
    delimitador=";",
    encoding="utf-8-sig",
    linha_cabecalho=1,
    decimal_brasileiro=True,
)
```

Decisão: **não usar YAML**. Um template em YAML precisaria de parser,
dependência nova, e um segundo lugar onde validar o próprio template. Em
Python ele é conferido pelo mesmo lint e pelos mesmos testes do resto do
repositório, e o autor de um conector novo não aprende uma segunda linguagem.

## Escopo desta entrega

O que **entra agora** (não depende de ninguém):

1. `ler_tabela()` — CSV e XLSX, mesma saída (dicionários por linha).
2. `validar_cabecalho()` — compara o cabeçalho encontrado com o template e
   levanta erro nomeando faltantes e excedentes.
3. `ConectorPlanilha` — base que junta as duas coisas ao runner existente.
4. Conversão de número brasileiro, extraída do conector ANEEL para uso comum.
5. Testes: arquivo certo, coluna faltando, coluna a mais, linha em branco,
   número BR, XLSX, cabeçalho fora da primeira linha, arquivo vazio.

O que **fica para depois** (depende da Alup):

- Os templates concretos de cada planilha — dependem do Questionário de Gaps
  (pendência A4) e das planilhas reais.
- Bronze/Silver/Gold de cada planilha: são por template, não do motor.

Isto é deliberado: o motor é a parte que não depende de resposta nenhuma, e
adiantá-lo agora tira 30h do caminho crítico da Onda 4.

## Decisões de leitura

| Assunto | Decisão | Por quê |
|---|---|---|
| Formato | CSV e XLSX | contrato, cláusula 2ª |
| XLSX | `openpyxl` em modo `read_only` | única dependência nova; planilha grande não cabe na memória de outro jeito |
| Delimitador | declarado no template, padrão `;` | Excel brasileiro exporta com `;`; adivinhar delimitador erra em arquivo de uma coluna só |
| Encoding | declarado, padrão `utf-8-sig` | Excel escreve BOM; `utf-8-sig` lê com e sem |
| Linha em branco | ignorada | linha vazia no fim é resíduo de edição, não dado |
| Célula vazia | `None`, nunca `""` nem `0` | ausência não é zero — mesma regra do `amount` do Hubspot |
| Número BR | `1.400,00` → `Decimal("1400.00")` | vírgula decimal é o padrão de quem edita a planilha |
| Aba do XLSX | a primeira, salvo declaração | arquivo com várias abas é ambíguo; se precisar de outra, declare |

## Contrato de erro

`TemplateInvalidoError` é levantado antes de qualquer linha ser lida, e a mensagem
diz as duas coisas que a pessoa precisa para consertar o arquivo:

```
planilha fora do template: faltam ['Valor (R$)']; sobram ['Valor R$', 'Obs']
```

Linha individual inválida continua no fluxo do runner: descartada, logada e
contada em `linhas_invalidas` — o arquivo inteiro não cai por causa de uma
linha, mas nenhuma linha some em silêncio.
