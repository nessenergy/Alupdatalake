# Credenciais — onde guardar antes e depois do ambiente GCP

O destino final de toda credencial é o **Google Secret Manager** (cláusula
8.5). Enquanto o projeto GCP não existe (pendência A3), há um cofre local que
serve de ponte — e que foi desenhado para não sobreviver à travessia.

## 1. Antes de A3 — o cofre local

### Onde fica

```
~/.alupdata/segredos.env
```

**Fora do repositório, sempre.** Não é preferência: o código recusa um cofre
dentro da árvore do projeto, porque esse é o único jeito de ele ser commitado
por acidente. `.gitignore` protege contra o descuido comum; ficar fora do
repositório protege contra o `git add -f` e contra a cópia do diretório.

### Como criar

Uma linha por credencial. **A chave é o nome canônico do secret** — o mesmo que
está declarado em `infra/modules/secrets/main.tf`:

```
# ~/.alupdata/segredos.env
alupdata-tempook-api-token=<o valor>
alupdata-hubspot-api-token=<o valor>
alupdata-bbce-api-token=<o valor>
```

Comentário e linha vazia são ignorados; espaço em volta do valor é removido.

No Windows, o caminho equivalente é `C:\Users\<voce>\.alupdata\segredos.env`.
Para guardar em outro lugar, aponte `ALUPDATA_SECRETS_ARQUIVO`.

### Como usar

O cofre é **opt-in explícito**. Sem a variável, o código vai ao Secret Manager
mesmo que o arquivo exista:

```bash
ALUPDATA_SECRETS_LOCAIS=1 uv run alupdata ingerir tempook_boletins --ultimos-dias 5 --dry-run
```

Não há fallback silencioso, de propósito: um token local antigo que mascarasse
o de produção produziria dado errado em vez de erro, e o problema só apareceria
na leitura.

### As três travas

| Trava | O que impede |
|---|---|
| Opt-in explícito | cofre local mascarar credencial de produção sem ninguém pedir |
| Recusa dentro do Cloud Run (`K_SERVICE`, `CLOUD_RUN_JOB`) | a ponte virar porta em produção |
| Recusa de arquivo dentro do repositório | commit acidental |

## 2. Quando A3 chegar — a travessia

Depois do primeiro `terraform apply`, que cria os secrets vazios:

```bash
# 1. simule primeiro: lista o que faria, sem gravar e sem imprimir valor
ALUPDATA_SECRETS_LOCAIS=1 make migrar-segredos projeto=alupdata-dev

# 2. grave
ALUPDATA_SECRETS_LOCAIS=1 make migrar-segredos projeto=alupdata-dev aplicar=1

# 3. apague o cofre
rm ~/.alupdata/segredos.env
```

A saída confere cada credencial por **tamanho e pontas** (`20 caracteres,
caf…def`), nunca pelo valor. É o suficiente para bater com o que o fornecedor
informou, e insuficiente para reconstruir a credencial a partir do log do
terminal.

### Por que um script, e não `gcloud` na mão

`gcloud secrets versions add ... --data-file=-` funciona, mas digitar o valor
na linha de comando o deixa no histórico do shell, no log do terminal e na
lista de processos enquanto o comando roda. O script lê do arquivo e nada
trafega pela linha de comando.

## 3. O que pedir à Alup

**Depois de A3, nenhuma credencial nova precisa passar pela ness.** O caminho
certo é a própria Alup gravar:

```bash
printf '%s' 'O-VALOR' | gcloud secrets versions add alupdata-bbce-api-token --data-file=-
```

O IAM restringe a leitura à conta de serviço da ingestão; ninguém da equipe
precisa ver o valor, e é melhor assim para as duas partes.

## 4. Credencial que já trafegou por e-mail

Um segredo que passou por e-mail está nas caixas postais dos destinatários, nos
servidores de trânsito e em qualquer cópia local — e não há como auditar onde
parou. Remover a mensagem não desfaz nada. **A regra é rotacionar.**

Com uma ressalva que importa: **rotacionar antes de existir Secret Manager
reproduz a exposição**, porque o valor novo teria de ser entregue pelo mesmo
e-mail. Rotação sem destino próprio não encerra nada — renova.

Por isso, para o **token do TempoOK** (recebido em 14/09), a rotação está
marcada para a **virada de produção**, quando a Alup grava o valor novo direto
no Secret Manager e ele nunca trafega por e-mail. A decisão, com dono, alcance
medido e gatilhos de antecipação, está na
[ADR 020](../arquitetura/decisoes/020-token-tempook-rotacao-na-producao.md).

Para toda credencial **seguinte** — BBCE, Hubspot, bases da Onda 3 — a regra é
a da seção 3: direto no Secret Manager, sem passar por e-mail. Isso não foi
adiado.

## 5. Checklist da virada de produção

Rodar **antes** de o ambiente `prod` receber carga real:

- [ ] **Rotacionar o token do TempoOK** junto ao fornecedor (ADR 020). O valor
      novo é gravado pela Alup direto no Secret Manager de `prod` — não passa
      por e-mail, por mensagem nem pela ness. **Em 21/09 os gatilhos 1 e 4 da
      ADR foram acionados** (o token alcança a previsão de ENA em dia): este item
      deixou de poder esperar a virada e passou a depender só de o Secret Manager
      existir — ver o adendo da ADR.
- [ ] Conferir que o valor antigo foi **revogado** no fornecedor, e não apenas
      substituído: token novo emitido não invalida o velho sozinho.
- [ ] Repetir para toda credencial que tenha trafegado por canal não
      controlado, mesmo que a leitura em `dev` estivesse funcionando.
- [ ] Conferir que **nenhum cofre local sobreviveu**: `~/.alupdata/segredos.env`
      apagado em toda estação, e `ALUPDATA_SECRETS_LOCAIS` desligado.
- [ ] Conferir que os secrets de `prod` são **distintos** dos de `dev` e `hml`
      (ADR 015, três ambientes) — reaproveitar valor entre ambientes anula a
      separação.
