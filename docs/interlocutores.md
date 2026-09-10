# Interlocutores do projeto

Quem é quem nas conversas do AlupData — Fase 1, contrato CPS-01025/2026.

Este arquivo responde uma pergunta operacional: **para quem eu levo isto?**
Ele não substitui a matriz RACI por domínio de dados (dependência **A5**), que é
artefato de governança e cabe à Alup produzir. Aqui ficam as pessoas que já
estão na mesa; lá ficará quem responde por cada domínio analítico.

---

## Quadro

### Alup — contratante

| Nome | Papel | Contato |
|---|---|---|
| Leonardo Guiel Marques | Product Owner | `lgmarques@alupar.com.br` |
| Saulo Rodrigues | TI | `srodrigues@alupar.com.br` |
| Taina Ulhoa Mota | Co-Owner | `tmota@alupar.com.br` |
| Mauricio Wilhelm Rios Cardoso | Co-Owner | `mwcardoso@alupar.com.br` |
| Eduardo Pires | Diretor · patrocinador do projeto | `epires@alupar.com.br` |

### ness. — contratada

| Nome | Papel | Contato |
|---|---|---|
| Ricardo Esper | Project Leader · assina os relatórios emitidos à contratante | `resper@ness.com.br` |
| Gabriel Teodoro da Paz | PMO | `gpaz@ness.com.br` |
| Thiago Bertuzzi | Líder Técnico | `bertuzzi@ness.com.br` |

> **Sobre o patrocinador.** Eduardo Pires não tem função direta na execução.
> Entra em cópia para acompanhamento; pedido operacional não se dirige a ele.

---

## Quem procurar para quê

| Assunto | Quem | Referência |
|---|---|---|
| Criação do projeto GCP, IAM, Workload Identity Federation, `billing_account` | Saulo (TI Alup) | [issue #55](https://github.com/nessenergy/Alupdatalake/issues/55), bloco E do questionário |
| Liberação de VPN, credencial de banco e token de API | Saulo (TI Alup) | dependência **A7**, bloco C |
| Priorização de escopo, regra de negócio, domínios analíticos | Leonardo (PO), com Taina e Mauricio (co-owners) | blocos A, B e D |
| Balanço Energético e o SQL Server que o recebe | Leonardo (PO Alup) | C11 e o adendo ao C4 |
| Cronograma, medição, marcos e relatórios de situação | Gabriel (PMO ness.) e Ricardo | [`plano-semanal.md`](plano-semanal.md), [`relatorios/`](relatorios/) |
| Arquitetura, decisões técnicas, código e entrega | Thiago (líder técnico) e Ricardo | [`arquitetura/decisoes/`](arquitetura/decisoes/) |

---

## Lacunas

Registradas porque cada uma tem efeito prático, e nenhuma se resolve do nosso
lado:

| # | O que falta | Por que importa | Onde é cobrado |
|---|---|---|---|
| 1 | **Substituto do ponto focal técnico** da Alup | se toda liberação de acesso passa por uma única pessoa, uma ausência para o projeto | B2 — marcada `[BLOQUEIA]` |
| 2 | **Matriz RACI e data owners** por domínio | dúvida de regra de negócio hoje não tem destinatário definido | **A5**, prazo 11/09 |
| 3 | **Quem administra o Workload Identity Federation** | é o único item do provisionamento que exige familiaridade com OIDC | E6 |
| 4 | **Quem recebe os alertas** de falha de ingestão | os alertas existem e não notificam ninguém | E3, [issue #87](https://github.com/nessenergy/Alupdatalake/issues/87) |

Preferência registrada para a lacuna 4: **grupo, não pessoa nominal.** Pessoa
sai de férias; grupo não.

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
