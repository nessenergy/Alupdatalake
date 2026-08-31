# Início da Onda 0 — o que está pronto e o que depende da Alup

**Emitido em** 31/08/2026 · **Para** Grupo Alupar · **Por** ness. Processos e Tecnologia
**Contrato** CPS-01025/2026 — AlupData Fase 1: DataLake
**Marco em jogo** Onda 0 · 15,52% · R$ 23.040,00 · homologação prevista para **11/09/2026**

---

## Em uma frase

A Onda 0 começa hoje com o trabalho técnico da ness. **adiantado** — inclusive
com entregas de ondas posteriores já feitas —, e com o caminho para homologar
**inteiramente dependente de insumo da Alup**, sendo o mais urgente o ambiente
Google Cloud, que vence nesta sexta.

---

## 1. Cronograma: onde estamos

O contrato prevê 19 semanas a partir do kickoff de 27/08/2026. Ancorado nesse
marco e alinhado de segunda a sexta, cada onda termina numa sexta-feira, que
passa a ser a data-alvo de homologação e de medição.

| Onda | Início | Término | Marco | Valor |
|---|---|---|---|---|
| **0 — Fundação** | 31/08/2026 | **11/09/2026** | 15,52% | R$ 23.040,00 |
| 1 — Mercado base | 14/09/2026 | 16/10/2026 | 20,69% | R$ 30.720,00 |
| 2 — APIs credenciadas | 19/10/2026 | 13/11/2026 | 18,97% | R$ 28.160,00 |
| 3 — Sistemas internos | 16/11/2026 | 18/12/2026 | 26,72% | R$ 39.680,00 |
| 4 — Planilhas e handoff | 21/12/2026 | 08/01/2027 | 18,10% | R$ 26.880,00 |

> **Recesso de fim de ano.** A Onda 4 atravessa 25/12 e 01/01. As datas acima
> seguem o cálculo contratual de 19 semanas corridas. Havendo recesso de 21/12
> a 01/01, o marco 5 desloca para **22/01/2027**. Precisa ser combinado.

---

## 2. Entregue

Tudo abaixo está no repositório, com testes automatizados e pipeline verde.

### Framework de ingestão

Um runner único cuida de janela de datas, gravação do dado bruto, validação,
colunas técnicas, carga e registro de execução. Um conector novo implementa
apenas como falar com a fonte. **229 testes automatizados**, cobertura de 92%.

Isso é o que sustenta a promessa de 13 conectores em 19 semanas sem que o
décimo terceiro seja escrito de um jeito diferente do primeiro.

### Conectores — 4 de 5 fontes públicas completas

| Fonte | Volume verificado |
|---|---|
| Câmbio BCB (PTAX) | diário, verificado contra a API real |
| IBGE (IPCA) | mensal, JSON aninhado |
| ANEEL (SIGA) | **25.263 registros**, zero inválidos, 28 segundos |
| ONS (carga) | CSV anual por subsistema |
| Hubspot | os 7 componentes prontos; **nunca executado** — falta o token (A9) |

As quatro primeiras foram verificadas contra as APIs reais em modo de simulação.

### Entregas adiantadas de ondas posteriores

Feitas porque não dependiam de insumo da Alup e reduzem risco mais adiante:

- **Motor de ingestão de planilhas** (escopo da Onda 4)
- **Caminho de acesso a bancos Oracle e MySQL** (escopo da Onda 3) — quando a
  VPN chegar, a tarefa é apontar a conexão, não começar a Onda 3
- **Portal MVP** com painel de saúde e de custo de nuvem
- **Reprocessamento** de dado já coletado, sem consultar a fonte de novo

### Segurança (cláusula 8ª)

- SAST (Bandit), SCA (pip-audit) e varredura de segredos (Gitleaks) em todo PR
- Credenciais exclusivamente no Secret Manager
- **Permissões restringidas por recurso**: a conta de serviço de ingestão
  acessa apenas o conjunto de dados, o bucket e os segredos de que precisa —
  não o projeto inteiro
- Remoção automática de credencial de registros de log e de mensagens de erro

---

## 3. O que trava a homologação da Onda 0

Nada nesta lista depende de trabalho da ness.

| # | Insumo | Prazo | Efeito de passar do prazo |
|---|---|---|---|
| **A3** | Projeto GCP `dev`: criar, habilitar APIs, IAM, federação de identidade, Artifact Registry e bucket de estado | **04/09** | nada sobe; as semanas de 07/09 e 14/09 escorregam inteiras |
| **A4** | Questionário de Gaps respondido | 11/09 | sem os 8 domínios analíticos, a camada de consumo fica sem alvo |
| **A5** | Matriz RACI e responsáveis por domínio | 11/09 | dúvida de regra de negócio sem destinatário |
| **A6** | Ferramenta de BI definida | 11/09 | Portal e camada Gold sem consumidor definido |
| **A9** | Token do Hubspot | 11/09 | conector pronto segue parado |
| — | Destinatários de alerta e conta de faturamento | 11/09 | alertas existem e não notificam ninguém |

### O ponto mais importante deste relatório

**Nada foi validado contra um Google Cloud real.** Não houve um único
`terraform apply`, nenhuma linha gravada em BigQuery, nenhum job executado em
nuvem. Todo o trabalho descrito na seção 2 foi verificado localmente.

O primeiro contato com o ambiente real é onde aparecem os erros que teste local
não pega: permissão insuficiente, cota de API, formato que o BigQuery recusa.
Por isso a ness. registra que **a Onda 0 não deve ser declarada homologada
antes de o ambiente existir e a primeira carga rodar de ponta a ponta**.

O caminho crítico inteiro passa por A3, com vencimento nesta sexta.

---

## 4. Questionário de Gaps — emitido hoje

As 47 perguntas foram entregues nesta data, em 7 blocos, com prazos escalonados
por dependência em vez de um prazo único:

| Bloco | Assunto | Prazo |
|---|---|---|
| E | Ambiente Google Cloud | **04/09** |
| A, B, D, F, G | Domínios, responsáveis, regras de negócio, LGPD, BI | 11/09 |
| C4 | Decisão sobre a CCEE | 18/09 |
| C | Fontes internas e acessos | 25/09 |

Doze perguntas estão marcadas como bloqueantes: travam trabalho já contratado e
parado. Se um bloco inteiro não puder ser respondido no prazo, são elas que
importam.

**"Não sei" é resposta válida e desejada.** O objetivo do instrumento é
localizar lacunas, não coletar respostas completas.

---

## 5. Questões abertas

Todas com issue de acompanhamento, conforme a convenção deste projeto.

| # | Questão | Quem decide | Prazo |
|---|---|---|---|
| [#55](https://github.com/nessenergy/Alupdatalake/issues/55) | Provisionamento do ambiente GCP (A3) | Alup | **04/09** |
| [#67](https://github.com/nessenergy/Alupdatalake/issues/67) | **Região do ambiente**: `us-east1` ou `southamerica-east1` | Alup (pergunta E7) | antes do primeiro apply |
| [#8](https://github.com/nessenergy/Alupdatalake/issues/8) | Questionário de Gaps respondido (A4) | Alup | 11/09 |
| [#9](https://github.com/nessenergy/Alupdatalake/issues/9) · [#10](https://github.com/nessenergy/Alupdatalake/issues/10) | RACI e ferramenta de BI (A5, A6) | Alup | 11/09 |
| [#52](https://github.com/nessenergy/Alupdatalake/issues/52) | CCEE responde 403 a acesso automatizado (A2) | Alup | 18/09 |
| [#12](https://github.com/nessenergy/Alupdatalake/issues/12) a [#15](https://github.com/nessenergy/Alupdatalake/issues/15) | Tokens e VPN das Ondas 2 e 3 (A7) | Alup | 25/09 |
| [#68](https://github.com/nessenergy/Alupdatalake/issues/68) | **Revisão obrigatória na branch principal** | **ness.** | antes da homologação |

### Duas questões novas, levantadas hoje

**Região do ambiente ([#67](https://github.com/nessenergy/Alupdatalake/issues/67)).**
A configuração atual aponta para os Estados Unidos; a pergunta E7 do
questionário assume São Paulo. Conjunto de dados do BigQuery **não muda de
região depois de criado** — corrigir mais tarde significa apagar, recriar e
recarregar. Sob a LGPD isso é residência de dado, não apenas latência. A
recomendação técnica da ness. é `southamerica-east1`.

**Revisão obrigatória na branch principal ([#68](https://github.com/nessenergy/Alupdatalake/issues/68)).**
Questão da ness., registrada aqui por transparência: o plano atual do GitHub
não permite exigir revisão antes de integrar código. O pipeline de segurança
roda em toda proposta de mudança, mas não bloqueia. Será resolvido por
mudança de plano ou por aceite formal de risco antes da homologação.

---

## 6. Efeito contratual — cláusula 3ª

Registrado porque a cláusula exige que a data do pedido conste do dia em que o
atraso começa, não do dia em que vira problema.

| Situação | Efeito |
|---|---|
| Atraso > 5 dias úteis em qualquer insumo | cronograma postergado automaticamente |
| Atraso > 5 dias úteis em VPN ou credencial | taxa de ociosidade de 4h/dia (R$ 256/h) |
| Atraso > 20 dias corridos | suspensão automática dos serviços |

O risco financeiro concentra-se em **A7** (tokens e VPN, prazo 25/09). Como o
caminho técnico de acesso a bancos já está pronto, o tempo perdido ali deixou
de ser desenvolvimento pendente e passou a ser ociosidade — que é exatamente o
que a cláusula precifica. **Abrir os pedidos internos agora**, mesmo para
acesso que só será usado em novembro, é a única mitigação disponível.

---

## 7. O que pedimos nesta semana

1. **Uma data para o ambiente GCP, com o nome de quem provisiona.** Não uma
   estimativa. Todo o cronograma pendura nela, e o prazo é sexta.
2. **Resposta ao bloco E do questionário até 04/09**, mesmo que os demais
   blocos venham depois — ele é pré-requisito de todo o restante.
3. **Abertura imediata dos pedidos de token e VPN** das Ondas 2 e 3.
4. **Confirmação da região** e da existência ou não de recesso de fim de ano.

---

*ness. Processos e Tecnologia Ltda. · CNPJ 72.027.097/0001-37*
*Situação corrente e viva em [`docs/status.md`](../status.md); este documento é um retrato de 31/08/2026 e não será editado.*
