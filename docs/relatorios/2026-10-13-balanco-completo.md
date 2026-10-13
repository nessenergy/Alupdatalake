# Balanço completo do projeto — 13/10/2026

Relatório interno da ness. Cada número vem de um comando ou documento citado; o que não foi medido está marcado. Contrato
CPS-01025/2026, 580 h, kickoff em 27/08, término previsto em 08/01/2027.

## 1. Em uma tela

| | Situação em 13/10 |
|---|---|
| Aceitas pela Alup | **Ondas 0 e 1**, por escrito, em 05/10 ("Medições aprovadas", Eduardo Pires). Marcos 1 e 2: R$ 53.760,00 de R$ 148.480,00 (36,2%). Faturamento confirmado pela ness. no mesmo dia |
| Progresso de horas | **343,8 de 580 h (59,3%)**, calculado de `painel/marcos.toml` (fração pronta de cada item × horas). Não é métrica de medição |
| Próximo prazo da Alup | **19/10**: tokens e APIs da Onda 2 (CCEE, BBCE, Hubspot, TempoOK). Faltam 4 dias úteis |
| Próximo prazo da ness. | Onda 2 (19/10 a 13/11) e fim da janela contratual da Onda 1 (16/10, já aceita) |
| Credenciais da Onda 2 | **Nenhuma útil em dev.** Teste de 13/10: BBCE sem versão no segredo; Hubspot com segredo, mas 401; TempoOK funciona (token de 14/09) |
| Estado técnico | 58 conectores registrados, **58 com os 7 componentes presentes** (conferido por script, abaixo). Testes do CI: 1.448 coletados, cobertura de linhas **95,59%** (5.157 de 5.395, artefato do run `38477573646`). Conferência de 13/10 em dev, depois dos testes de credencial: 55 OK, **2 SEM_SUCESSO (`bbce_curva_forward`, `hubspot_negocios`)** e **1 ATRASADA (`tempook_boletins`, último sucesso em 24/09)**. hml: 54 OK e 1 SEM_SUCESSO **ainda sem nome** (a conferência nominal depende do PR #385 na `main`) |
| Alerta aberto | SCA vermelho desde 12/10 (werkzeug 3.1.8, CVE-2026-102598, corrigido na 3.1.9). Cláusula 8ª exige Alta/Crítica corrigida antes da homologação |
| Produção | **Não existe.** O bootstrap esperava o aceite, que ocorreu em 05/10 |

## 2. Avaliação por entrega

Critério único, de cima para baixo. Uma entrega fica no primeiro nível que satisfaz:

- **A. Aceita:** a Alup aprovou por escrito.
- **B. Entregue e conferida:** 7 componentes e carga consultada no BigQuery (`Conferir cargas`), sem aprovação formal própria.
- **C. Escrita, sem carga real:** 7 componentes no repositório, sem a credencial para rodar.
- **D. Não entregue:** falta componente, origem ou decisão.

### Onda 0 — 90 h — marco 1 (R$ 23.040,00) — **A. Aceita em 05/10**

| Item | h | Nível | Evidência / ressalva |
|---|---:|---|---|
| 0.1–0.8 Framework, CLI, Terraform, CI/CD, ADRs | 40 | A | no repositório; dossiê de 25/09 |
| 0.9–0.11 Questionário, 8 domínios, dimensões | 24 | A | respondido em 11/09; domínios em `arquitetura/dominios-analiticos.md` |
| 0.12 RACI | 4 | A, com ressalva | recebida em 15/09; dois pontos abertos (#150) |
| 0.13–0.14 Ambiente GCP e deploy real | 14 | A | dev em 23/09; BCB com 3 dias consecutivos |
| 0.15 Portal MVP | 8 | A, com ressalva | no ar em dev e hml; primeiro login efetivo da Alup não registrado |

Prazo: contratual 11/09; postergado para 30/09 por A3 (GCP liberado em 23/09, 19 dias). Aceito em 05/10.

### Onda 1 — 120 h — marco 2 (R$ 30.720,00) — **A. Aceita em 05/10**, com itens da cláusula 4ª fora do aceite explícito

A aprovação de Eduardo respondeu ao e-mail da ness. de 05/10, que tratava das três cargas que ele citou (IGP-M, Tarifas Homologadas, PRC). Os itens abaixo da cláusula 4ª **não foram citados** e seguem sem entrega:

| Cláusula 4ª | Nível | Evidência |
|---|---|---|
| 1 ONS Core (EAR, ENA, PLD, Carga) | A | 7 componentes; cargas conferidas |
| 2 ONS Operacional (IPDO e ACOMPH) | **D, parcial** | só `ons_demanda_maxima` (seção 7 do IPDO) entregue; IPDO e ACOMPH dependem de aceite da ADR 027 |
| 3 ANEEL (tarifas, PRC) | B | Silver 327.763 linhas; Gold 10.366; PRC 24; dev = hml |
| 4 INMET por bacia | B, com regra provisória | Silver 10.332.120 linhas, 654 estações, 25 bacias; média e corte de distância sem aceite (ADRs 026) |
| 5 CPTEC | **D** | 403 mesmo de dentro do GCP; ADRs 028 e 029 |
| Proposta IGP-M | B | 25 meses; 3 últimos iguais ao BCB |

Aditivo 01 (fora das 580 h): **162 de 162 h** apontadas, itens 1 a 25, evidência na §5 do documento do aditivo. Item 26 fora do estimado (~185 GB, §4.1).

### Onda 2 — 110 h — marco 3 (R$ 28.160,00) — janela 19/10 a 13/11 — **C no que existe; D no item 2.1**

| Item | h | Nível | Situação em 13/10 |
|---|---:|---|---|
| 2.1 CCEE agente credenciado | 32 | **D** | nenhum arquivo; aguarda a posição da Alup (#260, vencida em 30/09) |
| 2.2 BBCE | 28 | C | segredo `alupdata-bbce-credenciais` sem versão em dev (teste de 13/10) |
| 2.3 Hubspot | 20 | C | segredo com versão, 401 do Hubspot (token inválido ou sem escopo) |
| 2.4 TempoOK | 18 | C, ENA em B | previsão de ENA carrega em dev; boletim sem acervo desde 26/10/2022 (#129); hml sem token (ADR 020) |
| 2.5 Gold de preço e posição | 12 | **D, escopo** | só existe a frase do contrato; Golds de preço e posição já existem, mas ninguém definiu se atendem |

### Onda 3 — 155 h — marco 4 (R$ 39.680,00) — janela 16/11 a 18/12 — **D**

Rede do lado GCP pronta (ADR 024). Em 07/10, Jefferson relatou o IP do servidor interno, 10.18.0.145, vindo do Leonardo (primeiro item do passo a passo de 29/09). Faltam rota, FortiGate, datacenter, listener e **todas as credenciais**. Cloud Workflows (3.5) escrito, sem uso. Nenhum conector das 4 fontes internas existe.

### Onda 4 — 105 h — marco 5 (R$ 26.880,00) — janela 21/12 a 08/01/2027

Motor de planilhas pronto; **sem templates** (#142, prazo movido por acordo para perto da Onda 4). Knowledge Catalog concluído (4.3); Gold consolidadas e documentação final parciais; handoff com runbook de incidente.

## 3. Prazos realinhados

| Data | Evento | Dono | Estado |
|---|---|---|---|
| 05/10 | Ondas 0 e 1 aprovadas | Alup | feito |
| 16/10 | Fim da janela contratual da Onda 1 | — | Onda já aceita |
| **19/10** | **Tokens da Onda 2 (contrato)** | Alup | aberto; nada útil em dev |
| 19/10 | Início da Onda 2 | ness. | começa sem credencial |
| 04/11 | Fim da garantia de 30 dias das Ondas 0 e 1 (aceite de 05/10) | — | corre |
| 13/11 | Homologação da Onda 2 | — | depende de 19/10 e de 2.1 |
| 16/11 | VPN e credenciais da Onda 3 | Alup | rede parcial; sem credencial |
| 18/12 | Homologação da Onda 3 | — | depende de 16/11 |
| 21/12 | Planilhas da Onda 4 | Alup | prazo movido por acordo |
| 08/01/2027 | Homologação da Onda 4 e handoff | — | 22/01 se houver recesso |

Pela cláusula 3ª, em contagem simples e só como registro: se os tokens não chegarem até 19/10, o atraso passa de 5 dias úteis em 27/10 (cronograma posterga) e de 20 dias corridos em 09/11 (suspensão). A decisão de cobrar, postergar ou suspender é do Ricardo.

## 4. Pendências e riscos, por dono

**Alup:**
- credenciais da Onda 2, com BBCE ausente e Hubspot recusado (#262);
- posição sobre as 32 h do item 2.1 (#260);
- quem assina o aceite (#258);
- rota, FortiGate, datacenter e credencial do FMB;
- planilhas (#142) e de-para de usina (#141);
- aceite das ADRs 026 a 029 e do corte de distância da bacia;
- Leonardo pediu acesso ao Bronze; assuntos de DECOMP e NEWAVE vieram à tona na reunião. O aditivo 01 os deixa fora da estimativa (§6) até haver desenho próprio.

**ness. (decisão do Ricardo):**
- bootstrap de produção, agora liberado pelo aceite de 05/10;
- T5 a T7 do plano de débitos;
- chave do GitHub App do quadro, ainda sem versão no segredo;
- PR #383 (Bronze em hml); falta a linha de `dev.tfvars`;
- werkzeug 3.1.9 para zerar o SCA;
- rascunhos sem envio: cobrança das credenciais (05/10, perdeu a razão de ser em parte) e resposta a Jefferson (08/10).

**Técnicos:**
- carga parcial por tempo limite não aparece na saúde (fila 1.14);
- 554 testes ignorados sem motivo catalogado (T5);
- a fonte em SEM_SUCESSO de hml não foi nomeada: o item `saude_fora_do_ok` do PR #385 só roda em hml depois de entrar na `main`, porque a proteção do ambiente recusa a branch;
- SCA vermelho por werkzeug 3.1.8: correção no PR #386 (3.1.9), com CI verde.

## 5. Como foi medido

- Horas: soma de horas × fração pronta de `painel/marcos.toml`, com `0.14` em 100% (3 dias seguidos de carga).
- 7 componentes: script sobre o registro do código (`carregar_conectores`) conferindo a existência de Bronze, Silver, Gold que cita o rótulo, teste, agendamento e dicionário. **É verificação de existência, não de qualidade**; a carga é conferida em separado pelo `Conferir cargas`.
- Conferência de dev e hml em 13/10: runs `38467092766` e `38467098953` (só contagem por situação). Fontes nomeadas em dev pela run `38477711568`, com o item `saude_fora_do_ok` do PR #385: `bbce_curva_forward` (segredo sem versão), `hubspot_negocios` (401) e `tempook_boletins` (ATRASADA, 24/09). A run de hml, `38477714404`, foi recusada pela proteção do ambiente.
- Credenciais: ingestões de teste em dev, 13/10, janela 12 a 13/10: Hubspot `38468669196`, BBCE `38468673738`, TempoOK `38468678153`.
- Testes e cobertura: CI do run `38477573646`, `pytest tests/ --cov=src`: 1.448 testes coletados, 95,59% de cobertura de linhas. Não contei os ignorados.
- Não medido: o conteúdo dos segredos, os testes ignorados e a fonte em SEM_SUCESSO de hml.
