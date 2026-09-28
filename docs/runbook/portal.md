# Portal MVP — como rodar e como publicar

Escopo em [`../arquitetura/decisoes/005-escopo-do-portal-mvp.md`](../arquitetura/decisoes/005-escopo-do-portal-mvp.md).
Leia a ADR antes de aceitar qualquer pedido de mudança na tela.

## Local

```bash
uv run flask --app src.portal.app run
# http://127.0.0.1:5000
```

Sem configuração, o Portal usa o **provedor simulado**: números de exemplo,
rotulados na própria tela como "dados de exemplo". Nenhum número vem do
DataLake enquanto o ambiente GCP não existir (pendência A3).

## Ligar contra o BigQuery

Quando A3 chegar:

```bash
export PORTAL_PROVEDOR=bigquery
export GCP_PROJECT_ID=<projeto>
uv run flask --app src.portal.app run
```

Variáveis (todas com padrão em `src/core/config.py`):

| Variável | Padrão | O quê |
|---|---|---|
| `PORTAL_PROVEDOR` | `simulado` | `simulado` ou `bigquery` |
| `PORTAL_VIEW` | `cambio_mensal` | view Gold exibida |
| `PORTAL_LIMITE_LINHAS` | `200` | teto de linhas por request |

## Rotas

| Rota | O quê |
|---|---|
| `/` | uma view Gold de negócio (item 0.15 do plano — [ADR 005](../arquitetura/decisoes/005-escopo-do-portal-mvp.md)) |
| `/lake` | painel de saúde da ingestão ([ADR 006](../arquitetura/decisoes/006-painel-de-saude.md)) |
| `/saude` | sonda do Cloud Run — responde sem tocar no BigQuery |

## Autenticação

**Não há login escrito no aplicativo, e isso é deliberado.** No Cloud Run o
acesso é restrito pelo IAP, ligado no próprio serviço: quem não está autorizado
não chega na aplicação. A identidade chega no cabeçalho
`X-Goog-Authenticated-User-Email`, e o Portal só a exibe. Em modo `bigquery`,
requisição sem o cabeçalho recebe 403.

Consequências operacionais:

- Rodando local, sem o cabeçalho, a tela mostra "não autenticado (execução
  local)". Isso é o esperado — não é bug.
- **Nunca libere o serviço para `allUsers` nem desligue o IAP.** O teste de
  infraestrutura recusa `allUsers` e `allAuthenticatedUsers` em `infra/`.
- Quem acessa é a variável `portal_acesso` do `.tfvars` do ambiente: só
  `group:<e-mail>` ou `domain:<domínio>` da Alup; `user:` é recusado na
  validação. Vazia, que é o padrão, o serviço sobe sem ninguém autorizado.

## Liberar o dado real para a Alup

Pedido em aberto: issue [#261](https://github.com/nessenergy/Alupdatalake/issues/261).
Falta só o e-mail do grupo Google da Alup — nada do lado da ness. bloqueia.
Quando ele chegar:

1. Em `infra/environments/hml.tfvars`, descomente as duas linhas
   `grupo_consumidores` e `portal_acesso`, e troque
   `<grupo-consumidores>@<dominio-da-alup>` (as duas ocorrências) pelo e-mail
   exato. Repita em `dev.tfvars` se a Alup também pedir acesso ao ambiente
   de desenvolvimento — não é o padrão.
2. PR, merge, e o deploy normal (`Deploy GCP`, `hml`, `infra` ou `all`)
   aplica. Não precisa de passo manual no console.
3. `grupo_consumidores` dá `roles/bigquery.dataViewer` na camada Gold e
   `roles/bigquery.jobUser` no projeto — quem estiver no grupo roda
   `SELECT * FROM gold.<tabela>` direto no BigQuery, para as 26 tabelas de
   negócio (materializadas, ADR 012). As três Gold operacionais
   (`saude_ingestao`, `volumetria_lake`, `custo_consultas`) não entram: são
   view sobre `bronze._execucoes`, métrica de operação da ness., e exigiriam
   `grupo_operacao` — não conceder sem pedido explícito.
4. `portal_acesso` libera o mesmo grupo no IAP do Portal, para a demonstração
   com login da Alup na reunião de aceite (item 0.15).
5. Avisar quem pediu (Leonardo, Taina) que o acesso está de pé, com o nome
   das 26 tabelas Gold como ponto de partida — `docs/dicionario-dados/` tem
   o campo a campo e a frequência de cada uma.

## Publicação

O serviço, o IAP e a SA `alupdata-portal` estão em `infra/modules/portal` e
sobem com o workflow **Deploy GCP** (`infra` ou `all`), junto com o
agendamento, sempre que houver imagem publicada. Não publique com
`gcloud run deploy`: recurso fora de `infra/` não existe (regra 5), e o
próximo `apply` o sobrescreve.

O Portal roda na **mesma imagem** da CLI — um artefato só para operar. O
serviço troca o entrypoint por `gunicorn`; não há código de servidor no
repositório para manter. A URL sai em `terraform output url_portal`.

A SA `alupdata-portal` só lê: `bronze`, `silver` e `gold`, mais o metadado de
jobs e de armazenamento que `gold.custo_consultas` usa. As três camadas, e não
só a Gold, porque as views da Gold não são views autorizadas e `/lake` lê
`bronze._execucoes`.

Se um serviço `alupdata-portal` já tiver sido criado à mão com `gcloud`,
importe-o antes do primeiro `apply` (`terraform import`) ou apague-o: senão o
`apply` falha com o nome já em uso.

A sonda de saúde é `GET /saude`, que responde sem tocar no BigQuery — sonda que
consulta banco derruba o serviço junto com o banco.
