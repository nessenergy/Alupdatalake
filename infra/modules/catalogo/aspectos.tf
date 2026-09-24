# *Aspect types* — os "Tag Templates" da cláusula, com o nome atual do produto
# (ADR 014). Eles são **estrutura**: dizem que campos uma anotação pode ter, não
# o que está escrito nela. Por isso entram antes da primeira carga; o
# preenchimento é que depende de tabela com dado dentro.

# O aspecto que a ADR 014 nomeia ao ativar a IA generativa do catálogo: quem
# consulta precisa saber se a descrição foi escrita por gente ou sugerida pelo
# serviço. Sem essa marca, texto gerado vira documentação com a mesma
# autoridade da curada, e a ADR fez questão de separar as duas.
resource "google_dataplex_aspect_type" "origem" {
  aspect_type_id = "origem"
  project        = var.project_id
  location       = var.region
  display_name   = "Origem da descrição"
  description    = "Se o texto do catálogo foi escrito por pessoa ou sugerido pelo serviço"

  metadata_template = jsonencode({
    name = "origem"
    type = "record"
    recordFields = [
      {
        name        = "origem"
        type        = "enum"
        index       = 1
        annotations = { displayName = "Origem", description = "Quem escreveu" }
        constraints = { required = true }
        enumValues = [
          { name = "curada", index = 1 },
          { name = "automatica", index = 2 },
        ]
      },
      {
        name        = "revisada_em"
        type        = "datetime"
        index       = 2
        annotations = { displayName = "Revisada em", description = "Quando uma pessoa conferiu pela última vez" }
      },
    ]
  })

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

# Domínio analítico e dono, do B1 e da matriz RACI. É o que permite responder
# "de quem é este dado" no próprio catálogo, em vez de na memória de quem
# estava na reunião. Os oito valores saem de `docs/arquitetura/dominios-analiticos.md`.
resource "google_dataplex_aspect_type" "dominio" {
  aspect_type_id = "dominio-analitico"
  project        = var.project_id
  location       = var.region
  display_name   = "Domínio analítico"
  description    = "A que domínio do B1 a tabela pertence, e quem responde por ela"

  metadata_template = jsonencode({
    name = "dominio_analitico"
    type = "record"
    recordFields = [
      {
        name        = "dominio"
        type        = "enum"
        index       = 1
        annotations = { displayName = "Domínio", description = "Domínio analítico do B1" }
        constraints = { required = true }
        enumValues = [
          { name = "mercado_de_energia", index = 1 },
          { name = "geracao_e_operacional", index = 2 },
          { name = "meteorologia", index = 3 },
          { name = "comercial_e_contratos", index = 4 },
          { name = "crm_e_marketing", index = 5 },
          { name = "risco_e_compliance", index = 6 },
          { name = "economico", index = 7 },
          { name = "planejamento", index = 8 },
        ]
      },
      {
        name        = "responsavel"
        type        = "string"
        index       = 2
        annotations = { displayName = "Responsável", description = "Data owner, como na matriz RACI" }
      },
    ]
  })

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

output "aspect_types" {
  description = "Aspect types declarados — os Tag Templates da cláusula"
  value       = [google_dataplex_aspect_type.origem.aspect_type_id, google_dataplex_aspect_type.dominio.aspect_type_id]
}
