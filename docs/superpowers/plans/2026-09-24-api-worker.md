# Plano: API do site (SP3)

**Spec:** [`../specs/2026-09-24-api-worker-design.md`](../specs/2026-09-24-api-worker-design.md)
**Criado:** 2026-09-24 · **Status:** rascunho · **Branch:** `feature/api-worker`

Teste antes do código em tudo. Nada é criado na conta da Cloudflare (D1, R2, secrets, deploy) sem o seu aviso: até a
fase 6 o Worker roda só localmente e nos testes, com D1 e R2 simulados pelo Miniflare.

## Estrutura

```
web/worker/
  wrangler.jsonc, package.json, tsconfig.json, vitest.config.ts
  migrations/0001_init.sql
  src/index.ts (Hono + export do SiteRpc)   src/routes/*.ts   src/services/*.ts   src/lib/*.ts
  test/*.test.ts
```

Módulos: `lib/` (auth, erros, código do pedido, hash, normalização de telefone, chaves de prévia), `services/` (pedidos,
catálogo e publicação, idempotência, Turnstile, retenção), `routes/` (só HTTP: valida entrada e delega). Rota não fala com
o banco; serviço não conhece HTTP.

## Tarefas

### Fase 1: esqueleto

| # | Tarefa | Arquivos |
|---|---|---|
| 1 | Projeto `web/worker`: Hono, `wrangler.jsonc` (bindings `DB`, `FILES`; sem IDs reais), Vitest do pool de Workers, `GET /api/health` com teste | `package.json`, `wrangler.jsonc`, `src/index.ts` |
| 2 | Migração `0001_init.sql` (5 tabelas e índices da spec) e teste que aplica a migração e confere as tabelas | `migrations/0001_init.sql`, `test/migrations.test.ts` |
| 3 | Erros no formato da spec, tratamento global, limite de corpo | `src/lib/errors.ts`, `src/index.ts`, `test/errors.test.ts` |

### Fase 2: núcleo do pedido

| # | Tarefa | Arquivos |
|---|---|---|
| 4 | `lib/order-code`: gerar `DTF-XXXXX` com rejeição de viés; formato e alfabeto | `src/lib/order-code.ts`, `test/order-code.test.ts` |
| 5 | `lib/phone`: normalizar WhatsApp (`55` + DDD, só dígitos, casos com 9 e sem 9, inválidos) | `src/lib/phone.ts`, `test/phone.test.ts` |
| 6 | Validação do pedido com `@cfworker/json-schema` lendo `contracts/order.schema.json` (cópia sincronizada por script) + regras extras (limites); mensagens em português | `src/services/order-validation.ts`, `test/order-validation.test.ts` |
| 7 | Serviço de pedido: cria em `batch`, servidor gera `code`/`created_at`, ignora os do cliente, guarda `catalog_version`, tenta de novo na colisão | `src/services/orders.ts`, `test/orders.test.ts` |
| 8 | Idempotência: mesma chave e corpo devolvem o mesmo pedido; corpo diferente `409`; concorrência | `src/services/idempotency.ts`, `test/idempotency.test.ts` |

### Fase 3: rotas de pedido e proteções (depende da fase 2)

| # | Tarefa | Arquivos |
|---|---|---|
| 9 | `lib/auth`: tokens `Bearer` em tempo constante (leitura e administrador, separados) | `src/lib/auth.ts`, `test/auth.test.ts` |
| 10 | Turnstile (`siteverify` com `fetch` simulado) e limite de taxa por IP | `src/services/turnstile.ts`, `src/lib/rate-limit.ts`, `test/protection.test.ts` |
| 11 | `POST /api/orders` (integra 4 a 10) | `src/routes/orders.ts`, `test/orders-route.test.ts` |
| 12 | `GET /api/order?code=` no formato do contrato e `POST /api/order/imported?code=` | `src/routes/order-read.ts`, `src/services/orders.ts`, `test/order-read.test.ts` |

### Fase 4: catálogo e publicação (destrava a 2B)

| # | Tarefa | Arquivos |
|---|---|---|
| 13 | `lib/keys`: chave de prévia segura (`previews/`, `.webp`, sem `..`) e hash `sha256` | `src/lib/keys.ts`, `test/keys.test.ts` |
| 14 | `GET /api/catalog` (ETag, cache) e `GET /api/preview?key=` | `src/routes/catalog.ts`, `test/catalog-read.test.ts` |
| 15 | `POST /api/admin/publish/plan` e `POST /api/admin/preview?key=` (confere hash e tamanho) | `src/routes/admin-publish.ts`, `src/services/publish.ts`, `test/publish-plan.test.ts` |
| 16 | `POST /api/admin/publish/commit`: confere prévias, troca atômica, remove órfãs, registra a versão | `src/services/publish.ts`, `src/routes/admin-publish.ts`, `test/publish-commit.test.ts` |

### Fase 5: integração e limpeza

| # | Tarefa | Arquivos |
|---|---|---|
| 17 | `SiteRpc.finishOrder(code)` (marca, apaga `uploads/<code>/`, idempotente) | `src/rpc.ts`, `src/index.ts`, `test/rpc.test.ts` |
| 18 | Cron de retenção (180 dias) e limpeza de idempotência | `src/services/retention.ts`, `src/index.ts`, `test/retention.test.ts` |

### Fase 6: nuvem (só com o seu aviso, uma a uma)

| # | Tarefa | O que faço |
|---|---|---|
| 19 | Criar D1 e bucket R2, ajustar IDs no `wrangler.jsonc`, aplicar a migração remota | Peço o "sim" antes; uso o `wrangler` já logado |
| 20 | Regra de ciclo de vida do bucket (`uploads/` em 7 dias) | Peço o "sim" antes |
| 21 | Cadastrar `ADMIN_TOKEN`, `READER_TOKEN`, `TURNSTILE_SECRET` | **Você** gera os valores; eu só rodo `wrangler secret put` se você colar por lá, nunca em arquivo |
| 22 | Primeiro deploy e teste real com `curl` (health, criar pedido, ler pedido) | Só depois de 19 a 21 |

### Fase 7: lado do Montador (Python, no repositório atual)

| # | Tarefa | Arquivos |
|---|---|---|
| 23 | `site_client.py`: chamadas HTTP (plan, preview, commit, ler pedido) com tratamento de erro; `site_config_service` ganha `api_base_url`, `admin_token`, `reader_token` | `src/services/site_client.py`, `src/services/site_config_service.py`, `tests/test_site_client.py` |
| 24 | Etapa **2B** em `publish_service`: enviar depois de gerar (só o que mudou, commit no fim), progresso e cancelar | `src/services/publish_service.py`, `src/ui/publish_window.py`, `tests/test_publish_upload.py` |
| 25 | **Importar por código**: campo no botão Importar Pedido; `GET /api/order` → `parse_site_order` → carrinho; marca como importado | `src/services/order_import_service.py`, `src/ui/order_panel.py`, `tests/test_order_by_code.py` |

## Paralelo e sequencial

| Grupo paralelo | Tarefas | Por quê |
|---|---|---|
| A | 4, 5, 9, 13 | Funções puras em `lib/`, sem dependência entre si |
| B | 17, 18 | Só dependem da fase 1 e do serviço de pedidos |
| C | 23 | O cliente Python pode ser escrito contra as rotas da spec antes do deploy |

| Sequencial | Depende de | Por quê |
|---|---|---|
| 6, 7 | 2 (migração) e 4, 5 | Serviço grava e valida com o esquema do banco |
| 11 | 4 a 10 | Integra tudo |
| 15, 16 | 13, 14 | Usam a chave segura e o R2 |
| 19 a 22 | 1 a 18 | Nuvem só com o código testado |
| 24, 25 | 22 (para o teste real) e 23 | Precisam do Worker no ar |

Ordem recomendada: 1–3, 4–5 e 9 e 13 (em paralelo), 6–8, 10–12, 14–16, 17–18, **pausa para você criar Turnstile e aprovar a nuvem**, 19–22, 23–25.

## Testes (mapa para a spec)

Cada linha da seção "Testes" da spec cai numa tarefa acima: contrato e servidor-manda (6, 7, 11), idempotência (8),
código (4), autenticação (9), Turnstile e limite (10), publicação (15, 16), prévia (13, 14), RPC (17), cron (18) e
compatibilidade com `parse_site_order` (25).

## Gate 2

- [x] Camadas: rota → serviço → banco/R2; funções puras em `lib/`
- [x] Todos os arquivos e a estrutura listados
- [x] Tarefas pequenas (no máximo 3 arquivos, um commit)
- [x] Dependências e paralelismo marcados
- [x] Testes para dados, regra, rotas, segurança e integração; nuvem só depois do código testado
- [x] Ações na conta da Cloudflare separadas e dependentes do seu aviso
