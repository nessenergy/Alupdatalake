# IGP-M em dev — Implementation Plan

> **Para agentes:** use superpowers:subagent-driven-development. Passos com checkbox.

**Goal:** deixar o IGP-M (`bcb_igpm`) carregado em `dev`, como já está em `hml`, e provar com `Conferir cargas`. É a única carga que falta dos três pedidos do Eduardo (IGP-M, Tarifas Homologadas, PRC), conferidas em 03/10/2026.

**Architecture:** nada de código novo. O `Executar ingestão` (workflow existente) carrega o IGP-M em `dev` quando `api.bcb.gov.br` responder. Se não responder até 04/10 à noite, plano B: reprocessar em `dev` o raw do IGP-M já arquivado no bucket do `hml` (`reprocessar-raw`).

**Tech Stack:** GitHub Actions (`Executar ingestão`, `Conferir cargas`), gh CLI, Cloud Run Job `ingestao-bcb-igpm`.

**Spec:** e-mail do Eduardo Pires de 02/10/2026 ("concluir os carregamentos de IGP-M, Tarifas Homologadas e PRC até segunda, 05/10"). Escopo literal: só isso. Fora: CPTEC, IPDO/ACOMPH, TUST/RAP, versão do contrato, resposta ao e-mail e confirmação do prazo (são do Ricardo).

## Global Constraints

- Regra 6: nenhuma atribuição de IA em commit, PR, issue, comentário ou documento; validar com `python scripts/verifica_atribuicao.py`.
- Nenhum recurso GCP fora de `infra/`; credencial só via Secret Manager.
- Ingestão por janela de datas; Bronze append-only, Silver deduplica.
- Não alterar o estado da Onda 1 no painel. Registrar fato e data; decisão comercial é do Ricardo.
- Adicionar arquivos por nome (nunca `git add -A`).

## Tarefa 1: Verificar o vigia e a API do BCB (passo 1)

- [ ] Ver se `vigia_bcb.py` roda (`tasklist`/processos Python) e ler `vigia_bcb.log`.
- [ ] Testar `https://api.bcb.gov.br/dados/serie/bcdata.sgs.189/dados/ultimos/1?formato=json` daqui e dizer o resultado.
- [ ] Se o BCB responde: disparar `gh workflow run "Executar ingestão" -f environment=dev -f conector=bcb_igpm -f de=2024-09-01 -f ate=2026-10-02` e esperar; ir à Tarefa 3.
- [ ] Se não responde e não há vigia: recriar o vigia (tentativa a cada 30 min, dispara a carga acima ao primeiro 200) e seguir para a Tarefa 2 só se for 04/10 à noite.

## Tarefa 2: Plano B, só com BCB fora até 04/10 à noite (passo 2)

- [ ] Achar o raw do `bcb_igpm` em `gs://alupar-hm-alupdata-raw/bcb/igpm/` (via execução que a conta de deploy leia; se ela não ler o bucket, **parar e avisar**, sem improvisar).
- [ ] Se lê: copiar o objeto para `gs://alupar-dev-alupdata-raw/bcb/igpm/dt=…/` e rodar `Executar ingestão` com `uri` e a janela original (`de`/`ate`) em `dev`. Se a cópia entre projetos não for permitida, parar e avisar.

## Tarefa 3: Prova final (passo 3)

- [ ] `gh workflow run "Conferir cargas" -f environment=dev` e `hml`; extrair as linhas de `bcb_igpm`, `igpm_mensal`, `aneel_tarifas`, `ace_prc` e as Golds de tarifa e PRC.
- [ ] Critério: as três fontes com linhas na Silver e na Gold, em `dev` e `hml`.

## Tarefa 4: Registro (passo 4)

- [ ] Em `docs/relatorios/2026-10-03-fechamento-onda-1.md`, uma seção curta com os runs, as contagens, a data e o que ficou pendente (se algo ficou). Só fato.
- [ ] Validar a mensagem de commit, abrir PR, esperar CI e mesclar.
