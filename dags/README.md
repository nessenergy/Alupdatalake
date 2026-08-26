# DAGs do Cloud Composer

**Vazio de propósito até a Onda 3.**

A orquestração das Ondas 1 e 2 é Cloud Run Job disparado por Cloud Scheduler,
declarado em [`infra/modules/scheduler`](../infra/modules/scheduler). O Composer
entra quando aparecer dependência real entre pipelines — pipelines internos
alimentando views Gold que cruzam fontes (ADR 004).

Quando entrar, a DAG chama a **mesma CLI**:

```python
alupdata ingerir <conector> --de <data> --ate <data>
```

Não reimplemente ingestão dentro da DAG. Se você precisa de algo que a CLI não
faz, o lugar de mudar é `src/`, não aqui.
