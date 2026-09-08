---
titulo: Relatório de situação 08/09/2026 — AlupData Fase 1
documento: Relatório de situação
referencia: REL-2026-09-08 · AlupData Fase 1
emitido_em: 08 de setembro de 2026
emitente: ness. Processos e Tecnologia Ltda.
destinatario: Alup
contrato: CPS-01025/2026 — AlupData Fase 1: DataLake
marco: Onda 0 · 15,52% · R$ 23.040,00
responsavel: Ricardo Esper
classificacao: Confidencial — uso restrito das partes
local_data: 08 de setembro de 2026
---

# A semana do primeiro deploy sem o ambiente, e uma correção no nosso quadro

Prezados,

Este relatório cobre o primeiro dia útil da semana **S2 (07/09 – 11/09)**, que o
plano reservava para o primeiro deploy real, e registra três coisas: o estado do
insumo **A3**, os prazos que vencem em 11/09 e uma **correção que fizemos no
nosso próprio quadro de acompanhamento**, que vinha superestimando o avanço do
projeto.

O terceiro ponto é o que mais nos importa comunicar hoje. A informação errada
estava a nosso favor, foi encontrada por nós e está corrigida — mas ela chegou a
ficar visível, e vocês precisam saber disso antes que qualquer número seja levado
à diretoria.

---

## 1. O insumo A3 segue pendente

O ambiente GCP `dev` tinha prazo útil em **04/09/2026** e não foi
disponibilizado até hoje. O registro do atraso foi emitido na própria data, em
[relatório de 04/09](2026-09-04-a3-nao-entregue.md), e a situação não mudou
desde então.

Como 05 e 06 recaíram sobre o fim de semana e 07 foi feriado nacional, **hoje é
o primeiro dia útil de atraso**. Não houve, portanto, perda de tempo útil entre
um relatório e outro, razão pela qual o assunto pode ser tratado agora sem
caráter de urgência.

A pendência **G1**, resposta do Google à revisão arquitetural que enviamos em
04/09, permanece **sem prazo acordado**
([issue #77](https://github.com/nessenergy/Alupdatalake/issues/77)). Como a Alup
optou por condicionar A3 a G1, a cadeia continua em série:

    G1 (Google responde) → A3 (ambiente GCP) → 1º apply → Onda 0 homologada

Seguimos considerando a escolha defensável: é preferível receber a análise
antes de instanciar o ambiente do que depois dele constituído. O que
solicitamos é que G1 receba uma data definida, qualquer que seja. Uma previsão
distante permite planejamento; a ausência de previsão, não.

## 2. O que a S2 previa, e o que acontece sem o ambiente

O plano semanal condiciona integralmente esta semana à disponibilização de A3.
Todo o conteúdo previsto depende do ambiente:

| Item previsto para a S2 | Situação |
|---|---|
| `terraform apply` real — datasets, bucket, secrets, IAM, Cloud Run Job, Scheduler | postergado |
| Imagem da CLI no Artifact Registry e job executado contra o BCB | postergado |
| `make deploy-views` — views Silver e Gold das 5 fontes aplicadas no ambiente | postergado |
| Hubspot executado contra a API real | depende de A9 |
| Destinatários de alerta e `billing_account` preenchidos | depende da Alup |

Enquanto o ambiente não existir, esta frente não produz entregável verificável.
Temos redirecionado o tempo para trabalho que não depende de insumo — foi assim
que quatro das cinco ondas chegaram a ter entrega —, mas a reserva de trabalho
independente de insumo é limitada e já se encontra substancialmente consumida.

## 3. Contagem de prazos da cláusula 3ª

Registramos as datas para que os dois lados tenham o mesmo quadro, não para
formalizar cobrança:

| Marco da cláusula 3ª | Data | Efeito |
|---|---|---|
| 1º dia útil de atraso de A3 | **08/09** (hoje) | contagem em curso |
| 5º dia útil | **14/09** | a partir daí, postergação dos prazos que dependem de A3 |
| 20 dias corridos | **24/09** | hipótese de suspensão dos serviços |

Vale repetir o que dissemos em 04/09: condicionar A3 a G1 não interrompe a
contagem, porque o contrato considera o atraso do insumo e não o seu motivo.
Isso não é uma objeção à decisão de aguardar o Google — é o registro que
protege os dois lados na medição.

## 4. Os prazos que vencem em 11/09

Faltam **três dias úteis** para cinco itens:

| # | Item | Efeito da não disponibilização | Issue |
|---|---|---|---|
| A4 | Questionário de Gaps respondido (47 perguntas) | os 8 domínios analíticos não se definem, e a camada Gold fica sem alvo | [#8](https://github.com/nessenergy/Alupdatalake/issues/8) |
| A9 | Token do Hubspot | o conector concluído permanece sem execução; nenhum registro de CRM é ingerido | [#11](https://github.com/nessenergy/Alupdatalake/issues/11) |
| A5 | Matriz RACI e data owners | questões de regra de negócio ficam sem destinatário definido | [#9](https://github.com/nessenergy/Alupdatalake/issues/9) |
| A6 | Ferramenta de BI definida | Portal MVP e views Gold ficam sem consumidor definido | [#10](https://github.com/nessenergy/Alupdatalake/issues/10) |
| — | Destinatários de alerta e `billing_account` | alertas e orçamento estão configurados, porém sem destinatário definido | [#87](https://github.com/nessenergy/Alupdatalake/issues/87) |

Chamamos atenção especial para **A4**. Ele é o único da lista que **não depende
do ambiente GCP**: mesmo que A3 e G1 se resolvam amanhã, sem as respostas do
questionário a semana S3 não tem conteúdo, porque não há alvo para a camada
Gold. A4 é, hoje, o insumo com melhor relação entre esforço de vocês e
volume de trabalho liberado do nosso lado.

## 5. Correção no quadro de acompanhamento

Em 24/08, ao popular o GitHub Projects, uma carga automática foi executada duas vezes e
criou **15 itens duplicados**. Em 27/08 fizemos a limpeza fechando uma cópia de
cada par — e é neste ponto que se produziu o erro: no GitHub Projects, **issue fechada conta
automaticamente como entrega concluída**. A limpeza produziu 15 conclusões que
não correspondiam a trabalho realizado.

O efeito era material. O quadro exibia **24 entregas quando o realizado eram
9**, e apresentava as Ondas 3 e 4 como tendo itens concluídos — incluindo
conectores de sistemas internos cujas credenciais sequer chegaram.

**Corrigido hoje.** Os 15 itens duplicados foram arquivados; o quadro passou de
58 para 43 itens e de 24 para **9 conclusões**, que são as reais. Uma décima
foi registrada ainda hoje, com o registro da decisão tratada na seção 6:

| Entrega concluída | Onda |
|---|---|
| Setup Terraform — módulos base | 0 |
| CI/CD em GitHub Actions | 0 |
| Documentação da arquitetura Medallion | 0 |
| Conector Câmbio BCB, de referência | 0 |
| Conectores ONS, ANEEL e IBGE | 1 |
| Decisão de região do ambiente (ADR 009) | 0 |
| Campos de acompanhamento semanal do quadro | 0 |
| Registro da decisão sobre revisão obrigatória na `main` (ADR 010) | 0 |

Nenhuma issue foi excluída e o arquivamento é reversível — o histórico está
íntegro para auditoria.

Duas observações que consideramos devidas. A primeira: o erro favorecia a
ness., e foi encontrado e corrigido por nós, sem que houvesse apontamento externo.
A segunda: ele demonstra por que o campo **Validado** existe no quadro. Entrega
técnica não é homologação. **Nenhum dos itens acima foi conferido pela Alup** —
todos estão marcados `Validado = Não` no quadro, e nenhum deles deve ser interpretado
como onda encerrada.

## 6. Registro sobre a cláusula 8ª

A `main` deste repositório não pode ter revisão obrigatória: o plano GitHub da
organização não oferece o recurso. O CI executa SAST e SCA em toda alteração —
Ruff, pytest, Bandit, pip-audit, Gitleaks e Terraform, sete verificações —, mas
não impede um envio direto.

Registramos formalmente a decisão em ADR, com os gatilhos que a reabrem, e
consignamos aqui o que dela decorre: **o dossiê de homologação da Onda 0 não
afirmará que existe barreira preventiva de SAST e SCA**. Descreverá o arranjo
real — varredura sistemática em toda alteração, mais o aceite de risco
registrado. Preferimos a descrição exata a uma afirmação confortável.

## 7. O outro lado do quadro

Este relatório trata de um atraso e de uma correção desfavorável a nós. Cabe,
por isso, repetir o dado que a leitura isolada esconde: **a entrega segue
adiantada em relação ao cronograma contratual**.

| Onda | Janela contratual | O que já existe |
|---|---|---|
| **1** — Mercado base | 14/09 – 16/10 | **4 de 5 fontes completas**, com os 7 componentes cada: BCB/PTAX, IBGE/IPCA, ANEEL/SIGA (25.263 registros verificados, 0 inválidos) e ONS/carga. Resta a CCEE, bloqueada na origem |
| **2** — APIs credenciadas | 19/10 – 13/11 | **Hubspot completo**, os 7 componentes, escritos antes do token |
| **3** — Sistemas internos | 16/11 – 18/12 | **Caminho de acesso a bancos concluído** — Oracle, MySQL e SQL Server |
| **4** — Planilhas e handoff | 21/12 – 08/01 | **Motor de ingestão de planilhas** concluído; templates dependem de A4 |

Com a ressalva que fazemos desde o início e que a correção da seção 5 só torna
mais importante: **nada foi validado contra um ambiente GCP real**, porque ele
ainda não existe. Onda 0 não deve ser declarada homologada antes do primeiro
`apply` e da primeira carga real.

## 8. O que pedimos

1. **Uma data para G1**, ainda que distante — [issue #77](https://github.com/nessenergy/Alupdatalake/issues/77).
2. **A4 respondido até 11/09** — é o insumo que libera mais trabalho com menor esforço,
   e o único que não depende do ambiente.
3. **A3 provisionado** assim que a resposta do Google permitir — [issue #55](https://github.com/nessenergy/Alupdatalake/issues/55).
4. **A9, A5 e A6 até 11/09**, conforme a seção 4.
5. **Decisão sobre a CCEE até 18/09** — 32 horas da Onda 1 permanecem sem execução
   ([issue #52](https://github.com/nessenergy/Alupdatalake/issues/52)).

Permanecemos à disposição para tratar de qualquer ponto deste registro, e
agradecemos a atenção de sempre.

---

*Situação corrente em [`../status.md`](../status.md). Questões abertas
acompanhadas na [issue #57](https://github.com/nessenergy/Alupdatalake/issues/57).*
