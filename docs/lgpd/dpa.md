# Registro do DPA — tratamento de dados pelo Google Cloud

**Versão** 0.1 · **Data** 2026-09-11 · **Situação**: registro técnico, para
conferência da controladora

Este arquivo **não é o DPA**. O DPA é o *Aditivo sobre Tratamento de Dados do
Cloud* do Google, incorporado ao contrato de nuvem da Alupar. Aqui ficam
registrados o que ele prevê e o que isso significa para a plataforma, como
pede a [ADR 023](../arquitetura/decisoes/023-regiao-us-central1.md). O resultado
alimenta o [RIPD](ripd.md) (R03) e o [RoPA](ropa.md).

| Item | Registro |
|---|---|
| Documento | Aditivo sobre Tratamento de Dados do Cloud (clientes) — [versão em português](https://services.google.com/fh/files/misc/pt-br-cloud-data-processing-addendum-customers.pdf); [versão web](https://cloud.google.com/terms/data-processing-addendum) |
| Versão consultada | A vigente em 11/09/2026. O documento não traz data de versão |
| Partes | Google, como operador, e a Alupar, como cliente do contrato de nuvem. A entidade Google é a indicada nesse contrato. **[ALUP]** confirmar a entidade e onde fica a cópia do contrato |
| Situação informada pela Alup | O DPA existe e está em vigor (11/09/2026) |

## Transferência internacional

O Aditivo tem termos específicos para o Brasil (Apêndice 3, seção "Brasil").

- **Transferência Restrita BR** é a transferência de dado sujeito à LGPD para
  país que a ANPD não reconhece como adequado. O ambiente fica em `us-central1`,
  nos Estados Unidos. Salvo decisão de adequação posterior, a transferência da
  plataforma se enquadra aqui.
- **Mecanismo**, pela seção 3.1 dos termos brasileiros:
  1. se o Google tiver adotado uma *Solução Alternativa de Transferência*,
     informa o cliente e a segue;
  2. se não tiver, valem as **SCCs do Brasil** — as cláusulas-padrão
     contratuais da ANPD (art. 33, II, *b*, da LGPD). A variante depende do
     endereço da entidade Google contratante:
     - no Brasil, que é País Adequado por definição: SCCs do Brasil
       (Operador para Operador, Exportador Google), para o repasse do Google aos
       subprocessadores;
     - fora do Brasil: SCCs do Brasil (Controlador para Operador) ou (Operador
       para Operador), conforme o papel do cliente.
- **Textos das SCCs:** [controlador para operador](https://cloud.google.com/sccs/br-c2p?hl=pt-br),
  [operador para operador](https://cloud.google.com/sccs/br-p2p?hl=pt-br) e
  [operador para operador, exportador Google](https://cloud.google.com/sccs/br-p2p-intra-group?hl=pt-br).
- **Instruções.** O Google notifica o cliente quando, na opinião dele, uma
  instrução contraria a LGPD ou a lei brasileira o impede de cumpri-la.

**[ALUP]** Com a entidade contratante confirmada, registrar aqui qual variante
se aplica.

## Outras garantias do Aditivo

| Tema | O que o Aditivo prevê |
|---|---|
| Incidente de segurança | O Google notifica o cliente "*promptly and without undue delay*" (seção 7.2.1 da versão web), sem prazo fixo em horas. A comunicação à ANPD e aos titulares continua sendo obrigação da controladora (art. 48) |
| Subprocessadores | A lista pública fica em [cloud.google.com/terms/subprocessors](https://cloud.google.com/terms/subprocessors). Subprocessador novo é notificado **pelo menos 30 dias** antes de tratar o dado. O cliente pode se opor em até **90 dias** depois da notificação, rescindindo o contrato sem motivo (seção 11.4) |
| Exclusão ao fim do contrato | Até 30 dias de período de recuperação e, depois, **no máximo 180 dias** para excluir o dado (seção 6.2) |
| Certificações | ISO 27001 e relatórios SOC, renovados a cada 12 meses (seção 7.4) |
| Auditoria | Documentação de segurança disponível ao cliente; auditoria pelo cliente quando a lei aplicável exigir, podendo haver cobrança (seção 7.5) |

## O que isso significa para a plataforma

- **R03 do RIPD** fica em nível baixo: há mecanismo do art. 33 previsto em
  contrato.
- **Prazo de exclusão.** Excluir um dado na plataforma (política de retenção ou
  pedido do titular) não o apaga do Google na hora: pelo Aditivo, o Google tem
  até 180 dias. O prazo informado ao titular deve considerar isso.
- **Incidente.** O plano de resposta da Alup não deve depender de um prazo em
  horas vindo do Google; a notificação do Aditivo é "sem demora indevida".
- **Subprocessadores.** Alguém da Alup precisa receber as notificações de
  subprocessador novo, que chegam pelo contato cadastrado no contrato de nuvem.
  **[ALUP]** indicar quem.

## Relação entre a Alup e a ness.

A ness. atua como operadora durante o desenvolvimento, sob o contrato
CPS-01025/2026. A cláusula 8ª trata de segurança, e a 8.3 da eliminação dos
dados após a homologação. Não há subcontratação de dado da ness. para
terceiros.
