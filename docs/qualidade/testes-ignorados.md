# Testes ignorados: motivo de cada um

Medido em **23/10/2026**, sobre 2.099 testes aprovados e **558 ignorados**. Reproduz-se com:

```bash
uv run pytest tests -q -rs
```

O `-rs` imprime uma linha `SKIPPED [n] arquivo:linha: motivo` por grupo. A regra de decisão é a do [plano de débitos técnicos](../superpowers/plans/2026-10-05-debitos-tecnicos.md): motivo de "falta credencial ou ambiente" só se documenta; motivo diferente (por exemplo "não implementado" ou "lento") vira issue.

## Resumo

| Grupo | Ignorados | Parcela | Natureza |
|---|---|---|---|
| Regras SQL que não se aplicam à camada testada | 536 | 96% | por desenho |
| Precisam de contêiner de banco | 9 | 2% | ambiente |
| Precisam de credencial ou chamam a origem real | 12 | 2% | credencial ou opt-in |
| Dependem do grafo do Dataform | 1 | menos de 1% | ambiente |
| **Total** | **558** | | |

**Nenhum motivo é "não implementado" ou "lento", então não há issue a abrir.**

## Detalhe

### Regras SQL por camada (536)

Os testes de `tests/unit/test_sql.py` são **parametrizados por arquivo de `definitions/`** e aplicam cada regra a todas as fontes. Cada regra vale só para uma camada, e o teste se ignora nos arquivos das outras camadas. Os ignorados são, portanto, a combinação regra × arquivo que não faz sentido, e não teste faltando.

| Ignorados | Motivo declarado |
|---|---|
| 238 | regra vale só para a Silver |
| 120 | regra vale para as tabelas Bronze de fonte |
| 119 | regra vale só para o Bronze |
| 59 | Bronze não referencia camada anterior |

### Ambiente ou credencial (21)

| Ignorados | Arquivo | Motivo declarado | O que o destrava |
|---|---|---|---|
| 9 | `tests/integration/test_banco_containers.py` | requer os contêineres de `docker-compose.bancos.yml` | subir os contêineres de banco localmente |
| 3 | `tests/integration/test_bbce_curva_forward.py` | acesso ao BBCE ainda não entregue (pendência A7, issue #23) | a credencial do BBCE |
| 3 | `tests/integration/test_tempook_boletins.py` | token do TempoOK ainda não entregue no Secret Manager (pendência A7) | a fonte saiu do escopo da Onda 2 |
| 3 | `tests/integration/test_tempook_ena_prevs.py` | opt-in explícito: chama a origem real com o token do TempoOK | idem |
| 2 | `tests/integration/test_ons_carga_api.py` | opt-in explícito: chama a API real do ONS (pública, sem credencial) | rodar com a variável de opt-in |
| 1 | `tests/integration/test_hubspot_negocios.py` | token do Hubspot ainda não entregue (pendência A9) | rodar com `ALUPDATA_INTEGRACAO_HUBSPOT=1` (o token já está no Secret Manager) |

### Grafo do Dataform (1)

| Ignorados | Arquivo | Motivo declarado |
|---|---|---|
| 1 | `tests/unit/test_sql.py` | grafo disponível no job de compilação Dataform |

Esse teste roda no job "Dataform Compile" do CI, onde o grafo existe.

## Observações

- **Hubspot:** o motivo declarado está desatualizado. O token do aplicativo privado foi gravado pela Alupar em 20/10/2026 e a fonte carrega em dev e hml. O teste de integração é opt-in: só roda com `ALUPDATA_INTEGRACAO_HUBSPOT=1` e lê o token do Secret Manager, o que exige credencial do GCP na máquina. A mensagem do `skipif` ("token ainda não entregue") e o texto no topo do arquivo de teste ficaram desatualizados; vale reescrevê-los para dizer que é opt-in.
- **TempoOK:** a fonte saiu do escopo da Onda 2 (confirmação por escrito pendente). Os seis testes ignorados dela só voltam a fazer sentido se o escopo for reaberto; se a saída for confirmada, podem ser removidos junto com o conector.
- **CPTEC:** não há mais testes ignorados dele; o conector saiu do escopo em 23/10/2026.
