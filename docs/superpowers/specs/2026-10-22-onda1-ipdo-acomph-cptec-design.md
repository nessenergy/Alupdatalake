# Onda 1: IPDO, ACOMPH e CPTEC — especificação

Data: 22/10/2026. Origem: o pedido de fechar os três itens da Onda 1 que seguiam sem entrega (relatório de 22/10, seção da Onda 1).
Base: ADR [027](../../arquitetura/decisoes/027-ons-operacional-ipdo-acomph.md), [028](../../arquitetura/decisoes/028-cptec-acesso.md) e
[029](../../arquitetura/decisoes/029-previsao-do-tempo-fonte.md).

## 1. O que mudou desde as ADRs, medido em 22/10/2026

| Fonte | Em 03/10 | Em 22/10 | Efeito |
|---|---|---|---|
| CPTEC (`servicos.cptec.inpe.br/XML`) | 403 em tudo, de dev e de dentro do GCP | **200**, com limite de 120 requisições por janela (`x-ratelimit-limit`); 27 capitais conferidas, XML em ISO-8859-1, 6 dias de previsão | a saída A da ADR 029 passa a valer: **dá para construir** |
| ONS, IPDO | PDF único, sem histórico, "uso interno" | sem verificação nova; o SINtegre responde 403 (portal) e `integra.ons.org.br` 503 | a decisão da ADR 027 não muda |
| ONS, ACOMPH | sem origem pública; hipótese de SINtegre com cadastro | a Alupar disse (20/10) que tem **login e senha do ONS**; a API do SINtegre não tem documentação pública que eu tenha achado (busca de 22/10 sem resultado útil) | falta o contrato da API e a credencial: **não dá para construir às cegas** |

## 2. Decisões

### 2.1 CPTEC — construir (executado)

- Conector `cptec_previsao`, com os 7 componentes, para as **27 capitais** (uma requisição cada).
- **Retrato, sem janela**: os dias previstos são de hoje em diante e a janela da CLI termina ontem; recortar por janela devolveria zero linhas. Mesmo padrão de `ace_prc` e `aneel_siga`. O histórico de previsões nasce do Bronze append-only, uma foto por emissão.
- Silver deduplica por cidade, dia previsto e emissão; Gold `previsao_tempo_capitais` traz a emissão mais recente de cada cidade e dia, com a antecedência da previsão.
- Falha alto: 403, corpo vazio ou XML sem previsão derrubam a execução. XML lido com `defusedxml`.
- **Lacunas ditas de frente**: a origem não traz precipitação em mm, e a "previsão climática" da cláusula não é coberta. A escolha das 27 capitais é minha; a Alupar pode preferir os municípios das usinas.

### 2.2 IPDO — manter a saída C da ADR 027

Sem conector. O PDF é preliminar, sem histórico e marcado "uso interno"; os números já vêm dos conjuntos abertos, e a demanda máxima entrou como `ons_demanda_maxima`. O que falta é o **aceite por escrito da Alupar** à substituição. Nada a executar até lá.

### 2.3 ACOMPH — preparar, não construir

Só se constrói com a credencial e o contrato da API do SINtegre. O que falta, por dono:

| Falta | De quem |
|---|---|
| Qual produto o login da Alupar enxerga (ACOMPH está nele?) | Alupar (Leonardo) |
| Documentação ou exemplo de chamada da API do SINtegre (autenticação, listagem e download do produto) | ONS, via Alupar |
| Formato do segredo: proposta `alupdata-ons-credenciais` com JSON `usuario` e `senha` | ness., depende do aceite da Alupar |
| Declarar o segredo em `infra/` (regra 2 e 5) | ness., ao receber o aceite |

Escrever o conector antes disso seria inventar a API: o BBCE foi escrito contra documentação pública, e aqui não há nenhuma.

## 3. Fora do escopo

- Previsão climática (mensal e sazonal) do CPTEC.
- Mapeamento de capital a submercado ou a usina.
- Conversão do código de tempo em texto (a tabela de códigos do CPTEC não foi conferida contra a documentação oficial).

## 4. Critérios de aceite

- `make componentes` com 59 de 59, `ruff`, `bandit` e a suíte verdes; Dataform compila no CI.
- Primeira carga em dev com 162 linhas (27 capitais x 6 dias) e `Conferir cargas` mostrando `cptec_previsao`.
- ADRs 028 e 029 com o adendo de 22/10.
