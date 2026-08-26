# Módulo de rede

**Vazio de propósito até a Onda 3.**

As fontes das Ondas 1 e 2 são APIs e arquivos públicos na internet: não há VPC,
peering ou VPN a declarar. A rede vira necessária quando os conectores
precisarem alcançar os sistemas internos da Alup — Oracle FMB, Portal Alup,
MySQL RDS —, o que depende da VPN que a contratante ainda vai prover.

Quando entrar, aqui ficam VPC, sub-redes, Serverless VPC Access (para o Cloud
Run Job alcançar a rede interna) e as regras de firewall. Acesso às origens é
sempre **read-only**.
