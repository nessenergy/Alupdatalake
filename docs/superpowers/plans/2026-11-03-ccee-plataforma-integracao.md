# CCEE Plataforma de Integração — plano

> **Para quem executa:** usar superpowers:executing-plans. Passos com caixa de seleção.

**Objetivo:** entregar o item 2.1 da Onda 2 com a primeira entidade da Plataforma de Integração da CCEE, `ccee_pi_ativo_medicao`, com os 7 componentes.

**Spec:** [2026-11-03-ccee-plataforma-integracao-design.md](../specs/2026-11-03-ccee-plataforma-integracao-design.md)

## Restrições globais

- Credencial só pelo Secret Manager (`src/core/secrets.py`); nada em código, fixture, log ou mensagem de erro.
- Fixture com XML **sintético**; nenhum dado real de cliente.
- Comentários, docs e commits em português; sem atribuição a ferramenta de IA (regra 6).
- TDD: teste antes do código.

## Portão: responder as três perguntas

**A Tarefa 2 em diante só começa depois da Tarefa 1.** As hipóteses H1, H2 e H3 do spec mudam a autenticação.

### Tarefa 1: perguntar à Alupar e registrar a resposta

**Arquivos:** rascunho no Gmail (fio das pendências da Alup); `docs/arquitetura/decisoes/018-vias-de-acesso-a-ccee.md` (adendo); `docs/status.md`.

- [ ] **Passo 1:** enviar ao Fabrizio e ao Leonardo as três perguntas da seção 2 do spec (usuário sistêmico e quem o guarda; código do perfil de agente; uso do certificado e acesso ao piloto).
- [ ] **Passo 2:** com a resposta, escolher H1, H2 ou H3 e escrever o adendo na ADR 018.
- [ ] **Passo 3:** gravar os campos que faltarem como **nova versão** de `alupdata-ccee-credenciais` em dev e hml (pelo console), sem repetir valores no chat.

### Tarefa 2: sessão SOAP e teste de autenticação

**Arquivos:** criar `src/conectores/ccee_pi_sessao.py`; teste `tests/unit/test_ccee_pi_sessao.py`; fixtures `tests/fixtures/ccee_pi/*.xml`.

**Produz:** `abrir_sessao() -> Sessao` e `Sessao.chamar(servico: str, acao: str, corpo: str) -> Element`, usados pela Tarefa 3.

- [ ] **Passo 1:** teste: o envelope tem o cabeçalho de segurança conforme a hipótese escolhida e o `codigoPerfilAgente`, e a mensagem de erro de `Fault` não contém segredo.
- [ ] **Passo 2:** rodar e ver falhar.
- [ ] **Passo 3:** implementar com `requests` por `criar_sessao` e `defusedxml`; respeitar 400 chamadas por minuto.
- [ ] **Passo 4:** comando `python -m src.cli testar-ccee` que chama `listarRepresentacao` e imprime só `ok` ou o código do erro.
- [ ] **Passo 5:** rodar em hml pelo workflow e anexar o resultado à #260.

### Tarefa 3: conector `ccee_pi_ativo_medicao` com os 7 componentes

**Arquivos:** `src/conectores/ccee_pi_ativo_medicao.py`; `definitions/{bronze,silver,gold}/…`; `tests/unit/` e `tests/integration/`; `infra/modules/scheduler/main.tf`; `docs/dicionario-dados/ccee_pi_ativo_medicao.md`.

- [ ] **Passo 1:** `make novo-conector fonte=ccee_pi entidade=ativo_medicao` e ajustar ao padrão de retrato sem janela.
- [ ] **Passo 2:** teste de parsing com fixture sintética, de paginação (várias páginas) e de idempotência (mesmo lote duas vezes não duplica a Silver).
- [ ] **Passo 3:** Bronze particionado e clusterizado; Silver com `QUALIFY ROW_NUMBER()` e `ceg` preenchido; Gold só se houver regra de negócio.
- [ ] **Passo 4:** agendamento mensal em `infra/`, sem ligar em dev e prod (o `test_infra` proíbe).
- [ ] **Passo 5:** `make all` verde; PR com `feat:`; 9 checks verdes; merge.

### Tarefa 4: carga em hml e fechamento

- [ ] **Passo 1:** `Deploy GCP` e `Executar ingestão` em hml; conferir com `Conferir cargas`.
- [ ] **Passo 2:** atualizar `docs/status.md`, `painel/marcos.toml` e a #260 (escopo das 32 h: o que foi entregue e o que fica para depois).
- [ ] **Passo 3:** o painel (`gh workflow run Painel`) mostra o item 2.1 andando.

## Revisão do plano

- **Cobertura:** autenticação (T1, T2), conector (T3), carga e painel (T4).
- **Risco principal:** a hipótese de autenticação. Por isso o portão da Tarefa 1; sem ele, a Tarefa 2 seria escrita às cegas.
- **Fora do plano:** a leitura das partes não lidas da documentação (cerca de 500 mil caracteres), a fazer ao escrever o dicionário de dados.
