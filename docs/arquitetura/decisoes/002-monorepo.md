# ADR 002: Estrutura Monorepo

## Status
Aceito

## Contexto
O projeto tem conectores Python, views SQL, DAGs Airflow, módulos Terraform e documentação. Precisamos decidir entre monorepo ou múltiplos repositórios.

## Decisão
Monorepo único (`nessenergy/alupdatalake`) contendo todos os componentes.

## Justificativa
- CI/CD unificado: um PR pode incluir conector + SQL + DAG + teste
- Versionamento atômico: mudanças correlacionadas sempre no mesmo commit
- Visibilidade: toda a equipe vê o estado completo do projeto
- O projeto tem tamanho contido (580h, 19 semanas) — não justifica a complexidade de multi-repo

## Consequências
- Disciplina na organização de pastas é essencial
- CI precisa ser inteligente (filtrar jobs por paths alterados — futuro)
