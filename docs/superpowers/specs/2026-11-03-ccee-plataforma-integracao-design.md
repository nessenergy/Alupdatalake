# CCEE Plataforma de Integração (item 2.1) — especificação

Data: 03/11/2026. Origem: item 2.1 "CCEE agente credenciado" (32 h) da Onda 2 e a [#260](https://github.com/nessenergy/Alupdatalake/issues/260).
Base: ADR [018](../../arquitetura/decisoes/018-vias-de-acesso-a-ccee.md), que registrou a Plataforma de Integração como escopo candidato.

## 1. O que está verificado

Fonte: coleção Postman pública da Plataforma de Integração, lida em 03/11 pela API do próprio documenter. A leitura de 03/11 foi parcial (cerca de 500 mil dos 774 mil caracteres ficaram de fora). **Em 06/11 a coleção foi lida por inteiro** e o resultado está em [`ccee_plataforma_integracao.md`](../../dicionario-dados/ccee_plataforma_integracao.md): 57 operações, 51 de leitura, com o XML de requisição de todas e 66 respostas de exemplo. A tabela abaixo continua valendo; o catálogo a complementa.

| Fato | Valor |
|---|---|
| Endereço | produção `https://servicos.ccee.org.br:443`; **piloto** `https://piloto-servicos.ccee.org.br:443`; WSDL na porta 442 |
| Protocolo | SOAP/XML, um serviço por caminho (`/ws/v2/<Servico>BSv2`) e uma `SOAPAction` por operação |
| Autenticação documentada | **WS-Security UsernameToken** no envelope (`Username`, `Password`) mais o cabeçalho obrigatório **`codigoPerfilAgente`** |
| Adesão | "possuir um certificado digital e realizar um cadastro na CCEE" |
| Limite | 400 chamadas por minuto por usuário sistêmico por serviço; erro 2003 ao exceder |
| Paginação | requisição `paginacao/numero` e `quantidadeItens` (menor que 100); resposta `totalPaginas` e `quantidadeTotalItens` |
| Operações lidas | ativos de medição, expressões contábeis, modelagens, perfis, representações, participantes |
| PLD | não apareceu nos trechos lidos; o PLD segue pela via pública (ADR 018) |

## 2. O que está em conflito e não decidimos

O Fabrizio (Alupar, 03/11) disse que **não há usuário**: o certificado é "espetado" e a assinatura usa a senha dele. A documentação diz que o envelope leva usuário e senha. As duas coisas podem ser verdade ao mesmo tempo, e **não sabemos qual**:

| Hipótese | Efeito no que construímos |
|---|---|
| H1: o certificado serve ao **cadastro**, e a CCEE emite um usuário sistêmico e uma senha | o .pfx não entra no conector; entram `usuario`, `senha` e `codigo_perfil_agente` |
| H2: o certificado é de **cliente no TLS** (mTLS) | o conector abre a sessão com o .pfx; o usuário e a senha podem ainda ser exigidos |
| H3: o envelope é **assinado** com o certificado | o conector assina com o .pfx; o desenho muda |

Três perguntas à Alupar fecham isso (Fabrizio e Leonardo):

1. Existe um **usuário sistêmico e senha** da Plataforma de Integração para a Alupar? Se sim, quem os guarda?
2. Qual é o **código do perfil de agente** (`codigoPerfilAgente`) a usar?
3. O certificado enviado é para **assinar no portal** (cadastro) ou para a **conexão** com `servicos.ccee.org.br`? O acesso ao **piloto** está liberado?

## 3. Decisões (valem nas três hipóteses)

- **Cliente SOAP:** `requests` com envelope montado à mão e `defusedxml` na leitura. Sem `zeep`: uma dependência a menos para o `pip-audit`, e o mesmo `src/core/http.py` dos demais conectores.
- **Retrato, sem janela:** os ativos de medição não têm competência (usam o mês da requisição). Mesmo padrão de `ace_prc` e `aneel_siga`; o histórico nasce do Bronze append-only.
- **Primeira entidade: `ccee_pi_ativo_medicao`.** Traz `ceg` e `codigo` do ativo, que ajudam o de-para de usina da #141. Prefixo `ccee_pi_` para não colidir com `ccee_perfil` e `ccee_agente` (CKAN).
- **Teste de autenticação:** `Listar Representacao` (corpo sem parâmetros). É inferência da documentação, a confirmar na primeira chamada.
- **Falha alto:** resposta com `Fault`, erro 2003 ou corpo vazio derruba a execução; a mensagem de erro nunca inclui senha, usuário ou conteúdo do certificado.
- **Ambiente:** dev e hml usam o **piloto** se a Alupar liberar o acesso; senão, a produção da CCEE em somente leitura, com a decisão registrada.
- **Segredos:** `alupdata-ccee-certificado` (.pfx, já na v1 em dev e hml) e `alupdata-ccee-credenciais` (JSON, hoje só `senha_certificado`). Campos novos entram como **nova versão** do mesmo segredo, sem mudar `infra/`.

### Adendo de 06/11/2026: o que a leitura completa muda

- **Não é preciso pedir o XML de cada endpoint à Alupar.** A coleção já traz o corpo de todas as 57 operações. O pedido só vale para os campos que a coleção não esclarece.
- **O ponto de exemplo pode vir da própria CCEE.** `Listar pontos de medição por agente relacionado`, `Listar perfis` e `Listar participantes` são cadastros, que têm exceção à regra de só consultar o que é do agente. Depende de a autorização funcionar, então o usuário dedicado continua sendo o gargalo.
- **Hipótese a verificar, não afirmada:** uma leitura de cadastro separaria as causas do `Server.2001`. Se ela também for negada, o problema é usuário ou perfil; se só a medição for, é permissão sobre o ponto. Vale uma tentativa única, depois do usuário dedicado.
- **Perfil:** para consultas de medição, o guia da CCEE manda usar o perfil do **agente principal do ponto**, devolvido por `Listar pontos de medição`. A pergunta "o 6166 vale para todos os pontos?" continua certa. O perfil também diferencia usina e carga do mesmo agente.
- **Piloto (pergunta 3):** os guias da CCEE dizem que o piloto usa os **mesmos usuários, senhas e certificados** da produção, com dados defasados em um mês. Não depende de liberação da Alupar; a decisão de ambiente da seção 3 pode apontar para o piloto.
- **Hipóteses da seção 2:** os guias oficiais indicam SSL mútuo com o certificado aderido (H2) **e** usuário e senha sistêmicos no envelope, criados na adesão (parte de H1). Não há indício de assinatura do envelope (H3). Segue pendente saber quem na Alupar detém o usuário sistêmico.
- **O erro (atualizado no mesmo dia):** o manual do serviço *Informar Coleta Medição* documenta o `Server.2001` / `Acesso Negado` como erro de **autenticação**, com a mensagem de exemplo "Usuario ou senha invalidos". Perfil não autorizado tem erro próprio (`Rejected: ...`). Logo, a causa mais provável da tentativa de 05/11 é usuário ou senha, ou permissão no serviço, e não o perfil. Não é prova: o conector descartou o campo `message` e o `transactionId` do `detail`, que decidiriam. Ver o catálogo, seção Erros.
- **Pequena mudança de código a propor:** incluir `errorCode`, `message` e `transactionId` (nunca o conteúdo do envelope) no erro do `ccee_pi_sessao`. O `transactionId` também é o que a CCEE pede ao abrir chamado.
- **Certificado:** validade menor que 395 dias. Renovação anual, com dono e data.

## 4. Fora do escopo

Contratos, montantes de energia, topologia, importação de arquivo e parcelas. Entram uma entidade por vez, depois da primeira passar.

## 5. Critérios de aceite

- As três perguntas respondidas e a hipótese registrada em ADR (adendo à 018).
- Teste de autenticação em hml devolvendo `ok` sem registrar segredo no log.
- `ccee_pi_ativo_medicao` com os 7 componentes, `make componentes` verde, ruff, bandit e a suíte verdes, e Dataform compilando no CI.
- Primeira carga em hml conferida em `Conferir cargas`.
