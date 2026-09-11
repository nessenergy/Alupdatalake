# Política de retenção de dados da plataforma AlupData — proposta

**Versão** 0.1 · **Data** 2026-09-11 · **Situação**: proposta da ness., para
aprovação da Alup (controladora) e da encarregada

Responde à pergunta F3 do [Questionário de Gaps](../questionario-gaps.md) e
trata os riscos R02 e R08 do [RIPD](ripd.md). Base: princípio da necessidade
(LGPD, art. 6º, III), término do tratamento (arts. 15 e 16) e cláusula 8.3 do
contrato CPS-01025/2026.

## Princípios

1. **O prazo depende do conteúdo, não só da camada.** Dado de mercado e de
   operação, sem dado pessoal, é o histórico que justifica o lake e fica sem
   prazo. Tabela com coluna de dado pessoal tem prazo.
2. **A Bronze guarda o histórico; o raw serve para reprocessar.** O registro
   bruto no bucket existe para refazer uma carga, não para ser uma segunda
   cópia permanente.
3. **Tudo configurado em `infra/`** (regra 5): regras de ciclo de vida do
   bucket e expiração de partição no BigQuery. Prazo que não está no Terraform
   não está valendo.

## Prazos propostos

| Onde | Sem dado pessoal | Com dado pessoal | Como se aplica |
|---|---|---|---|
| Bucket raw — versão atual do objeto | Classe NEARLINE aos 90 dias, como hoje; **exclusão aos 400 dias** | **Exclusão aos 90 dias** | Regra de ciclo de vida por idade, por prefixo de fonte |
| Bucket raw — versões antigas | Exclusão 30 dias depois de deixar de ser a atual | Idem | Regra de ciclo de vida para versões não atuais |
| Bronze | Sem expiração | **Expiração de partição em 5 anos** | Expiração de partição na tabela |
| Silver e Gold em view | Não guardam dado | — | — |
| Gold materializada (ADR 012) | Recalculada a cada execução; não guarda nada além da Bronze | Não deve ter coluna pessoal (RIPD, R04) | — |
| Dataset `qualidade` | 90 dias | 90 dias | Expiração padrão do dataset |
| `bronze._execucoes` | 2 anos | Não se aplica: o erro é gravado sanitizado | Expiração de partição |
| Cloud Logging | 30 dias, padrão do serviço | — | — |
| Log de auditoria de acesso a dados (RIPD, R07) | 1 ano | — | Bucket de log dedicado |
| Ambiente `dev` | Como `prod` | **90 dias** | Valores no `dev.tfvars` |

### Por que esses números

- **400 dias no raw** cobrem um ciclo anual completo de reprocessamento, com
  folga, sem transformar o bucket em arquivo permanente.
- **90 dias no raw com dado pessoal** bastam para refazer uma carga recente.
  Depois disso o dado continua na Bronze. A contrapartida é assumida: para
  essas fontes, reprocessar do raw só funciona dentro de 90 dias.
- **5 anos na Bronze com dado pessoal** acompanham os prazos de prescrição de
  cinco anos mais comuns — trabalhista, tributário e de consumo. **O jurídico da
  Alup valida** ou indica outro prazo.
- **90 dias em `dev`**: desenvolvimento não precisa de histórico longo de dado
  pessoal real, e a ness. só acessa dado real nesse período (ADR 011).

## Direito de eliminação do titular (art. 18, VI)

A Bronze só recebe acréscimos (regra 4). O pedido de eliminação de um titular é
a exceção, sempre registrada:

1. A encarregada recebe o pedido e confirma que não há hipótese de conservação
   (art. 16).
2. As linhas do titular são apagadas da Bronze com `DELETE`, e os objetos
   correspondentes, do raw.
3. As views da Silver refletem a exclusão na hora; a Gold materializada, na
   execução seguinte.
4. O atendimento é registrado com data, tabelas afetadas e quem executou.

## Fim do contrato (cláusula 8.3)

- Na homologação final e no handoff, a ness. **perde o acesso** aos projetos e
  **elimina qualquer cópia** de dado que tenha sob sua posse.
- O dado da plataforma é da Alup e continua sob esta política depois do
  handoff.
- O procedimento, com lista de verificação, vai para o runbook.

## O que muda em `infra/` depois da aprovação

- Regras de ciclo de vida no bucket raw: exclusão por idade, por prefixo de
  fonte, e exclusão de versões antigas. Hoje só existe a mudança para NEARLINE.
- Expiração de partição nas tabelas Bronze com dado pessoal; hoje nenhuma
  expira.
- Expiração padrão no dataset `qualidade`.
- Bucket de log dedicado aos logs de auditoria de acesso a dados.
- Variáveis de prazo por ambiente nos `.tfvars`.

## Aprovação

| Papel | Nome | Data |
|---|---|---|
| Proposta | ness. | 11/09/2026 |
| Encarregada | Rosimeire Miler dos Santos | |
| Controladora | Alup | |
