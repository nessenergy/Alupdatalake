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

## Autenticação

**Não há login escrito no aplicativo, e isso é deliberado.** No Cloud Run o
acesso é restrito por IAM/IAP: quem não está autorizado não chega na aplicação.
A identidade chega no cabeçalho `X-Goog-Authenticated-User-Email`, e o Portal só
a exibe.

Consequências operacionais:

- Rodando local, sem o cabeçalho, a tela mostra "não autenticado (execução
  local)". Isso é o esperado — não é bug.
- **Nunca publique o serviço com `--allow-unauthenticated`.** É o único jeito
  de essa tela vazar para a internet, já que não existe outra barreira.
- Restringir o acesso ao domínio da Alup é configuração de IAM, não de código.

## Publicação (quando houver Artifact Registry)

O Portal roda na **mesma imagem** da CLI — um artefato só para operar. O
serviço troca o entrypoint por `gunicorn`; não há código de servidor no
repositório para manter:

```bash
gcloud run deploy alupdata-portal \
  --image <registry>/alupdata:<tag> \
  --command gunicorn \
  --args "--bind=:8080,--workers=2,src.portal.app:app" \
  --no-allow-unauthenticated \
  --set-env-vars PORTAL_PROVEDOR=bigquery,GCP_PROJECT_ID=<projeto>
```

A sonda de saúde é `GET /saude`, que responde sem tocar no BigQuery — sonda que
consulta banco derruba o serviço junto com o banco.
