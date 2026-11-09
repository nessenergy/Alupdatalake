# CCEE_PI — ponto_medicao

Cadastro dos pontos de medição em que o agente da credencial tem relação, e do perfil de agente de cada relação. É a
primeira entidade da Plataforma de Integração da CCEE (item 2.1, #22 e #260) e a base da medição: o `listarMedida`
exige o perfil do agente principal do ponto, e é este cadastro que o devolve. Contexto e catálogo das 57 operações:
[`ccee_plataforma_integracao.md`](ccee_plataforma_integracao.md); decisão de acesso: ADR 018.

| Item | Valor |
|---|---|
| Fonte | SOAP `https://servicos.ccee.org.br:443/ws/v2/PontoMedicaoBSv2`, operação `listarPontoMedicao` ("Listar pontos de medição por agente relacionado") |
| Onda | 2 (item 2.1, CCEE agente credenciado) |
| Frequência | Mensal, dia 2 às 6h (`infra/modules/scheduler`); retrato sem janela |
| Dono do dado (Alup) | A confirmar com a Alupar (usuário `ace`, perfil `6166`) |
| Credencial | Secret Manager: `alupdata-ccee-credenciais` (JSON com `senha_certificado`, `usuario`, `senha`, `codigo_perfil_agente`) e `alupdata-ccee-certificado` (.pfx). O certificado vence em 22/07/2027 |

## Campos

Uma linha por ponto e agente relacionado; um ponto sem agente relacionado vira uma linha com os campos do agente nulos.

| Origem (XML) | Bronze | Silver | Gold | Tipo | Transformação |
|---|---|---|---|---|---|
| fim da janela da execução | `data_referencia` | `data_referencia` | `data_referencia` | DATE | data do retrato; a Gold usa o mais recente |
| `pontoMedicao/codigo` | `ponto_codigo` | `ponto_codigo` | `ponto_codigo` | STRING | — |
| `pontoMedicao/nome` | `ponto_nome` | `ponto_nome` | `ponto_nome` | STRING | — |
| `pontoMedicao/tipoColeta/codigo` | `tipo_coleta` | `tipo_coleta` | `tipo_coleta` | STRING | — |
| `participanteMercadoRelacionado/tipoRelacao/nome` | `tipo_relacao` | `tipo_relacao` | colunas `perfil_*` | STRING | AGENTE_CONECTADO, AGENTE_CONECTANTE, AGENTE_MEDICAO ou AGENTE_USO_FIO |
| `participanteMercadoRelacionado/perfis/perfil/codigo` | `perfil_codigo` | `perfil_codigo` | `perfil_conectante`, `perfil_medicao`, `perfil_conectado`, `perfil_uso_fio`, `perfil_para_medicao` | STRING | a Gold coloca um perfil por relação; `perfil_para_medicao` é o do conectante, ou o da medição se faltar |
| `participanteMercadoRelacionado/parte/pessoaJuridica/nomeEmpresarial` | `agente_nome` | `agente_nome` | — | STRING | — |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | data do retrato, não a de um fato do ponto |
| `submercado` | não (NULL) | o cadastro não traz submercado |
| `codigo_usina` | não (NULL) | o ponto não é a usina; o de-para é da #141 |
| `agente_ccee` | não (NULL) | a origem traz o nome empresarial e o perfil, não o código do agente |
| `periodo_apuracao` | sim | `YYYY-MM` da data do retrato |

## Qualidade e observações

- **Retrato, sem janela.** O Bronze guarda um retrato por execução (append-only). A Silver deduplica por retrato, ponto, relação, perfil e agente; a Gold fica com o retrato mais recente.
- **Falha alto.** Cadastro vazio derruba a execução: seria credencial sem relação com ponto nenhum, não um dia sem dados.
- **Paginação.** Páginas de 50 itens; a leitura segue até `totalPaginas`. A cota da CCEE é de 400 chamadas por minuto por usuário e por serviço, dividida com os sistemas da Alupar; o cliente espera 0,2 s entre chamadas.
- **Perfil do ponto.** Para consultar a medição, o guia da CCEE manda usar o perfil do agente principal do ponto. A regra `perfil_para_medicao` (conectante, senão medição) é a leitura deste guia e **está a confirmar** na primeira carga real; se o perfil do agente `6166` aparecer em outra relação, a Gold muda.
- **Dado de cliente.** Códigos de ponto e nomes de agente são dados da Alupar: ficam só no BigQuery. A fixture de teste usa o exemplo sintético da coleção pública da CCEE.
- **Pendências:** validar o formato com uma carga real em hml; a ampliação para outros cadastros (perfis, participantes) fica para depois.
