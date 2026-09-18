# Plano de correção dos achados técnicos

**Objetivo:** corrigir quatro achados da avaliação de 18/09 com evidências locais e de CI, durante a espera pela disponibilização do ambiente pela Alup.

**Arquitetura:** manter Medallion, runner compartilhado, formato JSONL gzip e um raw por execução. A ingestão real conclui o raw antes de consumir esse objeto em lotes para o Bronze; o replay reutiliza a mesma leitura em fluxo. A Gold explicita dependências de qualidade, e o deploy deixa de depender de Composer ou de `latest`.

**Tecnologias:** Python 3.12, pytest, SDK de Cloud Storage existente, Dataform 3.0.69, Terraform e GitHub Actions. Nenhuma dependência de runtime nova.

**Base de requisitos:** avaliação da `main` em `45aa239`, solicitação de correção de 18/09/2026, `AGENTS.md` e ADRs 003, 012, 015 e 017. As decisões e critérios abaixo constituem a especificação deste reparo; não há especificação separada.

**Execução:** tarefas com teste de regressão antes da implementação, revisão e commit por entrega. Três entregas independentes: qualidade da Gold; raw e replay (tarefas 2 e 3 juntas); deploy. Podem formar três PRs. Este documento não autoriza provisionamento nem representa homologação.

## Restrições globais

- A entrega do ambiente é dependência externa da Alup. Não atribuir essa espera à equipe de desenvolvimento, nem condicionar os reparos locais à liberação do GCP.
- Não executar `terraform apply`, publicar imagem, disparar workflow de deploy, acessar dados reais ou alterar o Project como parte da execução deste plano.
- Não alterar 580h, cinco ondas, horas apontadas, aceites ou datas externas. Essas pendências não fazem parte dos quatro reparos.
- Bronze append-only; deduplicação na Silver; janelas explícitas; credenciais exclusivamente no Secret Manager; recursos declarados em `infra/`.
- Preservar objetos raw antigos, layout das URIs, CLI e identificação da ingestão de origem no replay. Não introduzir manifesto, shards ou novo serviço.
- Dry-run continua sem GCS/BigQuery: extrai e valida em lotes. Não apresentá-lo como medida de desempenho da ingestão real.
- Preservar `.claude/settings.json` e demais alterações locais alheias. Executar em branch de assunto, preferencialmente em worktree isolada; não implementar diretamente em `main`.
- Código novo em inglês; documentação, comentários e commits em português. Cumprir a regra 6 de `AGENTS.md` nos artefatos e publicações.
- Ler as instruções locais de GCP e segurança antes de implementar. Nos trechos legados de Composer, aplicar a ADR 017 e corrigir a orientação junto com o deploy.

## Mapa de arquivos

| Frente | Arquivos e responsabilidade |
|---|---|
| Gold | `definitions/gold/*.sqlx`: dependências das tabelas de negócio; `scripts/novo_conector.py`: mesmo padrão para novas fontes |
| Testes Gold | `tests/unit/test_sql.py`, `tests/unit/test_novo_conector.py`: regressão da configuração; grafo compilado: comprovação das dependências |
| Leitura raw | `src/core/storage.py`: leitura progressiva, limites por registro, fechamento e integridade gzip; `tests/unit/core/test_storage.py`: simulação do GCS |
| Runner/replay | `src/core/conector.py`: ordenação e carga em lotes; `tests/unit/core/test_conector_lote.py`, `test_replay.py`, `test_linhagem.py`: comportamento e compatibilidade |
| Deploy | `.github/workflows/deploy.yml`: remover Composer e exigir referência imutável para infra; `infra/variables.tf`: rejeitar imagem mutável quando configurada |
| Documentação | `docs/runbook/deploy.md`, `docs/runbook/primeiro-deploy.md`, `.claude/skills/gcp-alupdata/SKILL.md`: procedimento vigente; `docs/status.md`: distinguir reparo validado localmente de operação pendente |

## Tarefa 1 — Fazer a Gold depender das validações da Silver

**Interfaces:** preservar nomes, schemas e SQL de negócio. Produzir dependências explícitas no grafo Dataform. Não modificar as três views operacionais `saude_ingestao`, `volumetria_lake` e `custo_consultas`, que precisam continuar mostrando falhas.

- [x] Acrescentar a regressão em `tests/unit/test_sql.py`, reutilizando `ARQUIVOS`, `config` e `GOLD_OPERACIONAL`:

```python
def test_business_gold_requires_dependency_assertions():
    tables = [p for p in ARQUIVOS
              if p.parent.name == "gold" and p.stem not in GOLD_OPERACIONAL]
    assert tables
    for path in tables:
        assert "dependOnDependencyAssertions: true" in config(path), path.name
```

- [x] Executar `uv run pytest tests/unit/test_sql.py -q`; observar falha pela ausência da propriedade.
- [x] Acrescentar a propriedade nas tabelas Gold de negócio e no template `GOLD` de `scripts/novo_conector.py`, preservando as chaves existentes:

```javascript
config {
  type: "table",
  schema: "gold",
  tags: ["gold"],
  dependOnDependencyAssertions: true
}
```

- [x] Estender o teste existente do scaffolding para verificar a propriedade no Gold gerado em diretório temporário, sem gerar fonte no repositório. Rodar `uv run pytest tests/unit/test_sql.py tests/unit/test_novo_conector.py -q`.
- [x] Compilar com `npx --yes @dataform/cli@3.0.69 compile --json`, salvando a saída em arquivo temporário fora do repositório. Conferir no JSON compilado que as assertions da Silver referenciada estão em `dependencyTargets` da Gold, não apenas presentes em `assertions`. Usar este verificador sobre o arquivo passado como primeiro argumento:

```python
import json
import sys

with open(sys.argv[1], encoding="utf-8-sig") as stream:
    graph = json.load(stream)
def key(target):
    return tuple(target.get(k, "") for k in ("database", "schema", "name"))
assertions = graph["assertions"]
checked = 0
for table in graph["tables"]:
    if table["target"]["schema"] != "gold" or table["type"] != "table":
        continue
    dependencies = {key(t) for t in table.get("dependencyTargets", [])}
    required = {key(a["target"]) for a in assertions
                if a.get("parentAction") and key(a["parentAction"]) in dependencies}
    assert required, table["target"]
    assert required <= dependencies, (table["target"], required - dependencies)
    checked += 1
assert checked > 0
```

- [x] Caso o compilador represente `parentAction` de forma diferente, conferir o JSON real e adequar a leitura dessa propriedade, mantendo a exigência de arestas explícitas. Não substituir a prova do grafo por busca textual.
- [x] Commit: `fix: bloqueia Gold quando validacoes da origem falham`.

**Aceite local:** SQL e scaffolding aprovados; compilação sem erro e dependências de assertions verificadas. **Aceite posterior em GCP:** assertion que falha impede atualização da Gold; última tabela válida permanece disponível. A execução real fica pendente da Alup liberar o ambiente.

## Tarefa 2 — Ler raw em fluxo e reprocessar em lotes

**Interfaces:** alterar `ler_raw(uri: str)` para retornar `Iterator[dict[str, Any]]`. Todos os consumidores identificados estão em `src/core/conector.py` e nos testes de storage, replay e linhagem. Criar no runner `_carregar_em_lotes(self, execucao: Execucao, registros: Iterable[dict[str, Any]]) -> None`; reutilizar `_validar_e_carregar`. O helper soma apenas inválidos e carregados; a contagem de extraídos pertence ao chamador.

- [x] Adaptar o GCS falso de `test_storage.py` para `reload()`, `generation` e `open("rb", ...)`, retornando `io.BytesIO` do gzip. O falso deve rejeitar `download_as_bytes()` e registrar os argumentos de abertura.
- [x] Converter as verificações de leitura para `list(ler_raw(URI))`. Escrever regressões: leitura incremental; arquivo com mais de 100 MiB descomprimidos composto de linhas pequenas; linha acima do limite; JSON inválido ou não objeto; gzip truncado/CRC incorreto; Unicode inválido; fechamento mesmo quando o consumidor falha. Produzir o gzip grande por escrita repetida em arquivo temporário, sem montar o corpo inteiro em memória.
- [x] Trocar os testes que exigem o limite global de 100 MiB por proteção de linha individual e comprovação de consumo incremental. Usar limite de linha de 1 MiB inicialmente, verificando que fixtures dos conectores cabem. Aplicar a mesma restrição na escrita JSONL para não criar um raw que o leitor rejeitará.
- [x] Rodar `uv run pytest tests/unit/core/test_storage.py tests/unit/core/test_replay.py -q` e confirmar as falhas esperadas.
- [x] Implementar o leitor com `blob.reload()` para fixar a geração e leitura binária sem expansão HTTP automática. Núcleo proposto, dentro de `ler_raw`, após validação da URI e obtenção do blob:

```python
MAX_RAW_LINE_BYTES = 1024 * 1024

blob.reload()
if blob.generation is None:
    raise ValueError("raw sem geração identificada")
with blob.open("rb", chunk_size=1024 * 1024, raw_download=True,
               if_generation_match=int(blob.generation)) as source:
    with gzip.GzipFile(fileobj=source) as stream:
        number = 0
        while line := stream.readline(MAX_RAW_LINE_BYTES + 1):
            number += 1
            if len(line) > MAX_RAW_LINE_BYTES:
                raise ValueError(f"linha {number} do raw excede o limite")
            if not line.strip():
                continue
            record = json.loads(line.decode("utf-8"))
            if not isinstance(record, dict):
                raise ValueError(f"linha {number} do raw não é um objeto JSON")
            yield record
```

- [x] Preservar mensagem clara de gzip inválido para `gzip.BadGzipFile`, `EOFError` e `zlib.error`, sem converter falha de rede/IAM em erro de formato. Não incluir conteúdo da linha no erro. Consumir até EOF para validar o trailer gzip; manter timeouts e deadline do job. O limite por linha protege memória, não substitui o limite de tempo da execução.
- [x] Implementar o helper de lotes, incluindo teto de 8 MiB de JSON bruto por lote além do limite de registros existente, para não acumular milhares de registros próximos de 1 MiB:

```python
def _carregar_em_lotes(self, execucao, registros):
    batch = []
    batch_bytes = 0
    for record in registros:
        size = len(json.dumps(record, ensure_ascii=False, default=str).encode("utf-8"))
        if batch and (len(batch) >= self.tamanho_do_lote
                      or batch_bytes + size > 8 * 1024 * 1024):
            self._validar_e_carregar(execucao, batch)
            batch = []
            batch_bytes = 0
        batch.append(record)
        batch_bytes += size
    if batch:
        self._validar_e_carregar(execucao, batch)
```

- [x] Acrescentar as anotações de tipos e imports indicados na interface. No replay, envolver o gerador em `contextlib.closing`, contar extraídos conforme leitura e passá-lo ao helper; nunca usar `len`, `list` ou nova consulta à origem:

```python
with closing(ler_raw(uri)) as records:
    def counted_records():
        for record in records:
            execucao.linhas_extraidas += 1
            yield record
    self._carregar_em_lotes(execucao, counted_records())
```

- [x] Nos mocks de `ler_raw`, devolver geradores fecháveis, não listas. Testar cinco registros/lote de dois, carga antes do fim da leitura, preservação de `origem_ingestao_id`, inválidos, lote limitado por bytes e falha depois do primeiro lote. Falha tardia registra `ERRO`; lotes anteriores permanecem no Bronze e a reexecução é deduplicada pela Silver.
- [x] Rodar `uv run pytest tests/unit/core/test_storage.py tests/unit/core/test_replay.py tests/unit/core/test_linhagem.py -q`.
- [x] Commit: `fix: reprocessa raw em fluxo com memoria limitada`.

**Aceite:** arquivos grandes são consumidos progressivamente; limites protegem cada linha e lote; recursos fecham em sucesso e erro; não há consulta à fonte durante replay. Não afirmar atomicidade de carga entre lotes.

## Tarefa 3 — Concluir o raw antes de carregar o Bronze

**Depende:** tarefa 2. **Interfaces:** mesma `ingerir(janela) -> Execucao`, mesmos arquivos e identificadores. A ingestão mantém modo original; não chamar `reprocessar_raw`, pois criaria outra execução e outra semântica de linhagem.

- [x] Ajustar `espiao` em `test_conector_lote.py` para registrar fechamento do raw e fornecer os mesmos registros via leitor falso. Tornar explícitos os modos real e dry-run nos testes.
- [x] Substituir o teste que exige carga antes do fim da extração por prova de persistência anterior à carga. No falso, usar a seguinte guarda na função `carregar`:

```python
assert raw_closed, "Bronze não pode receber lote antes do fechamento do raw"
```

- [x] Criar caso em que `RawFalso.__exit__` lança `OSError("falha ao concluir raw")`; exigir nenhuma carga e execução registrada como `ERRO`. Criar também falha da extração depois de dois registros: raw parcial pode ser preservado, mas nenhuma carga é iniciada.
- [x] Rodar `uv run pytest tests/unit/core/test_conector_lote.py -q` e observar falha na implementação atual.
- [x] Reorganizar `_ingerir` mantendo tratamento de erros, sanitização, registro de execução e linhagem. Estrutura proposta:

```python
def extracted_records():
    for part in self._janelas(janela):
        for record in self.extrair(part):
            execucao.linhas_extraidas += 1
            yield record

if get_settings().dry_run:
    self._carregar_em_lotes(execucao, extracted_records())
else:
    with abrir_raw(execucao) as raw:
        for record in extracted_records():
            raw.escrever(record)
    with closing(ler_raw(raw.uri)) as records:
        self._carregar_em_lotes(execucao, records)
```

- [x] Testar ordem extrair → escrever → fechar → ler → carregar, contadores sem duplicação, volume zero, inválidos, erro do BigQuery e dry-run sem SDKs. Preservar testes do TempoOK, cujo PDF é gravado separadamente antes do ponteiro JSONL.
- [x] Atualizar comentários que associam memória limitada a carregar durante a extração. A nova proteção é streaming nas duas etapas. Atualizar `docs/runbook/primeiro-deploy.md`: o custo adicional é uma leitura GCS por ingestão; medir tempo, memória e bytes no primeiro ambiente disponível.
- [x] Rodar `uv run pytest tests/unit/core tests/unit/conectores/test_tempook_boletins.py -q`.
- [x] Commit: `fix: confirma persistencia do raw antes da carga Bronze`.

**Aceite:** nenhuma gravação Bronze antes do fechamento bem-sucedido do raw; um único identificador de execução; memória limitada; layout antigo continua legível. O novo caminho aumenta I/O e latência, mas não exige memória ou disco proporcionais ao arquivo. Não reutilizar os picos medidos do dry-run como evidência desse novo caminho real.

## Tarefa 4 — Alinhar o deploy à arquitetura vigente

**Interfaces:** manter ambientes `dev`, `hml`, `prod` e opções `all`, `infra`, `connectors`. `connectors` continua apenas publicando a imagem, como documentado. Acrescentar entrada opcional `image_sha`, obrigatória em tempo de execução somente para `infra`, contendo SHA completo de imagem já publicada no ambiente escolhido. Para `all`, usar `GITHUB_SHA`.

- [x] Remover opção `dags` e job `sync-dags`; não criar workflow substituto de orquestração da Onda 3 neste reparo.
- [x] Adicionar a entrada e passar seu valor ao shell por variável de ambiente, evitando interpolação direta de entrada do usuário no script:

```yaml
image_sha:
  description: 'SHA completo da imagem já publicada; obrigatório para infra'
  required: false
  type: string
```

```bash
if [ "$DEPLOY_MODULE" = "all" ]; then
  TAG="$GITHUB_SHA"
else
  TAG="$IMAGE_SHA"
fi
if [[ ! "$TAG" =~ ^[0-9a-f]{40}$ ]]; then
  echo "::error::Informe o SHA completo de uma imagem já publicada."
  exit 1
fi
```

- [x] Definir `DEPLOY_MODULE` e `IMAGE_SHA` via `env` do step. Executar essa validação antes de `terraform init/plan/apply`. Manter imagem publicada em `latest` apenas como conveniência, nunca como entrada do Terraform. Confirmar existência da imagem no Artifact Registry antes do plano quando o workflow for executado no ambiente real.
- [x] Adicionar validação em `infra/variables.tf`, permitindo vazio para bootstrap e exigindo SHA completo ou digest para qualquer imagem configurada:

```hcl
validation {
  condition = var.imagem_ingestao == "" || can(regex(
    "(:[0-9a-f]{40}|@sha256:[0-9a-f]{64})$", var.imagem_ingestao
  ))
  error_message = "Use imagem vazia, tag de SHA completo ou digest sha256."
}
```

- [x] Exercitar o shell em Bash/CI com entradas: `all` com SHA válido, `infra` com SHA válido, vazio, `latest`, SHA abreviado e caracteres de shell. Só os dois primeiros devem passar; nenhum teste executa GCP ou Terraform apply. Conferir a validação Terraform com valores vazio, SHA, digest e `latest`, usando console/teste local com backend desabilitado.
- [x] Corrigir os dois runbooks e a skill local de GCP: retirar instrução vigente de sincronizar DAGs, referência a `COMPOSER_BUCKET` e uso de `latest` no deploy de infra. Preservar ADRs e relatórios históricos. Descrever Workflows como destino da Onda 3, sem afirmar que já foi implantado.
- [x] Rodar `terraform -chdir=infra fmt -check -recursive`, `terraform -chdir=infra init -backend=false` e `terraform -chdir=infra validate`; conferir YAML e casos de shell. Não disparar o workflow de deploy para testar essa alteração.
- [x] Commit: `fix: remove Composer do deploy e exige imagem imutavel`.

**Aceite:** `all` não referencia Composer; `infra` sem SHA falha antes de qualquer alteração; `all` e `infra` usam imagem identificável. Nenhum recurso é provisionado durante a validação local.

## Fechamento e evidências

- [x] Executar `make all` e `make dataform-compile`. Em Windows sem Make, usar os comandos equivalentes do `Makefile`; definir `PYTHONUTF8=1` no processo de auditoria se necessário pelo caminho acentuado. Não alterar arquivos de dependências por conveniência.
- [x] Conferir os oito checks existentes do CI nos PRs; revisar diff para excluir arquivos temporários, fixtures com dados reais e mudanças alheias.
- [x] Atualizar `docs/status.md` com testes executados e links dos PRs, registrando separadamente “corrigido e validado localmente/CI” e “validação operacional aguardando ambiente da Alup”. Não promover cartões a homologados ou preencher horas a partir de estimativas.
- [x] Conferir que os quatro achados têm evidência: grafo Gold, falha no fechamento raw sem carga, replay grande em lotes, deploy sem Composer e sem imagem mutável.

Quando o ambiente estiver disponível, executar o runbook existente em dev: uma fonte pequena e uma volumosa, raw recuperável, Silver deduplicada, assertion bloqueando Gold, falha/replay, alertas e imagem efetiva. Essas verificações são pendências externas ao aceite dos reparos locais; não justificam deixar o código corrigível parado agora.

## Referências técnicas consultadas

- [Dataform: dependências de assertions](https://docs.cloud.google.com/dataform/docs/dependencies): `dependOnDependencyAssertions` é falso por padrão.
- [Cloud Storage: leitura e escrita de blobs](https://github.com/googleapis/python-storage/blob/main/docs/storage/blob.md): leitura progressiva, geração fixada e `raw_download`.
- [Cloud Storage: BlobReader](https://github.com/googleapis/python-storage/blob/main/docs/storage/fileio.md): buffers e argumentos da leitura. Downloads por ranges não verificam checksum do objeto inteiro; o consumo completo do gzip verifica seu trailer e a geração fixada impede misturar versões.

## Registro de execução — 18/09/2026

- Implementação em `fix/correcao-achados-tecnicos`, a partir de `45aa239`.
- Gold: 25 tabelas de negócio, 62 arestas de assertions no grafo compilado; três views operacionais preservadas. O CI verifica o grafo explicitamente.
- Raw/replay: testes de regressão falharam antes da implementação; leitura acima de 100 MiB, limite simétrico de 1 MiB por linha, lote de até 8 MiB e fechamento antes do Bronze aprovados. Limite por quantidade descarrega imediatamente, sem antecipar leitura do próximo registro.
- Deploy: referências distintas entre o commit do workflow e a imagem solicitada foram testadas; Terraform executa cinco casos locais sem providers. O CI instala Terraform no job de testes.
- Verificação integrada: 983 testes aprovados, 264 ignorados, cobertura de 94%; Ruff e formatação aprovados; Bandit sem achados médios/altos (13 baixos preexistentes); auditoria de dependências sem vulnerabilidades conhecidas; Terraform fmt/init sem backend/validate aprovados.
- Dos testes ignorados, 248 são regras SQL não aplicáveis à camada; não representam 248 integrações pendentes.
- Testes reais no ambiente continuam pendentes de liberação pela Alup; nenhum provisionamento ou deploy foi executado.
- Melhoria separada identificada na revisão: `ccee_perfil` e `ons_capacidade` usam `_data_retrato` inicializado na extração; replay em instância nova precisa recuperar essa referência. É comportamento anterior a este reparo, que preserva a instância na ingestão. Preparar regressão específica antes de corrigir, sem alterar datas por suposição.

- [PR #165](https://github.com/nessenergy/Alupdatalake/pull/165): oito verificações do GitHub aprovadas no commit `110ec2c`; [execução do CI](https://github.com/nessenergy/Alupdatalake/actions/runs/35344381627). Confirmar novamente no commit final antes do merge.

### Seguimento do replay dos cadastros — 18/09/2026

A melhoria separada acima foi implementada: CCEE/perfil e ONS/capacidade
persistem `_data_retrato` no raw, permitindo replay em instância nova, sem
consultar a origem. Datas ausentes ou inválidas interrompem a execução;
a extração não assume mais o dia atual. Bronze, Silver e Gold mantêm o schema.

Os 16 testes novos reproduziram o defeito antes do reparo; depois, 43 testes
focados e 999 testes da suíte completa passaram (264 ignorados, 94% de cobertura).
Raw legado sem o metadado exige evidência da publicação original: nova
extração representa o retrato corrente e não recupera automaticamente o antigo.
Runbook e dicionários descrevem a recuperação. Nenhum acesso ao GCP foi realizado.
