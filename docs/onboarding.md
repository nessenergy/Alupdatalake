# Onboarding — AlupData DataLake

## Pré-requisitos

| Ferramenta | Versão mínima | Instalação |
|-----------|-------------|----------|
| Python | 3.12+ | [python.org](https://python.org) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Terraform | 1.5+ | [terraform.io](https://terraform.io) |
| gcloud CLI | latest | [cloud.google.com](https://cloud.google.com/sdk) |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |

## Setup Local

```bash
# 1. Clone
git clone https://github.com/nessenergy/alupdatalake.git
cd alupdatalake

# 2. Instalar dependências Python
uv sync

# 3. Instalar hooks de pre-commit
uv run pre-commit install

# 4. Copiar variáveis de ambiente
cp .env.example .env
# Editar .env com os valores do seu ambiente

# 5. Verificar setup
make test
make lint
```

## Workflow de Desenvolvimento

1. Criar branch a partir de `main`: `git checkout -b feat/conector-ccee`
2. Implementar seguindo TDD (teste primeiro, depois código)
3. Rodar `make all` (lint + testes + segurança)
4. Commitar com conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `ci:`
5. Abrir PR para `main`
6. CI roda automaticamente (lint, testes, SAST, SCA)
7. Review e merge

## Convenções

- **Código**: variáveis e funções em inglês
- **Comentários e docs**: português (PT-BR)
- **Commits**: conventional commits em português
- **Branches**: `feat/`, `fix/`, `docs/`, `chore/`
