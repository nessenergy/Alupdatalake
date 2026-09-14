# Interlocutores do projeto

Quem é quem nas conversas do AlupData — Fase 1, contrato CPS-01025/2026.

Este arquivo responde uma pergunta operacional: **para quem eu levo isto?**
Ele não substitui a matriz RACI por domínio de dados (dependência **A5**), que é
artefato de governança e cabe à Alup produzir. Aqui ficam as pessoas que já
estão na mesa; lá ficará quem responde por cada domínio analítico. Os data
owners por domínio de dado, respondidos no B1 em 11/09, estão na seção própria
abaixo.

---

## Quadro

### Alup — contratante

| Nome | Papel | Contato |
|---|---|---|
| Leonardo Guiel Marques | Product Owner · ponto focal técnico de acesso (B2) | `lgmarques@alupar.com.br` |
| Saulo Rodrigues | TI | `srodrigues@alupar.com.br` |
| Taina Ulhoa Mota | Co-Owner · data owner (B1) · aprova a homologação e assina a medição (B4) | `tmota@alupar.com.br` |
| Mauricio Wilhelm Rios Cardoso | Co-Owner · substituto do ponto focal técnico (B2) | `mwcardoso@alupar.com.br` |
| Eduardo Pires | Diretor · patrocinador do projeto | `epires@alupar.com.br` |
| Letícia Ferreira | Data owner (B1) · Gestão de Portfólio e Back-Office | `lcferreira@alupar.com.br` |
| Tahigo Santos | Data owner (B1) · Comercial | `tasantos@alupar.com.br` |
| Gabriel Barreto | Data owner (B1) · Trading | `gbsantos@alupar.com.br` |
| Alertas (grupo) | Falha de ingestão (E3) e relatório semanal de SAST/SCA (F5) | `alup.alertas@alupar.com.br` |

### ness. — contratada

| Nome | Papel | Contato |
|---|---|---|
| Ricardo Esper | Project Leader · assina os relatórios emitidos à contratante | `resper@ness.com.br` |
| Gabriel Teodoro da Paz | Product Owner do projeto · divisão DevArch | `gpaz@ness.com.br` |
| Thiago Bertuzzi | Líder Técnico | `bertuzzi@ness.com.br` |
| Gabriela Paula Torres | Dev Líder | `gptorres@ness.com.br` |

> **Sobre o patrocinador.** Eduardo Pires não tem função direta na execução.
> Entra em cópia para acompanhamento; pedido operacional não se dirige a ele.

---

## Quem procurar para quê

| Assunto | Quem | Referência |
|---|---|---|
| Criação do projeto GCP e `billing_account` | Saulo (TI Alup) | [issue #55](https://github.com/nessenergy/Alupdatalake/issues/55), bloco E do questionário. O Workload Identity Federation é administrado pela ness. (E6) |
| Liberação de VPN, credencial de banco, firewall e token de API | Leonardo (ponto focal técnico), com Mauricio como substituto | B2, dependência **A7**, bloco C |
| Priorização de escopo e domínios analíticos | Leonardo (PO), com Taina e Mauricio (co-owners) | blocos A, B e D |
| Dúvida de regra de negócio | data owner do domínio — quadro abaixo | B1; resposta em até 3 dias úteis (B3) |
| Homologação de onda e assinatura da medição | Taina | B4 |
| Acompanhamento do projeto | reunião às sextas-feiras, com a Comercialização e o time técnico da ness. | B5 |
| Balanço Energético, hoje no MySQL RDS na AWS, e o acesso a esse banco | Leonardo (PO Alup) | C4, C8 e C11 |
| Cronograma, medição, marcos e relatórios de situação | Gabriel (PO ness.) e Ricardo | [`plano-semanal.md`](plano-semanal.md), [`relatorios/`](relatorios/) |
| Arquitetura e decisões técnicas | Thiago (líder técnico) e Ricardo | [`arquitetura/decisoes/`](arquitetura/decisoes/) |
| Código, conectores e entrega técnica | Gabriela (dev líder) e Thiago | [`AGENTS.md`](../AGENTS.md), [`plano-semanal.md`](plano-semanal.md) |

---

## Data owners por domínio

Resposta da Alup ao B1, em 11/09. **Prazo para responder dúvida de regra de
negócio: até 3 dias úteis** (B3). Dúvida sem resposta nesse prazo é insumo em
atraso e entra na contagem da cláusula 3ª.

**São 8 domínios em 11 linhas** — três deles têm responsáveis distintos por
subtemas. Detalhe em
[`arquitetura/dominios-analiticos.md`](arquitetura/dominios-analiticos.md).

| Domínio | Data owner |
|---|---|
| Mercado de Energia — PLD, EAR, ENA, CCEE (CVU, ESS, EER), ONS (carga, térmicas, geração) | Taina |
| Mercado de Energia — BBCE e prêmio | Gabriel Barreto |
| Geração e Operacional — usinas do SIN e DESSEM | Taina |
| Geração e Operacional — usinas da Alupar e medição | Letícia Ferreira |
| Meteorologia — precipitação, vento, clima | Taina |
| Comercial e Contratos — book, sazonalização, garantias | Letícia Ferreira |
| Comercial e Contratos — contratos de varejo e Hubspot | Tahigo Santos |
| CRM e Marketing — leads, campanhas, documentos | Tahigo Santos |
| Risco e Compliance — exposição, GSF, Proinfa | Letícia Ferreira |
| Econômico — IPCA, Selic, câmbio, CDI | Letícia Ferreira |
| Planejamento — orçamento, premissas | gestores da Comercialização: Letícia Ferreira, Tahigo Santos e Taina |

---

## Lacunas

Registradas porque cada uma tem efeito prático, e nenhuma se resolve do nosso
lado:

| # | O que falta | Por que importa | Onde é cobrado |
|---|---|---|---|
| 1 | ~~**Substituto do ponto focal técnico** da Alup~~ | se toda liberação de acesso passa por uma única pessoa, uma ausência para o projeto | **Resolvida em 11/09**: Mauricio (B2) |
| 2 | **Matriz RACI** por domínio — os data owners já vieram | a matriz completa diz também quem aprova, quem é consultado e quem é informado | **A5**; data owners respondidos no B1 em 11/09 |
| 3 | ~~**Quem administra o Workload Identity Federation**~~ | é o único item do provisionamento que exige familiaridade com OIDC | **Resolvida em 11/09**: a ness. (E6) |
| 4 | ~~**Quem recebe os alertas** de falha de ingestão~~ | os alertas existem e não notificam ninguém | **Resolvida em 11/09**: `alup.alertas@alupar.com.br` (E3) |

Preferência registrada para a lacuna 4: **grupo, não pessoa nominal.** Pessoa
sai de férias; grupo não. Atendida: o destinatário é um endereço de grupo.

---

## Convenções deste arquivo

- **Papel no projeto, não cargo na empresa.** O que interessa aqui é quem decide
  o quê nesta entrega.
- **Endereço funcional é melhor que pessoal.** Onde existir grupo ou lista, é
  ele que deve entrar — sobrevive a troca de time e reduz dado pessoal em
  repositório versionado.
- **Sem telefone, sem dado pessoal além do necessário ao contato profissional.**
  Vale a mesma regra do resto do repositório, e é coerente com o que o bloco F
  do questionário pergunta à própria Alup.
- **Nome sem confirmação não entra.** Se aparecer numa conversa e não estiver
  claro o papel, fica de fora até ser confirmado — cadastro com palpite é pior
  que cadastro incompleto.
