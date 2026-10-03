# ADR 028 — Acesso ao CPTEC: bloqueio na origem, fonte fora da Onda 1 até haver resposta do INPE

**Status**: proposto · **Data**: 2026-10-03 · **Complementa** a
[ADR 018](018-vias-de-acesso-a-ccee.md) (que resolveu um 403 por `User-Agent`)

## Contexto

A cláusula 4ª, Onda 1, prevê "CPTEC — previsão do tempo e climática de 7 dias",
"APIs públicas sem dependência de credenciais da Alup". Em 02/10 as primeiras
tentativas de leitura responderam 403. Esta ADR investiga a causa e classifica
a fonte em uma de três saídas: (A) endpoint público acessível, (B) acesso
condicionado a cadastro, token ou liberação de IP, (C) endpoint descontinuado
sem substituto público.

## O que foi verificado (03/10/2026, TLS ligado)

Todas as requisições partiram da máquina de desenvolvimento, com
`src.core.http.criar_sessao()` (cabeçalho de identificação do projeto), salvo
onde indicado.

| Requisição | Resultado |
|---|---|
| `http://servicos.cptec.inpe.br/XML/...` | 301 para `https://` |
| `https://servicos.cptec.inpe.br/XML/listaCidades?city=sao` | **403 Forbidden** (página HTML padrão do Apache) |
| `https://servicos.cptec.inpe.br/` (raiz do host) | **403** (curl) |
| `https://servicos.cptec.inpe.br/XML/cidade/244/previsao.xml`, `User-Agent: curl/8` | **403** |
| `https://servicos.cptec.inpe.br/XML/listaCidades?city=sao`, sem `User-Agent` | **403** |
| `http://servicos.cptec.inpe.br/XML/` buscada pela ferramenta de leitura web (origem de rede distinta da máquina de desenvolvimento) | **403** |
| `https://api.cptec.inpe.br/` | falha de conexão: o domínio **não existe no DNS** (`NXDOMAIN` no resolvedor 8.8.8.8) |
| `https://dados.cptec.inpe.br/` | domínio **não existe no DNS** |
| `https://www.cptec.inpe.br/` | 200. A página inicial **ainda anuncia** o Webservice em `http://servicos.cptec.inpe.br/XML/` e remete a dados abertos em `gov.br/inpe/.../dados-abertos` |
| `https://www.cptec.inpe.br/webservice/` | 404 |
| `https://clima.cptec.inpe.br/` | 200 (portal de previsão climática, sem documentação de API na página consultada) |
| página de dados abertos do INPE (`gov.br/inpe/.../dados-abertos`) | 200, **sem** menção a API de previsão, endpoint, cadastro ou token |
| `https://brasilapi.com.br/api/cptec/v1/cidade/sao` | 500, `CITY_INTERNAL` ("Erro ao buscar informações sobre cidade") |
| `https://brasilapi.com.br/api/cptec/v1/clima/previsao/244/3` | 500, `CITY_WEATHER_PREDICTIONS_ERROR` |

## O que se conclui, e o que não

**Fato:** o host `servicos.cptec.inpe.br` recusa com 403 toda requisição, até a
raiz, independente de `User-Agent`, e recusou também de uma segunda origem de
rede. Não é o filtro de `User-Agent` da CCEE (ADR 018). O 500 do proxy da
BrasilAPI, cujo erro nomeia a falha de busca de cidades e de previsões, é
coerente com o proxy também não alcançar a origem; é inferência, não está
provado.

**Fato:** o `api.cptec.inpe.br` que se imaginava como API nova **não existe no
DNS**. Não há segunda via pública documentada.

**Fato:** nenhuma página oficial consultada descreve exigência de cadastro,
token ou liberação de IP para o webservice. Quem recebe o 403 não recebe
instrução.

**Hipótese (não verificada):** bloqueio por faixa de IP ou geografia do
cliente, ou webservice fora do ar com o 403 como sintoma. A segunda origem de
rede reforça "bloqueio na origem" contra "IP da máquina de desenvolvimento",
mas é uma única amostra de outra rede.

**Não verificado:** o comportamento a partir de um IP do Google Cloud. Seria
necessário um job descartável **declarado em `infra/`** (recurso fora de
`infra/` não existe) que fizesse um `GET` do endereço acima a partir do Cloud
Run de `dev` e imprimisse apenas o status. Não foi criado: esta tarefa é só de
investigação. Se o job devolver 200, o bloqueio é de IP de origem e a fonte
passa a (A); se devolver 403, confirma-se (B) ou (C).

## Decisão

**Classificação: (B), provisória.** Não é (A): não há endpoint que se consiga ler.
Não é (C) comprovado: o próprio site do CPTEC ainda anuncia o webservice, e não
há como afirmar descontinuação sem resposta do INPE. Por isso a fonte **sai da
execução da Onda 1** até haver resposta, e o registro, não um conector, é a
entrega desta tarefa.

1. **Nenhum conector, tabela, view ou agendamento é criado para o CPTEC agora.**
   Conector sem acesso entregaria 0 de 7 componentes funcionando, e a regra do
   projeto é falhar alto, nunca carregar zero linhas como sucesso.
2. **Pedido de esclarecimento ao INPE**, pelo canal da Alup (texto abaixo).
3. **Teste a partir do GCP** (job descartável em `infra/`, descrito acima), a
   executar apenas se o INPE responder que o acesso depende de origem, ou se a
   Alup quiser eliminar a hipótese do IP de desenvolvimento.
4. **Se o INPE confirmar descontinuação ou restrição sem previsão (saída C):**
   propor à Alup a troca do provedor. Um candidato verificado como acessível
   hoje, sem credencial, é a API Open-Meteo
   (`GET https://api.open-meteo.com/v1/forecast?latitude=-23.5&longitude=-46.6&daily=precipitation_sum&forecast_days=7`
   respondeu 200 em 03/10 com a precipitação diária de 7 dias). **Os termos de
   uso e a licença para o uso comercial da Alup não foram verificados** e
   precisam de aceite antes de qualquer conector. A troca da fonte altera o
   escopo da cláusula 4ª e é decisão da Alup, não do projeto.
5. Se o conector vier a existir, em (A) ou na fonte substituta: ele levanta
   `LayoutInesperadoError` em 403 ou corpo vazio e **nunca** devolve lista
   vazia. A fixture será a resposta real, curta.

### Texto do pedido de aceite (não enviado)

> Assunto: Webservice de previsão do CPTEC — acesso retornando 403
>
> O coletor da Alupar (identificado em `User-Agent`) consome dados públicos para
> o data lake corporativo. O webservice anunciado em
> https://www.cptec.inpe.br/ (`servicos.cptec.inpe.br/XML/`) responde HTTP 403
> a qualquer requisição, inclusive à raiz do host, a partir de duas redes
> distintas, desde 02/10/2026. Também não localizamos o domínio
> `api.cptec.inpe.br`. Pedimos: (1) o serviço está ativo, em manutenção ou
> descontinuado? (2) o acesso exige cadastro, chave ou liberação de IP, e como
> solicitar? (3) existe endereço substituto para a previsão de 7 dias e a
> previsão climática? Podemos informar o IP de saída do coletor, se for o caso.
> Contato: comercializacao@alupar.com.br

## Consequências

- A cláusula 4ª, Onda 1, fica com o CPTEC **pendente de terceiro** (INPE), não
  de credencial da Alup; registrar o fato e a data em `docs/status.md`, sem
  decidir efeito contratual.
- A decisão final (esperar o INPE, trocar de provedor ou excluir o item) é da
  Alup, com esta evidência.
- Reabrir esta ADR quando o INPE responder ou quando o teste do GCP rodar.
