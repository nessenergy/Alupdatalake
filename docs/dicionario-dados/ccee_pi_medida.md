# CCEE_PI — medida

Medição horária **final** por ponto de medição, da Plataforma de Integração da CCEE (item 2.1, #22 e #260). Os pontos
e o perfil de agente de cada um vêm do cadastro [`ccee_pi_ponto_medicao`](ccee_pi_ponto_medicao.md), pela Gold
`perfil_vigente_ponto_medicao`. Contexto e catálogo: [`ccee_plataforma_integracao.md`](ccee_plataforma_integracao.md); acesso: ADR 018.

| Item | Valor |
|---|---|
| Fonte | SOAP `https://servicos.ccee.org.br:443/ws/medc/ListarMedidaBSv1`, operação `listarMedida`, `tipoMedida` FINAL |
| Onda | 2 (item 2.1, CCEE agente credenciado) |
| Frequência | Diária, 7h (`infra/modules/scheduler`); janela de 7 dias para reabrir a medida final revisada |
| Dono do dado (Alup) | A confirmar com a Alupar (usuário `ace`) |
| Credencial | Secret Manager: `alupdata-ccee-credenciais` e `alupdata-ccee-certificado`; o certificado vence em 22/07/2027 |

## Campos

Uma linha por ponto e hora.

| Origem (XML) | Bronze | Silver | Gold | Tipo | Transformação |
|---|---|---|---|---|---|
| `periodo/fim` menos 1 hora, só a data | `data_referencia` | `data_referencia` | `data_referencia` | DATE | dia da hora medida |
| `pontoMedicao/codigo` | `ponto_codigo` | `ponto_codigo` | `ponto_codigo` | STRING | — |
| tipo pedido | `tipo_medida` | `tipo_medida` | — | STRING | FINAL |
| `periodo/fim` | `fim_periodo` | `fim_periodo` | — | TIMESTAMP | a hora termina neste instante, fuso -03:00 |
| `subTipo` | `sub_tipo` | `sub_tipo` | — | STRING | — |
| `status` | `status` | `status` | — | STRING | — |
| `geracaoAtiva` | `geracao_ativa` | `geracao_ativa` | `geracao_ativa` | NUMERIC | Gold: soma do dia |
| `geracaoReativo` | `geracao_reativa` | `geracao_reativa` | `geracao_reativa` | NUMERIC | Gold: soma do dia |
| `consumoAtivo` | `consumo_ativo` | `consumo_ativo` | `consumo_ativo` | NUMERIC | Gold: soma do dia |
| `consumoReativo` | `consumo_reativo` | `consumo_reativo` | `consumo_reativo` | NUMERIC | Gold: soma do dia |

A Gold `medicao_diaria_ponto` soma as horas de cada ponto e dia, e traz `horas_com_dado` e `dia_completo` (23 ou mais horas).

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da hora medida |
| `submercado` | não (NULL) | a medição não traz submercado |
| `codigo_usina` | não (NULL) | o ponto não é a usina; o de-para é da #141 |
| `agente_ccee` | não (NULL) | a origem traz o ponto, não o código do agente |
| `periodo_apuracao` | sim | `YYYY-MM` do dia medido |

## Qualidade e observações

- **Hora que termina.** A medida das 00:00 é a energia da última hora do dia anterior; por isso o dia vem da hora, uma hora antes do fim do período.
- **Revisão.** A medida final pode ser revisada; a Silver fica com a ingestão mais recente de cada ponto e fim de período.
- **Unidade.** A coleção não declara a unidade de `listarMedida`; os valores ficam como a origem manda e a Gold só soma. **A confirmar** com a primeira carga real.
- **Perfil por ponto.** Cada chamada usa o perfil do ponto (`perfil_para_medicao`), regra ainda a confirmar (ver o dicionário do cadastro). Ponto sem perfil é pulado e contado no log; o código do ponto não vai ao log.
- **Falha alto.** Sem nenhum ponto no cadastro a execução falha: o cadastro ainda não carregou.
- **Janela e cota.** O limite de período por chamada não está documentado; o conector pede até 31 dias por chamada. A cota é de 400 chamadas por minuto por usuário e por serviço, dividida com os sistemas da Alupar.
- **Dado de cliente.** Códigos de ponto e valores medidos são dados da Alupar: ficam só no BigQuery. A fixture de teste é o exemplo sintético da coleção pública da CCEE.
