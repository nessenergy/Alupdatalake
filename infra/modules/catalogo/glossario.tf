# Glossário de negócio do Knowledge Catalog — ADR 014, issue #36, item 4.3 do
# plano de execução. `docs/glossario.md` é a fonte da verdade; ele não é lido
# em tempo de apply — HCL não tem parser de Markdown, e regex sobre prosa de
# terceiro seria mais frágil que manter os dois em sincronia por teste.
# `tests/unit/test_catalogo.py` extrai os termos do `.md` e confere que todos
# existem aqui, e que nenhum termo de fora das quatro seções de negócio vaza.
#
# Só entram Instituições, Sistema e mercado, Geração e Unidades. "Do projeto"
# documenta o repositório e o contrato (Onda, Homologação, SSDLC, dry-run),
# não o dado — um termo desses no catálogo confundiria quem procura o que uma
# coluna significa.
#
# Sem `google_dataplex_glossary_category`: a label `categoria` no termo
# agrupa por seção sem precisar de outro tipo de recurso para manter em
# sincronia. Nem a ADR nem o brief pedem hierarquia de categorias.

resource "google_dataplex_glossary" "negocio" {
  glossary_id  = "glossario-negocio"
  project      = var.project_id
  location     = var.region
  display_name = "Glossário de negócio — setor elétrico"
  description  = "Vocabulário operacional do setor elétrico para quem lê as views sem vir do setor. Fonte: docs/glossario.md."

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

locals {
  # Chave = term_id, mesma slugueira que test_catalogo.py aplica ao `.md`
  # (sem acento, minúsculo, espaço vira `_`). Termo novo no `.md`: acrescentar
  # aqui com a mesma regra, ou o teste de sincronização falha.
  glossario_termos = {
    aneel = {
      categoria    = "instituicoes"
      display_name = "ANEEL"
      description  = "Agência Nacional de Energia Elétrica. Regula o setor; mantém o cadastro de empreendimentos de geração (SIGA) e concede as outorgas."
    }
    ons = {
      categoria    = "instituicoes"
      display_name = "ONS"
      description  = "Operador Nacional do Sistema Elétrico. Opera o SIN em tempo real; publica carga, geração e restrições."
    }
    ccee = {
      categoria    = "instituicoes"
      display_name = "CCEE"
      description  = "Câmara de Comercialização de Energia Elétrica. Contabiliza e liquida a energia comercializada; calcula o PLD; mantém o registro dos agentes."
    }
    agente_ccee = {
      categoria    = "instituicoes"
      display_name = "Agente CCEE"
      description  = "Pessoa jurídica registrada na CCEE — gerador, comercializador, distribuidor ou consumidor livre. Cada coligada da Alup é um agente."
    }
    sin = {
      categoria    = "sistema_e_mercado"
      display_name = "SIN"
      description  = "Sistema Interligado Nacional — a rede que conecta quase toda a geração e o consumo do país."
    }
    submercado = {
      categoria    = "sistema_e_mercado"
      display_name = "Submercado"
      description  = "Subdivisão do SIN para formação de preço: SE/CO (Sudeste/Centro-Oeste), S (Sul), NE (Nordeste), N (Norte). Existem porque a transmissão entre regiões tem limite: quando ele aperta, o preço descola entre submercados. No projeto é a dimensão comum submercado, com as siglas SE, S, NE, N."
    }
    carga_de_energia = {
      categoria    = "sistema_e_mercado"
      display_name = "Carga de energia"
      description  = "O consumo verificado, por submercado e período. É o que o conector ONS/carga ingere."
    }
    pld = {
      categoria    = "sistema_e_mercado"
      display_name = "PLD"
      description  = "Preço de Liquidação das Diferenças. O preço da energia no mercado de curto prazo, por submercado e período, calculado pela CCEE. É a referência de quanto vale a energia que sobra ou falta em relação ao contratado."
    }
    cmo = {
      categoria    = "sistema_e_mercado"
      display_name = "CMO"
      description  = "Custo Marginal de Operação — quanto custa produzir o próximo MWh. Calculado pelo ONS; é a base do PLD."
    }
    mercado_de_curto_prazo = {
      categoria    = "sistema_e_mercado"
      display_name = "Mercado de curto prazo"
      description  = "Onde se liquida a diferença entre o que foi contratado e o que foi de fato gerado ou consumido, ao PLD."
    }
    ceg = {
      categoria    = "geracao"
      display_name = "CEG"
      description  = "Código Único de Empreendimento de Geração. Identificador da usina no cadastro da ANEEL — no projeto, a dimensão comum codigo_usina."
    }
    outorga = {
      categoria    = "geracao"
      display_name = "Outorga"
      description  = "A autorização ou concessão da ANEEL para gerar energia. Potência outorgada é o que foi autorizado; potência fiscalizada é o que a ANEEL verificou instalado."
    }
    garantia_fisica = {
      categoria    = "geracao"
      display_name = "Garantia física"
      description  = "Quanto de energia uma usina pode comercializar em contrato de longo prazo — não é a mesma coisa que sua potência instalada, e é o número que limita a venda."
    }
    fase_da_usina = {
      categoria    = "geracao"
      display_name = "Fase da usina"
      description  = "Onde o empreendimento está: Operação, Construção, Construção não iniciada. Diferencia parque existente de expansão."
    }
    tipos = {
      categoria    = "geracao"
      display_name = "Tipos"
      description  = "UHE hidrelétrica · PCH pequena central hidrelétrica · CGH central geradora hidrelétrica · EOL eólica · UFV solar fotovoltaica · UTE térmica."
    }
    mw = {
      categoria    = "unidades"
      display_name = "MW"
      description  = "Potência instantânea."
    }
    mwh = {
      categoria    = "unidades"
      display_name = "MWh"
      description  = "Energia — potência × tempo."
    }
    mwmed = {
      categoria    = "unidades"
      display_name = "MWmed"
      description  = "MW médio: a energia de um período dividida pelo tempo dele. 1 MWmed ao longo de um mês de 30 dias equivale a 720 MWh. O ONS publica carga em MWmed, e é a unidade das views de carga."
    }
    kw = {
      categoria    = "unidades"
      display_name = "kW"
      description  = "Mil watts. O cadastro da ANEEL publica potência em kW; a Gold converte para MW dividindo por 1.000."
    }
  }
}

resource "google_dataplex_glossary_term" "termo" {
  for_each = local.glossario_termos

  parent      = "projects/${var.project_id}/locations/${var.region}/glossaries/${google_dataplex_glossary.negocio.glossary_id}"
  glossary_id = google_dataplex_glossary.negocio.glossary_id
  project     = var.project_id
  location    = var.region
  term_id     = each.key

  display_name = each.value.display_name
  description  = each.value.description

  labels = {
    projeto   = "alupdata"
    ambiente  = var.environment
    categoria = each.value.categoria
  }
}

output "glossario" {
  description = "Glossário de negócio declarado e a contagem de termos"
  value = {
    glossary_id = google_dataplex_glossary.negocio.glossary_id
    termos      = length(local.glossario_termos)
  }
}
