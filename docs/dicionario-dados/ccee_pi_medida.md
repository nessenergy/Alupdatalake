# CCEE_PI — medida

Medição horária **final** por ponto de medição, da Plataforma de Integração da CCEE (item 2.1, #22 e #260). Os pontos
vêm de uma de duas vias (ver **Linhagem**): o campo opcional `pontos` da credencial, ou o cadastro
[`ccee_pi_ponto_medicao`](ccee_pi_ponto_medicao.md) pela Gold `perfil_vigente_ponto_medicao`. Contexto e catálogo: [`ccee_plataforma_integracao.md`](ccee_plataforma_integracao.md); acesso: ADR 018.

| Item | Valor |
|---|---|
| Fonte | SOAP `https://servicos.ccee.org.br:443/ws/medc/ListarMedidaBSv1`, operação `listarMedida`, `tipoMedida` FINAL |
| Onda | 2 (item 2.1, CCEE agente credenciado) |
| Frequência | Diária, 7h (`infra/modules/scheduler`); janela de 7 dias para reabrir a medida final revisada |
| Dono do dado (Alup) | A confirmar com a Alupar (usuário `ace`) |
| Credencial | Secret Manager: `alupdata-ccee-credenciais` (JSON com `senha_certificado`, `usuario`, `senha`, `codigo_perfil_agente` e o opcional `pontos`) e `alupdata-ccee-certificado` (.pfx); o certificado vence em 22/07/2027 |
| Bronze | `bronze.ccee_pi_medida`, append-only, particionada por `DATE(_ingestao_timestamp)` e clusterizada por `ponto_codigo, data_referencia` |

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

Exemplo sintético de uma linha (valores fictícios): ponto `<PONTO>`, `fim_periodo` `2026-01-01T01:00:00-03:00`, `data_referencia` `2026-01-01`,
`geracao_ativa` `<NUMERO>`.

A Gold `medicao_diaria_ponto` soma as horas de cada ponto e dia, e traz `horas_com_dado` e `dia_completo` (23 ou mais horas).

## Linhagem

```
credencial (Secret Manager)
  ├─ campo opcional `pontos` (códigos separados por vírgula) ──────────────┐  perfil = `codigo_perfil_agente` da sessão
  └─ sem `pontos`: ccee_pi_ponto_medicao → silver → gold.perfil_vigente_ponto_medicao ─┤  perfil = `perfil_para_medicao` do ponto
                                                                            ▼
SOAP ListarMedidaBSv1 / listarMedida (uma chamada por ponto e por fatia de até 31 dias, tipoMedida FINAL)
  → gs://<bucket>-raw/ccee_pi/medida/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_pi_medida
      → silver.ccee_pi_medida        (dedup por ponto_codigo, tipo_medida, fim_periodo; vence a ingestão mais recente)
        → gold.medicao_diaria_ponto  (soma por dia e ponto)
```

**Mecanismo do campo `pontos`.** `abrir_sessao` lê `pontos` do JSON da credencial; se existir, o conector mede esses pontos com o
perfil da própria sessão e **não consulta o cadastro**. Se faltar, usa a Gold do cadastro e pula o ponto sem perfil, contando-o no
log (o código do ponto não vai ao log). Existe porque o cadastro nega o perfil `6166` (`4001`, ver o dicionário do cadastro) e a
lista de pontos foi pedida à Alupar (#462, #463). Quem grava o campo é a Alupar, no Secret Manager; ele não é versionado.

**Regra da hora que termina (hour-ending).** A CCEE informa o instante em que a hora termina (`periodo/fim`, -03:00): a medida das
00:00 é a energia da última hora do dia anterior. Por isso:

```
data_referencia = (fim_periodo − 1 hora).date()
```

`transformar` aplica a regra; a janela é por `data_referencia`, e a Gold conta `horas_com_dado` e marca `dia_completo` com 23 horas
ou mais.

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
- **Unidade (aguarda a Alupar, #462).** A coleção não declara a unidade de `listarMedida`; os valores ficam como a origem manda e a Gold só soma, sem converter. A primeira carga real (09/11) trouxe 24 horas de um ponto sem resolver a dúvida (MWh ou kWh): a pergunta foi feita ao Gabriel (Alupar) em 09/11. Até a resposta, não somar a medição com nada que tenha unidade definida.
- **Regra da hora (aguarda a Alupar, #462).** Hora que termina é a leitura do guia e da primeira carga; a confirmação de que a hora informada é a que termina (e não a que começa) também foi pedida. Se for a que começa, `transformar` perde a subtração de 1 hora e a Silver precisa ser recarregada.
- **Alcance do perfil `6166` (aguarda a Alupar, #462).** Não se sabe se vale para todos os pontos ou só para o ponto da primeira leitura.
- **Perfil por ponto.** Pela via do cadastro, cada chamada usa o perfil do ponto (`perfil_para_medicao`), regra ainda a confirmar (ver o dicionário do cadastro). Ponto sem perfil é pulado e contado no log; o código do ponto não vai ao log. Pela via `pontos`, vale o perfil da sessão.
- **Falha alto.** Sem lista na credencial e sem ponto no cadastro a execução falha: nada a medir.
- **Janela e cota.** O limite de período por chamada não está documentado; o conector pede até 31 dias por chamada. A cota é de 400 chamadas por minuto por usuário e por serviço, dividida com os sistemas da Alupar.
- **Dado de cliente.** Códigos de ponto e valores medidos são dados da Alupar: ficam só no BigQuery. A fixture de teste é o exemplo sintético da coleção pública da CCEE.
