# ADR 015 — Fundação do ambiente: dois ambientes, construída pela ness., chave gerenciada pelo Google

**Status**: aceito · **Data**: 2026-09-11 · **Complementa** a
[ADR 011](011-regiao-us-east1.md)

## Contexto

A reunião de revisão arquitetural com o Google, em 10/09 (G1), deixou três
pontos da fundação em aberto:

- **Ambientes.** O Google sugeriu separar desenvolvimento, homologação e
  produção em projetos distintos. A ADR 011 e o `infra/` preveem `dev` e `prod`.
- **Quem constrói.** Saíram da reunião tarefas para o Google — "criar a
  fundação de dados" e "estruturar os projetos e a esteira de CI/CD". Pela
  regra 5, recurso que não está em `infra/` não existe: um Terraform paralelo,
  ou recurso criado pelo console, deixaria o ambiente com duas fontes de
  verdade.
- **Criptografia.** Foi levantada a opção de criptografar o dado com chave
  própria da Alupar (CMEK).

## Decisão

### Dois ambientes: `dev` e `prod`

Ficam os dois projetos que o `infra/` já prevê. O projeto de homologação
sugerido na reunião não é adotado: cada ambiente a mais é um projeto a mais
para a Alup criar (E1) e faturar (E2), e um conjunto a mais de recursos para
manter em Terraform.

### A fundação é da ness., toda em `infra/`

Tudo o que existe dentro dos projetos — APIs, IAM, contas de serviço, rede,
datasets, buckets, Artifact Registry, Dataform, Knowledge Catalog,
agendamentos e a esteira de CI/CD — é declarado no `infra/` deste repositório e
construído pela ness. Não há Terraform paralelo nem recurso criado pelo
console. As tarefas de fundação que a reunião atribuiu ao Google passam para a
ness.

A fronteira com a Alup continua a esclarecida em 09/09: **criar os projetos na
organização e vincular a conta de faturamento é da Alup** (E1 e E2). A ness.
não tem, e não deve ter, permissão de criar projeto na organização da
contratante. A ness. acompanha a abertura da conta de faturamento junto à Qi.

### Criptografia com chave gerenciada pelo Google

Sem CMEK. BigQuery, Cloud Storage e os demais serviços usam a criptografia em
repouso padrão, com chave gerenciada pelo Google.

Chave própria perdida ou desabilitada torna o dado ilegível, sem recuperação,
e a troca periódica da chave passaria a ser uma operação da Alup. Esse risco
pesou mais do que a restrição adicional de acesso que a chave própria daria.

## Consequências

- O `infra/` continua com dois `.tfvars`, `dev` e `prod`; nada muda no código.
- Nenhum recurso de KMS entra em `infra/`. Adotar CMEK depois é ADR própria.
- O primeiro `apply` segue dependendo da Alup criar o projeto `dev` (A3) e
  vincular a conta de faturamento.
