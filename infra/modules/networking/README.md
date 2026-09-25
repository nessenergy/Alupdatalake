# Módulo de rede

**Sem recursos, de propósito** ([ADR 024](../../../docs/arquitetura/decisoes/024-rede-das-fontes-internas.md)).

A rede das fontes internas é a VPC compartilhada da Alupar, no projeto
`alupar-networking`, administrada por ela. O AlupData entra como projeto de
serviço e não cria VPC, sub-rede, rota, firewall nem NAT.

O que é nosso está no módulo `scheduler`: com `rede_interna` preenchida, os
jobs de `conectores_rede_interna` e os `teste-conexao-<fonte>` saem pela
sub-rede da Alupar (*Direct VPC egress*, todo o tráfego). Passo a passo de cada
lado em [`docs/runbook/rede-onda3.md`](../../../docs/runbook/rede-onda3.md).
