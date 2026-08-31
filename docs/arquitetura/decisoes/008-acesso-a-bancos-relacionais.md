# ADR 008 — Acesso a bancos relacionais das fontes internas

**Status**: aceito · **Data**: 2026-08-29

## Contexto

A Onda 3 são 155h — a maior das cinco, 26,72% do contrato — e é inteiramente
composta por fontes que não falam HTTP: Oracle FMB, MySQL do Portal Alup, MySQL
RDS de Comercialização e RM/TOTVS.

Até aqui o framework só sabia falar HTTP e ler CSV. As cinco fontes entregues
(BCB, IBGE, ANEEL, ONS, Hubspot) passam todas por `src/core/http.py`. Nenhuma
linha do projeto jamais abriu conexão com um banco relacional.

O acesso depende de VPN e credencial read-only da Alup (dependência A7), que
ainda não chegaram. A cláusula 3ª prevê **taxa de ociosidade de 4h/dia (R$
256/h)** para atraso maior que 5 dias úteis nesse insumo — ou seja, é o único
item do contrato cujo atraso tem preço, e o pior cenário é o acesso chegar e a
Onda 3 começar do zero.

Escrever o caminho de banco **antes** do acesso é o trabalho de maior valor
disponível sem depender de terceiros: quando a credencial chegar, a tarefa é
apontar uma DSN e ajustar SQL, não descobrir como o framework fala com banco.

## Decisão

`src/core/banco.py` é o equivalente de `http.py` para fonte relacional. Expõe
`conectar(dsn)`, `criar_conexao(fonte)` e `consultar(conexao, sql, parametros)`.
Um conector da Onda 3 segue implementando apenas `extrair()` e `transformar()`.

### Drivers puro-Python

`oracledb` em modo *thin* e `pymysql`. Nenhum dos dois exige biblioteca nativa
do sistema — sem Oracle Instant Client, sem `libmysqlclient` na imagem. Isso
mantém o `Dockerfile` sem etapa de compilação e o build reproduzível.

Ambos ficam em `[project.optional-dependencies].bancos`, fora das dependências
base: conector de API pública não paga por driver de banco.

### DSN única no Secret Manager

Um secret por fonte, `alupdata-<fonte>-dsn`, com a conexão inteira em uma linha:

```
oracle://usuario:senha@host:1521/SERVICO
mysql://usuario:senha@host:3306/base
```

A alternativa — um secret por campo (host, porta, usuário, senha, base) — são
cinco objetos para rotacionar em vez de um, e cinco chances de o ambiente ficar
meio configurado. O parsing é `urllib.parse`, sem dependência nova.

Consequência que precisa estar explícita: **a DSN carrega a senha**. Nenhuma
mensagem de erro de `banco.py` pode ecoá-la. Por isso o erro de driver
desconhecido cita só o esquema, e há teste que falha se usuário ou senha
aparecerem na exceção (cláusula 8.5).

### Paginação no cursor, não `fetchall`

`consultar()` usa `fetchmany` em lotes de `banco_lote` (1000 por padrão). O
lote é também o `arraysize`, isto é, quantos round-trips a VPN paga.

### Nomes de coluna em minúsculas

Oracle devolve identificadores em maiúsculas; o resto do framework trabalha em
`snake_case`. A normalização acontece em um lugar só.

### Defesa de somente leitura

`consultar()` recusa comandos que não comecem por `SELECT` ou `WITH`, e
`abrir_conexao()` garante o fechamento da conexão. Essa validação reduz erro
acidental, mas não substitui a credencial read-only fornecida pela Alup.

## Limite conhecido

`Conector._ingerir` materializa o resultado de `extrair()` numa lista antes de
validar. `consultar()` pagina no cursor — o que protege o banco de origem e a
rede —, mas o processo ainda segura todas as linhas da janela em memória.

Para o FMB isso significa manter `max_dias_por_requisicao` curto. A correção
real é o runner carregar em lotes, o que muda a assinatura de `carregar_bronze`
e afeta os cinco conectores existentes: não se justifica antes de existir uma
medição de volume real do FMB.

## Consequências

- A Onda 3 começa no dia em que a VPN chega, em vez de começar do zero.
- Duas dependências novas, ambas puro-Python e opcionais.
- O que **não** foi feito: nenhuma fonte da Onda 3 tem os 7 componentes ainda.
  Isto é capacidade de framework, não entrega de fonte — a modelagem de cada
  tabela depende do schema real, que só se conhece com acesso (ver
  `docs/status.md` §5: escrever schema por adivinhação cria retrabalho com
  aparência de progresso).
- RM/TOTVS pode não ser banco e sim API ou exportação — pergunta C7 do
  Questionário de Gaps. Se for HTTP, usa `http.py` e não este caminho.
