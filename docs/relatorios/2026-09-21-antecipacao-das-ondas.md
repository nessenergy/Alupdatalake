---
titulo: Proposta 21/09/2026 — o que podemos antecipar e o que precisamos da Alup
documento: Proposta de antecipação de entregas
referencia: REL-2026-09-21 · AlupData Fase 1
emitido_em: 21 de setembro de 2026
emitente: ness. Processos e Tecnologia Ltda.
destinatario: Alup
contrato: CPS-01025/2026 — AlupData Fase 1: DataLake
marco: Ondas 0 a 4 — antecipação de entregas
responsavel: Ricardo Esper
classificacao: Confidencial — uso restrito das partes
local_data: 21 de setembro de 2026
---

# O que podemos antecipar, e o que precisamos da Alup para isso

## Resumo

Adiantamos tudo que não dependia de insumo: o lake tem **27 conectores**, 24 já
verificados contra a origem real. Propomos **fechar ondas antes das datas do
cronograma** — a cláusula 1ª permite redefinir a sequência, e nada aqui muda
escopo nem valor.

Para isso, o que mais destrava é o **ambiente GCP**: com ele, homologamos as
Ondas 0 e 1 juntas.

## Onde estamos

| Onda | Calendário | Pronto do nosso lado | Falta |
|---|---|---|---|
| **0 — Fundação** | até 11/09 | Tudo | Ambiente GCP |
| **1 — Mercado base** | até 16/10 | Tudo, e mais: 20 conjuntos de CCEE, ONS e ANEEL | Ambiente GCP |
| **2 — APIs com credencial** | 19/10 a 13/11 | Hubspot, BBCE e TempoOK escritos; TempoOK já em uso | Token do Hubspot e acesso do BBCE |
| **3 — Sistemas internos** | 16/11 a 18/12 | Conexão com Oracle, MySQL e SQL Server | Credenciais e rede |
| **4 — Planilhas e handoff** | 21/12 a 08/01 | Motor de planilhas | Planilhas de exemplo |

Nenhuma onda está homologada: homologar exige carga real no ambiente GCP.

## O que podemos antecipar

- **Ondas 0 e 1, juntas**, assim que o GCP existir. Não há desenvolvimento
  pendente em nenhuma das duas.
- **Onda 2 em outubro**, antes de começar formalmente — com o token do Hubspot
  e o acesso do BBCE.
- **Onda 3 pelo MySQL RDS**, que não precisa de VPN. Basta a credencial para
  começar já em outubro.
- **Templates da Onda 4**, assim que chegarem as planilhas de exemplo.

## O que precisamos da Alup

### Ambiente — destrava as Ondas 0 e 1

- Projeto GCP `dev` com os papéis das quatro contas enviadas em 16/09 — [#55](https://github.com/nessenergy/Alupdatalake/issues/55)
- Conta de faturamento vinculada ao projeto — [#87](https://github.com/nessenergy/Alupdatalake/issues/87)

### Acessos — Ondas 2 e 3, prazo 25/09

- Token do Hubspot — [#24](https://github.com/nessenergy/Alupdatalake/issues/24)
- Acesso do BBCE e o endereço do serviço — [#23](https://github.com/nessenergy/Alupdatalake/issues/23)
- Credencial do MySQL RDS, e se a liberação é por lista de IPs — [#14](https://github.com/nessenergy/Alupdatalake/issues/14)
- Oracle FMB: credencial, e se é alcançável sem VPN — [#12](https://github.com/nessenergy/Alupdatalake/issues/12)
- Portal Alup: credenciais e caminho de rede — [#13](https://github.com/nessenergy/Alupdatalake/issues/13)
- RM/TOTVS: endpoints e credencial — [#15](https://github.com/nessenergy/Alupdatalake/issues/15)

### Confirmações e listas

- Fuso da janela de leitura dos sistemas internos (22h às 6h) — [#12](https://github.com/nessenergy/Alupdatalake/issues/12)
- Planilhas de exemplo da proposta — [#142](https://github.com/nessenergy/Alupdatalake/issues/142)
- Siglas internas das usinas com o CEG ao lado, cerca de vinte linhas — [#141](https://github.com/nessenergy/Alupdatalake/issues/141)
- TempoOK: quais arquivos interessam — [#174](https://github.com/nessenergy/Alupdatalake/issues/174)
- RACI: quem compõe o Comitê e o papel do Google — [#150](https://github.com/nessenergy/Alupdatalake/issues/150)

Os acessos e as confirmações cabem numa reunião curta com o Leonardo.

## Credenciais

Com o GCP liberado, a Alup grava cada credencial **direto no Secret Manager**,
sem e-mail — os nomes já estão definidos e ninguém da ness. vê o valor. No mesmo
dia pedimos a rotação do token do TempoOK, que chegou por e-mail em 14/09.

Obrigado pela parceria até aqui: cada insumo enviado foi usado no mesmo dia.
