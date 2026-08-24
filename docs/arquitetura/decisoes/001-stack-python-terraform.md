# ADR 001: Stack Python + Terraform

## Status
Aceito

## Contexto
O contrato CPS-01025/2026 define conectores Python com pytest como padrão (componentes 01 e 05). A infraestrutura GCP precisa ser gerenciada como código para reproducibilidade e auditoria.

## Decisão
- Python 3.12+ para conectores, pipelines e testes
- uv como package manager (lockfile determinístico, velocidade)
- ruff como linter/formatter (substitui flake8+black+isort)
- Terraform >= 1.5 para toda infraestrutura GCP

## Consequências
- Equipe precisa conhecer Terraform (curva de aprendizado aceitável)
- uv é relativamente novo mas estável e mantido pela Astral (mesmos criadores do ruff)
