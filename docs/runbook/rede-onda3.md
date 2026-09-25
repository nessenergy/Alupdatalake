# Rede das fontes internas (Onda 3): passo a passo

Desenho e motivos na [ADR 024](../arquitetura/decisoes/024-rede-das-fontes-internas.md).
Levantamento da rede da Alupar feito em **25/09/2026**, em leitura, no projeto
`alupar-networking`.

**Resultado final:** o job `teste-conexao-fmb`, rodando no projeto do
AlupData, abre conexão com o Oracle FMB e responde `SELECT 1`. Nada aqui dá à
ness. acesso de escrita à rede da Alupar.

## Situação

| Data | O que | Quem |
|---|---|---|
| 25/09 | N1 em `dev` e `hml` (API `compute` pelo bootstrap) | ness. |
| 25/09 | 0, G1 a G5 em `dev` e `hml`, pelo [`rede-onda3-alupar.sh`](rede-onda3-alupar.sh), com a conta `ness@alupar.com.br`. O papel `roles/iam.infrastructureAdmin` que o grupo `operacao-datalake@` tinha no `alupar-networking` saiu; ficou só leitura | ness., a pedido da Alupar |
| 25/09 | N2 em `dev`: `teste-conexao-fmb` criado. Rodou dentro da sub-rede e parou na DSN ausente, o que confirma a parte GCP | ness. |
| pendente | L1 (IP e rede do FMB), G6, L2 a L6 e a credencial do FMB (N3) | Alupar |
| depois do aceite | `prod-alupdata`: bootstrap de produção, depois o script com `prod` nas duas listas | ness. |

Todos os passos da Parte G têm equivalente no script, que mostra tudo antes de
aplicar (`bash rede-onda3-alupar.sh`) e só aplica com `APLICAR=1`.

## Valores usados em todo o documento

| Nome | Valor |
|---|---|
| Projeto host da VPC | `alupar-networking` |
| VPC | `vpc-dr-prd` |
| Região | `us-central1` |
| Sub-rede nova do AlupData | `snet-vpc-dr-prd-us-central1-alupdata` |
| Faixa da sub-rede nova | `172.16.9.0/26` (se colidir com alguma faixa do datacenter, a TI escolhe outra `/26` livre e troca em **todos** os passos) |
| Gateway da sub-rede nova | `172.16.9.1` (a GCP reserva o primeiro IP) |
| FortiGate | `alpfgt01`, zona `us-central1-a`, tag de rede `allow-fgt` |
| Lado interno do FortiGate | `nic1` na `vpc-dr-prd`, IP `172.16.8.5` (no FortiOS, a porta com esse IP; normalmente `port2`) |
| Gateway da sub-rede do FortiGate | `172.16.8.1` |
| Cloud NAT da `vpc-dr-prd` | `nat-dr-prd`, IP fixo `pip-nat-dr-prd-0` |
| Projetos do AlupData | `alupar-dev-alupdata` (nº 674823725603), `alupar-hm-alupdata` (nº 3658282685), `prod-alupdata` (nº 652049397367) |
| Agentes do Cloud Run | `service-674823725603@serverless-robot-prod.iam.gserviceaccount.com`, `service-3658282685@serverless-robot-prod.iam.gserviceaccount.com`, `service-652049397367@serverless-robot-prod.iam.gserviceaccount.com` |
| Porta do Oracle FMB | `1521/tcp` |
| `<IP_FMB>` e `<REDE_FMB>` | IP do servidor do FMB e a faixa da rede dele. **Informados pela TI no passo L1** |

## Ordem

| # | Quem | Passo | Depende de |
|---|---|---|---|
| N1 | ness. | Habilitar a API `compute` nos três projetos | — |
| L1 | TI Alupar | Informar `<IP_FMB>` e `<REDE_FMB>` | — |
| G1 a G6 | Admin GCP da Alupar | Sub-rede, vínculo, permissões, política, firewall e rota | N1 (para G2) e L1 (para G6) |
| L2 a L6 | Rede da Alupar | FortiGate e datacenter | G1 |
| N2 a N4 | ness. | Ligar a rede nos jobs e testar | tudo acima |

As partes G e L podem andar em paralelo, exceto G6, que precisa de L1.

---

## Parte N1 — ness.: API de rede nos projetos do AlupData

A API `compute` entrou no `infra/bootstrap` (ADR 024). Reaplicar o bootstrap
nos três projetos, como no [`primeiro-deploy.md`](primeiro-deploy.md).
**Pronto quando:** em cada projeto, *APIs e serviços → Compute Engine API*
aparece como **Ativada**. Sem isso, o passo G2 recusa o vínculo.

---

## Parte G — GCP da Alupar (projeto `alupar-networking`)

Quem executa precisa de **Admin de VPC compartilhada** (`roles/compute.xpnAdmin`)
na organização ou na pasta, e de **Admin de políticas da organização**
(`roles/orgpolicy.policyAdmin`) para o G4. Cada passo tem o caminho no console
e o comando equivalente no Cloud Shell; basta um dos dois.

### G1. Criar a sub-rede

Console: projeto `alupar-networking` → **Rede VPC → Redes VPC → `vpc-dr-prd`
→ Sub-redes → Adicionar sub-rede**:

- Nome: `snet-vpc-dr-prd-us-central1-alupdata`
- Região: `us-central1`
- Faixa IPv4: `172.16.9.0/26`
- **Acesso privado do Google: Ativado** (obrigatório: os jobs falam com
  BigQuery, Cloud Storage e Secret Manager por dentro da VPC)
- Registros de fluxo: a critério da Alupar

```bash
gcloud compute networks subnets create snet-vpc-dr-prd-us-central1-alupdata \
  --project=alupar-networking --network=vpc-dr-prd --region=us-central1 \
  --range=172.16.9.0/26 --enable-private-ip-google-access
```

### G2. Ligar os três projetos à VPC compartilhada

Console: **Rede VPC → VPC compartilhada** (projeto `alupar-networking`) →
**Anexar projetos** → marcar `alupar-dev-alupdata`, `alupar-hm-alupdata` e
`prod-alupdata` → em compartilhamento, **Sub-redes individuais** → marcar só
`snet-vpc-dr-prd-us-central1-alupdata` → **Salvar**.

```bash
for p in alupar-dev-alupdata alupar-hm-alupdata prod-alupdata; do
  gcloud compute shared-vpc associated-projects add $p --host-project=alupar-networking
done
```

### G3. Permissões para o Cloud Run usar a sub-rede

Para **cada um dos três agentes do Cloud Run** da tabela de valores:

1. **Usuário de rede do Compute** (`roles/compute.networkUser`) **na sub-rede**
   `snet-vpc-dr-prd-us-central1-alupdata`. Console: **Rede VPC → Redes VPC →
   `vpc-dr-prd` → Sub-redes → `snet-vpc-dr-prd-us-central1-alupdata` →
   Permissões → Adicionar principal**.
2. **Leitor de rede do Compute** (`roles/compute.networkViewer`) **no projeto**
   `alupar-networking`. Console: **IAM e administrador → IAM → Conceder acesso**.

```bash
for n in 674823725603 3658282685 652049397367; do
  sa="serviceAccount:service-$n@serverless-robot-prod.iam.gserviceaccount.com"
  gcloud compute networks subnets add-iam-policy-binding snet-vpc-dr-prd-us-central1-alupdata \
    --project=alupar-networking --region=us-central1 --member="$sa" --role=roles/compute.networkUser
  gcloud projects add-iam-policy-binding alupar-networking --member="$sa" \
    --role=roles/compute.networkViewer --condition=None
done
```

Nenhuma outra conta recebe papel na rede. As contas de serviço do AlupData não
entram aqui: quem liga o job à sub-rede é o agente do Cloud Run.

### G4. Exceção na política da organização

Hoje `compute.restrictSharedVpcSubnetworks` nega **todas** as sub-redes
compartilhadas. A exceção vale só para a sub-rede nova e só nos três projetos.

Console, **para cada um dos três projetos do AlupData**: selecionar o projeto →
**IAM e administrador → Políticas da organização** → **Restringir sub-redes
de VPC compartilhada** → **Gerenciar política** → **Substituir a política do
pai** → **Aplicação da política: Substituir** → **Adicionar regra** →
**Valores da política: Personalizado**, **Tipo: Permitir**, valor:

```
projects/alupar-networking/regions/us-central1/subnetworks/snet-vpc-dr-prd-us-central1-alupdata
```

→ **Definir política**.

```bash
for p in alupar-dev-alupdata alupar-hm-alupdata prod-alupdata; do
  gcloud resource-manager org-policies allow compute.restrictSharedVpcSubnetworks \
    projects/alupar-networking/regions/us-central1/subnetworks/snet-vpc-dr-prd-us-central1-alupdata \
    --project=$p
done
```

**Conferir:** no mesmo lugar, a política efetiva de cada projeto mostra a sub-rede
como permitida, e a dos demais projetos da Alupar continua negando tudo.

### G5. Firewall da GCP: da sub-rede nova até o FortiGate

Console: **Rede VPC → Firewall → Criar regra de firewall**:

- Nome: `vpc-dr-prd-ingress-allow-alupdata-fgt`
- Rede: `vpc-dr-prd` · Prioridade: `900` · Direção: **Entrada** · Ação: **Permitir**
- Destinos: **Tags de destino especificadas** → `allow-fgt`
- Intervalos IPv4 de origem: `172.16.9.0/26`
- Protocolos e portas: **TCP** `1521`

```bash
gcloud compute firewall-rules create vpc-dr-prd-ingress-allow-alupdata-fgt \
  --project=alupar-networking --network=vpc-dr-prd --direction=INGRESS --priority=900 \
  --action=ALLOW --rules=tcp:1521 --source-ranges=172.16.9.0/26 --target-tags=allow-fgt
```

A resposta do FMB volta pela mesma conexão: não precisa de regra de saída.

### G6. Rota da sub-rede nova até a rede do FMB

Precisa de `<REDE_FMB>` (L1). Console: **Rede VPC → Rotas → Gerenciamento
de rotas → Criar rota**:

- Nome: `route-alupdata-to-fmb`
- Rede: `vpc-dr-prd` · Intervalo de destino: `<REDE_FMB>` · Prioridade: `100`
- Próximo salto: **Especificar um endereço IP** → `172.16.8.5`

```bash
gcloud compute routes create route-alupdata-to-fmb --project=alupar-networking \
  --network=vpc-dr-prd --destination-range=<REDE_FMB> --next-hop-address=172.16.8.5 --priority=100
```

Se `<REDE_FMB>` já estiver coberta por outra rota da `vpc-dr-prd` pelo mesmo
FortiGate, este passo não é necessário. Hoje só existe a rota `192.168.168.0/24`,
dos usuários remotos.

### Sem mudança na GCP

- **Cloud NAT:** o `nat-dr-prd` já cobre todas as sub-redes da `vpc-dr-prd`, e
  a nova entra sozinha.
- **DNS:** a DSN usa o IP do FMB (L1), e nenhum nome interno precisa resolver.

---

## Parte L — Rede local da Alupar (FortiGate e datacenter)

### L1. Informar o endereço do FMB

A TI informa à ness. **`<IP_FMB>`**, o IP do servidor Oracle do FMB (o mesmo
host recebido em 11/09, agora como IP), e **`<REDE_FMB>`**, a faixa da rede
onde ele está (por exemplo `10.10.20.0/24`). Os dois são usados em G6, L3 a L5.

### L2. FortiGate: rota de volta para a sub-rede nova

A sub-rede nova não é diretamente ligada ao FortiGate. Sem esta rota, a
resposta do FMB não volta.

FortiOS: **Rede → Rotas estáticas → Criar nova**:

- Destino: `172.16.9.0/26`
- Gateway: `172.16.8.1`
- Interface: a porta com IP `172.16.8.5` (normalmente `port2`)

```
config router static
    edit 0
        set dst 172.16.9.0 255.255.255.192
        set gateway 172.16.8.1
        set device "port2"
        set comment "AlupData - sub-rede GCP das fontes internas"
    next
end
```

### L3. FortiGate: caminho até o datacenter do FMB

**Se já existe túnel IPsec do FortiGate até o datacenter onde está o FMB**
(o mais provável, porque os usuários remotos chegam lá por ele):

1. Na fase 2 do túnel, **nos dois lados** (FortiGate e equipamento do
   datacenter), incluir o par **local `172.16.9.0/26` ↔ remoto `<REDE_FMB>`**.
   Se a fase 2 já usa `0.0.0.0/0` dos dois lados, não há o que mudar.
2. Confirmar que o FortiGate tem rota para `<REDE_FMB>` pela interface do
   túnel. Se não tiver, criar: destino `<REDE_FMB>`, interface = o túnel.

**Se não existe túnel até o datacenter:** criar um IPsec site a site entre o
FortiGate e o firewall do datacenter, com fase 2 **local `172.16.9.0/26` ↔
remoto `<REDE_FMB>`**, e a rota estática para `<REDE_FMB>` pela interface do
túnel. O FortiGate já aceita IPsec (UDP 500 e 4500).

### L4. FortiGate: política de firewall

**Política e objetos → Política de firewall → Criar nova**:

| Campo | Valor |
|---|---|
| Nome | `ALUPDATA-GCP-para-FMB` |
| Interface de entrada | a porta com IP `172.16.8.5` (normalmente `port2`) |
| Interface de saída | a interface do túnel do L3 |
| Origem | objeto de endereço `ALUPDATA-GCP` = `172.16.9.0/26` |
| Destino | objeto de endereço `FMB-ORACLE` = `<IP_FMB>/32` |
| Serviço | objeto `ORACLE-1521` = TCP `1521` |
| Ação | **ACEITAR** |
| NAT | **Desativado**: o FMB precisa ver a origem real, para log e para o L5 |
| Registro | **Todas as sessões** |

Nenhuma outra porta nem outro destino. Se no futuro outra fonte interna
entrar por aqui, ela recebe política própria.

### L5. Datacenter: firewall, rota de volta e o próprio Oracle

1. **Rota:** o datacenter precisa devolver `172.16.9.0/26` pelo túnel do L3.
   Com fase 2 configurada dos dois lados, o equipamento do datacenter
   normalmente já cria essa rota; confirmar.
2. **Firewall do datacenter** (se houver outro entre o túnel e o servidor):
   permitir origem `172.16.9.0/26` → destino `<IP_FMB>`, TCP `1521`.
3. **Firewall do servidor do FMB** (se houver): o mesmo.
4. **Oracle:** se o `sqlnet.ora` usa verificação de nó
   (`tcp.validnode_checking = yes`), incluir `172.16.9.0/26` em
   `tcp.invited_nodes` e recarregar o listener.
5. **Usuário:** continua o de leitura, só nas views, recebido em 11/09. Nada muda.

### L6. MySQL RDS e Portal Alup (AWS), se entrarem por IP

Estas fontes não passam pelo FortiGate: saem para a internet pelo Cloud NAT.
Nos *security groups* das instâncias na AWS, liberar **entrada TCP `3306`**
somente do **IP fixo `pip-nat-dr-prd-0`**, com máscara `/32`. O IP aparece no
console da GCP em **Rede VPC → Endereços IP** (projeto `alupar-networking`).
A conexão do AlupData exige TLS com certificado verificado (ADR 013).

---

## Parte N2 a N4 — ness.: ligar e testar

### N2. Declarar a rede no ambiente

Por PR, no `infra/environments/dev.tfvars`:

```hcl
rede_interna = {
  projeto_host = "alupar-networking"
  rede         = "vpc-dr-prd"
  sub_rede     = "snet-vpc-dr-prd-us-central1-alupdata"
}
fontes_teste_conexao = ["fmb"]
```

Merge e *Deploy GCP* com `environment=dev`, `module=all`. O deploy cria o job
`teste-conexao-fmb`. Se o deploy falhar com `constraints/compute.restrictSharedVpcSubnetworks`,
o G4 não foi aplicado no projeto; com `compute.subnetworks.use`, falta o G3.

### N3. DSN com o IP

A DSN do FMB no secret `alupdata-fmb-dsn` passa a usar `<IP_FMB>` como host.
Quem grava é o grupo `operacao-datalake@ness.com.br`, pelo console
(**Secret Manager → `alupdata-fmb-dsn` → Nova versão**), como nas demais
credenciais. O valor nunca passa por chat, e-mail ou repositório.

### N4. Rodar o teste

GitHub: **Actions → Testar conexão → Run workflow**, com `environment = dev`
e `fonte = fmb`. Pessoa não executa job direto (ADR 015): o workflow roda pela
conta de deploy e registra quem testou. O resumo da execução diz se passou e
leva ao job no console, onde a mensagem do teste está em **Registros**:

| Saída | Significado | Onde olhar |
|---|---|---|
| `fmb: conexão aberta e SELECT 1 respondido` | **pronto**: rede e credencial funcionam | — |
| `NotFound` … `alupdata-fmb-dsn not found or has no versions` | a rede da GCP está certa (o job subiu na sub-rede e alcançou o Secret Manager), mas a DSN não foi gravada | N3 |
| `timed out` ou `DPY-6005` com o host | o pacote não chega ou não volta | G5, G6, L2, L3 e L4, nessa ordem; o log de sessões do L4 mostra se o FortiGate viu o pacote |
| `connection refused` | chegou ao servidor, mas nada escuta na porta, ou o firewall do servidor recusa | L5 |
| `ORA-12505`, `ORA-12514` | chegou ao listener, com serviço errado na DSN | N3 |
| `ORA-01017` | chegou ao banco, com usuário ou senha errados | N3 |
| `ORA-12537` ou conexão encerrada logo após abrir | verificação de nó do Oracle | L5, item 4 |

Com `dev` verde, repetir N2 e N4 em `hml` e em `prod` (mesma sub-rede; o G4 já
cobriu os três projetos).
