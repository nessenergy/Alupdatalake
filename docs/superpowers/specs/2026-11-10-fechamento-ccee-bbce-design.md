# Fechamento da CCEE (item 2.1) e do BBCE — especificação

Data: 10/11/2026. Origem: frente D da fila (item 2.1, #462, #463; BBCE, #434 e item 1 da fila).

## D1. Cadastro de pontos sem alarme falso

**Fato (09/11):** o cadastro (`listarPontoMedicao` e `obterPontoMedicao`) devolve `errorCode 4001` ao perfil `6166`. **Hipótese,
não confirmada pela Alupar (#462):** a CCEE nega o cadastro a esse perfil. O job `ingestao-ccee-pi-ponto-medicao` roda no dia 2
(próximo: 02/12) e hoje sai com código 1, o que dispara o alerta `job_falhou` (e-mail), sem que haja o que a ness. corrigir.

**Decisão:** `4001` vira o status de execução **`SEM_PERMISSAO`**, distinto de `ERRO`.

- A `CceeError` passa a carregar o `errorCode` da CCEE (`codigo`). O conector do cadastro converte `4001` em
  `SemPermissaoError`; qualquer outro erro continua `ERRO`.
- O runner grava a execução com `status = SEM_PERMISSAO` e o texto completo do erro (`errorCode`, `message`, `transactionId`),
  loga em **WARNING** e **sai com código 0**. Sem código de saída diferente de zero o `job_falhou` não dispara, então o
  Terraform de agendamento e de monitoramento não muda.
- O erro continua visível: `bronze._execucoes.erro` guarda o texto, o log traz o aviso, e a `gold.saude_ingestao` conta
  `SEM_PERMISSAO` como erro (`ultimo_erro`) e marca `aguardando_credencial`, de modo que o painel mostra "aguardando credencial"
  em vez de vermelho. A fonte segue sem sucesso (`SEM_SUCESSO`) até a Alupar resolver, o que é verdade.
- Opção descartada: manter o alerta. Ele avisaria uma vez por mês de um problema já sabido e dependente de terceiro, e treinaria
  a equipe a ignorar o e-mail. Também descartada: engolir o erro e gravar `SUCESSO`, que esconderia o problema.
- Efeito aceito: a linhagem registra `FAIL` (status diferente de `SUCESSO`), o que é correto, pois não houve carga.

Se a Alupar confirmar que o `6166` não terá acesso ao cadastro, a decisão é outra (retirar o job ou deixar o `pontos` da
credencial como via definitiva); nada aqui a impede.

## D2. Dicionário da medição

`docs/dicionario-dados/ccee_pi_medida.md` já traz os campos e a origem→Bronze→Silver→Gold. Entram: a linhagem completa (credencial,
campo opcional `pontos`, cadastro, Gold `perfil_vigente_ponto_medicao`), a regra da hora que termina
(`data_referencia = (fim_periodo − 1 h).date()`) e as pendências da #462 (unidade, regra da hora, alcance do `6166`).
Sem código de ponto nem valor reais: só placeholders. O dicionário do cadastro ganha o status `SEM_PERMISSAO`.

## D3. BBCE

Conferência dos 7 componentes do `bbce_curva_forward` no repositório (conector, Bronze, Silver, Gold, testes, agendamento,
documentação) e das asserções de chave; o que faltar é corrigido. A contagem em hml só se confere no ambiente (sem BigQuery aqui).
O resultado está no PR.
