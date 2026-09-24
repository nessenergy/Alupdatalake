# Origem

Skill copiada de <https://github.com/github/awesome-copilot>
(`skills/github-actions-hardening/`), licença **MIT**, preservada em `LICENSE`.

Revisão: `1f56440` · Copiada em 24/09/2026, depois de lida na íntegra.

Não edite estes arquivos à mão; para ajustar comportamento, altere a skill do
projeto correspondente (`ssdlc-alupdata`), que tem precedência.

## Por que ela está aqui

O workflow de deploy assume a SA de deploy do GCP por Workload Identity
Federation (ADR 015). Um workflow vulnerável é uma credencial de nuvem da
contratante exposta — cláusula 8ª. A skill revisa o que linter de código não
enxerga: injeção por `${{ }}`, gatilho privilegiado, ação por tag mutável e
token com escopo demais.

## Atualizar

Não há script: clone o repositório, confira o diff da pasta contra esta
revisão, leia o que mudou antes de copiar e atualize a revisão aqui.
