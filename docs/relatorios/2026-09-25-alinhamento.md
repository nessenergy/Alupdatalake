---
titulo: Alinhamento — onde estamos e o caminho até o aceite — 25/09/2026
documento: Pauta de alinhamento
referencia: REL-2026-09-25 · AlupData Fase 1
emitido_em: 25 de setembro de 2026
emitente: ness. Processos e Tecnologia Ltda.
destinatario: Alup — Leonardo Guiel Marques, Taina Ulhoa Mota, Mauricio Cardoso e Saulo Rodrigues
contrato: CPS-01025/2026 — AlupData Fase 1: DataLake
marco: Ondas 0 e 1 — dossiês e aceite
responsavel: Ricardo Esper
classificacao: Confidencial — uso restrito das partes
local_data: 25 de setembro de 2026
---

# Onde estamos, e o caminho até o aceite

Este documento serve de pauta para a reunião de alinhamento. Em uma página:
**o lake está de pé e carregando dado real**, as Ondas 0 e 1 têm dossiê
previsto para **29–30/09**, e propomos a reunião de aceite para **01/10**.

## 1. O que aconteceu desde a liberação do GCP

A Alup liberou os três projetos em 23/09. Desde então:

| Data | O quê |
|---|---|
| 23/09 | Ambiente de desenvolvimento provisionado: bases, armazenamento, 27 rotinas de carga agendadas e o Portal publicado com login |
| 24/09 | Transformações (Bronze, Silver e Gold) de pé; primeira carga real às 9h34 |
| 24/09 | **As 23 fontes públicas carregaram com sucesso, sem registro recusado** — incluindo a geração horária por usina da CCEE de julho/2026, com 2.964.096 linhas |
| 24/09 | **22 tabelas Gold de mercado com dado**; as que seguem vazias esperam insumo (BBCE, Hubspot, acervo do TempoOK) |
| 25/09 | Ambiente de homologação provisionado e com as transformações executando; **22 das 23 fontes públicas já carregadas nele**, e a maior — a geração horária por usina da CCEE — em andamento |

A primeira carga real revelou sete ajustes que teste local não mostra —
formato novo publicado pelo Banco Central, precisão de números do ONS, tempo
e volume da carga mensal da CCEE, uma regra de qualidade que recusava dado
legítimo, entre outros. **Todos foram corrigidos no mesmo dia, com teste**, e
a carga ganhou um alarme próprio para quando uma origem mudar de formato.

<figure class="diagrama">
<svg viewBox='0 0 720 160' width='100%' xmlns='http://www.w3.org/2000/svg' font-family='Inter, Arial, sans-serif' role='img' aria-label='Fluxo do dado, das fontes ao consumo'>
<defs><marker id='seta' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto'><path d='M0,0 L10,5 L0,10 z' fill='#00ade8'/></marker></defs>
<rect x='8' y='28' width='132' height='96' rx='8' fill='#f1f5f9' stroke='#64748b' stroke-width='1.4'/>
<text x='74.0' y='50' text-anchor='middle' font-size='13' font-weight='700' fill='#0f172a'>Fontes</text>
<text x='74.0' y='70' text-anchor='middle' font-size='10.5' fill='#64748b'>APIs públicas</text>
<text x='74.0' y='85' text-anchor='middle' font-size='10.5' fill='#64748b'>APIs com credencial</text>
<text x='74.0' y='100' text-anchor='middle' font-size='10.5' fill='#64748b'>Bancos internos</text>
<text x='74.0' y='115' text-anchor='middle' font-size='10.5' fill='#64748b'>Planilhas</text>
<rect x='152' y='28' width='104' height='96' rx='8' fill='#f1f5f9' stroke='#64748b' stroke-width='1.4'/>
<text x='204.0' y='50' text-anchor='middle' font-size='13' font-weight='700' fill='#0f172a'>Dado bruto</text>
<text x='204.0' y='70' text-anchor='middle' font-size='10.5' fill='#64748b'>guardado como veio</text>
<text x='204.0' y='85' text-anchor='middle' font-size='10.5' fill='#64748b'>no GCS</text>
<text x='204.0' y='100' text-anchor='middle' font-size='10.5' fill='#64748b'>permite reprocessar</text>
<rect x='282' y='28' width='104' height='96' rx='8' fill='#f1f5f9' stroke='#64748b' stroke-width='1.4'/>
<text x='334.0' y='50' text-anchor='middle' font-size='13' font-weight='700' fill='#0f172a'>Bronze</text>
<text x='334.0' y='70' text-anchor='middle' font-size='10.5' fill='#64748b'>uma linha por</text>
<text x='334.0' y='85' text-anchor='middle' font-size='10.5' fill='#64748b'>registro recebido</text>
<text x='334.0' y='100' text-anchor='middle' font-size='10.5' fill='#64748b'>com a execução</text>
<rect x='402' y='28' width='104' height='96' rx='8' fill='#f1f5f9' stroke='#64748b' stroke-width='1.4'/>
<text x='454.0' y='50' text-anchor='middle' font-size='13' font-weight='700' fill='#0f172a'>Silver</text>
<text x='454.0' y='70' text-anchor='middle' font-size='10.5' fill='#64748b'>limpa, sem</text>
<text x='454.0' y='85' text-anchor='middle' font-size='10.5' fill='#64748b'>duplicata, com</text>
<text x='454.0' y='100' text-anchor='middle' font-size='10.5' fill='#64748b'>regras de qualidade</text>
<rect x='522' y='28' width='104' height='96' rx='8' fill='#e0f6fd' stroke='#00ade8' stroke-width='1.4'/>
<text x='574.0' y='50' text-anchor='middle' font-size='13' font-weight='700' fill='#0f172a'>Gold</text>
<text x='574.0' y='70' text-anchor='middle' font-size='10.5' fill='#64748b'>tabelas prontas</text>
<text x='574.0' y='85' text-anchor='middle' font-size='10.5' fill='#64748b'>para análise</text>
<text x='574.0' y='100' text-anchor='middle' font-size='10.5' fill='#64748b'>por domínio</text>
<rect x='636' y='28' width='78' height='96' rx='8' fill='#f1f5f9' stroke='#64748b' stroke-width='1.4'/>
<text x='675.0' y='50' text-anchor='middle' font-size='13' font-weight='700' fill='#0f172a'>Consumo</text>
<text x='675.0' y='70' text-anchor='middle' font-size='10.5' fill='#64748b'>Portal</text>
<text x='675.0' y='85' text-anchor='middle' font-size='10.5' fill='#64748b'>Power BI</text>
<line x1='140' y1='76' x2='149' y2='76' stroke='#00ade8' stroke-width='2' marker-end='url(#seta)'/>
<line x1='256' y1='76' x2='279' y2='76' stroke='#00ade8' stroke-width='2' marker-end='url(#seta)'/>
<line x1='386' y1='76' x2='399' y2='76' stroke='#00ade8' stroke-width='2' marker-end='url(#seta)'/>
<line x1='506' y1='76' x2='519' y2='76' stroke='#00ade8' stroke-width='2' marker-end='url(#seta)'/>
<line x1='626' y1='76' x2='633' y2='76' stroke='#00ade8' stroke-width='2' marker-end='url(#seta)'/>
<text x='360' y='148' text-anchor='middle' font-size='10.5' fill='#64748b'>Agendamento e execução: Cloud Scheduler e Cloud Run · Transformações: Dataform · Alertas: Cloud Monitoring</text>
</svg>
<figcaption>Figura 1 — O caminho do dado: da fonte ao consumo, com o bruto guardado para reprocessar.</figcaption>
</figure>

Os alertas de falha de carga estão ativos e chegam à equipe de operação. Em
homologação, também ao endereço de alertas da Alup (`alup.alertas@alupar.com.br`).

## 2. Onda por onda

| Onda | Situação | Próximo marco |
|---|---|---|
| **0 — Fundação** | entregue e em operação; falta completar três dias seguidos de carga (26/09) | dossiê em **29–30/09** |
| **1 — Mercado base** | as 23 fontes públicas carregadas com sucesso | dossiê em **29–30/09**, junto com a Onda 0 — antes do prazo de 16/10 |
| **2 — APIs com credencial** | previsão de ENA do TempoOK em carga diária; Hubspot e BBCE prontos, esperando credencial | dossiê cerca de uma semana depois das credenciais |
| **3 — Sistemas internos** | caminho de banco e orquestração prontos | começa quando chegarem VPN e credenciais |
| **4 — Planilhas e handoff** | motor de planilhas pronto; espaço de envio criado; catálogo de dados estruturado | planilhas de exemplo; depois, templates |


<figure class="diagrama">
<svg viewBox='0 0 720 204' width='100%' xmlns='http://www.w3.org/2000/svg' font-family='Inter, Arial, sans-serif' role='img' aria-label='Ondas: janela do contrato e dossiê previsto'>
<line x1='124.5' y1='22' x2='124.5' y2='182' stroke='#e2e8f0' stroke-width='1'/>
<text x='127.5' y='18' font-size='10' fill='#64748b'>set</text>
<line x1='258.3' y1='22' x2='258.3' y2='182' stroke='#e2e8f0' stroke-width='1'/>
<text x='261.3' y='18' font-size='10' fill='#64748b'>out</text>
<line x1='396.6' y1='22' x2='396.6' y2='182' stroke='#e2e8f0' stroke-width='1'/>
<text x='399.6' y='18' font-size='10' fill='#64748b'>nov</text>
<line x1='530.5' y1='22' x2='530.5' y2='182' stroke='#e2e8f0' stroke-width='1'/>
<text x='533.5' y='18' font-size='10' fill='#64748b'>dez</text>
<line x1='668.8' y1='22' x2='668.8' y2='182' stroke='#e2e8f0' stroke-width='1'/>
<text x='671.8' y='18' font-size='10' fill='#64748b'>jan</text>
<text x='8' y='46' font-size='11' font-weight='600' fill='#0f172a'>Onda 0 · Fundação</text>
<rect x='120.0' y='34' width='49.099999999999994' height='16' rx='3' fill='#f1f5f9' stroke='#64748b' stroke-width='1'/>
<path d='M253.8,34 L261.8,42 L253.8,50 L245.8,42 z' fill='#00ade8' stroke='#00ade8' stroke-width='1.6'/>
<text x='265.8' y='46' text-anchor='start' font-size='10' fill='#64748b'>dossiê 29–30/09 (postergada por A3)</text>
<text x='8' y='76' font-size='11' font-weight='600' fill='#0f172a'>Onda 1 · Mercado</text>
<rect x='182.5' y='64' width='142.7' height='16' rx='3' fill='#f1f5f9' stroke='#64748b' stroke-width='1'/>
<path d='M253.8,64 L261.8,72 L253.8,80 L245.8,72 z' fill='#00ade8' stroke='#00ade8' stroke-width='1.6'/>
<text x='337.2' y='76' text-anchor='start' font-size='10' fill='#64748b'>dossiê 29–30/09, antes do prazo</text>
<text x='8' y='106' font-size='11' font-weight='600' fill='#0f172a'>Onda 2 · Credenciais</text>
<rect x='338.6' y='94' width='111.59999999999997' height='16' rx='3' fill='#f1f5f9' stroke='#64748b' stroke-width='1'/>
<path d='M356.5,94 L364.5,102 L356.5,110 L348.5,102 z' fill='#ffffff' stroke='#00ade8' stroke-width='1.6'/>
<text x='462.2' y='106' text-anchor='start' font-size='10' fill='#64748b'>~23/10, se credenciais até 12/10</text>
<text x='8' y='136' font-size='11' font-weight='600' fill='#0f172a'>Onda 3 · Internos</text>
<rect x='463.5' y='124' width='142.79999999999995' height='16' rx='3' fill='#f1f5f9' stroke='#64748b' stroke-width='1'/>
<text x='457.5' y='136' text-anchor='end' font-size='10' fill='#64748b'>depende de VPN e credenciais</text>
<text x='8' y='166' font-size='11' font-weight='600' fill='#0f172a'>Onda 4 · Planilhas</text>
<rect x='619.7' y='154' width='80.29999999999995' height='16' rx='3' fill='#f1f5f9' stroke='#64748b' stroke-width='1'/>
<text x='613.7' y='166' text-anchor='end' font-size='10' fill='#64748b'>após a Onda 3</text>
<line x1='231.5' y1='24' x2='231.5' y2='182' stroke='#0f172a' stroke-width='1.2' stroke-dasharray='4 3'/>
<text x='235.5' y='196' font-size='10' font-weight='600' fill='#0f172a'>hoje, 25/09</text>
<rect x='470' y='186' width='12' height='10' fill='#f1f5f9' stroke='#64748b'/><text x='486' y='195' font-size='10' fill='#64748b'>janela do contrato</text>
<path d='M600,186 L606,191 L600,196 L594,191 z' fill='#00ade8' stroke='#00ade8'/><text x='611' y='195' font-size='10' fill='#64748b'>dossiê previsto</text>
</svg>
<figcaption>Figura 2 — Cada onda na janela do contrato, e a data prevista do dossiê.</figcaption>
</figure>


## 3. O que o dossiê das Ondas 0 e 1 vai mostrar

Para que a reunião de aceite seja conferência, e não primeira leitura:

- cada fonte com os sete componentes do contrato — conector, Bronze, Silver,
  Gold, testes, agendamento e documentação com linhagem;
- carga real com sucesso, com o registro de cada execução;
- três dias seguidos de carga da fonte de referência (Banco Central);
- reprocessamento a partir do dado bruto guardado, sem nova chamada à origem
  (já demonstrado em 24/09);
- o Portal mostrando uma tabela Gold com dado real;
- os portões de segurança do pipeline aprovados;
- a correspondência entre as 13 fontes do contrato e as entidades entregues.

## 4. O que precisamos da Alup

| # | Pedido | Para quando |
|---|---|---|
| 1 | **Quem assina o aceite** das Ondas 0 e 1 — a Taina, conforme o questionário (B4), ou o Comitê da matriz RACI, com os nomes | antes de 29/09 |
| 2 | **Confirmar a reunião de aceite** em 01/10, das 10h às 11h (alternativa: 02/10) | 29/09 |
| 3 | **Token do Hubspot e acesso e host do BBCE**, gravados pelo grupo da Alup no cofre de segredos do GCP — nunca por e-mail | 12/10 |
| 4 | **Posição sobre as 32h do item 2.1** (CCEE agente credenciado): solicitar a credencial à CCEE, ou realocar as horas para os conjuntos públicos da CCEE já entregues | 30/09 |
| 5 | **Exemplos das planilhas** no espaço de envio (`alupar-dev-alupdata-entrada`, pastas `planilhas/` e `usinas/`) | 01/10 |
| 6 | **Grupos da Alup** que passam a ler os dados e a entrar no Portal em homologação | antes da reunião de aceite |
| 7 | **VPN e credenciais** das fontes internas (Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS) | 09/11 |
| 8 | **Sigla interna das usinas**, para completar o de-para com o código oficial (CEG) | sem data — encaixamos quando vier |

## 5. Calendário proposto

| Data | Marco |
|---|---|
| 26/09 | terceiro dia seguido de carga da fonte de referência |
| 29–30/09 | dossiês das Ondas 0 e 1 entregues |
| 01/10 | reunião de aceite das Ondas 0 e 1 |
| 12/10 | credenciais da Onda 2 |
| ~1 semana depois | dossiê da Onda 2 |


<figure class="diagrama">
<svg viewBox='0 0 720 160' width='100%' xmlns='http://www.w3.org/2000/svg' font-family='Inter, Arial, sans-serif' role='img' aria-label='Linha do tempo de 23/09 a 12/10'>
<line x1='40' y1='84' x2='680' y2='84' stroke='#64748b' stroke-width='2'/>
<line x1='40' y1='84' x2='253.3' y2='84' stroke='#00ade8' stroke-width='4'/>
<circle cx='40.0' cy='84' r='7' fill='#00ade8' stroke='#00ade8' stroke-width='2'/>
<line x1='40.0' y1='77' x2='40.0' y2='60' stroke='#e2e8f0'/>
<text x='40.0' y='22' text-anchor='middle' font-size='11' font-weight='700' fill='#0f172a'>23/09</text>
<text x='40.0' y='37' text-anchor='middle' font-size='10.5' fill='#0f172a'>GCP liberado</text>
<text x='40.0' y='51' text-anchor='middle' font-size='10.5' fill='#64748b'>dev no ar</text>
<circle cx='146.7' cy='84' r='7' fill='#00ade8' stroke='#00ade8' stroke-width='2'/>
<line x1='146.7' y1='91' x2='146.7' y2='106' stroke='#e2e8f0'/>
<text x='146.7' y='122' text-anchor='middle' font-size='11' font-weight='700' fill='#0f172a'>24/09</text>
<text x='146.7' y='137' text-anchor='middle' font-size='10.5' fill='#0f172a'>1ª carga</text>
<text x='146.7' y='151' text-anchor='middle' font-size='10.5' fill='#64748b'>23 fontes públicas</text>
<circle cx='253.3' cy='84' r='7' fill='#00ade8' stroke='#00ade8' stroke-width='2'/>
<line x1='253.3' y1='77' x2='253.3' y2='60' stroke='#e2e8f0'/>
<text x='253.3' y='22' text-anchor='middle' font-size='11' font-weight='700' fill='#0f172a'>25/09</text>
<text x='253.3' y='37' text-anchor='middle' font-size='10.5' fill='#0f172a'>homologação</text>
<text x='253.3' y='51' text-anchor='middle' font-size='10.5' fill='#64748b'>no ar</text>
<circle cx='360.0' cy='84' r='7' fill='#ffffff' stroke='#00ade8' stroke-width='2'/>
<line x1='360.0' y1='91' x2='360.0' y2='106' stroke='#e2e8f0'/>
<text x='360.0' y='122' text-anchor='middle' font-size='11' font-weight='700' fill='#0f172a'>26/09</text>
<text x='360.0' y='137' text-anchor='middle' font-size='10.5' fill='#0f172a'>3º dia seguido</text>
<text x='360.0' y='151' text-anchor='middle' font-size='10.5' fill='#64748b'>de carga</text>
<circle cx='466.7' cy='84' r='7' fill='#ffffff' stroke='#00ade8' stroke-width='2'/>
<line x1='466.7' y1='77' x2='466.7' y2='60' stroke='#e2e8f0'/>
<text x='466.7' y='22' text-anchor='middle' font-size='11' font-weight='700' fill='#0f172a'>29–30/09</text>
<text x='466.7' y='37' text-anchor='middle' font-size='10.5' fill='#0f172a'>dossiês</text>
<text x='466.7' y='51' text-anchor='middle' font-size='10.5' fill='#64748b'>Ondas 0 e 1</text>
<circle cx='573.3' cy='84' r='7' fill='#ffffff' stroke='#00ade8' stroke-width='2'/>
<line x1='573.3' y1='91' x2='573.3' y2='106' stroke='#e2e8f0'/>
<text x='573.3' y='122' text-anchor='middle' font-size='11' font-weight='700' fill='#0f172a'>01/10</text>
<text x='573.3' y='137' text-anchor='middle' font-size='10.5' fill='#0f172a'>reunião</text>
<text x='573.3' y='151' text-anchor='middle' font-size='10.5' fill='#64748b'>de aceite</text>
<circle cx='680.0' cy='84' r='7' fill='#ffffff' stroke='#00ade8' stroke-width='2'/>
<line x1='680.0' y1='77' x2='680.0' y2='60' stroke='#e2e8f0'/>
<text x='680.0' y='22' text-anchor='middle' font-size='11' font-weight='700' fill='#0f172a'>12/10</text>
<text x='680.0' y='37' text-anchor='middle' font-size='10.5' fill='#0f172a'>credenciais</text>
<text x='680.0' y='51' text-anchor='middle' font-size='10.5' fill='#64748b'>da Onda 2</text>
</svg>
<figcaption>Figura 3 — Linha do tempo: marcos cumpridos (cheios) e previstos (vazados).</figcaption>
</figure>


Seguimos à disposição para ajustar datas e prioridades na reunião.

Ricardo Esper — ness.
