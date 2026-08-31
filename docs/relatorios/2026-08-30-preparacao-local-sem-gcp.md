# Preparação local sem acesso ao GCP — 2026-08-30

## Objetivo

Reduzir o risco do primeiro deploy e avançar o que não depende do projeto GCP,
sem confundir verificação local com homologação contratual.

## Alterações realizadas

### Segurança e IAM

- A service account de ingestão mantém no projeto apenas
  `roles/bigquery.jobUser`.
- Escrita BigQuery foi limitada ao dataset Bronze.
- Leitura e criação de objetos foram limitadas ao bucket raw.
- `secretAccessor` passou do projeto para cada secret declarado.
- `run.invoker` passou do projeto para cada Cloud Run Job.
- Secrets vazios de DSN foram incluídos para as fontes relacionais previstas.
- Mensagens e stack traces passam por sanitização central antes de log ou
  persistência; erros Pydantic não incluem mais o valor bruto do campo.

### Confiabilidade da ingestão

- Falha ao registrar `bronze._execucoes` agora impede declarar sucesso completo.
- A exceção original da ingestão é preservada se o registro do erro também
  falhar.
- HubSpot habilita retry de POST somente no endpoint de consulta idempotente.
- O registry passou a carregar o catálogo inteiro mesmo quando um conector foi
  importado isoladamente antes da CLI.

### Replay do raw

- Adicionado `alupdata reprocessar-raw`.
- O leitor valida o layout `gs://`, descompacta JSONL gzip e rejeita conteúdo
  incompatível.
- O replay não chama `extrair()` e passa novamente por transformação, Pydantic
  e carga Bronze.
- `_execucoes` ganhou `modo` e `origem_ingestao_id` para preservar a linhagem.
- O bucket raw ganhou permissão de leitura para a identidade de ingestão.

### Bancos relacionais

- Consultas aceitam somente comandos iniciados por `SELECT` ou `WITH`.
- Adicionado contexto que garante o fechamento da conexão em sucesso ou erro.
- A credencial read-only na origem continua obrigatória; a validação textual é
  uma defesa adicional, não substituta.

### Deploy e custo

- O workflow `all` publica a imagem antes do Terraform.
- Terraform referencia a tag imutável do commit, não `latest`.
- As views são aplicadas após o `terraform apply`.
- Consultas fixas do Portal passaram a selecionar colunas explícitas.

## Evidências locais

- 274 testes coletados: **226 aprovados e 48 pulados**.
- Cobertura total: **92%**.
- Os pulos incluem a integração real do HubSpot e condições específicas dos
  testes parametrizados de SQL.
- SQL BigQuery analisado por `sqlglot` na suíte.
- Dry-run do deploy de views executável sem credencial.
- Terraform 1.15.8: `fmt -check`, `init -backend=false` e `validate` aprovados
  com provider Google 6.50.0.
- Gitleaks 8.28.0: 69 commits e aproximadamente 2,10 MB analisados, sem
  vazamentos encontrados.
- `pip-audit --strict`: nenhuma vulnerabilidade conhecida na resolução
  exportada do `uv.lock`.
- Actionlint 1.7.12: os três workflows foram aceitos sem diagnóstico.

Os portões finais devem ser repetidos após todas as alterações. Este relatório
não registra Docker ou GCP como aprovados localmente.

## Limitações e pendências

- Terraform e Gitleaks foram instalados e executados nesta estação. O lock do
  provider passou a ser versionado para manter a resolução reproduzível.
- Docker Desktop foi iniciado em segundo plano, mas não disponibilizou o daemon
  após 45 segundos; a imagem não foi reconstruída nesta rodada.
- Nenhum recurso foi criado ou alterado no GCP.
- Replay ainda precisa ser exercitado contra GCS e BigQuery reais.
- HubSpot continua sem token e sua integração real permanece pulada.
- CCEE, BBCE, TempoOK e fontes internas continuam bloqueadas pelos insumos já
  registrados em `docs/status.md`.
- O runner ainda materializa a janela inteira em memória. A carga em lotes foi
  mantida como evolução condicionada à medição real do FMB, conforme ADR 008.
- Não foram criados conectores incompletos das fontes internas: sem schema real,
  isso violaria a regra dos sete componentes e produziria contrato fictício.

## Critério para o primeiro deploy

1. Revisar `terraform plan`, principalmente IAM.
2. Publicar a imagem imutável.
3. Aplicar infraestrutura e SQL.
4. Executar BCB em janela curta.
5. Conferir raw, Bronze, Silver, Gold e `_execucoes`.
6. Reprocessar o raw criado e conferir `modo=REPLAY` e a deduplicação Silver.
7. Testar alertas, orçamento e Portal.
8. Guardar as evidências no pacote de homologação.

Até completar esses passos, o estado correto é **preparado localmente para
implantação e validação**, não homologado.
