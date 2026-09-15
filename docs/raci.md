# Matriz RACI do projeto

Documento **recebido da Alup em 15/09/2026** (`Data_Lake_Comercializadora_RACI.docx`),
transcrito aqui na íntegra. É a matriz de responsabilidade **por atividade e por
fase**; não é a matriz por domínio de dado, que continua sendo a lacuna 2 de
[`interlocutores.md`](interlocutores.md).

Quem é quem, com nome e contato, está em [`interlocutores.md`](interlocutores.md).
Este arquivo trata de papéis; aquele, de pessoas.

---

## 1. Função de cada parte

| Parte | Função no projeto | Responsabilidade principal |
|---|---|---|
| Área de negócio | Dona do produto de dados | Define fontes oficiais, prioridades, regras de negócio, owners, consumidores e critérios de aceite dos dados |
| TI corporativa | Guardião de segurança e integração corporativa | Define padrões de acesso, rede, IAM, compliance, integração com ambientes internos e modelo de sustentação |
| ness. | Integradora e engenharia de dados | Desenha e implementa pipelines, camadas Bronze/Silver/Core, data quality, documentação, versionamento, logs e handover |
| Google/GCP | Plataforma cloud e advisor técnico | Apoia landing zone, arquitetura GCP, escolha de serviços, boas práticas, segurança, escalabilidade e FinOps |

## 2. Responsabilidades por etapa

| Etapa | Área de negócio | TI | ness. | Google/GCP |
|---|---|---|---|---|
| Fase 0 — Arquitetura e governança | Define objetivos, fontes oficiais, consumidores, owners e prioridades | Valida requisitos de segurança, acesso, rede e integração | Propõe arquitetura técnica, padrões de ingestão, camadas e documentação | Valida aderência à GCP e boas práticas cloud |
| Fase 1 — Industrialização inicial | Homologa dados tratados e orienta desativação de scripts paralelos | Libera acessos e acompanha segurança operacional | Constrói pipelines e camadas Bronze/Silver/Core das fontes priorizadas | Apoia dimensionamento, FinOps e desenho de operação |
| Fase 2 — Expansão | Prioriza novas fontes e consolida política de consumo oficial | Apoia escalabilidade, backup, acesso e compliance | Expande fontes, qualidade, catálogo e runbooks | Apoia otimização de custo, governança e eventual uso de IA |
| Operação assistida | Monitora aderência da base oficial às necessidades do negócio | Assume ou compartilha sustentação técnica conforme modelo acordado | Suporte pós-entrega, correções, transferência e evolução contratada | Acompanha melhores práticas e eventuais ajustes de arquitetura |

## 3. Matriz RACI

Legenda: **R** = responsável por executar · **A** = accountable/aprova ·
**C** = consultado · **I** = informado.

| Atividade / Entregável | Negócio | TI | ness. | Google/GCP | Comitê |
|---|---|---|---|---|---|
| Definir objetivo, escopo e critérios de sucesso | A/R | C | C | C | I |
| Priorizar fontes e consumidores | A/R | C | C | I | C |
| Definir owner por domínio de dado | A/R | C | I | I | I |
| Desenhar arquitetura alvo GCP | C | C | R | A/C | I |
| Definir landing zone, IAM, rede e segurança | C | A/R | C | C | I |
| Criar catálogo de fontes e data dictionary | A/C | C | R | C | I |
| Inventariar scripts e automações existentes | A/R | C | R | I | I |
| Definir padrão Bronze/Silver/Core | A/C | C | R | C | I |
| Construir framework de ingestão | C | C | A/R | C | I |
| Construir pipelines das fontes priorizadas | C | C | A/R | I/C | I |
| Implementar data quality e validações | A/C | C | R | C | I |
| Implementar logs, alertas e retries | I | C | R | C | I |
| Homologar dados tratados e camada Core | A/R | C | C | I | I |
| Definir política de consumo oficial | A/R | C | C | I | I |
| Medir e projetar consumo GCP | I | C | R | A/C | I |
| Aprovar passagem de fase | C | C | C | I | A/R |
| Executar handover técnico e runbook | I | C | A/R | I/C | I |
| Definir modelo de sustentação | A/C | A/C | C | C | R |

---

## 4. Leitura da ness.

### 4.1 O que o documento confirma — e é útil ter por escrito

**"Definir landing zone, IAM, rede e segurança: TI = A/R."** É a própria Alup
declarando, por escrito e em documento de governança, que o provisionamento do
ambiente é responsabilidade dela. Sustenta o registro de atraso de **A3** e
**A1**, em curso desde 04/09 — ver [`status.md`](status.md) §6.

**"Fase 1 — TI: libera acessos e acompanha segurança operacional."** Mesma
leitura para **A7** e **A9**: token, VPN e credencial são liberação da Alup,
não pedido em aberto.

**"Negócio: orienta desativação de scripts paralelos."** Compromisso novo e
bem-vindo — a base oficial só vira oficial quando o que roda em paralelo sai.

### 4.2 Divergências a conciliar

| # | No documento | No contrato CPS-01025/2026 | Efeito se ficar como está |
|---|---|---|---|
| 1 | Camada **Core** | Camada **Gold** (cláusula 2ª, 7 componentes por fonte) | Só vocabulário, mas atravessa dicionário de dados, views e medição. Um de-para resolve |
| 2 | **Fase 0/1/2 + operação assistida** | **Ondas 0 a 4**, com marcos de 15,52%, 20,69%, 18,97%, 26,72% e 18,10% | A medição é por onda. Sem de-para, "passagem de fase" não corresponde a nenhum marco financeiro |
| 3 | **"Aprovar passagem de fase: A/R = Comitê"** e **"Definir modelo de sustentação: R = Comitê"** | **B4**: Taina Ulhoa Mota homologa e assina a medição | O Comitê não tem membros nomeados nem periodicidade. Homologação que espera um colegiado indefinido é atraso com aparência de processo |
| 4 | **"Desenhar arquitetura alvo GCP: A = Google/GCP"**, R = ness. | A arquitetura é entrega da ness. (ADRs 001–020) | É o padrão que já custou caro: **A3 foi condicionada pela Alup à resposta do Google (G1)**, sem prazo pactuado. Formalizar o Google como *accountable* institucionaliza a dependência de um terceiro sem contrato com a ness. e sem prazo |

### 4.3 O que este documento **não** é

Não é a **RACI por domínio de dado** — a lacuna 2 de
[`interlocutores.md`](interlocutores.md). Ele diz quem aprova *atividades*; falta
quem aprova, é consultado e é informado *por domínio*. Os data owners por
domínio vieram no B1 em 11/09 e estão em
[`interlocutores.md`](interlocutores.md#data-owners-por-domínio); o R/A/C/I em
cima deles, não.

Também não nomeia pessoas: trabalha com funções ("Área de negócio", "TI
corporativa"). Para uso operacional, é preciso ler junto com
[`interlocutores.md`](interlocutores.md).

### 4.4 Perguntas à Alup

1. **Quem compõe o Comitê**, quem o convoca e com que periodicidade? Enquanto
   não houver resposta, a ness. mantém **B4** — Taina homologa e assina a
   medição — como o rito válido.
2. **O papel do Google é de consultado (C) ou de aprovador (A)?** A recomendação
   da ness. é **C**. Aprovador sem contrato e sem prazo acordado vira caminho
   crítico, como já ocorreu em G1.
3. **De-para entre "Fase" e "Onda"** — a medição é por onda; convém fixar a
   correspondência antes da primeira homologação.

> Nenhuma destas questões bloqueia trabalho técnico. O que bloqueia continua
> sendo **A3** (ambiente GCP), **A7** e **A9**.
