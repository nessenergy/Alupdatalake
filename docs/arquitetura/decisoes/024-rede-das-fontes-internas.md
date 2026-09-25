# ADR 024 — Rede das fontes internas: VPC compartilhada da Alupar

**Status**: aceito · **Data**: 2026-09-25 · **Complementa** a
[ADR 013](013-ingestao-em-lote.md) (rede e TLS) e a
[ADR 008](008-acesso-a-bancos-relacionais.md) (acesso a bancos)

## 1. Contexto

As fontes da Onda 3 (Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS) não estão na
internet pública. A ADR 013 deixou o caminho de rede em aberto até a Alupar
informar como a rede dela chega a esses sistemas.

Em 25/09 a rede foi lida diretamente, com acesso somente leitura concedido ao
grupo `operacao-datalake@ness.com.br` no projeto `alupar-networking`:

- `alupar-networking` é **host de VPC compartilhada**, com `alupar-prd-app` e
  `alupar-backup` já ligados. Os três projetos do AlupData não estão.
- Três VPCs em `us-central1`: `vpc-prd`, `vpc-dr-prd` e `vpc-dr-dmz`, com
  peering entre `vpc-prd` e `vpc-dr-prd` sem troca de rotas personalizadas.
- **Não há Cloud VPN nem Interconnect.** A VPN é um FortiGate em máquina
  virtual (`alpfgt01`), com o lado externo na `vpc-prd` e o **lado interno na
  `vpc-dr-prd`** (172.16.8.5).
- A única rota para fora da GCP é a dos usuários remotos (`192.168.168.0/24`,
  FortiClient), na `vpc-dr-prd`, pelo lado interno do FortiGate. **Não há
  rota para a rede do Oracle FMB.**
- Cloud NAT com IP fixo nas duas VPCs de produção, cobrindo todas as sub-redes.
- Política de DNS com encaminhamento de entrada, sem zona privada.
- A política da organização `compute.restrictSharedVpcSubnetworks` está em
  **negar tudo**, inclusive nos três projetos do AlupData.

## 2. Decisão

1. **Os três projetos do AlupData entram como projetos de serviço** do
   `alupar-networking`. O AlupData não cria VPC própria: a rede é da Alupar,
   administrada por ela, e o nosso `infra/` só declara como os jobs a usam.
2. **Uma sub-rede dedicada, `snet-vpc-dr-prd-us-central1-alupdata`, na
   `vpc-dr-prd`**, `/26`, com acesso privado ao Google ligado. Uma só para
   `dev`, `hml` e `prod`: são poucos jobs, e uma exceção de política basta.
   Fica na `vpc-dr-prd` porque é lá que está o lado interno do FortiGate e a
   rota interna que já existe; a rota não atravessaria o peering.
3. **Só os jobs das fontes internas saem pela VPC**, por saída direta do Cloud
   Run (*Direct VPC egress*), com **todo o tráfego** pela VPC. Os conectores de
   API pública continuam como estão. Com todo o tráfego pela VPC, o acesso ao
   MySQL RDS, que é público na AWS, sai pelo **IP fixo do Cloud NAT da
   `vpc-dr-prd`**, que é o IP a liberar no RDS. Nenhum NAT nosso.
4. **Oracle FMB pelo FortiGate**: rota na `vpc-dr-prd` para a rede do FMB com
   próximo salto no lado interno do FortiGate, túnel do FortiGate até o
   datacenter e liberação da porta 1521 só a partir da nossa sub-rede, **sem
   NAT no caminho**, para que o log do banco mostre a origem real.
5. **A DSN aponta para o IP do FMB, não para um nome.** Sem zona privada, nome
   interno não resolve na GCP; com IP, nenhuma mudança de DNS é necessária.
6. **Teste de conexão como job próprio**: `teste-conexao-<fonte>` abre a DSN e
   roda `SELECT 1` de dentro da sub-rede, com a mesma imagem e a mesma conta de
   serviço da carga. É a resposta verificável a "já temos VPN?".

No código: `rede_interna`, `conectores_rede_interna` e `fontes_teste_conexao`
em `infra/variables.tf`, todas vazias por padrão; a API `compute` no bootstrap.
Com `rede_interna = null`, nenhum job muda.

## 3. Consequências

- O passo a passo de quem faz o quê está em
  [`runbook/rede-onda3.md`](../../runbook/rede-onda3.md). A parte da GCP da
  Alupar e a parte da rede local (FortiGate e datacenter) são da Alupar; a
  nossa começa depois delas.
- `infra/modules/networking` continua sem recursos: não há rede nossa a
  declarar.
- A API `compute` passa a ser habilitada pelo bootstrap, que é aplicado por
  pessoa, fora do deploy.
- Um único FortiGate fica no caminho do FMB. É a arquitetura atual da Alupar,
  não uma escolha do AlupData; a carga tolera a indisponibilidade dele como
  tolera a de qualquer origem: a execução falha, o alerta dispara e a janela é
  reprocessada.
- Se o FMB estiver numa rede já alcançável por outro caminho, o item 4 muda e
  esta ADR recebe adendo.
