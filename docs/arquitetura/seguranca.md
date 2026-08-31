# Política de Segurança — AlupData DataLake

## SSDLC (Ciclo de Desenvolvimento Seguro)

Conforme cláusula 8.4 do contrato CPS-01025/2026, o projeto adota práticas de SSDLC:

### Ferramentas Integradas ao CI/CD

| Ferramenta | Tipo | Descrição | Cláusula |
|-----------|------|-----------|----------|
| **Bandit** | SAST | Análise estática de segurança do código Python | 8.4 |
| **pip-audit** | SCA | Varredura de vulnerabilidades em dependências | 8.4 |
| **Gitleaks** | Secrets | Detecção de credenciais no código/histórico Git | 8.5 |
| **Ruff** | Lint | Qualidade e padronização de código | — |

### Gestão de Segredos (Cláusula 8.5)

**PROIBIDO:**
- Armazenar credenciais, chaves de API, tokens ou senhas no código-fonte
- Commitar secrets no repositório Git

**OBRIGATÓRIO:**
- Usar Google Cloud Secret Manager para todas as credenciais
- Variáveis de ambiente para configuração não-sensível
- `.env` está no `.gitignore`
- Sanitizar mensagem e stack trace antes de logar ou persistir erro
- Conceder `secretAccessor` por secret, não no projeto inteiro

O módulo `src/core/seguranca.py` remove padrões de DSN, Bearer e parâmetros
sensíveis. Erros de validação não incluem o valor bruto que foi rejeitado.

### Menor privilégio

- A identidade de ingestão cria jobs BigQuery no projeto, mas edita apenas o
  dataset Bronze.
- O bucket raw concede criação e leitura de objetos, sem administração do
  bucket.
- Invocação de Cloud Run é concedida por job.
- Credencial read-only na origem continua obrigatória para bancos internos.

### Gestão de Vulnerabilidades (Cláusula 8.6)

- Varredura automática em **todo PR** e **semanalmente**
- Vulnerabilidades **Alta/Crítica (CVSS)** devem ser corrigidas antes da homologação
- Relatórios de segurança arquivados como artefatos do GitHub Actions

### Eliminação de Dados (Cláusula 8.3)

- Dados de teste/produção em ambientes de dev devem ser eliminados após homologação
- Procedimento documentado no Runbook
