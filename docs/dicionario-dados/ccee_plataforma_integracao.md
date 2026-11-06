# Plataforma de Integração da CCEE — catálogo de operações

Fonte: coleção Postman pública da Plataforma de Integração
([documenter](https://documenter.getpostman.com/view/12351215/UzJJucpF)), lida **por inteiro** em 06/11/2026 pela API do próprio
documenter. Substitui a leitura parcial de 03/11 citada na [spec do item 2.1](../superpowers/specs/2026-11-03-ccee-plataforma-integracao-design.md).
Só documentação: nenhuma chamada à CCEE foi feita para montar este catálogo e nenhum dado de agente consta aqui.

## O que a leitura completa estabelece

| Fato | Valor |
|---|---|
| Operações em `servicos.ccee.org.br` | 57, das quais 51 de leitura e 6 de escrita |
| XML de requisição | **a coleção traz o XML de todas as operações**; não é preciso pedi-los à Alupar |
| Respostas de exemplo | 66 na coleção (valores fictícios) |
| Produção | `https://servicos.ccee.org.br:443` |
| Portas | 442 (WSDL) e 443, tanto em produção quanto no piloto |
| Piloto | `https://piloto-servicos.ccee.org.br`. **Mesmos usuários, senhas e certificados da produção.** Tem todos os serviços, menos a DRI. Dados defasados em um mês, atualizados no primeiro sábado do mês; não funciona 24/7 |
| Duas verificações | (1) **autenticação**: usuário e senha *sistêmicos* e certificado; (2) **autorização**: `codigoPerfilAgente` no cabeçalho. Perfil não autorizado devolve `Rejected: Usuário não está autorizado a usar o codigoPerfilAgente` |
| Conexão | **SSL mútuo**: a chave privada do certificado previamente aderido (`.pfx`, `.p12`, `.jks`) acompanha toda chamada a `*.ccee.org.br` |
| Certificado | servidor web SSL, ICP-Brasil, RSA 2048, SHA-2, validade **menor que 395 dias** (renovação anual) e *subject* único por certificado |
| Usuário | o *usuário sistêmico* nasce da adesão à Plataforma, feita no SGP junto com o cadastro do certificado |
| Autenticação no envelope | WS-Security `UsernameToken` (`Username`, `Password`) |
| Perfil | `messageHeader/codigoPerfilAgente`, **obrigatório em toda requisição**. Não confundir com o código do agente; consulta pelo serviço de perfis ou pela planilha pública Infomercado Dados Individuais |
| Perfil na medição | o guia de medições manda usar o perfil do **agente principal do ponto** (Conectante ou Medição), que `Listar pontos de medição` devolve no retorno. Pode ser diferente do perfil do solicitante. O perfil também diferencia usinas e cargas do mesmo agente |
| Limite | 400 chamadas por minuto por usuário sistêmico e por serviço (erro `2003`); `SituacaoColetaMedicao` tem 60 por hora |
| Paginação | `paginacao/numero` e `paginacao/quantidadeItens` (menor que 100; 500 em `MedidaCincoMinutosBSv2`) |
| Restrição de acesso | o agente só consulta o que é seu ou de quem representa; **cadastros** (ativos, parcelas, agentes, perfis) têm exceção |

## Catálogo

Escrita não entra no escopo do AlupData: o conector só lê. `Paginada` indica se o XML de exemplo tem o bloco `paginacao`.

| Grupo | Operação | Caminho | SOAPAction | Paginada | Tipo |
|---|---|---|---|---|---|
| Ativos / Ativos de medição | Listar ativos de medição | `/ws/v2/AtivoMedicaoBSv2` | `listarAtivoMedicao` | sim | leitura |
| Ativos / Expressões contábeis | Listar expressões contábeis | `/ws/v2/ExpressaoContabilBSv2` | `listarExpressaoContabil` | sim | leitura |
| Ativos / Expressões contábeis | Listar subexpressões contábeis | `/ws/v2/ExpressaoContabilBSv2` | `listarExpressaoContabil` | sim | leitura |
| Ativos / Modelagens de ativo | Listar modelagens de ativo | `/ws/v2/ModelagemAtivoBSv2` | `listarModelagemAtivo` | sim | leitura |
| Ativos / Parcelas de ativos | Listar parcelas associadas a contratos | `/ws/v2/ParcelaAtivoBSv2` | `listarParcelaAtivo` | sim | leitura |
| Ativos / Parcelas de ativos | Listar parcelas associadas a contratos PROINFA | `/ws/v2/ParcelaAtivoBSv2` | `listarParcelaAtivo` | sim | leitura |
| Ativos / Parcelas de ativos | Listar parcelas de ativos | `/ws/v2/ParcelaAtivoBSv2` | `listarParcelaAtivo` | sim | leitura |
| Ativos / Parcelas de carga | Listar parcelas de carga | `/ws/v2/ParcelaCargaBSv2` | `listarParcelaCarga` | sim | leitura |
| Ativos / Parcelas de usina | Listar parcelas de usina | `/ws/v2/ParcelaUsinaBSv2` | `listarParcelaUsina` | sim | leitura |
| Ativos / Topologias | Listar topologias por ativo | `/ws/v2/TopologiaBSv2` | `listarTopologia` | sim | leitura |
| Cadastros / Contato | Listar Contato | `/ws/v2/ContatoBSv2` | `listarContato` | não | leitura |
| Cadastros / Contato | Obter Contato | `/ws/v2/ContatoBSv2` | `listarContato` | não | leitura |
| Cadastros / Participante de mercado | Listar participantes | `/ws/v2/ParticipanteMercadoBSv2` | `listarParticipanteMercado` | sim | leitura |
| Cadastros / Perfil de participante de mercado | Listar perfis | `/ws/v2/PerfilParticipanteMercadoBSv2` | `listarPerfilParticipanteMercado` | sim | leitura |
| Cadastros / Representacao | Listar Representacao | `/ws/v2/RepresentacaoBSv2` | `listarRepresentacao` | sim | leitura |
| Cadastros / Representacao | Obter Representacao | `/ws/v2/RepresentacaoBSv2` | `obterRepresentacao` | sim | leitura |
| Contratos / Listar e Obter Contratos | Listar contratos livres (ACL) | `/ws/v2/ContratoBSv2` | `listarContrato` | sim | leitura |
| Contratos / Listar e Obter Contratos | Listar contratos regulados (ACR) | `/ws/v2/ContratoBSv2` | `listarContrato` | sim | leitura |
| Contratos / Listar e Obter Contratos | Obter contrato livre (ACL) | `/ws/v2/ContratoBSv2` | `obterContrato` | não | leitura |
| Contratos / Listar e Obter Contratos | Obter contrato regulado (ACR) | `/ws/v2/ContratoBSv2` | `obterContrato` | não | leitura |
| Contratos / Montantes de energia | Listar montantes - ano contratual | `/ws/v2/MontanteEnergiaBSv2` | `listarMontanteEnergia` | sim | leitura |
| Contratos / Montantes de energia | Listar montantes - obrigação de entrega | `/ws/v2/MontanteEnergiaBSv2` | `listarMontanteEnergia` | sim | leitura |
| Contratos / Montantes de energia | Listar montantes de energia anual | `/ws/v2/MontanteEnergiaBSv2` | `listarMontanteEnergia` | sim | leitura |
| Contratos / Montantes de energia | Listar montantes de energia mensal | `/ws/v2/MontanteEnergiaBSv2` | `listarMontanteEnergia` | sim | leitura |
| Contratos / Montantes de energia | Listar montantes modularizados | `/ws/v2/MontanteEnergiaBSv2` | `listarMontanteEnergia` | sim | leitura |
| Contratos / Montantes de energia | Listar montantes médios | `/ws/v2/MontanteEnergiaBSv2` | `listarMontanteEnergia` | sim | leitura |
| Contratos / Obter Empreendimento | Obter empreendimento | `/ws/v2/EmpreendimentoBSv2` | `obterEmpreendimento` | não | leitura |
| Contratos / Registro e validação de contratos | Importar arquivo XML | `/ws/cntr/ImportarArquivoBSv1` | `importarArquivo` | não | escrita |
| Contratos / Registro e validação de contratos | Importar arquivo XML Contrato Simplificado | `/ws/cntr/ImportarArquivoBSv1` | `importarArquivo` | não | escrita |
| Contratos / Resultado do processamento de contratos | Obter resultado do processamento | `/ws/cntr/ResultadoProcessamentoBSv1` | `obterResultadoProcessamento` | não | leitura |
| DRI / Acrônimos mapeados | Listar acrônimo mapeado por id | `/ws/v2/AcronimoBSv2` | `listarAcronimo` | sim | leitura |
| DRI / Acrônimos mapeados | Listar todos acrônimos mapeados | `/ws/v2/AcronimoBSv2` | `listarAcronimo` | sim | leitura |
| DRI / Eventos contábeis | Listar divulgações de eventos contábeis | `/ws/v2/DivulgacaoEventoContabilBSv2` | `listarDivulgacaoEventoContabil` | sim | leitura |
| DRI / Relatórios mapeados | Listar relatórios mapeados | `/ws/v2/RelatorioBSv2` | `listarRelatorio` | sim | leitura |
| DRI / Resulados de relatórios | Listar resultados de relatórios | `/ws/v2/ResultadoRelatorioBSv2` | `listarResultadoRelatorio` | sim | leitura |
| DRI / Resultados de acrônimos | Acrônimo com dimensão horária - CQ e,j | `/ws/v2/ResultadoBSv2` | `listarResultado` | sim | leitura |
| DRI / Resultados de acrônimos | Acrônimo com dimensão horária - CQ_EFE_CE e,j | `/ws/v2/ResultadoBSv2` | `listarResultado` | sim | leitura |
| DRI / Resultados de acrônimos | Acrônimos com dimensão mensal | `/ws/v2/ResultadoBSv2` | `listarResultado` | sim | leitura |
| DRI / Resultados de acrônimos | Acrônimos com dimensão semanal | `/ws/v2/ResultadoBSv2` | `listarResultado` | sim | leitura |
| Medição / Coleta Medicao | Informar Coleta Medicao | `/ws/v2/ColetaMedicaoBSv2` | `informarColetaMedicao` | não | escrita |
| Medição / Listar Medida | Listar medidas consolidadas | `/ws/medc/ListarMedidaBSv1` | `listarMedida` | não | leitura |
| Medição / Listar Medida | Listar medidas faltantes | `/ws/medc/ListarMedidaBSv1` | `listarMedida` | não | leitura |
| Medição / Listar Medida | Listar medidas finais | `/ws/medc/ListarMedidaBSv1` | `listarMedida` | não | leitura |
| Medição / Medidas - 5 minutos | Listar Medidas - 5 Minutos por medidor | `/ws/v2/MedidaCincoMinutosBSv2` | `listarMedidaCincoMinutos` | sim | leitura |
| Medição / Situacao Coleta Medicao | Obter Situacao Coleta Medicao | `/ws/v2/SituacaoColetaMedicaoBSv2` | `obterSituacaoColetaMedicao` | não | leitura |
| Notificação de eventos (webhook) / Eventos para notificação | Listar eventos disponíveis para notificação | `/ws/v2/EventoNotificacaoBSv2` | `listarEventoNotificacao` | sim | leitura |
| Notificação de eventos (webhook) / Preferências de notificação | Atualizar preferência de notificação | `/ws/v2/PreferenciaNotificacaoBSv2` | `atualizarPreferenciaNotificacao` | não | escrita |
| Notificação de eventos (webhook) / Preferências de notificação | Excluir preferência de notificação | `/ws/v2/PreferenciaNotificacaoBSv2` | `excluirPreferenciaNotificacao` | não | escrita |
| Notificação de eventos (webhook) / Preferências de notificação | Incluir preferência de notificação | `/ws/v2/PreferenciaNotificacaoBSv2` | `incluirPreferenciaNotificacao` | não | escrita |
| Notificação de eventos (webhook) / Preferências de notificação | Listar preferências de notificação | `/ws/v2/PreferenciaNotificacaoBSv2` | `listarPreferenciaNotificacao` | sim | leitura |
| Notificação de eventos (webhook) / Resultados de notificação | Listar resultados de notificação | `/ws/v2/ResultadoNotificacaoBSv2` | `listarResultadoNotificacao` | sim | leitura |
| PLD / Listar PLD | Listar PLDs horários | `/ws/prec/PLDBSv1` | `listarPLD` | sim | leitura |
| PLD / Listar PLD | Listar PLDs mensais | `/ws/prec/PLDBSv1` | `listarPLD` | sim | leitura |
| PLD / Listar PLD | Listar PLDs semanais | `/ws/prec/PLDBSv1` | `listarPLD` | sim | leitura |
| Pontos de Medição / Cadastros de pontos de medição | Listar pontos de medição por agente relacionado | `/ws/v2/PontoMedicaoBSv2` | `listarPontoMedicao` | sim | leitura |
| Pontos de Medição / Cadastros de pontos de medição | Obter ponto de medição por código | `/ws/v2/PontoMedicaoBSv2` | `obterPontoMedicao` | sim | leitura |
| Pontos de Medição / Cadastros de pontos mapeados | Obter ponto mapeado por código | `/ws/v2/PontoMapeadoBSv2` | `obterPontoMapeado` | não | leitura |

Não estão na tabela os endpoints de recebimento de notificações (webhook) e de retorno de situação da coleta: ficam do lado do agente, não da CCEE.

## Pontos que orientam o conector

- **Cadastros primeiro.** `Listar perfis`, `Listar participantes` e `Listar pontos de medição por agente relacionado` permitem descobrir perfil e pontos sem que a Alupar os informe um a um.
- **Medição** tem três variantes em `ListarMedidaBSv1` (consolidadas, faltantes, finais), todas com a `SOAPAction` `listarMedida`. A resposta é horária e traz ponto, subtipo, status e quatro grandezas (geração e consumo, ativo e reativo).
- **Medição de 5 minutos** é um serviço à parte (`MedidaCincoMinutosBSv2`, por medidor).
- **Descobrir o perfil do ponto:** chamar `Listar pontos de medição por agente relacionado` com o perfil que já temos e usar o perfil devolvido em cada ponto nas consultas de medição.
- **Piloto antes da produção.** Usa as mesmas credenciais, então a primeira tentativa de leitura pode ser no piloto. Atenção à defasagem de um mês dos dados.
- **Certificado vence em menos de um ano.** A renovação precisa de dono e de data, e entra como nova versão do segredo `alupdata-ccee-certificado`.

## Fontes

- Coleção Postman atual (documenter `12351215/UzJJucpF`), lida por inteiro.
- Repositório [`devccee/postman-collections`](https://github.com/devccee/postman-collections): a mesma coleção em versão anterior (julho de 2022, menor que a do documenter) e o passo a passo de SSL mútuo no Postman.
- Guias [`devccee/guia-primeiros-passos`](https://github.com/devccee/guia-primeiros-passos) e [`devccee/guia-medicoes`](https://github.com/devccee/guia-medicoes), lidos em 06/11/2026.
- **Ainda não lidos**, só citados nos guias: Manual de Autenticação, Manual de Alertas e Exceções (onde o `Server.2001` deve estar descrito), manual de adesão e atualização de certificado no SGP e o manual de `ListarMedida`. Estão em `https://www.ccee.org.br/documentos/plataforma-de-integracao`, que respondeu 403 ao acesso automatizado de 06/11.
- Atendimento da CCEE: `atendimento@ccee.org.br` (assunto "Erro no Ambiente piloto" para o piloto).
