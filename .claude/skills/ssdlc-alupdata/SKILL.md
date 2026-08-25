---
name: ssdlc-alupdata
description: Portões de segurança contratuais do AlupData (cláusula 8ª) — Bandit (SAST), pip-audit (SCA), Gitleaks, Secret Manager e eliminação de dados de teste. Use ao lidar com credenciais, tokens, VPN, conexões a bancos da Alup, dependências novas, achados de vulnerabilidade, pre-commit/CI, ou antes de declarar uma onda pronta para homologação.
---

# Segurança — cláusula 8ª do CPS-01025/2026

Não é higiene opcional: vulnerabilidade Alta/Crítica em aberto **bloqueia a
homologação da onda**, e homologação é o que dispara a medição.

## Os quatro portões

| Ferramenta | O que pega | Como rodar |
|---|---|---|
| Ruff | qualidade e padrão | `make lint` |
| Bandit | SAST no código Python | `make security` (`bandit -r src/ -ll`) |
| pip-audit | CVE em dependência | `make audit` (`--strict`) |
| Gitleaks | secret no código/histórico | pre-commit |

`make all` roda lint + testes + Bandit + pip-audit. É o que se roda antes de
abrir PR; `pre-commit install` garante Ruff/Bandit/Gitleaks a cada commit.

## Segredos

**Proibido**: credencial, token, chave ou senha em código, em teste, em fixture,
em default de função, em log, em mensagem de erro, em `.tfvars` versionado, em
docstring ou em commit — inclusive "temporariamente".

**Obrigatório**: Google Secret Manager (`alupdata-<fonte>-<campo>`), lido em
runtime. `.env` fica fora do versionamento; `.env.example` só com placeholders.

Se um segredo vazou para o Git: **rotacione o segredo primeiro**, depois limpe o
histórico. Remover o commit sem rotacionar não conserta nada — o valor já
circulou.

## Dependências

Antes de adicionar uma dependência: ela é necessária, é mantida, e `pip-audit`
passa com ela? Achado de CVE Alta/Crítica se resolve subindo a versão; se não há
correção, documente a exposição e proponha alternativa — não adicione exceção
silenciosa.

Supressão de achado (`# nosec`, ignore de CVE) só com justificativa escrita no
próprio diff. Sem justificativa, é dívida invisível na homologação.

## Dados

- Nada de dado real de cliente no repositório — nem em fixture, nem em seed, nem
  em exemplo de dicionário. Use dado sintético ou anonimizado.
- Dados de teste em ambiente de dev são eliminados após a homologação de cada
  etapa (cláusula 8.3); o procedimento vive no runbook.
- Acesso a bancos da Alup é **read-only**. Um conector que precise escrever na
  origem está mal desenhado.

## Ao fechar uma onda

- [ ] `make all` verde no head da branch
- [ ] Nenhum achado Alto/Crítico aberto (Bandit, pip-audit)
- [ ] Nenhum secret no histórico da branch
- [ ] Toda credencial usada está no Secret Manager, com IAM mínimo
- [ ] Dados de teste eliminados e registrados no runbook
