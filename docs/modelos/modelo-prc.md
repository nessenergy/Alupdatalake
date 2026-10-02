# Modelo de planilha — PRC (Preço de Referência Comparável)

Arquivo para preencher: [`modelo-prc.csv`](modelo-prc.csv) (CSV com `;`, UTF-8; o Excel em português abre e
salva assim). O código que o lê é `src/conectores/planilha_prc.py`.

O PRC é divulgado por cada comercializadora varejista no próprio site (Procedimentos de Comercialização da
CCEE, submódulo 1.6, e REN ANEEL 1.011/22). Não há base pública única nem API, e o layout muda de uma
comercializadora para outra. Por isso a entrada é esta planilha, preenchida a cada atualização.

## Colunas

| Coluna | Obrigatória | Como preencher |
|---|---|---|
| Comercializadora | sim | nome de quem publica o PRC |
| Data de atualização | sim | `dd/mm/aaaa`, a data que consta na tabela publicada |
| Submercado | sim | `SE`, `S`, `NE` ou `N`, **uma sigla por linha** (a tabela "SE/CO e Sul" vira duas linhas) |
| Tipo de energia | sim | `convencional` ou `incentivada_50` (desconto de 50% na TUSD) |
| Ano | um dos dois | ano da linha (por exemplo, 2027), quando a tabela é por ano |
| Prazo (meses) | um dos dois | 12, 36, 60…, quando a tabela é por prazo. **Ano ou prazo, nunca os dois** |
| Preço (R$/MWh) | sim | número com vírgula (`216,00`), entre 1 e 2.000 |
| Indexador | não | por exemplo `IPCA` |
| Premissas | não | texto livre: tributos, flexibilidade, modulação, prazo de pagamento |

## Regras de leitura

- Arquivo com coluna a mais ou a menos é **rejeitado inteiro**, com a lista do que falta e do que sobra.
- A linha de exemplo do modelo (`EXEMPLO — apague esta linha`) é recusada se for enviada.
- Linha inválida é descartada e contada em `linhas_invalidas`; nenhuma some em silêncio.

## O que ainda não existe

O canal que leva o arquivo ao job (bucket de entrada) é da Onda 4, e por isso a classe não está registrada e
não há Bronze, Silver, Gold nem agendamento. Este modelo fixa a forma da entrada; os demais componentes
vêm quando a Alup confirmar de qual(is) comercializadora(s) é o PRC e o canal de envio.
