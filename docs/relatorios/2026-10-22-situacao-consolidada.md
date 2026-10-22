# Situação consolidada do projeto — 22/10/2026

Relatório interno da ness. Dado técnico e de andamento. Cada número leva a data e a fonte; o que não foi medido está dito. A visão de uma página está em [`docs/visao-consolidada.md`](../visao-consolidada.md).

## 1. Resumo

- **Ondas 0 e 1 aprovadas por escrito em 05/10.** As Ondas 2, 3 e 4 seguem em andamento, cada uma esperando respostas pontuais da Alupar.
- **Onda 2:** o Hubspot passou a carregar dado real em dev e hml em 22/10, depois que o token do aplicativo privado foi gravado. O BBCE continua sem credencial. O TempoOK saiu do escopo como fonte do lake (comunicado em 20/10). A CCEE credenciada ainda não tem nenhum código.
- **Onda 3:** dos três bancos, **dois conectam** (MySQL Comercialização e MySQL Alup) e **um não** (FMB, Oracle, que passa pela DCIDE). Faltam os esquemas das bases para escrever os conectores.
- **Código:** 58 conectores com os 7 componentes presentes, 2.013 testes aprovados e cobertura de 96%. A varredura de dependências está verde.
- **Saúde:** dev com 56 fontes OK e hml com 55; as não-OK são explicadas (seção 5).

## 2. Avaliação por onda

Critério único, de cima para baixo. Cada item fica no primeiro nível que satisfaz:

- **A. Aceita:** aprovada por escrito pela Alupar.
- **B. Conferida:** 7 componentes e carga consultada no BigQuery, sem aprovação própria.
- **C. Escrita, sem carga real:** 7 componentes no repositório; falta a credencial ou o acesso.
- **D. Não entregue:** falta componente, origem ou decisão.

### Onda 0 — Fundação e arquitetura: **A**

Aprovada em 05/10 (Eduardo Pires). Framework de ingestão, CLI, Terraform, CI, ambientes dev e hml, Portal e os 8 domínios analíticos.

### Onda 1 — Inteligência de mercado base: **A**, com itens fora do aceite explícito

Aprovada em 05/10. O aceite respondeu às três cargas que a Alupar citou (IGP-M, Tarifas Homologadas, PRC). Seguem sem entrega, e por isso rastreados:

| Item da cláusula 4ª | Nível | Situação |
|---|---|---|
| ONS Core, ANEEL, INMET, IGP-M | B | cargas conferidas em dev e hml |
| ONS Operacional (IPDO e ACOMPH) | D, parcial | só a demanda máxima existe; IPDO e ACOMPH dependem de aceite da ADR 027 |
| CPTEC | D | 403 mesmo de dentro do GCP (ADRs 028 e 029) |

A regra da média de chuva por bacia e o corte de distância (ADR 026) seguem sem aceite da Alupar.

### Onda 2 — APIs com credenciais (19/10 a 13/11)

| Item | Nível | Situação em 22/10 |
|---|---|---|
| 2.1 CCEE credenciado | **D** | nenhum arquivo. Em 20/10 a Alupar informou que tem dois tipos de acesso: usuário, senha e certificado, ou token de API. Falta escolher o caminho e confirmar o escopo (#260) |
| 2.2 BBCE | **C** | o segredo não tem versão. O formato está definido (JSON com `base_url`, `company_external_code`, `email`, `password` e `api_key`). O e-mail que o pede ao Leonardo **ainda não foi enviado** |
| 2.3 Hubspot | **B, a fechar** | carga executada com sucesso em dev e hml em 22/10 (runs `39776552963` e `39776564873`), e a fonte saiu da lista de não-OK. **Não medi** a quantidade de linhas: a ferramenta de leitura do BigQuery não tem permissão no projeto |
| 2.4 TempoOK | **fora do escopo** | o Leonardo respondeu em 20/10, pelo Gabriel, que sai "integralmente do escopo como fonte para o lake". Os 7 componentes existem no código e a previsão de ENA ainda carrega em dev. **Confirmação por escrito pendente** |
| 2.5 Gold de preço e posição | **D, escopo** | só existe a frase do contrato; as Golds de preço e posição existem, mas ninguém definiu se atendem ao item |

### Onda 3 — Sistemas internos (16/11 a 18/12)

| Item | Nível | Situação |
|---|---|---|
| 3.1 Oracle FMB | **C** | credencial recebida e lida. O teste de conexão expira (22/10): falta o caminho de rede até a DCIDE. Relato de 20/10 de que a VPN foi resolvida; **o teste de 22/10 ainda não confirma** |
| 3.2 DB Alup (MySQL) | **C** | **conecta** (teste de 22/10). O conector não existe: falta o esquema das tabelas |
| 3.3 MySQL Comercialização | **C** | **conectou** em 19/10, com TLS verificado, em duas tentativas. Falta o esquema (#14) |
| 3.4 RM/TOTVS | **D** | consumo só por webservice, segundo o Thiago (20/10). Faltam endpoints e credencial |
| 3.5 Cloud Workflows | **B** | mecanismo pronto e validado; sem uso até haver fonte interna ingerida |
| 3.6 Gold interno × mercado | **D** | depende dos dados internos |

### Onda 4 — Planilhas, governança e handoff (21/12 a 08/01/2027)

| Item | Situação |
|---|---|
| 4.1 Motor de planilhas | motor pronto. A Alupar aceitou a pasta do Google Drive (15/10); o leitor do Drive não existe. Faltam os modelos de planilha (#142) |
| 4.3 Knowledge Catalog | concluído |
| 4.5 Documentação final | dicionário das 58 fontes conferido contra o registro (57 documentos e 2 técnicos). Completa para o que existe; as fontes das Ondas 2 e 3 ainda não implementadas não têm dicionário |
| 4.6 Handoff | runbooks de incidente e de conferência e sondas escritos |

## 3. Credenciais e conexões (teste de 19 e 22/10, em dev)

| Fonte | Credencial | Conexão ou carga | Nota |
|---|---|---|---|
| Hubspot | gravada, token de aplicativo privado | **carga OK** (dev e hml) | corrigido pela Alupar em 20/10 |
| MySQL Comercialização | gravada | **conecta** (19/10) | exigiu corrigir a imagem (ver seção 6) |
| MySQL Alup | gravada | **conecta** (22/10) | o IP de saída está liberado |
| FMB (Oracle) | gravada | **expira** | falta o caminho até a DCIDE |
| BBCE | **não gravada** | não testável | aguarda o formato |
| ONS | a gravar | não testável | usuário e senha de um usuário sem vínculo a pessoa |
| CCEE credenciado | a gravar | não testável | a definir entre usuário, senha e certificado, ou token de API |
| TempoOK | fora do escopo | n/a | |

## 4. Qualidade do código

Medido em 22/10, localmente, com `uv sync --frozen --extra dev --extra bancos` e `uv run pytest tests/ --cov=src`.

| Medida | Valor |
|---|---|
| Conectores registrados | **58**, todos com Bronze, Silver, Gold, teste, agendamento e dicionário presentes (verificação de existência, não de qualidade) |
| Distribuição | ONS 29, CCEE 17, BCB 3, ANEEL 2, TempoOK 2, e um de cada: ACE, BBCE, Hubspot, IBGE, INMET |
| Testes | **2.013 aprovados** e 558 ignorados (2.010 antes dos 3 testes novos do `make componentes`, que entram neste mesmo PR) |
| Cobertura de linhas | **96%** (5.399 linhas, 238 sem cobertura) |
| Código | 12.056 linhas em `src/`, 113 arquivos de teste, 178 definições SQL (59 Bronze, 59 Silver e 60 Gold) |
| Documentação | 30 ADRs, 60 dicionários, 9 runbooks, 19 relatórios, 10 workflows e 12 módulos de infraestrutura |

**Sobre os 558 testes ignorados** (débito T5 do plano de débitos): cerca de 96% são regras de SQL parametrizadas por arquivo que, por desenho, não se aplicam à camada testada (por exemplo, a regra da Silver rodando sobre uma Bronze). O resto são testes que exigem contêineres de banco (9), uma chamada real opt-in à origem (poucos) ou a credencial do TempoOK. Nenhum esconde defeito.

**Correção de uma medida anterior:** em 14/10 citei "1.448 testes" e 95,6% de cobertura. O primeiro número era uma contagem parcial. O correto, com todas as dependências, é o da tabela acima.

## 5. Saúde da ingestão (`Conferir cargas`, 22/10)

| Ambiente | OK | Fora do OK |
|---|---|---|
| dev | 56 | 1 ATRASADA (`tempook_boletins`, último sucesso em 24/09, acervo termina em 2022); 1 SEM_SUCESSO (`bbce_curva_forward`, sem credencial) |
| hml | 55 | 1 SEM_SUCESSO (`tempook_ena_prevs`, token sem versão em hml) |

As duas fontes do TempoOK deixam de ser pendência com a saída do escopo. Restam, no histórico de 3 dias, erros do Hubspot (anteriores ao token novo) e do `bcb_juros` (queda do BCB).

## 6. Infraestrutura e entrega

- **Ambientes:** dev e hml aplicados e iguais. **Produção não existe.** O plano do bootstrap está em [`superpowers/plans/2026-10-14-bootstrap-producao.md`](../superpowers/plans/2026-10-14-bootstrap-producao.md), com quatro decisões antes do primeiro apply.
- **Defeitos de imagem achados e corrigidos em 19/10:** a imagem não instalava os drivers de banco (PR #401) e não trazia a CA pública do RDS (PR #402). Isso valia para todo conector de banco; foi achado pelos testes de conexão.
- **CI fora do GitHub Actions** ([ADR 030](../arquitetura/decisoes/030-cicd-fora-do-github-actions.md)): fase 1 em andamento. A conta de serviço do CI existe em dev; os gatilhos aguardam o papel que o bootstrap concede à conta de deploy.
- **Acesso:** o grupo da Alupar lê o Bronze em dev e hml (somente leitura).
- **Canal da equipe:** o acompanhamento diário fica no canal Alup Datalake do Teams.

## 7. Mudanças de escopo e decisões da Alupar

| Data | O quê | Registro |
|---|---|---|
| 15/10 | Planilhas por pasta do Google Drive; o servidor `10.18.0.145` não será necessário | e-mail do Leonardo |
| 20/10 | TempoOK sai integralmente do escopo como fonte do lake | relato do Gabriel no canal; confirmação por escrito pendente |
| 20/10 | ONS por usuário e senha; CCEE por usuário, senha e certificado ou por token de API | idem |
| 20/10 | Responsável pelos aceites: Eduardo Pires | idem; encerra a #258 |

Seguem fora do escopo e sem definição: Airflow, Metabase e a API de WhatsApp do servidor interno, e os decks DECOMP e NEWAVE (aditivo 01, seção 6).

## 8. Riscos

1. **Caminho até o FMB:** depende da DCIDE, que é terceiro. O teste de 22/10 ainda expira.
2. **Conectores da Onda 3** dependem dos esquemas das bases; sem eles não se escreve conector sem adivinhar.
3. **CCEE credenciada** tem 32 horas previstas e nenhum código; o caminho de acesso ainda não foi escolhido.
4. **Bootstrap pendente em dev e hml:** dev não cria os gatilhos do Cloud Build, e hml não lê o log do contêiner. Enquanto isso, o deploy de dev termina vermelho no passo dos gatilhos, sem afetar o restante.
5. **Confirmação por escrito do TempoOK:** o escopo mudou por relato.

## 9. Decisões e ações pendentes, por dono

**Alupar:** credencial do BBCE; formato e envio das credenciais da ONS e da CCEE; esquema das duas bases MySQL; endpoints e credencial do RM/TOTVS; chamado com a DCIDE (IP privado do Oracle, VPC e aceite da nossa sub-rede); pasta do Drive e exemplos de planilha (#142); confirmação por escrito do TempoOK.

**ness. (equipe):** Gabriel, relação com a Alupar; Thiago, rota do FMB e RM/TOTVS.

**ness. (Ricardo):** enviar o e-mail com o formato do BBCE; reaplicar o bootstrap em dev e hml; decidir a produção (região, acessos e orçamento); decidir sobre DECOMP e NEWAVE.

## 10. Como foi medido

- Saúde: workflow `Conferir cargas` em dev e hml, 22/10.
- Conexões: workflow `Testar conexão`, 19 e 22/10 (logs do contêiner).
- Carga do Hubspot: workflow `Executar ingestão` em dev e hml, 22/10, e a conferência seguinte.
- Testes e cobertura: `uv run pytest tests/ --cov=src`, 22/10, ambiente local completo.
- Conectores: `carregar_conectores()` sobre o registro do código.
- Escopo: mensagens do canal Alup Datalake (20/10) e e-mail do Leonardo (19/10).
- **Não medido:** linhas do Hubspot; conteúdo dos segredos; comportamento do CI no Cloud Build (gatilhos ainda não criados).
