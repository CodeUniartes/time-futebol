# Roadmap: site de pedidos DTF + Montador

Visão completa do projeto. Cada sub-projeto ganha spec e plano próprios (`docs/superpowers/specs/`, `docs/superpowers/plans/`).
Decisões de produto: memória do projeto `project-site-pedidos-dtf`. Cliente "Maycol" é um cliente, não o dono da gráfica.

## Arquitetura alvo

```
 PC do dono (Montador, Python)                Cloudflare                       Celular do cliente
 ┌────────────────────────────┐   publica   ┌──────────────────────┐  lê catálogo  ┌───────────────┐
 │ catalogo.json + .tif       │ ──────────► │ R2: catalog.json     │ ◄──────────── │ Site (React)  │
 │ Publicar catálogo (SP2)    │             │     previews .webp   │               │ monta pedido  │
 │                            │  busca por  │ Worker (API) + D1    │  POST pedido  │ abre WhatsApp │
 │ Importar Pedido (SP1 + SP3)│ ◄────────── │ orders, order_items  │ ◄──────────── │  com o código │
 └────────────────────────────┘   código    └──────────────────────┘               └───────────────┘
```

Regra de ouro: **os `.tif` de produção nunca saem do PC.** Só prévias reduzidas e dados do pedido trafegam.

## Layout alvo do repositório

```
app.py, src/, tests/      Montador (desktop, Python)
contracts/                schemas JSON compartilhados (fonte única do formato)
web/worker/               API (TypeScript, Hono) + migrations D1     (SP3)
web/site/                 site do cliente (React + Vite + Tailwind)  (SP4)
docs/                     roadmap, specs, plans
```

`web/` só é criado quando o SP3 começar (sem pastas vazias antes).

## Sub-projetos

| # | Nome | Tamanho | Depende de | Entrega |
|---|---|---|---|---|
| 1 | Catálogo v2 + importar pedido (arquivo) | S/M | - | Contrato do pedido, `season`/`active`, botão Importar Pedido |
| 2 | Publicar catálogo | M | 1 | `catalog.public.json` + prévias `.webp` publicados |
| 3 | API (Worker + D1) | M | 1 (contratos) | Criar/ler pedido; importar por código no Montador |
| 4 | Site do cliente | M | 2 e 3 | Catálogo, montagem, envio, WhatsApp |

SP2 e SP3 podem andar em paralelo (só compartilham contratos). SP4 precisa de ambos.

### SP2: publicar catálogo (Montador)

- **Gera** `catalog.public.json` (contrato em `contracts/catalog.public.schema.json`): só camisas `active`, categorias
  `enabled`, itens vindos de `list_available_items`. Categorias "todos os arquivos" (camisa completa, e fila/logos com
  `quick_action_all_files`) expõem o item `ALL_FILES_LABEL` ("Todos os arquivos").
- **Prévias:** Pillow abre o `.tif`, redimensiona (~400 px), aplica marca d'água e grava `.webp` em
  `previews/<time>/<camisa>/<categoria>/<item>.webp`. Hash do arquivo de origem evita reprocessar o que não mudou.
- **Envio:** `POST /api/admin/publish` (manifesto + `catalog_version` = data/hora UTC) e `POST /api/admin/preview?key=`
  por arquivo, com token de administrador. Estilo RPC (só GET/POST, ids em query), como nas regras do projeto.
- **Config local:** `config/site.json` (`api_base_url`, `admin_token`, `reader_token`), **ignorado pelo git**.
- **Riscos:** TIFF com transparência, CMYK, 16 bits ou compressão exótica quebrando o Pillow (testar com 5 arquivos
  reais antes de qualquer outra coisa); tamanho do executável com Pillow; publicar por engano camisa inativa.
- **Pronto quando:** publicar o catálogo real gera prévias legíveis e o site consegue listá-las.

### SP3: API (Cloudflare Worker + D1)

- **Endpoints:**
  - `GET /api/catalog` (público): devolve `catalog.public.json` do R2.
  - `POST /api/orders` (público, com Turnstile + limite de taxa + `Idempotency-Key`): valida contra o schema, grava,
    devolve `code`.
  - `GET /api/order?code=` (token de leitura, usado pelo Montador): devolve o JSON no formato do contrato.
  - `POST /api/admin/publish`, `POST /api/admin/preview` (token de administrador; SP2).
- **Código do pedido:** `DTF-` + 5 caracteres de um alfabeto sem ambíguos (sem 0/O/1/I/L), com nova tentativa em colisão.
- **D1 (rascunho, conforme regras do projeto: TEXT, sem FK, datas em UTC, exclusão lógica):**

  ```sql
  CREATE TABLE orders (
    id TEXT PRIMARY KEY, code TEXT NOT NULL, customer_name TEXT NOT NULL, customer_whatsapp TEXT,
    note TEXT, catalog_version TEXT, created_at TEXT NOT NULL, imported_at TEXT, deleted_at TEXT);
  CREATE UNIQUE INDEX idx_orders_code_unique ON orders(code) WHERE deleted_at IS NULL;
  CREATE TABLE order_items (
    id TEXT PRIMARY KEY, order_id TEXT NOT NULL, team_id TEXT NOT NULL, team_name TEXT, season INTEGER,
    model_id TEXT NOT NULL, model_name TEXT, category_id TEXT NOT NULL, category_name TEXT,
    item_label TEXT NOT NULL, quantity INTEGER NOT NULL, deleted_at TEXT);
  CREATE INDEX idx_order_items_order_id ON order_items(order_id) WHERE deleted_at IS NULL;
  ```

- **Montador:** "Importar por código" reaproveita `parse_site_order` do SP1; só troca a origem (arquivo → `GET /api/order`).
- **Testes:** Vitest com o pool de Workers da Cloudflare; validação usa o mesmo `contracts/order.schema.json`.
- **Riscos:** spam no endpoint público (Turnstile + limite obrigatórios); tokens vazando (repositório público: segredos só
  em `wrangler secret` e `config/site.json` local); código adivinhável (mitigado por token de leitura).
- **Retenção:** pedidos apagados (lógico) após 180 dias, decisão a confirmar no SP3.

### SP4: site do cliente

- React + Vite + Tailwind, mobile primeiro, servido pelos assets do próprio Worker.
- Telas (da matriz de estados da fase de design): Time → Ano → Versão; grade de itens por categoria; resumo; pedido
  enviado. Todos os estados: vazio, carregando, erro, parcial. Carrinho em `localStorage`; reenvio seguro (idempotência).
- WhatsApp: link `wa.me` com texto curto (código, cliente, total de peças e link). Lista completa só se couber; o código
  garante a importação de qualquer forma.
- Cor de destaque troca por time. Tokens de design saem das imagens de referência (`/spartan:ux system`).
- Testes: Vitest (lógica de carrinho) + Playwright (fluxo completo). Acessibilidade: alvos de 44 px, foco visível,
  contraste, `prefers-reduced-motion`.
- **Pronto quando:** um pedido feito no celular vira código, abre o WhatsApp e importa no Montador.

## v2 (depois da base)

| Item | O que precisa existir antes |
|---|---|
| Preço por metro linear + área de impressão | Tamanho em cm de cada arquivo (Pillow: pixels ÷ DPI), largura útil da película, algoritmo de encaixe, prévia visual |
| Caixa de pedidos do dono | Endpoint de listagem (`POST /api/admin/orders/list`, offset/limit) + tela protegida (Cloudflare Access) |
| Nome e número personalizados | Novo tipo de categoria (`custom_text`); campo aditivo `custom` no item do pedido (`{name, number}`); geração da arte por fonte |
| Pagamento / login | Fora do plano; só se a operação mudar |

## Ganchos de extensão que o SP1 já deixa prontos

1. **Contratos versionados** em `contracts/`. Campo novo opcional = mesma versão; mudança que quebra = nova versão.
2. **Parser tolerante:** ignora campos desconhecidos, então o site pode evoluir (ex.: `custom`) sem quebrar Montadores antigos.
3. **`updated_at` no catálogo** (UTC): base do `catalog_version` que o SP2 publica e os pedidos carregam.
4. **IDs estáveis** e `season` no catálogo; `active` decide o que o SP2 publica.
5. **Origem do pedido separada do parser:** hoje arquivo, no SP3 código online, com a mesma função `parse_site_order`.
6. **`config/site.json` já ignorado pelo git**, antes de existir, para nenhum token entrar no repositório público.
7. **CI de testes** (GitHub Actions) rodando `pytest` a cada push.

## Decisões em aberto (resolver no spec do sub-projeto indicado)

| Decisão | Onde |
|---|---|
| Retenção de pedidos no D1 | SP3 |
| Marca d'água: texto, posição, opacidade | SP2 |
| Domínio do site (subdomínio próprio ou `workers.dev`) | SP4 |
| Proteção da caixa de pedidos (Cloudflare Access vs senha) | v2 |
