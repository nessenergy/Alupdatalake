# ADR 029 — Previsão do tempo de 7 dias: o CPTEC também responde 403 de dentro do GCP; nenhuma alternativa pública serve

**Status**: proposto, depende de resposta do INPE e de decisão da Alup · **Data**: 2026-10-03 · **Complementa** a
[ADR 028](028-cptec-acesso.md)

## Contexto

A ADR 028 achou 403 em todo caminho do webservice do CPTEC a partir da máquina de desenvolvimento e deixou aberta a
hipótese de que fosse bloqueio do IP dessa máquina. Esta ADR fecha a hipótese com a chamada saindo de dentro do GCP, e
avalia se alguma fonte pública substitui o CPTEC para a "previsão do tempo de 7 dias" da cláusula 4ª, Onda 1.

## Evidência (03/10/2026)

A sonda é o subcomando `alupdata sondar` (lista fixa de endereços em `src/core/sonda.py`), executado pelo workflow
`Sondar rede` num Cloud Run Job de cada ambiente. O resultado é gravado em `sondas/<nome>/` no bucket raw.

| Ambiente | Endereço | Status | Tipo | Corpo |
|---|---|---|---|---|
| dev (`us-central1`) | `servicos.cptec.inpe.br/XML/listaCidades?city=sao%20paulo` | **403** | text/html | "403 Forbidden", 199 bytes |
| dev | `servicos.cptec.inpe.br/XML/cidade/7dias/244/previsao.xml` | **403** | text/html | idem |
| hml | os mesmos dois endereços | **403** | text/html | idem |

Conclusão: o bloqueio **não é do IP da máquina de desenvolvimento**. Vale para o IP de saída do GCP também.

Alternativas avaliadas (leitura pública, da máquina de desenvolvimento, em 03/10/2026):

| Fonte | Resultado | Serve? |
|---|---|---|
| API de previsão do INMET (`apiprevmet3.inmet.gov.br/previsao/{codigo_ibge}`) | 200, JSON, **5 dias** (03 a 07/10), com temperatura, umidade e vento, **sem campo de precipitação**; resposta de ~260 KB por cidade por causa de ícones em base64 | **Não**: cobre 5 dias, não 7, e não traz chuva |
| Open-Meteo (`api.open-meteo.com`) | 200, JSON, 7 dias com `precipitation_sum` | **Não por padrão**: o uso gratuito é para fins não comerciais; uso comercial exige plano pago ou licença que a ness. não verificou, e a cláusula 4ª fala em API pública sem credenciais. Não vira conector sem a Alup aceitar por escrito |

## Decisão (saída C, provisória)

1. **Não construir** conector de previsão do tempo agora. Nenhuma fonte testada entrega 7 dias de previsão com
   precipitação por via pública e livre para uso comercial.
2. O CPTEC segue **fora da Onda 1, como não entregue**, e o painel não o marca como feito.
3. O caminho para destravar é uma resposta do INPE/CPTEC sobre o 403 (ou o acesso à API nova), a ser buscada pela
   Alup ou pela ness. com o canal institucional. Se vier acesso, entra a saída A do plano (conector do CPTEC com os
   7 componentes); a sonda `cptec` serve para conferir.
4. Se a Alup aceitar por escrito uma alternativa (por exemplo, a API do INMET com 5 dias e sem chuva, ou um provedor
   pago), entra como conector rotulado "substituto do CPTEC", e a diferença de cobertura fica no dicionário.

## Consequências

- A cláusula 4ª, Onda 1, fica com o CPTEC pendente de causa externa. A ness. registra o fato e a data; a decisão
  comercial é da Alup e do Ricardo.
- A sonda e o workflow `Sondar rede` ficam como ferramenta para qualquer origem pública que passe a bloquear.
- Risco: a Open-Meteo e o INMET podem mudar formato ou licença; esta ADR vale para 03/10/2026.
