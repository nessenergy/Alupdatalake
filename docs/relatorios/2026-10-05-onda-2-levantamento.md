# Onda 2 — levantamento por fonte e componente (05/10/2026)

Relatório interno da ness. Só leitura do repositório: nada foi criado nem alterado nas fontes. Cada marca da tabela vem de um
comando de `ls` ou `git grep` sobre o repositório em 05/10/2026; o estado das credenciais vem de `docs/status.md`.

## 1. O que a Onda 2 prevê

Contrato (`docs/contrato/resumo-contrato.md`): Onda 2, "Modelos Preditivos & APIs com Credenciais", de 19/10 a 13/11/2026, 110 h,
marco 3 (18,97%, R$ 28.160,00, homologação em 13/11). Tokens e APIs (CCEE, BBCE, Hubspot, TempoOK) devem chegar **até 19/10/2026**
(cláusula 3ª). O prazo interno que a ness. pediu à Alup é 12/10 (#262).

Itens do plano (`docs/plano-execucao.md` §4):

| # | Item | Horas |
|---|---|---:|
| 2.1 | CCEE agente credenciado | 32 |
| 2.2 | BBCE | 28 |
| 2.3 | Hubspot | 20 (restam ~4) |
| 2.4 | TempoOK | 18 |
| 2.5 | "Tabelas Gold de preço e posição comercial" | 12 |

**Critério do item 2.5.** O único texto que o repositório traz é a frase acima, entre aspas, com 12 h e sem credencial. O resumo
do contrato não detalha o item. Por isso o levantamento **não** afirma se alguma Gold atende ao 2.5.

## 2. Os 7 componentes por fonte

Legenda: ✔ presente (arquivo ou entrada encontrados) · ✘ ausente.

| Fonte | Conector | Bronze | Silver | Gold que a consome | Testes unitários (funções `test_`) | Agendamento | Dicionário |
|---|---|---|---|---|---|---|---|
| BBCE (`bbce_curva_forward`) | ✔ | ✔ | ✔ | ✔ `curva_forward_vigente` | ✔ 14 | ✔ | ✔ |
| Hubspot (`hubspot_negocios`) | ✔ | ✔ | ✔ | ✔ `funil_comercial` | ✔ 7 | ✔ | ✔ |
| TempoOK, boletim (`tempook_boletins`) | ✔ | ✔ | ✔ | ✔ `cobertura_boletins_tempook` | ✔ 13 | ✔ | ✔ |
| TempoOK, previsão de ENA (`tempook_ena_prevs`) | ✔ | ✔ | ✔ | ✔ `cobertura_ena_prevs_tempook` | ✔ 15 | ✔ | ✔ |
| CCEE agente credenciado (item 2.1) | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |

Notas de leitura:

- **`tempook_arquivos`** é a base compartilhada dos dois produtos do TempoOK (`fonte = "tempook"`, ADR 019): não é fonte própria e
  não tem Bronze, Silver, teste ou dicionário próprios. Não entra como linha da tabela.
- **`ccee_agente`** existe e tem os 7 componentes, mas é da **Onda 1** (dataset público `lista_agente_associado`, sem credencial,
  segundo seu dicionário). **Não é** o "CCEE agente credenciado" do item 2.1, que não tem nenhum arquivo no repositório.
- A contagem de testes é de funções `test_`; casos de `parametrize` não estão expandidos.

## 3. Testes que só rodam com a credencial real

Os quatro conectores têm um teste de integração em `tests/integration/` com `pytestmark = pytest.mark.skipif(...)` no módulo:
sem a credencial, **todo** o arquivo é ignorado. São eles: `test_bbce_curva_forward.py`, `test_hubspot_negocios.py`,
`test_tempook_boletins.py` e `test_tempook_ena_prevs.py`. Os testes unitários rodam sem rede e sem credencial.

## 4. Classe de cada item

| Item | Classe | O que falta e por quê |
|---|---|---|
| 2.1 CCEE agente credenciado | **Decisão da Alup** | Nada existe. O plano registra "sem caminho definido em 27/09": aguarda a posição da Alup sobre as 32 h (#260). Se o item sair do escopo, a realocação das horas é decisão de coordenação. |
| 2.2 BBCE | **Só falta a credencial (Alup)** | Os 7 componentes existem (PR #131). Faltam acesso e host (#23). Segredo sem versão em dev e hml. |
| 2.3 Hubspot | **Só falta a credencial (Alup)** | Os 7 componentes foram escritos contra a documentação pública em 26/08/2026, sem acesso real. Falta o token de API (private app) e rodar contra a API real e ajustar (~4 h). Segredo sem versão em dev e hml. |
| 2.4 TempoOK | **Só falta a credencial (Alup), com duas ressalvas** | Os 7 componentes existem para os dois produtos. (a) O boletim tem contrato verificado, mas o acervo só vai até 26/10/2022 (#129). (b) A previsão de ENA responde para a data de hoje (verificada em 21/09), mas só o caminho de exemplo é conhecido: a Alup vai indicar os demais. |
| 2.5 Gold de preço e posição comercial | **Escopo sem definição** | O texto do item é uma frase. Existem Golds de preço e de posição (abaixo), mas não dá para dizer se atendem ao 2.5 sem a definição do que o item entrega. Nada foi criado. |

**Golds existentes de preço, posição e comercial** (consulte o cabeçalho de cada arquivo em `definitions/gold/`):
`curva_forward_vigente` (preço: último pregão da BBCE por vértice, para comparar com o PLD), `pld_mensal_submercado` (preço: PLD
mensal por submercado), `posicao_contratual_mensal_perfil` (posição contratual como a CCEE enxerga, via pública de Comercial e
Contratos, ADR 021 §4), `exposicao_mercado_mensal` (exposição do mercado de curto prazo) e `funil_comercial` (Hubspot).

## 5. Credenciais (segundo `docs/status.md`)

A Alup prometeu as credenciais da Onda 2 para 01/10; **não chegaram**. Os segredos do Hubspot e do BBCE não têm versão em `dev`
nem em `hml`. O prazo contratual é 19/10/2026; atraso superior a 5 dias úteis posterga o cronograma e superior a 20 dias
corridos permite a suspensão dos serviços (cláusula 3ª). Este relatório registra o fato e a data; cobrança e consequências
contratuais são decisão do decisor da ness.
