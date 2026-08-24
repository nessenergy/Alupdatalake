# Contrato CPS-01025/2026 — AlupData Fase 1: DataLake

## Partes

| Papel | Entidade |
|-------|----------|
| **CONTRATANTES** | 6 coligadas do Grupo Alupar: FGE, IJUI, FOZ, QUELUZ, LAVRINHAS, VERDE 08 |
| **CONTRATADA** | **ness. Processos e Tecnologia Ltda.** (CNPJ 72.027.097/0001-37) — Rep.: Rogério Salerno |

---

## Objeto (Cláusula 1ª)

Prestação de serviços especializados de **arquitetura, modelagem e engenharia de dados** para implementação da **Fase 1 — DataLake** do projeto **AlupData**.

- **Regime**: alocação de horas técnicas (não empreitada)
- **Horas estimadas**: **580h**
- **Arquitetura**: Medallion (Bronze → Silver → Gold) na **Google Cloud Platform** (BigQuery, Cloud Storage)
- Atividades, prioridades e sequência podem ser redefinidas durante execução

---

## Padrão de Entrega — 7 Componentes por Conector (Cláusula 2ª)

| # | Componente | Descrição |
|---|-----------|-----------|
| 01 | **Conector Python** | Código estruturado para extração e transporte |
| 02 | **Tabela Bronze** | Append-only, schema versionado, log de ingestão |
| 03 | **View Silver** | Dados higienizados, tipados, deduplicados, dimensões comuns |
| 04 | **View Gold** | Regras de negócio complexas e KPIs consolidados |
| 05 | **Testes (pytest)** | Validação automatizada unitária e integração e2e |
| 06 | **Agendamento GCP** | Orquestração via Cloud Scheduler / Cloud Composer |
| 07 | **Documentação & Linhagem** | Dicionário de dados, mapeamento de campos, linhagem completa |

---

## Cronograma — Ondas de Desenvolvimento (Cláusula 4ª)

**Duração total estimada: 19 semanas**

| Onda | Nome | Semanas | Horas | Atividades-chave |
|------|------|---------|-------|-------------------|
| **0** | Fundação & Arquitetura | 2 | 90h | Mapeamento de fontes, 8 domínios analíticos, arquitetura Medallion, dimensões comuns Silver, CI/CD, portal base com auth |
| **1** | Inteligência de Mercado Base | 5 | 120h | Conectores para APIs públicas (sem credencial Alup), tabelas Bronze, views Silver/Gold |
| **2** | Modelos Preditivos & APIs com Credenciais | 4 | 110h | Conectores dependentes de credenciais/contratos da Alup |
| **3** | Sistemas Internos | 5 | 155h | Conectores para bancos internos e sistemas corporativos (FMB Oracle, Portal Alup MySQL/NoSQL, RM/TOTVS, etc.) |
| **4** | Planilhas, Fontes Pendentes, Governança & Handoff | 3 | 105h | Motor de ingestão "S2 Data Intake" (CSV/XLSX), Dataplex, views Gold KPIs, documentação final, handoff |

---

## Dependências Críticas da Contratante (Cláusula 3ª)

| Quando | O que a Alup deve fornecer |
|--------|---------------------------|
| **Onda 0** | Questionário de Gaps (47 perguntas), RACI, data owners, definição de ferramenta BI |
| **Até Onda 2** | Tokens/APIs: CCEE, BBCE, Hubspot, TempoOK |
| **Até Onda 3** | VPN, credenciais read-only Oracle FMB, Portal Alup (MySQL/NoSQL/Storage), MySQL RDS Comercialização, endpoints RM/TOTVS |
| **Até Onda 4** | Planilhas padronizadas sob templates definidos |

> [!WARNING]
> - Atraso > 5 dias úteis → cronograma postergado automaticamente
> - Atraso > 5 dias úteis em VPN/credenciais → **taxa de ociosidade de 4h/dia (R\$ 256/h)**
> - Atraso > 20 dias corridos → **suspensão automática dos serviços**

---

## Valores e Pagamentos (Cláusula 6ª)

| Item | Valor |
|------|-------|
| **Valor total** | **R\$ 148.480,00** |
| Hora técnica | R\$ 256,00/h |

### Faturamento por Marco

| Marco | Meta | % | Valor |
|-------|------|---|-------|
| 1 | Homologação Onda 0 | 15,52% | R\$ 23.040,00 |
| 2 | Homologação Onda 1 | 20,69% | R\$ 30.720,00 |
| 3 | Homologação Onda 2 | 18,97% | R\$ 28.160,00 |
| 4 | Homologação Onda 3 | 26,72% | R\$ 39.680,00 |
| 5 | Homologação Onda 4 + Handoff | 18,10% | R\$ 26.880,00 |

### Rateio entre Coligadas

Cada uma das 6 coligadas: **R\$ 24.746,67** (divisão igualitária)

**Pagamento**: 10 dias após aceitação formal da medição + NF emitida

---

## Exclusões de Escopo (Cláusula 5ª)

- ❌ Custos de infra GCP (BigQuery, Cloud Composer, Storage, APIs de terceiros)
- ❌ Painéis/relatórios de BI (PowerBI, Tableau) — exceto Portal MVP da Onda 0
- ❌ Treinamento operacional de usuários finais (exceto handoff técnico)
- ❌ Modelos de IA/ML avançados (Fase 3 futura)

---

## Segurança & Compliance (Cláusula 8ª)

- **SSDLC** obrigatório com SAST e SCA no CI/CD
- **Secret Manager** obrigatório (proibido credenciais em código/Git)
- **Varreduras de vulnerabilidades** em todas as dependências antes do deploy
- Vulnerabilidades **Alta/Crítica (CVSS)** devem ser corrigidas antes da homologação
- Eliminação segura de dados de teste/produção após homologação de cada etapa

---

## Garantia e Sustentação (Cláusulas 9ª e 10ª)

| Item | Detalhe |
|------|---------|
| **Garantia** | 30 dias após homologação de cada Onda (correção de bugs sem custo) |
| **Sustentação pós-garantia** (opcional) | Franquia de **20h/mês** por **R\$ 5.120,00/mês** |
| Hora excedente | R\$ 256,00/h (com aprovação prévia) |
| Reajuste | Anual pelo IPCA |
| Escopo sustentação | Monitoramento, correção, patch management, ajustes menores em conectores |
| Exclusões sustentação | Novos pipelines, novas fontes, novas regras de negócio, relatórios BI |

---

## Propriedade Intelectual (Cláusula 7ª)

- **Alup**: código dos conectores sob medida, schemas SQL, views estruturadas
- **ness.**: ferramentas pré-existentes, metodologias de ETL/ELT, arquiteturas de referência, frameworks genéricos

---

## Rescisão (Cláusula 11ª)

- Imotivada: aviso prévio de 30 dias
- Se por iniciativa da Contratante: **multa de 15% sobre saldo remanescente**
- Por justo motivo: imediata (inadimplemento não sanado em 15 dias, falência, etc.)
