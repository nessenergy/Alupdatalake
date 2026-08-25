# Instruções para agentes neste repositório

O contexto canônico deste projeto está em [`AGENTS.md`](../AGENTS.md) na raiz.
Leia aquele arquivo antes de propor ou escrever qualquer mudança — ele traz as
regras que não se negociam, o padrão de conector, os comandos, as convenções e
o estado atual do trabalho.

Resumo mínimo, para o caso de você só ler este arquivo:

- Toda fonte de dados entrega **7 componentes** (conector, Bronze, Silver, Gold,
  testes, agendamento, dicionário). Fonte com 5 de 7 é retrabalho, não entrega.
- Credencial **só** via Secret Manager. Nunca em código, `.env` versionado,
  fixture, log ou mensagem de erro.
- Ingestão **sempre por janela de datas**; nenhum conector decide "hoje".
- Bronze é **append-only**; a deduplicação vive na view Silver.
- Recurso GCP que não está em `infra/` **não existe** — nada de console.
- Rode `make all` antes de abrir PR.
