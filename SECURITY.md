# Política de segurança

## Reportar uma vulnerabilidade

**Não abra issue pública** com detalhe explorável — nem em repositório privado,
onde ela fica visível a todos os colaboradores.

Envie para **dev@bekaa.eu** (ness. Processos e Tecnologia) com:

- o que é vulnerável e como reproduzir;
- impacto estimado (dado exposto, acesso obtido, disponibilidade);
- versão/commit onde encontrou.

Retorno em até **2 dias úteis**. Vulnerabilidades de severidade Alta ou Crítica
(CVSS) são corrigidas **antes da homologação da onda corrente** — é exigência
contratual, não meta interna (cláusula 8.6).

## Se um segredo vazou

**Rotacione o segredo primeiro**, depois limpe o histórico. Remover o commit sem
rotacionar não conserta nada: o valor já circulou. Avise quem opera o ambiente
afetado antes de mexer no Git.

## Práticas obrigatórias (cláusula 8ª)

| Controle | Ferramenta | Quando roda |
|---|---|---|
| SAST | Bandit | pre-commit e CI |
| SCA | pip-audit | CI e varredura semanal |
| Detecção de segredos | Gitleaks | pre-commit e CI |
| Gestão de credenciais | Google Secret Manager | runtime |

Proibido em qualquer circunstância: credencial, token, chave ou senha em
código, `.env` versionado, fixture, log, mensagem de erro, `.tfvars`
versionado ou commit — inclusive "temporariamente".

Acesso a bancos da Alup é **read-only**. Dado real de cliente não entra no
repositório, em nenhuma forma. Dados de teste são eliminados após a homologação
de cada etapa (cláusula 8.3).

Detalhes em [`docs/arquitetura/seguranca.md`](docs/arquitetura/seguranca.md) e
na skill [`ssdlc-alupdata`](.claude/skills/ssdlc-alupdata/SKILL.md).
