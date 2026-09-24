# API do site (sub-projeto 3): Cloudflare Worker + D1 + R2

Data: 2026-09-24 · Status: rascunho para revisão · Tamanho estimado: M (~2 dias) · Depende de: SP1 e SP2A (prontos)

## Contexto

O Worker é o elo entre o Montador (PC do dono), o site do cliente (SP4) e o Worker de pedidos do ClickUp. Ele guarda o
catálogo público e as prévias (R2), recebe e guarda pedidos (D1) e entrega o pedido ao Montador pelo código. Visão geral em
[`docs/roadmap.md`](../../roadmap.md); formatos em [`contracts/`](../../../contracts/). Login de clientes (SP7) e upload de
artes (SP6) usam este Worker mas têm spec própria.

## Objetivo e critério de sucesso

1. O Montador envia o catálogo e as prévias (**etapa 2B**) e o site consegue ler o catálogo.
2. Um pedido enviado pelo site (mesmo em teste, por `curl`) vira um código `DTF-XXXXX`; o Montador o importa por esse código
   com o mesmo `parse_site_order` do SP1.
3. O Worker do ClickUp consegue avisar "pedido finalizado" por service binding.

## Decisões

| Tema | Decisão |
|---|---|
| Nomes (sugeridos, a confirmar) | Worker `pedido-dtf-site`, D1 `pedido-dtf-site-db`, bucket R2 `pedido-dtf-site-files`, endereço `*.workers.dev` no começo |
| Stack | TypeScript, Hono, Vitest com `@cloudflare/vitest-pool-workers`, `wrangler.jsonc`; código em `web/worker/` |
| Estilo da API | Só `GET` e `POST`; ids em query (`?code=`), nunca em caminho; JSON em `snake_case`; datas ISO 8601 UTC com `Z` |
| Validação | `contracts/order.schema.json` compilado com `@cfworker/json-schema` (o Ajv usa `new Function`, bloqueado nos Workers) |
| Autenticação | Público: catálogo, prévias, criar pedido (Turnstile). Montador: token de **leitura** (ler pedido) e token de **administrador** (publicar). Comparação em tempo constante |
| Segredos | `wrangler secret`: `ADMIN_TOKEN`, `READER_TOKEN`, `TURNSTILE_SECRET`. Nada no repositório (é público) |
| Erros | `{ "error": { "code", "message", "status", "details" } }`, mensagem em português, sem detalhe interno |
| CORS | Nenhum: o site é servido pelo próprio Worker (mesma origem). Rotas de administrador nunca aceitam origem de navegador |

## Rotas

| Rota | Quem | O que faz |
|---|---|---|
| `GET /api/catalog` | Público | Devolve `catalog/catalog.public.json` do R2, com `ETag` e `Cache-Control: public, max-age=60` |
| `GET /api/preview?key=` | Público | Devolve a prévia `.webp` (só chaves em `previews/`), `Cache-Control: public, max-age=31536000`; o site acrescenta `&v=<catalog_version>` para renovar |
| `POST /api/orders` | Público | Cria o pedido (ver abaixo) |
| `GET /api/order?code=` | Leitura | Devolve o pedido no formato do contrato, para `parse_site_order` |
| `POST /api/order/imported?code=` | Leitura | Marca o pedido como importado (`imported_at`, status) |
| `POST /api/admin/publish/plan` | Admin | Recebe o manifesto das prévias (chave, `sha256`, tamanho) e devolve só as que faltam ou mudaram |
| `POST /api/admin/preview?key=` | Admin | Recebe uma prévia (corpo binário, cabeçalho `X-Sha256`); confere o hash antes de gravar |
| `POST /api/admin/publish/commit` | Admin | Recebe o `catalog.public.json`; confere que **todas** as prévias citadas existem; troca o catálogo atual de uma vez e devolve as chaves órfãs removidas |
| `GET /api/health` | Público | `{ "ok": true }` para monitoramento |

### Publicação em três passos (etapa 2B)

1. **plan:** o Montador manda o manifesto; o Worker compara com o que já está no R2 e responde quais enviar.
2. **preview:** o Montador envia cada arquivo novo ou alterado (sequencial ou em pequenos lotes), com o hash.
3. **commit:** só agora o `catalog.public.json` novo substitui o antigo, e as prévias que não aparecem mais são apagadas.
   Se o envio cair no meio, o catálogo antigo continua íntegro e válido: o site nunca aponta para prévia inexistente.

## Pedido: criar

`POST /api/orders` com o corpo no formato de `contracts/order.schema.json` mais `turnstile_token`, e o cabeçalho
`Idempotency-Key` (obrigatório, 16 a 64 caracteres).

1. Confere o tamanho do corpo (máx. 256 KB), o Turnstile (`siteverify`) e o limite de taxa por IP.
2. Valida contra o esquema; regras extras: até 300 itens, `quantity` 1 a 999, nome do cliente até 120 caracteres, `note` até 500.
3. **Ignora** `code`, `created_at` e `catalog_version` vindos do cliente: o servidor gera `code` e `created_at`, e guarda o
   `catalog_version` que estava publicado no momento.
4. Normaliza o WhatsApp para só dígitos com `55` + DDD (base do SP7).
5. Idempotência: mesma chave e mesmo corpo devolvem o **mesmo** pedido; mesma chave com corpo diferente devolve `409`.
6. Grava `orders` e `order_items` numa única operação `batch` do D1 (atômica) e responde `201` com `{ code, created_at }`.

**Código do pedido:** `DTF-` + 5 caracteres de `23456789ABCDEFGHJKMNPQRSTUVWXYZ` (31 símbolos, sem 0/O/1/I/L), sorteados com
`crypto.getRandomValues` e rejeição de viés; colisão no índice único tenta de novo (até 5 vezes). Espaço de ~28,6 milhões.
O código não é segredo: ler o pedido exige o token de leitura.

## Dados (D1)

Regras do projeto: `TEXT`, sem chave estrangeira, datas em UTC, exclusão lógica, índices parciais.

```sql
CREATE TABLE orders (
  id TEXT PRIMARY KEY, code TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open',
  customer_name TEXT NOT NULL, customer_whatsapp TEXT, customer_id TEXT, note TEXT,
  catalog_version TEXT, created_at TEXT NOT NULL, imported_at TEXT, finished_at TEXT, deleted_at TEXT);
CREATE UNIQUE INDEX idx_orders_code_unique ON orders(code) WHERE deleted_at IS NULL;
CREATE INDEX idx_orders_status ON orders(status, created_at) WHERE deleted_at IS NULL;

CREATE TABLE order_items (
  id TEXT PRIMARY KEY, order_id TEXT NOT NULL, position INTEGER NOT NULL,
  team_id TEXT NOT NULL, team_name TEXT, season INTEGER, model_id TEXT NOT NULL, model_name TEXT,
  category_id TEXT NOT NULL, category_name TEXT, item_label TEXT NOT NULL, quantity INTEGER NOT NULL,
  deleted_at TEXT);
CREATE INDEX idx_order_items_order_id ON order_items(order_id) WHERE deleted_at IS NULL;

CREATE TABLE idempotency_keys (
  key TEXT PRIMARY KEY, request_hash TEXT NOT NULL, order_id TEXT NOT NULL, created_at TEXT NOT NULL);

CREATE TABLE catalog_versions (
  catalog_version TEXT PRIMARY KEY, published_at TEXT NOT NULL, item_count INTEGER NOT NULL);

CREATE TABLE preview_files (
  key TEXT PRIMARY KEY, sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL, updated_at TEXT NOT NULL);
```

Status do pedido: `open` → `imported` (Montador leu) → `finished` (ClickUp finalizou). `customer_id` fica vazio até o SP7.

## R2

```
catalog/catalog.public.json      catálogo atual (troca atômica no commit)
previews/<time>/<camisa>/<categoria>/<item>.webp
uploads/<code>/...               artes de clientes, temporárias (SP6)
```

Regra de ciclo de vida do bucket: prefixo `uploads/` expira em 7 dias (rede de segurança do SP6).

## Integração com o Worker do ClickUp (`pedido-terceiro-ca-dtf`)

- **Service binding com RPC:** este Worker exporta `class SiteRpc extends WorkerEntrypoint` com
  `finishOrder(code)`. Não existe rota HTTP para isso.
- `finishOrder(code)`: marca `finished_at` e `status`, apaga tudo de `uploads/<code>/` e devolve
  `{ found, deleted_files }`. Idempotente; código inexistente devolve `found: false` sem erro.
- No outro Worker só entram um binding no `wrangler` e uma chamada *best-effort* depois de `finalizeClickUpTask`. **Nenhuma
  alteração nele sem a sua autorização.**

## Retenção e limpeza

Cron diário (06:00 UTC): pedidos `finished` com mais de **180 dias** recebem exclusão lógica, e ali se apagam
`idempotency_keys` com mais de 7 dias. O prazo é decisão sua (o Worker de pedidos usa 30 dias para dados operacionais).

## Segurança

- Tokens comparados em tempo constante; falhas de autenticação viram `401` sem indicar qual token estava errado.
- Turnstile e limite de taxa no `POST /api/orders`; corpo com tamanho máximo em todas as rotas.
- Sem PII em log (nome, telefone e observação ficam fora); só `code`, status e tempo.
- Prévias: só chaves que começam com `previews/` e terminam em `.webp`, sem `..` (evita ler outros arquivos do bucket).
- Resposta de erro nunca devolve pilha nem texto do banco.

## Testes (escritos antes do código)

- **Contrato:** pedido válido cria; todos os casos inválidos do esquema e de tamanho voltam `400` em português.
- **Servidor manda:** `code`, `created_at` e `catalog_version` enviados pelo cliente são ignorados.
- **Idempotência:** mesma chave e corpo devolvem o mesmo `code`; corpo diferente devolve `409`; concorrência não duplica.
- **Código:** formato e alfabeto; colisão tenta de novo; sem viés grosseiro na distribuição.
- **Autenticação:** cada rota recusa sem token e com o token errado, inclusive o de leitura numa rota de administrador.
- **Turnstile e limite:** token inválido recusa; excesso de pedidos por IP recebe `429`.
- **Publicação:** `plan` só devolve o que falta; hash errado recusa o upload; `commit` com prévia ausente recusa e mantém o
  catálogo antigo; `commit` válido troca e remove órfãs; falha no meio não altera o catálogo publicado.
- **Prévia (leitura):** só `previews/*.webp`; tentativa de `../` ou de outro prefixo recusa.
- **RPC:** `finishOrder` marca, apaga `uploads/<code>/`, é idempotente e não falha com código desconhecido.
- **Cron:** aplica a retenção só aos pedidos elegíveis.
- **Compatibilidade:** o JSON de `GET /api/order` passa em `parse_site_order` do Montador (teste no repositório Python
  com um exemplo gerado pelo Worker).

## Riscos

- **Spam no endpoint público:** Turnstile e limite de taxa são obrigatórios antes de abrir o site.
- **Vazamento de token do Montador** (`config/site.json`): tokens separados (leitura e administrador), rotação com
  `wrangler secret put`, arquivo fora do git.
- **Limites da Cloudflare:** corpo de requisição, tamanho de objeto e CPU por requisição; a validação é leve e as
  prévias são pequenas (~9 KB).
- **Custo:** dentro do plano gratuito para o volume esperado; `workers.dev` não exige domínio.
- **Dependência do Worker de pedidos:** a chamada é opcional; se cair, a expiração do R2 limpa `uploads/`.

## Pré-requisitos (ações suas, com o meu aviso antes)

1. Aprovar os nomes acima (ou trocar).
2. Criar o **widget do Turnstile** no painel da Cloudflare (chave do site e chave secreta).
3. Autorizar a criação do D1 e do bucket R2 na sua conta (faço com o `wrangler`, que já está logado).
4. Gerar os tokens de administrador e de leitura (você guarda em `config/site.json`; eu nunca os coloco no repositório).

## Fora do escopo

Site (SP4), painel de encaixe (SP5), upload de arte e sua limpeza no Montador (SP6), login de clientes (SP7), caixa de
pedidos do dono, pagamento.
