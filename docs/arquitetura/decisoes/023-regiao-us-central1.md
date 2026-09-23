# ADR 023 — Região do ambiente: `us-central1`

**Status**: aceito · **Data**: 2026-09-23 · **Substitui** a
[ADR 011](011-regiao-us-east1.md)

## Contexto

A [ADR 011](011-regiao-us-east1.md) fixou `us-east1` em 10/09, depois da
revisão arquitetural com o Google, e registrou a mesma ressalva que a
[ADR 009](009-regiao-do-ambiente.md) antes dela: enquanto o primeiro
`terraform apply` não acontece, trocar a região é editar uma variável.

Em 23/09 a Alup liberou os três projetos GCP e a conferência do ambiente
mostrou o que ninguém tinha como saber antes de ter acesso: a política de
organização `constraints/gcp.resourceLocations`, **herdada da pasta que
contém os três projetos**, admite apenas

    us-central1 · us-central1-a · us-central1-b · us-central1-c ·
    us-central1-f · us-central1-locations · us · global

`us-east1` não está na lista. A política não está definida nos projetos: ela
vem de cima, e só a Alup a altera. Com ela em vigor, **nenhum recurso do
`infra/` sobe** — nem o bucket de state do bootstrap.

Havia duas saídas: pedir à Alup uma exceção para os três projetos, ou adotar
a região que a política já permite. O pedido custaria uma nova espera de
prazo desconhecido — A3 levou 12 dias úteis além do vencimento — e pediria à
Alup que abrisse exceção na própria governança dela para uma escolha que,
pelo texto da ADR 011, tinha uma vantagem só. **A decisão da ness., em
23/09, é adotar `us-central1`.**

## Decisão

Todo o ambiente — datasets Bronze/Silver/Gold, dataset `faturamento`, bucket
raw, bucket de state, Artifact Registry, Cloud Run Jobs, Scheduler, Portal,
secrets, repositório Dataform (ADR 012) e o lake do Knowledge Catalog
(ADR 014) — fica em **`us-central1`** (Iowa), nos três ambientes.
`us-central1` passa a ser o padrão de `variable "region"`, em `infra/` e em
`infra/bootstrap/`.

A decisão de manter o ambiente **nos Estados Unidos**, tomada com o Google em
10/09, não muda. Muda a região americana.

### Por que `us-central1` e não insistir em `us-east1`

- **É o que a política permite hoje.** Região fora dela não é escolha
  técnica, é recurso que não cria.
- **A ADR 011 descartou `us-central1` por um motivo único** — distância das
  origens brasileiras — e registrou, no mesmo parágrafo, que o preço é da
  mesma faixa e que **não há serviço do projeto que exista lá e falte em
  `us-east1`**. A recíproca vale: Dataform, Knowledge Catalog, Cloud Run,
  Scheduler e BigQuery estão em `us-central1`, que é a região onde o Google
  lança recurso novo primeiro.
- **A espera tem custo contratual; a latência, não.** O efeito de latência
  aparece na Onda 3, em leitura de banco por VPN, e é proporcional ao número
  de idas e voltas — controlável por `banco_lote` (ADR 008). O efeito da
  espera é ociosidade e cronograma, que a cláusula 3ª precifica.

### O que não se sustentaria

- **Pedir exceção de política e esperar.** Sustentável se a latência fosse
  requisito, com número medido, e não uma preferência. Não é o caso: nenhuma
  medição foi feita, e nenhum requisito do contrato fixa tempo de ingestão.
- **Multirregião `US`.** Descartada pela ADR 011 e pelos mesmos motivos —
  Cloud Run, Scheduler e Airflow são regionais, e os *scans* do Knowledge
  Catalog não rodam em localização multirregião. A política a permitiria,
  mas ela nunca foi a melhor opção.

## Consequências

- **A troca é gratuita agora e cara depois.** Nada existe em região alguma:
  são variáveis de Terraform, `workflow_settings.yaml` e o padrão de
  `src/core/config.py`. Depois do primeiro `apply`, dataset do BigQuery não
  muda de região e a mudança vira migração de dado, com ADR própria.
- **Latência maior às origens brasileiras da Onda 3.** Iowa é mais distante
  de São Paulo que a Carolina do Sul. O acréscimo por ida e volta não foi
  medido — medir exige a VPN, que é A7 — e incide por lote, não por linha.
  Se a ingestão de alguma fonte interna ficar longa, o primeiro ajuste é
  `banco_lote`, não a região.
- **Documentos de LGPD atualizados, análise inalterada.** DPA, RoPA e RIPD
  passam a dizer `us-central1`. A transferência internacional continua sendo
  para os Estados Unidos, com a mesma base legal e o mesmo DPA do contrato de
  nuvem da Alupar: muda o endereço, não o país nem o fundamento.
- **O pedido de exceção sai da mesa.** A pendência A14 do
  [`status.md`](../../status.md) se encerra por decisão, não por resposta da
  Alup. Se a Alup quiser `us-east1` depois de ver esta ADR, a conversa volta
  — mas só vale antes do primeiro `apply`.
- **`INFORMATION_SCHEMA` é por região.** Consulta de custo e de linhagem
  apontada para a região errada devolve zero linha em silêncio. Quem tiver
  `.env` local com `GCP_REGION=us-east1` precisa trocar.

## Fontes

- Política conferida em 23/09 nos três projetos:
  `gcloud resource-manager org-policies describe gcp.resourceLocations
  --project=<projeto> --effective`.
- [Restrição de locais de recursos](https://docs.cloud.google.com/resource-manager/docs/organization-policy/defining-locations)
- [Localizações do Google Cloud](https://cloud.google.com/about/locations)
