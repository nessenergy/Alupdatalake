# Origem

Skills copiadas de <https://github.com/hashicorp/agent-skills>
(`plugins/terraform/skills/`), licença **MPL 2.0**, preservada em `LICENSE`.

Revisão: `c2d65df` · Copiadas em 24/09/2026, depois de lidas na íntegra.

Não edite estes arquivos à mão. A MPL 2.0 é *copyleft* por arquivo: estes
arquivos seguem sob ela, e nada fora desta pasta é afetado. Para ajustar
comportamento, altere a skill do projeto — `gcp-alupdata` tem precedência.

## Shortlist

- `terraform-style-guide` — estilo e organização de HCL
- `terraform-test` — o framework `terraform test`

## Onde o projeto diverge, e vale o projeto

- **Nomes em português**, não em inglês; um `main.tf` por módulo, sem separar
  `variables.tf` e `outputs.tf` dentro de `infra/modules/`.
- **`terraform test` só em `plan` ou com provider simulado.** O modo `apply`,
  padrão do framework, cria recurso real — e a conta do GCP é da Alup.

## Atualizar

Não há script: clone o repositório, confira o diff das pastas acima contra
esta revisão, leia o que mudou antes de copiar e atualize a revisão aqui.
