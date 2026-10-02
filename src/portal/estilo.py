"""Folha de estilo do Portal (ADR 022: identidade da Alup, só aqui).

Vem do pacote de design aprovado, com uma troca: os ícones são `<svg>` inline no HTML
(`pagina.icone`), não `mask-image` com `data:`, porque a política de segurança do
Portal não admite imagem (`img-src 'none'`). As fontes entram por `<link>` no `<head>`.
"""

from __future__ import annotations

ESTILO = """<style>
/* =====================================================================
   Portal AlupData — especificação CSS
   Telas: Saúde do lake · Indicadores · Custo de nuvem
   HTML e CSS gerados no servidor. Sem JavaScript. Gráficos e tira em SVG/CSS puro.
   Prefixo .ad-*   Modo telão: classe ad-page--telao no body, com a troca de tela por refresh do navegador
   ===================================================================== */

/* ---------- 1. Tokens ---------- */
:root{
/* base (briefing v2) */
--background:#fcfcfb;--foreground:#212121;--card:#ffffff;--muted:#f4f4f4;--muted-foreground:#6b6675;--border:#e6e3ea;--primary:#520042;--radius:.6rem;
/* faixa ameixa */
--primary-700:#3d0031;--primary-900:#2a0022;--band-card:#651a58;--band-fg:#ffffff;--band-fg-2:#ecd6e7;--band-rule:rgba(255,255,255,.4);
/* estados: reservados, nunca como cor de série */
--ok:#0E8A6B;--warn:#B26A00;--crit:#C2185B;--idle:#8A94A0;
--ok-ink:#0b6e55;--warn-ink:#6b3f00;--crit-ink:#9c1149;--idle-ink:#5b6470;
--warn-soft:#ffe9c2;--crit-soft:#fde4ee;--warn-row:#fff7e8;--crit-row:#fff1f5;
/* variantes luminosas, só sobre ameixa (lâmpada, filete) — ver DECISOES.md */
--ok-bright:#19b48c;--warn-bright:#f0a32a;--crit-bright:#ec4f8a;
/* séries de gráfico */
--series-1:#8B2A78;--series-2:#1863dc;--series-3:#0E8A6B;--series-4:#B26A00;--series-5:#C2185B;
/* tira de 30 dias */
--cell-ok:var(--ok);--cell-none:#dcd9e0;--cell-fail:var(--crit);--cell-fail-2:#8c0f40;
--cell-w:9px;--cell-gap:3px;--cell-h:22px;--cell-none-h:6px;
--strip-w:calc(30 * var(--cell-w) + 29 * var(--cell-gap));
/* tipografia */
--font-text:'Hanken Grotesk',ui-sans-serif,system-ui,sans-serif;
--font-title:'Zilla Slab',Georgia,serif;
--fs-verdict:76px;--fs-summary-num:96px;--fs-card-num:50px;
/* layout */
--gutter:64px;--head-h:72px;--telao-band-h:288px;--telao-dwell:20s;/* @kind other */
}

/* ---------- 2. Página ---------- */
*,*::before,*::after{box-sizing:border-box}
.ad-page{margin:0;background:var(--background);color:var(--foreground);font:400 16px/1.5 var(--font-text);font-variant-numeric:tabular-nums}
.ad-page a{color:var(--primary)}
.ad-page a:hover{color:#7a1a66}
.ad-page :focus-visible{outline:3px solid var(--primary);outline-offset:2px;border-radius:4px}
.ad-head :focus-visible,.ad-band :focus-visible{outline-color:#fff}
.ad-main{padding:20px var(--gutter) 32px;display:flex;flex-direction:column;gap:16px}

/* ---------- 3. Cabeçalho fixo (faixa de topo, linha 1) + navegação ---------- */
.ad-head{position:sticky;top:0;z-index:10;background:var(--primary);color:var(--band-fg)}
.ad-head__bar{display:flex;align-items:center;flex-wrap:wrap;gap:12px 20px;min-height:var(--head-h);padding:0 var(--gutter)}
.ad-logo{display:block;height:34px;width:auto}
.ad-divider{width:1px;height:32px;background:var(--band-rule)}
.ad-title{margin:0;font:500 22px/1.2 var(--font-text)}
.ad-title b{font-weight:700}
.ad-head__meta{margin-left:auto;display:flex;align-items:center;flex-wrap:wrap;gap:8px 28px}
.ad-stamp{margin:0;font:500 20px/1.2 var(--font-text);color:var(--band-fg-2)}
.ad-stamp time{color:var(--band-fg);font-weight:700}
.ad-page .ad-telao-link{color:var(--band-fg-2);font:500 16px var(--font-text)}
.ad-nav{display:flex;gap:4px;padding:0 calc(var(--gutter) - 14px);background:var(--primary-700);overflow-x:auto}
.ad-page .ad-nav a{display:block;padding:12px 14px 10px;border-bottom:3px solid transparent;color:var(--band-fg-2);font:500 16px/1.2 var(--font-text);text-decoration:none;white-space:nowrap}
.ad-page .ad-nav a:hover{color:var(--band-fg)}
.ad-page .ad-nav a[aria-current="page"]{color:var(--band-fg);font-weight:700;border-bottom-color:var(--band-fg)}

/* ---------- 4. Faixa (linha 2): veredito / síntese + contadores ---------- */
.ad-band{background:var(--primary);color:var(--band-fg);padding:12px var(--gutter) 28px;display:flex;flex-direction:column;gap:22px;border-top:1px solid rgba(255,255,255,.12)}

/* semáforo vertical: só a lâmpada do estado acende; posição = 2º sinal */
.ad-verdict{display:flex;align-items:center;gap:32px}
.ad-lamps{flex:none;display:flex;flex-direction:column;gap:8px;padding:10px;border-radius:999px;background:var(--primary-900)}
.ad-lamp{position:relative;width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,.1)}
.ad-verdict--crit .ad-lamp--crit{background:var(--crit-bright);box-shadow:0 0 0 3px rgba(255,255,255,.18),0 0 28px var(--crit-bright)}
.ad-verdict--warn .ad-lamp--warn{background:var(--warn-bright);box-shadow:0 0 0 3px rgba(255,255,255,.18),0 0 28px var(--warn-bright)}
.ad-verdict--ok .ad-lamp--ok{background:var(--ok-bright);box-shadow:0 0 0 3px rgba(255,255,255,.18),0 0 28px var(--ok-bright)}
.ad-verdict--crit .ad-lamp--crit svg,.ad-verdict--warn .ad-lamp--warn svg,.ad-verdict--ok .ad-lamp--ok svg{opacity:1}
.ad-lamp svg{position:absolute;inset:9px;width:22px;height:22px;opacity:0;stroke:#fff}
.ad-lamp--warn svg{stroke:var(--primary-900)}
.ad-verdict__title{margin:0;font:600 var(--fs-verdict)/1.05 var(--font-title);letter-spacing:-.01em;text-wrap:balance}
.ad-verdict__sub{margin:10px 0 0;font:500 26px/1.3 var(--font-text);color:var(--band-fg-2)}

/* síntese neutra (Indicadores, Custo): ocupa o lugar do semáforo */
.ad-summary{display:flex;align-items:flex-end;flex-wrap:wrap;gap:16px 40px}
.ad-summary__num{margin:0;font:600 var(--fs-summary-num)/.95 var(--font-text);letter-spacing:-.03em}
.ad-summary__num small{font-size:.42em;font-weight:500;letter-spacing:0;margin-right:.2em}
.ad-summary__text{display:flex;flex-direction:column;gap:6px;padding-bottom:6px}
.ad-summary__title{margin:0;font:600 34px/1.15 var(--font-title)}
.ad-summary__sub{margin:0;font:500 22px/1.35 var(--font-text);color:var(--band-fg-2)}
.ad-summary>.ad-pill{align-self:center;font-size:20px;padding:8px 16px 8px 8px}
.ad-summary>.ad-pill .ad-ico{width:24px;height:24px}

/* contadores por grupo: só nome + ✓ quando em dia; exceção = nome + pílula + filete. Uma linha para 1–8 grupos em ≥1100px */
.ad-tiles{list-style:none;margin:0;padding:0;display:grid;grid-auto-flow:column;grid-auto-columns:minmax(0,1fr);gap:16px}
.ad-tile{min-width:0;display:flex;flex-direction:column;align-items:flex-start;justify-content:center;gap:10px;padding:14px 20px 16px;border-radius:var(--radius);background:var(--band-card);border-top:5px solid transparent}
.ad-tile--warn{border-top-color:var(--warn-bright)}
.ad-tile--crit{border-top-color:var(--crit-bright)}
.ad-tile__name{display:flex;align-items:center;gap:12px;margin:0;font:600 26px/1.15 var(--font-title)}
.ad-tile__name .ad-ico{width:26px;height:26px}

/* ---------- 5. Ícone de estado (cor + glifo) ---------- */
.ad-ico{position:relative;flex:none;display:inline-block;width:22px;height:22px;border-radius:50%}
.ad-ico svg{position:absolute;inset:20%;width:60%;height:60%;stroke:#fff}
.ad-ico--ok{background:var(--ok)}
.ad-ico--warn{background:var(--warn)}
.ad-ico--crit{background:var(--crit)}
.ad-ico--idle{background:transparent;border:2px dashed var(--idle)}.ad-ico--idle svg{stroke:var(--idle-ink)}
.ad-band .ad-ico--warn{background:var(--warn-bright)}.ad-band .ad-ico--warn svg{stroke:var(--primary-900)}
.ad-band .ad-ico--crit{background:var(--crit-bright)}
.ad-band .ad-ico--ok{background:var(--ok-bright)}.ad-band .ad-ico--ok svg{stroke:var(--primary-900)}
.ad-band .ad-ico--idle{border-color:var(--band-fg-2)}.ad-band .ad-ico--idle svg{stroke:var(--band-fg-2)}

/* ---------- 6. Pílula (quebra em até 2 linhas, ícone nunca encolhe) ---------- */
.ad-pill{display:inline-flex;align-items:flex-start;gap:8px;max-width:100%;min-width:0;padding:5px 12px 5px 6px;border-radius:14px;font:600 16px/1.3 var(--font-text)}
.ad-pill .ad-ico{width:20px;height:20px;margin-top:1px}
.ad-band .ad-pill--warn,.ad-pill--warn{background:var(--warn-soft);color:var(--warn-ink)}
.ad-band .ad-pill--warn .ad-ico--warn,.ad-pill--warn .ad-ico--warn{background:var(--warn)}
.ad-band .ad-pill--warn .ad-ico--warn svg,.ad-pill--warn .ad-ico--warn svg{stroke:#fff}
.ad-pill--crit{background:var(--crit-soft);color:var(--crit-ink)}
.ad-pill--idle{padding:3.5px 10.5px 3.5px 4.5px;border:1.5px dashed var(--idle);color:var(--idle-ink);font-weight:500}
.ad-band .ad-pill--idle{border-color:var(--band-fg-2);color:var(--band-fg-2)}
.ad-pill--idle .ad-ico--idle,.ad-band .ad-pill--idle .ad-ico--idle{border:1.5px solid currentColor}

/* ---------- 7. Lista de fontes (Saúde) — legenda da tira vai no rodapé ---------- */
.ad-legend{display:flex;flex-wrap:wrap;align-items:center;justify-content:flex-start;gap:6px 22px;margin:0;padding-top:10px;border-top:1px solid var(--border);font:500 14px/1.2 var(--font-text);color:var(--muted-foreground)}
.ad-legend__item{display:inline-flex;align-items:center;gap:8px}
.ad-legend .ad-strip{grid-template-columns:var(--cell-w);height:16px}
.ad-sources{column-count:2;column-gap:64px}
.ad-group{container-type:inline-size}
.ad-group{break-inside:avoid;margin:0 0 14px}
.ad-group__head{display:flex;align-items:center;min-height:40px;border-bottom:1px solid #cfcad3}
.ad-group__head h2{margin:0;font:600 20px/1 var(--font-title)}
.ad-row{border-bottom:1px solid var(--border)}
.ad-row:last-child{border-bottom:none}
.ad-row>summary{list-style:none;display:grid;grid-template-columns:22px minmax(0,1fr) 100px var(--strip-w) 18px;grid-template-areas:"ico name age strip chev";align-items:center;column-gap:14px;min-height:32px;margin:0 -10px;padding:3px 10px;border-radius:6px;cursor:pointer}
.ad-row>summary::-webkit-details-marker{display:none}
.ad-row>summary:hover{background:var(--muted)}
.ad-row>summary>.ad-ico{grid-area:ico}
.ad-row--ok>summary>.ad-ico{width:10px;height:10px;justify-self:center}
.ad-row--ok>summary>.ad-ico svg{display:none}
.ad-row__name{grid-area:name;min-width:0;font:400 19px/1.2 var(--font-text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ad-row__note{display:block;font:600 15px/1.3 var(--font-text);white-space:normal}
.ad-row__age{grid-area:age;text-align:right;white-space:nowrap;font:500 17px/1 var(--font-text);color:var(--muted-foreground)}
.ad-row--warn>summary{background:var(--warn-row)}
.ad-row--warn .ad-row__note,.ad-row--warn .ad-row__age{color:var(--warn-ink)}
.ad-row--crit>summary{background:var(--crit-row)}
.ad-row--crit .ad-row__note,.ad-row--crit .ad-row__age{color:var(--crit-ink)}
.ad-row--idle .ad-row__name,.ad-row--idle .ad-row__age{color:var(--idle-ink)}
.ad-row>summary>.ad-strip,.ad-row>summary>.ad-pending{grid-area:strip}
.ad-chev{grid-area:chev;position:relative;width:18px;height:18px;opacity:0;transition:transform .2s}
.ad-chev::before{content:"";position:absolute;left:5px;top:3px;width:7px;height:7px;border:solid var(--muted-foreground);border-width:0 2px 2px 0;transform:rotate(45deg)}
.ad-row>summary:hover .ad-chev,.ad-row>summary:focus-visible .ad-chev,.ad-row[open] .ad-chev{opacity:1}
.ad-row[open] .ad-chev{transform:rotate(180deg)}
.ad-evid{display:flex;flex-wrap:wrap;gap:10px 44px;margin:2px 0 10px 36px;padding:10px 16px;border-radius:8px;background:var(--muted)}
.ad-evid div{display:flex;flex-direction:column;gap:2px}
.ad-evid dt{font:400 14px/1.3 var(--font-text);color:var(--muted-foreground)}
.ad-evid dd{margin:0;font:600 17px/1.3 var(--font-text)}

/* linha estreita (container < 640px): tira desce para baixo do nome */
@container (max-width:640px){.ad-row>summary{grid-template-columns:22px minmax(0,1fr) auto;grid-template-areas:"ico name age" ". strip strip";row-gap:6px;padding:8px 10px}.ad-chev{display:none}.ad-evid{margin-left:0}}

/* tira de 30 dias: cheia verde = carregou · toco cinza = sem carga · cheia hachurada = falha */
.ad-strip{display:grid;grid-template-columns:repeat(30,var(--cell-w));gap:var(--cell-gap);height:var(--cell-h);align-items:end}
.ad-strip>i{display:block;height:100%;border-radius:2px;background:var(--cell-ok)}
.ad-strip>i.n{height:var(--cell-none-h);background:var(--cell-none)}
.ad-strip>i.f{background:repeating-linear-gradient(135deg,var(--cell-fail) 0 3px,var(--cell-fail-2) 3px 5px)}
.ad-pending{display:flex;align-items:center;justify-content:center;height:var(--cell-h);border:1.5px dashed var(--idle);border-radius:6px;font:500 15px/1 var(--font-text);color:var(--idle-ink)}

/* ---------- 8. Cartão de indicador (valor > conta > variação > tendência) ---------- */
.ad-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:20px}
.ad-card{display:flex;flex-direction:column;gap:4px;min-width:0;padding:16px 20px 12px;background:var(--card);border:1px solid var(--border);border-radius:var(--radius)}
.ad-card__head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;min-height:48px}
.ad-card__title{margin:0;font:600 19px/1.25 var(--font-title)}
.ad-chip{flex:none;padding:3px 8px;border-radius:6px;background:var(--muted);color:var(--muted-foreground);font:700 13px/1.2 var(--font-text);letter-spacing:.03em}
.ad-card__value{margin:4px 0 2px;font:600 var(--fs-card-num)/1 var(--font-text);letter-spacing:-.02em}
.ad-card__value small{font-size:.5em;font-weight:500;letter-spacing:0;margin-left:2px}
.ad-calc{margin:0;font:600 16px/1.35 var(--font-text)}
.ad-calc__terms{display:block;font:400 13px/1.35 var(--font-text);color:var(--muted-foreground)}
.ad-delta{margin:4px 0 0;font:500 16px/1.3 var(--font-text);color:var(--muted-foreground)}
.ad-delta b{color:var(--foreground);font-weight:600}
.ad-spark{display:block;width:100%;height:auto;margin-top:6px;overflow:visible}
.ad-spark polyline{fill:none;stroke:var(--series-1);stroke-width:2.5;stroke-linejoin:round;stroke-linecap:round}
.ad-spark circle{fill:var(--series-1)}
.ad-spark text{font:500 11px var(--font-text);fill:var(--muted-foreground)}
.ad-series>summary{list-style:none;cursor:pointer;margin-top:4px;font:500 14px/1.6 var(--font-text);color:var(--primary);text-decoration:underline;text-underline-offset:3px}
.ad-series>summary::-webkit-details-marker{display:none}
.ad-series table{width:100%;margin-top:6px;border-collapse:collapse;font:400 14px/1.6 var(--font-text)}
.ad-series td{padding:0 4px;border-bottom:1px solid var(--border)}
.ad-series td:last-child{text-align:right;font-weight:600}

/* ---------- 9. Bloco de custo (Operacional → Orçamento → Diretoria) ---------- */
.ad-cost{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr) minmax(0,.85fr);gap:24px;align-items:start}
.ad-block{display:flex;flex-direction:column;gap:12px;min-width:0;padding:18px 24px;background:var(--card);border:1px solid var(--border);border-radius:var(--radius)}
.ad-block__eyebrow{margin:0;font:700 13px/1 var(--font-text);letter-spacing:.08em;text-transform:uppercase;color:var(--muted-foreground)}
.ad-block__title{margin:2px 0 0;font:600 26px/1.15 var(--font-title)}
.ad-block h3{margin:4px 0 0;font:600 17px/1.2 var(--font-title)}
.ad-qlist{list-style:none;margin:0;padding:0}
.ad-qrow{display:grid;grid-template-columns:22px minmax(0,1fr) auto auto;align-items:start;column-gap:14px;padding:6px 10px;margin:0 -10px;border-bottom:1px solid var(--border)}
.ad-qrow:last-child{border-bottom:none}
.ad-qrow--ok>.ad-ico{visibility:hidden}
.ad-qrow--warn{background:var(--warn-row);border-radius:6px}
.ad-qrow__name{font:500 17px/1.3 var(--font-text)}
.ad-qrow__note{display:block;font:600 14px/1.3 var(--font-text);color:var(--warn-ink)}
.ad-qrow__meta{font:400 15px/1.3 var(--font-text);color:var(--muted-foreground);text-align:right;white-space:nowrap}
.ad-qrow__cost{font:600 17px/1.3 var(--font-text);text-align:right;white-space:nowrap}
.ad-stat{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 12px;margin:0}
.ad-stat b{font:600 28px/1.1 var(--font-text)}
.ad-stat span{font:400 15px/1.3 var(--font-text);color:var(--muted-foreground)}
.ad-meter{position:relative;height:14px;border-radius:7px;background:var(--muted)}
.ad-meter>span{display:block;height:100%;border-radius:7px;background:var(--series-1)}
.ad-meter>i{position:absolute;top:-4px;bottom:-4px;width:2px;background:var(--foreground)}
.ad-budget{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px 14px;align-items:center;margin:0}
.ad-budget dt{font:500 16px/1.3 var(--font-text)}
.ad-budget dd{margin:0;font:400 15px/1.3 var(--font-text);color:var(--muted-foreground);text-align:right}
.ad-budget dd b{color:var(--foreground);font-weight:600}
.ad-budget .ad-meter{grid-column:1/-1;margin-bottom:8px}
.ad-bars{display:block;width:100%;height:auto}
.ad-bars rect{fill:var(--series-1)}
.ad-bars line{stroke:var(--foreground);stroke-width:2}
.ad-bars text{font:500 12px var(--font-text);fill:var(--muted-foreground)}
.ad-bars text.v{fill:var(--foreground);font-weight:600}
.ad-key{display:flex;gap:18px;flex-wrap:wrap;margin:0;font:400 13px/1 var(--font-text);color:var(--muted-foreground)}
.ad-key i{display:inline-block;width:12px;height:12px;margin-right:6px;vertical-align:-1px;border-radius:2px;background:var(--series-1)}
.ad-key i.p{height:2px;vertical-align:3px;background:var(--foreground)}
.ad-glance{display:flex;flex-direction:column;gap:16px;margin:0}
.ad-glance div{display:flex;flex-direction:column;gap:2px}
.ad-glance dt{font:400 16px/1.3 var(--font-text);color:var(--muted-foreground)}
.ad-glance dd{margin:0;font:600 34px/1.1 var(--font-text);letter-spacing:-.01em}

/* ---------- 10. Aviso ---------- */
.ad-notice{display:flex;gap:12px;align-items:flex-start;margin:0;padding:10px 14px;border-radius:8px;background:var(--warn-soft);color:var(--warn-ink);font:500 16px/1.4 var(--font-text)}
.ad-notice .ad-ico{margin-top:1px}
.ad-foot{margin:0;font:400 13px/1.5 var(--font-text);color:var(--muted-foreground)}

/* ---------- 11. Modo telão (?telao=1) ---------- */
.ad-telao{display:none}
.ad-page--telao{height:100vh;overflow:hidden}
.ad-page--telao .ad-head{position:relative}
.ad-page--telao .ad-nav,.ad-page--telao .ad-telao-link{display:none}
.ad-page--telao .ad-telao{display:flex;align-items:center;gap:14px;font:500 16px/1 var(--font-text);color:var(--band-fg-2)}
.ad-page--telao .ad-telao a{color:var(--band-fg)}
.ad-page--telao .ad-band{height:var(--telao-band-h);overflow:hidden}
.ad-page--telao .ad-band--centered{justify-content:center}
.ad-page--telao .ad-main{padding-top:16px;padding-bottom:16px;gap:12px}
.ad-page--telao .ad-cards{grid-template-columns:repeat(6,minmax(0,1fr))}
.ad-page--telao .ad-foot{font-size:12px}

/* ---------- 12. Responsivo (fora do telão) ---------- */
@media (max-width:1400px){.ad-cost{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.ad-cost>.ad-block:first-child{grid-column:1/-1}}
@media (max-width:1100px){
:root{--gutter:32px;--fs-verdict:52px;--fs-summary-num:68px}
.ad-sources{column-count:1}
/* 3 por linha sem órfão: grade de 6, cada contador ocupa 2; sobras de 2 ou 4 dividem a linha ao meio */
.ad-tiles{grid-auto-flow:row;grid-template-columns:repeat(6,minmax(0,1fr))}
.ad-tile{grid-column:span 2}
.ad-tile:only-child{grid-column:1/-1}
.ad-tile:nth-child(3n+1):nth-last-child(2),.ad-tile:nth-child(3n+1):nth-last-child(2)~.ad-tile{grid-column:span 3}
.ad-tile:nth-child(3n+1):nth-last-child(4),.ad-tile:nth-child(3n+1):nth-last-child(4)~.ad-tile{grid-column:span 3}
.ad-cost{grid-template-columns:minmax(0,1fr)}
.ad-cost>.ad-block:first-child{grid-column:auto}
}
@media (max-width:700px){
:root{--gutter:16px;--head-h:56px;--fs-verdict:34px;--fs-summary-num:52px;--fs-card-num:40px;--cell-w:6px;--cell-gap:2px}
.ad-logo{height:26px}.ad-title{font-size:17px}.ad-stamp{font-size:15px}
.ad-head__meta{margin-left:0;width:100%;padding-bottom:10px}
.ad-verdict{gap:18px}.ad-lamp{width:26px;height:26px}.ad-lamp svg{inset:6px;width:14px;height:14px}.ad-lamps{padding:7px;gap:6px}
.ad-verdict__sub,.ad-summary__sub{font-size:17px}.ad-summary__title{font-size:24px}
.ad-tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
.ad-tiles>.ad-tile{grid-column:span 1}
.ad-tiles>.ad-tile:nth-child(odd):last-child{grid-column:1/-1}
.ad-tile{padding:10px 14px 12px}.ad-tile__name{font-size:19px}
.ad-legend{justify-content:flex-start}
.ad-row>summary{grid-template-columns:22px minmax(0,1fr) auto;grid-template-areas:"ico name age" ". strip strip";row-gap:6px;padding:8px 10px}
.ad-chev{grid-area:chev;position:relative;width:18px;height:18px;opacity:0;transition:transform .2s}
.ad-chev::before{content:"";position:absolute;left:5px;top:3px;width:7px;height:7px;border:solid var(--muted-foreground);border-width:0 2px 2px 0;transform:rotate(45deg)}
.ad-evid{margin-left:0}
.ad-qrow{grid-template-columns:22px minmax(0,1fr) auto}.ad-qrow__meta{grid-column:2;text-align:left}
}
/* ---------- 13. Peças do Portal fora do pacote de design ---------- */
.ad-lista{width:100%;border-collapse:collapse;font:400 16px/1.4 var(--font-text)}
.ad-lista th{text-align:left;padding:8px 10px;border-bottom:2px solid var(--border);font:700 13px/1.2 var(--font-text);letter-spacing:.06em;text-transform:uppercase;color:var(--muted-foreground)}
.ad-lista td{padding:8px 10px;border-bottom:1px solid var(--border)}
.ad-lista tr>*:not(:first-child){text-align:right}
.ad-rolagem{overflow-x:auto}
.ad-premissa{margin:0;padding:12px 16px;border-radius:var(--radius);background:var(--muted);font:400 14px/1.5 var(--font-text);color:var(--muted-foreground)}
.ad-page--telao .ad-sources--densa{column-count:3;column-gap:40px}
.ad-page--telao .ad-quem{display:none}
/* Cartão de indicador: o recorte vai abaixo do título, que assim nunca quebra em três linhas. */
.ad-card__head{flex-direction:column;align-items:flex-start;gap:6px;min-height:0}
/* Gráficos de custo e legenda (grafico.py). */
.grafico{display:block;width:100%;height:64px}
.grafico-alto{height:132px}
.legenda{display:flex;flex-wrap:wrap;gap:6px 16px;margin:8px 0 0;padding:0;list-style:none;font:400 13px/1.2 var(--font-text);color:var(--muted-foreground)}
.legenda .chave{display:inline-block;width:10px;height:10px;margin-right:6px;border-radius:2px}
/* Telão: faixa um pouco mais alta para caber veredito e contadores, e cartões sem o que só se lê de perto. */
.ad-page--telao{--telao-band-h:296px}
.ad-page--telao .ad-band{padding-bottom:14px;gap:14px}
.ad-page--telao .ad-calc__terms,.ad-page--telao .ad-series{display:none}

</style>"""
