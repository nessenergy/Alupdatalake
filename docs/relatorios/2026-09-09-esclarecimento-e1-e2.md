---
titulo: Registro de esclarecimento 09/09/2026 — AlupData Fase 1
documento: Registro de esclarecimento
referencia: REL-2026-09-09 · AlupData Fase 1
emitido_em: 09 de setembro de 2026
emitente: ness. Processos e Tecnologia Ltda.
destinatario: Alup
contrato: CPS-01025/2026 — AlupData Fase 1: DataLake
marco: Onda 0 · 15,52% · R$ 23.040,00
responsavel: Ricardo Esper
classificacao: Confidencial — uso restrito das partes
local_data: 09 de setembro de 2026
---

# Esclarecimento sobre os itens E1 e E2 do Questionário de Gaps

## 1. Objeto

Registro de dúvida levantada pela Alup em **09/09/2026** a respeito dos itens
**E1** e **E2** do [Questionário de Gaps](../questionario-gaps.md), ambos
integrantes do insumo **A3** (ambiente GCP), e do esclarecimento prestado pela
ness. **na mesma data**.

Este registro existe por uma razão simples: se parte da espera por A3 decorria
de uma dúvida de atribuição, ela não era falta de decisão da Alup — era um
ponto que só precisava ser esclarecido. Convém que fique documentado que a
dúvida surgiu e foi respondida no mesmo dia, tanto para a leitura correta do
prazo quanto para que nenhuma das partes precise reconstituir depois o que se
combinou.

## 2. A dúvida

Em 09/09/2026, a equipe da Alup consultou a ness. sobre dois pontos:

| Item | Pergunta da Alup |
|---|---|
| E1 | Se a criação do projeto GCP `dev` caberia à equipe da ness. ou à própria Alup |
| E2 | Se a conta de faturamento (`billing_account`) seria da ness. ou vinculada a uma conta da Alup |

A dúvida é legítima e a formulação foi oportuna: os dois pontos estão
marcados como bloqueantes no questionário, e é preferível esclarecê-los agora a
descobrir a divergência no momento do provisionamento.

## 3. O esclarecimento prestado

Ambos os itens são de responsabilidade da **Alup**, conforme já registrado na
[issue #55](https://github.com/nessenergy/Alupdatalake/issues/55) e no contrato.

### 3.1 E1 — criação do projeto

A criação do projeto compete a quem administra a organização GCP da Alup. A
ness. não possui — e, pelo desenho de segurança acordado, não deve possuir —
permissão para criar projeto dentro da organização da contratante. O que a
ness. precisa receber é acesso ao projeto já criado, nos papéis descritos na
issue #55.

### 3.2 E2 — conta de faturamento

A `billing_account` é da Alup. A **cláusula 5ª** do contrato CPS-01025/2026
exclui do escopo da ness. os custos de infraestrutura GCP, que correm por conta
da contratante. Não há, portanto, hipótese de vinculação a conta de faturamento
da ness.

### 3.3 Ordem de grandeza do custo, para dimensionar o teto do alerta

Apresentada para auxiliar a definição do teto mensal solicitado em E2:

| Fase | Estimativa mensal |
|---|---|
| Ondas 0 a 2 | US$ 5 a 15 |
| A partir da Onda 3, com orquestração gerenciada | US$ 420 a 500 |

Sugerimos, para o ambiente `dev`, teto de **R$ 500/mês** no alerta de
orçamento. Registramos que orçamento no GCP **avisa, mas não interrompe**
consumo — é instrumento de visibilidade, não de bloqueio.

### 3.4 E3, na mesma linha

Aproveitamos para reiterar o item **E3**: a infraestrutura de alerta de falha
de ingestão está pronta e permanece sem destinatário. Preferencialmente um
grupo, e não endereços individuais, para que a rotatividade de equipe não
interrompa a notificação. Acompanhado na
[issue #87](https://github.com/nessenergy/Alupdatalake/issues/87).

## 4. Efeito sobre os prazos

Nenhum. O esclarecimento não altera a contagem em curso, e registramos isso
com transparência: A3 venceu em **04/09/2026**, 08/09 foi o primeiro dia útil
de atraso e os marcos da cláusula 3ª seguem os já informados no
[relatório de 08/09](2026-09-08-s2-sem-ambiente.md).

O que este documento acrescenta é que a dúvida de atribuição foi levantada e
respondida em 09/09, sem consumo de dia útil adicional.

## 5. Próximo passo proposto

Colocamo-nos à disposição para uma conversa de **30 minutos** com a equipe de
TI da Alup, em que o projeto `dev` seja criado e os acessos concedidos ao vivo,
com a issue #55 aberta como roteiro. É o caminho mais curto entre a decisão e o
ambiente funcionando.

Permanecemos à disposição para qualquer esclarecimento adicional.
