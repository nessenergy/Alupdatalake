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
| `/` | abre em Indicadores (redireciona para `/indicadores`, levando `?telao=1` junto) |
| `/dado` | uma view Gold de negócio (item 0.15 do plano — [ADR 005](../arquitetura/decisoes/005-escopo-do-portal-mvp.md)) |
| `/indicadores` | razões técnicas do setor, um cartão por recorte (ADR 012) |
| `/lake` | painel de saúde da ingestão ([ADR 006](../arquitetura/decisoes/006-painel-de-saude.md), [ADR 025](../arquitetura/decisoes/025-portal-redesenhado-e-modo-telao.md)) |
| `/custo` | custo de nuvem, em três leituras |
| `/saude` | sonda do Cloud Run — responde sem tocar no BigQuery |

### Cache das leituras

O Portal guarda cada leitura do BigQuery por 300 s (variável `PORTAL_CACHE_SEGUNDOS`, `0`
desliga), para o modo telão não consultar a cada 20 s. O carimbo "consultado às" mostra a
hora da leitura. Depois de uma carga, o dado novo aparece em até cinco minutos; reiniciar
a revisão do Cloud Run zera o cache.

### Modo telão

Para a reunião: abra `<url do Portal>/?telao=1` (ou `/indicadores?telao=1`, `/lake?telao=1`,
`/custo?telao=1`) em tela cheia (F11). As telas passam sozinhas a cada 20 s —
Indicadores, Saúde do lake, Custo — e voltam ao começo. O link "sair do modo telão"
no canto devolve a tela normal. Não há JavaScript: cada página manda o navegador
para a próxima. A navegação some no telão, e o modo só liga com `?telao=1`.

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

## Acesso da ness. (dev e hml)

**Quem entrega confere o que entregou.** O grupo `operacao-datalake@ness.com.br`
está em `portal_acesso` de `dev` e `hml`. Em `prod`, só a Alup.

A concessão sozinha não basta: o IAP com o cliente OAuth gerenciado pelo Google
só aceita contas da organização dona do projeto (a Alupar), e recusa
`@ness.com.br` mesmo concedida (visto no log de auditoria, #242). A saída é a
mesma do painel vivo: **cliente OAuth próprio, público "Externo"**, em cada
projeto (`alupar-dev-alupdata` e `alupar-hm-alupdata`). O cliente OAuth
externo não se declara em Terraform — é passo de console, registrado aqui.

No console do Google Cloud, no projeto do ambiente:

1. **Google Auth Platform → Branding**: nome do app e e-mails de suporte e de
   contato do desenvolvedor. Sem eles o público não publica.
2. **Google Auth Platform → Público → Externo** → **Publicar app** (status
   "Em produção"). Em `hml` isso é obrigatório: no status "Teste" só entram
   usuários de teste cadastrados um a um, e a Alup fica de fora. O login só
   pede e-mail e perfil, que não exigem verificação do Google.
3. **Clientes → Criar cliente → Aplicativo da Web**, criado sem URI (o ID só
   existe depois de criar). Abra o cliente, copie o ID e ponha em
   *URIs de redirecionamento autorizados*:
   `https://iap.googleapis.com/v1/oauth/clientIds/<ID>:handleRedirect`.
4. **Segurança → Identity-Aware Proxy** → serviço `alupdata-portal` →
   **Configurações** → *Cliente OAuth personalizado*: cole o ID e o segredo.
   O segredo só é digitado no console; nunca em chat, issue ou repositório.
   **Se a tela do IAP não listar o serviço** (ela exige `run.services.update`,
   que a ness. não tem em `hml`), faça pelo Cloud Shell, que só exige
   `iap.settingsAdmin`. O comando espera o segredo sem mostrá-lo:

   ```bash
   read -rs S && umask 077 && printf 'accessSettings:\n  oauthSettings:\n    clientId: <ID>\n    clientSecret: %s\n' "$S" > /tmp/iap.yaml && gcloud iap settings set /tmp/iap.yaml --project=<projeto> --resource-type=cloud-run --service=alupdata-portal --region=us-central1; rm -f /tmp/iap.yaml; unset S
   ```

   Não use "Corrigir acesso" nessa tela: ele concede papel fora do `infra/`.
   Em `hml`, aplicado assim em 29/09.
5. Teste em aba anônima com uma conta de cada lado (ness. e, em `hml`, Alup).
   Para desfazer, volte o passo 4 ao cliente gerenciado pelo Google.

Quem entra continua definido por `portal_acesso`: o público "Externo" só
decide quem consegue fazer login, não quem passa pelo IAP.

Quem executa precisa de `roles/oauthconfig.editor`, `roles/iap.settingsAdmin` e `roles/iap.admin` no
projeto. Se faltar, é pedido à Alup, como os papéis de bootstrap (ADR 015).
Enquanto isso, a conferência é local, com a conta da pessoa e o dado real:

```powershell
gcloud auth application-default login --account=<voce>@ness.com.br
$env:PORTAL_PROVEDOR = "bigquery"; $env:GCP_PROJECT_ID = "alupar-dev-alupdata"
uv run flask --app src.portal.app run   # http://127.0.0.1:5000/lake
```

## Liberar o dado real para a Alup

Pedido em aberto: issue [#261](https://github.com/nessenergy/Alupdatalake/issues/261).
Falta só o e-mail do grupo Google da Alup — nada do lado da ness. bloqueia.
Quando ele chegar:

1. Em `infra/environments/hml.tfvars`, descomente `grupo_consumidores` com o
   e-mail exato e **acrescente** `"group:<e-mail>"` à lista `portal_acesso`,
   que já tem o grupo de operação da ness. (não troque: os dois ficam). Repita em `dev.tfvars` se a Alup também pedir acesso ao ambiente
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
