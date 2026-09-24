# Mensagens de coordenação — aceite conjunto das Ondas 0 e 1

Rascunhos para envio pela coordenação (Ricardo). Três mensagens curtas, para
os dossiês das Ondas 0 e 1, entregues juntos em 29–30/09, e a reunião de
aceite conjunto em ~01/10.

---

## Mensagem 1 — Quem assina o aceite

**Assunto:** AlupData — confirmação de quem assina o aceite das Ondas 0 e 1

**Destinatário sugerido:** Leonardo Marques (PO) — cc: Taina Mota

**Corpo:**

Leonardo, bom dia.

Estamos organizando os dossiês das Ondas 0 e 1 para entrega conjunta em
29–30/09, com reunião de aceite em seguida. Antes de marcar, queremos
confirmar um ponto de forma que a reunião já saia certa.

Na resposta ao questionário de gaps (item B4), a Taina ficou como quem aprova
a homologação de cada onda e assina a medição. Já na matriz RACI que
recebemos depois, "aprovar passagem de fase" aparece como responsabilidade de
um Comitê, sem membros nomeados até aqui.

Para não levar a reunião com essa dúvida em aberto: quem assina o aceite das
Ondas 0 e 1 — a Taina, conforme o B4, ou o Comitê? Se for o Comitê, pedimos os
nomes de quem o compõe, para já incluir na convocação.

Abraço,
Ricardo Esper — ness.

---

## Mensagem 2 — Convite da reunião de homologação

**Assunto:** AlupData — reunião de aceite das Ondas 0 e 1, dossiês em anexo em 29–30/09

**Destinatário sugerido:** Leonardo Marques (PO) — cc: Taina Mota, Mauricio Cardoso

**Corpo:**

Leonardo, bom dia.

Os dossiês das Ondas 0 e 1 ficam prontos em 29–30/09. Para que a reunião seja
uma conferência do que já está no dossiê, e não uma primeira leitura,
adiantamos abaixo a lista de critérios de cada onda — é o que o dossiê vai
demonstrar, ponto a ponto.

Proposta de data: **01/10, das 10h às 11h** (uma hora). Alternativa, se não
couber: **02/10**, mesmo horário. Fica à vontade para sugerir outro horário
nesses dois dias.

**Onda 0 — Fundação (mapeamento de fontes, 8 domínios, dimensões comuns,
CI/CD, portal base):**
- Cada fonte da onda com os sete componentes do contrato: conector, tabela
  Bronze, view Silver, view Gold, testes, agendamento e documentação com
  linhagem
- Dicionário de dados e linhagem atualizados
- Portões de segurança do pipeline (CI) aprovados
- Recursos de nuvem versionados e aplicados no ambiente da onda
- Reprocessamento (replay) demonstrado em pelo menos uma fonte
- Portal com uma consulta real na camada final
- Evidências reunidas: plano de infraestrutura sem alterações pendentes,
  execução completa registrada, agendamento em funcionamento

**Onda 1 — APIs públicas (CCEE InfoMercado, ONS, ANEEL, IBGE, câmbio BCB):**
- As 23 entidades públicas da onda com os sete componentes e execução com
  sucesso
- Portões de segurança do pipeline (CI) aprovados
- Recursos de nuvem versionados e aplicados no ambiente da onda
- Mesmos critérios de dicionário, linhagem, reprocessamento e evidências da
  Onda 0, aplicados a cada fonte da onda
- De-para entre as fontes do contrato e as entidades entregues, para conferir
  escopo por escopo

Qualquer fonte que não constar como pronta vem identificada no próprio
dossiê, com o motivo.

Fico no aguardo da confirmação da data.

Abraço,
Ricardo Esper — ness.

---

## Mensagem 3 — Onda 2: credenciais e as 32h do item 2.1

**Assunto:** AlupData — credenciais da Onda 2 (Hubspot e BBCE) e as 32h do item 2.1

**Destinatário sugerido:** Leonardo Marques (ponto focal técnico de acesso) — cc: Taina Mota

**Corpo:**

Leonardo, bom dia.

Aproveitando o encaminhamento da Onda 1, dois pontos para avançar a Onda 2.

**Credenciais.** Para o Hubspot, precisamos do token; para o BBCE, do acesso
e do host. Como já combinado, pedimos que o grupo da Alup grave os dois
diretamente no Secret Manager, pelo canal já definido entre os times — não
por e-mail. O Gabriel Paz, da ness., está à disposição para apoiar esse
passo, se for útil. Prazo que propomos: **12/10**.

**CCEE agente credenciado (item 2.1, 32h).** Esse item depende de uma
credencial de agente que hoje não temos — é escopo diferente do InfoMercado
público, já entregue na Onda 1. Vemos dois caminhos: (a) solicitar essa
credencial junto à CCEE, ou (b) realocar as 32h para os conjuntos públicos da
CCEE já entregues, o que o contrato permite. Pedimos a posição da Alup **até
30/09, junto com a entrega dos dossiês**; se não for possível até lá,
tratamos na reunião de 01/10.

Abraço,
Ricardo Esper — ness.
