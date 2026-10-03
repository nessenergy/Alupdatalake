# ADR 027 — ONS Operacional: IPDO e ACOMPH

**Status**: proposto (depende do aceite da Alup) · **Data**: 2026-10-03 · **Relaciona-se
com** a [ADR 018](018-vias-de-acesso-a-ccee.md) (vias de acesso, mesmo método de
investigação)

## 1. Contexto

A cláusula 4ª, Onda 1, prevê "ONS Operacional — dados do IPDO e ACOMPH", como APIs
públicas sem dependência de credenciais da Alup. Em 02/10/2026 já se sabia que o
CKAN do ONS (dados.ons.org.br) não tem conjunto chamado `ipdo` nem `acomph`. Faltava
saber onde os dois são distribuídos, em que formato, e se exigem login.

## 2. Evidência (03/10/2026, TLS verificado, sem login)

**CKAN do ONS**

| Consulta | Status | Resultado |
|---|---|---|
| `package_search?q=ipdo` | 200 | 0 conjuntos |
| `package_search?q=acomph` | 200 | 0 conjuntos |
| `resource_search?query=name:ipdo` | 200 | 0 recursos |
| `resource_search?query=name:acomph` | 200 | 0 recursos |
| `package_search?q=acompanhamento` | 200 | 1 conjunto (`cvu-usitermica`, sem relação) |

**IPDO** (fato verificado)

- A página `https://www.ons.org.br/paginas/resultados-da-operacao/boletins-da-operacao`
  (200) descreve o IPDO como "informações preliminares não consolidadas para uso das
  equipes de operação" e aponta para o Acervo Digital, categoria `IPDO`.
- O Acervo Digital é uma lista do SharePoint, lida por JavaScript. A lista responde
  sem autenticação em `https://www.ons.org.br/_api/web/lists/getbytitle(...)/items`
  (200), com filtro `Categoria eq 'IPDO'`.
- Em 03/10/2026 a lista tinha **um único item** da categoria: o IPDO de 01/10/2026,
  `https://www.ons.org.br/AcervoDigitalDocumentosEPublicacoes/IPDO-01-10-2026.pdf`
  (200, `application/pdf`, 1,2 MB, 21 páginas, sem login).
- Os PDFs de 30/09/2026 e 01/09/2026, no mesmo padrão de nome, devolveram 404. O
  nome é previsível por data, mas **o ONS não guarda o histórico**: só o último
  informativo fica no ar.
- O PDF traz no cabeçalho "USO INTERNO - SOMENTE PARA CONFERÊNCIA". Não é um dado
  aberto com licença declarada, como são os conjuntos do CKAN (CC-BY).
- Formato: PDF de tabelas e gráficos, não CSV nem API.
- A página `publico.ons.org.br/sistemasons.aspx` lista um link `/resultados_operacao/ipdo.aspx`,
  que devolve 404.

**ACOMPH** (o que foi e o que não foi verificado)

- Nenhuma página pública do ONS testada traz o ACOMPH: `boletins-da-operacao` não o
  cita, a lista do Acervo Digital não tem categoria nem título com "ACOMPH" ou
  "hidroenerg" (`items?$filter=substringof(...)`, 200, 0 itens) e
  `.../historico-da-operacao/acomph.aspx` devolve 404.
- `https://sintegre.ons.org.br/` devolve 403 sem sessão. O portal de acesso
  restrito do ONS é o SINtegre, com "Novo Cadastro". Não foi feita nenhuma tentativa
  de login.
- **Hipótese, não verificada:** o ACOMPH é distribuído aos agentes pelo SINtegre,
  com cadastro. As buscas na web descrevem o ACOMPH como relatório de divulgação aos
  agentes de geração e aos centros de operação do ONS, o que combina com isso, mas
  nenhuma fonte pública confirma o canal.

## 3. Conteúdo do IPDO contra o que o lake já tem

Seções do IPDO de 01/10/2026 (lidas no PDF) e onde o mesmo dado está nos conjuntos
abertos já entregues, todos sem credencial:

| Seção do IPDO | Onde está no lake |
|---|---|
| 1 e 2. Balanço de energia, carga verificada, produção por fonte e intercâmbios | `ons_balanco_energia`, `ons_carga`, `ons_carga_verificada`, `ons_intercambio_nacional`, `ons_intercambio_internacional` |
| 3 e 9. Energia armazenada (variação e acompanhamento por submercado) | `ons_ear`, `ons_ear_bacia`, `ons_ear_reservatorio` |
| 5 e 6. Geração térmica Tipo I e II-A, diferenças entre verificada e programada | `ons_geracao_termica_despacho`, `ons_geracao_usina`, `ons_carga_programada` |
| 5.5 e 5.6. Capacidade instalada e disponibilidade | `ons_capacidade`, `ons_disponibilidade_usina` |
| 8. Dados hidráulicos das usinas por bacia | `ons_dados_hidrologicos`, `ons_ena_bacia`, `ons_ena_reservatorio` |
| 7. Demandas máximas do SIN e por submercado | Sem tabela no lake. O conjunto aberto `demanda_maxima_di` existe no CKAN do ONS; não foi aberto nesta investigação |
| 4. Destaques da operação | Texto livre do operador; sem equivalente estruturado |

## 4. Decisão

**IPDO: saída (C).** Não se constrói conector. O informativo é um PDF preliminar de
uso interno, sem histórico (um arquivo no ar por vez, então não há como carregar uma
janela de datas nem reprocessar), e o conteúdo numérico já vem dos conjuntos abertos,
que são a versão consolidada e histórica dos mesmos dados. Um conector faria ler
tabelas de PDF, que muda de layout sem aviso, para obter o dado preliminar do que o
lake já tem consolidado.

**ACOMPH: saída (B), por hipótese.** Não há origem pública verificada. Se a
distribuição é pelo SINtegre, exige cadastro e credencial, o que não é Onda 1 ("sem
dependência de credenciais da Alup"). Pela regra 2 do contrato, o segredo, a
declaração em `infra/` e o pedido à Alup são de Onda 2. A necessidade de analítica
hidrológica (vazões e condições por usina) pode ser atendida, em parte, pelos conjuntos
de EAR, ENA e dados hidrológicos da tabela acima.

Em ambos os casos o escopo do item não é entregue como "IPDO e ACOMPH" literais, e
isso depende do aceite da Alup. Enquanto o aceite não vem, nada é construído para
esse item, e os conjuntos operacionais do ONS seguem entregues.

## 5. Pedido de aceite à Alup (texto proposto; não enviado)

> Assunto: ONS Operacional (IPDO e ACOMPH) — proposta de substituição na Onda 1
>
> A cláusula 4ª prevê, na Onda 1, dados do IPDO e do ACOMPH do ONS. Verificamos em
> 03/10/2026 as origens públicas do ONS:
>
> 1. **IPDO**: é publicado apenas como PDF preliminar, marcado "uso interno, somente
>    para conferência", e o ONS mantém no ar só o informativo mais recente, sem
>    histórico. Não permite carga por janela de datas. Os números do IPDO (carga,
>    balanço de energia, geração, intercâmbio, energia armazenada e dados hidráulicos)
>    já estão no AlupData, a partir dos conjuntos de dados abertos do ONS, em versão
>    consolidada e com histórico. Falta apenas a demanda máxima, que pode ser
>    incluída a partir do conjunto aberto correspondente.
> 2. **ACOMPH**: não encontramos distribuição pública. Se o acesso é pelo SINtegre,
>    exige cadastro e credencial, o que está fora da Onda 1.
>
> Propomos: (a) dar o IPDO por atendido pelos conjuntos já entregues, acrescentando a
> demanda máxima; (b) deslocar o ACOMPH para a Onda 2, condicionado à
> obtenção do cadastro no SINtegre e à guarda da credencial no Secret Manager; (c) usar as horas
> liberadas dentro das 580 h previstas na cláusula, que admite alteração de fontes. Pedimos o aceite
> por escrito.

A decisão de enviar, e a forma, é de quem fala com o cliente.

**Atualização:** a demanda máxima do IPDO (seção 7) passou a existir como fonte no lake
(`ons_demanda_maxima`, PR #361), o que reduz a lacuna de conteúdo que esta ADR aponta; a decisão
acima não muda.

## 6. Não verificado

- Se o ACOMPH é de fato distribuído pelo SINtegre, em que formato e com qual
  periodicidade (exigiria login; não foi tentado).
- Se existe, no SINtegre ou em outro canal, um arquivo de histórico do IPDO.
- O conteúdo do conjunto `demanda_maxima_di` e se cobre a seção 7 do IPDO.
- Se a lista pública do Acervo Digital continua aberta (é um endpoint do SharePoint
  sem contrato de estabilidade; não deve ser usado em conector sem decisão nova).

## 7. Consequências

- Nenhum conector, tabela, view ou recurso de `infra/` é criado por esta ADR.
- Se a Alup aceitar (a), a demanda máxima entra como fonte nova do CKAN, com os 7
  componentes, em tarefa própria.
- Se a Alup recusar, o IPDO volta a ser avaliado como carga de PDF, com a fixture real
  e a ressalva de que não há histórico.
