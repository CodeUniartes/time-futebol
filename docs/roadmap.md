# Roadmap: site de pedidos DTF + Montador

Visão completa do projeto. Cada sub-projeto ganha spec e plano próprios (`docs/superpowers/specs/`, `docs/superpowers/plans/`).
Decisões de produto: memória do projeto `project-site-pedidos-dtf`. "Cliente" neste documento é quem faz o pedido; o dono da gráfica é quem opera o Montador.

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
| 5 | Painel de prévia de impressão (58 × 200 cm) | M | 2 e 4 | Encaixe automático em páginas, comprimento usado |
| 6 | Upload de arte do cliente | M | 3, 4 e 5 | Arte própria no pedido, com tamanho ditado e aceite de responsabilidade |
| 7 | Login e cadastro de clientes (telefone verificado) | M | 3 | Cliente identificado pelo WhatsApp, com código de confirmação |

SP2 e SP3 podem andar em paralelo (só compartilham contratos). SP4 precisa de ambos. SP5 precisa do tamanho em cm de cada
arte (SP2) e da tela de resumo (SP4). SP6 entra por último. Spec do SP5: `docs/superpowers/specs/2026-09-24-painel-previa-impressao-design.md`.

### SP2: publicar catálogo (Montador)

- **Gera** `catalog.public.json` (contrato em `contracts/catalog.public.schema.json`): só camisas `active`, categorias
  `enabled`, itens vindos de `list_available_items`. Categorias "todos os arquivos" (camisa completa, e fila/logos com
  `quick_action_all_files`) expõem o item `ALL_FILES_LABEL` ("Todos os arquivos").
- **Prévias:** Pillow abre o `.tif`, redimensiona (~400 px), aplica marca d'água e grava `.webp` em
  `previews/<time>/<camisa>/<categoria>/<item>.webp`. Hash do arquivo de origem evita reprocessar o que não mudou.
- **Envio:** `POST /api/admin/publish` (manifesto + `catalog_version` = data/hora UTC) e `POST /api/admin/preview?key=`
  por arquivo, com token de administrador. Estilo RPC (só GET/POST, ids em query), como nas regras do projeto.
- **Config local:** `config/site.json` (`api_base_url`, `admin_token`, `reader_token`), **ignorado pelo git**.
- **Tamanho físico (necessário ao SP5):** cada item do catálogo público sai com `width_cm` e `height_cm` (pixels ÷ resolução
  gravada no arquivo), medidos no **retângulo com tinta**, sem margem transparente; a prévia `.webp` é recortada nesse
  retângulo.
- **Leitura dos `.tif` (testada em 2026-09-24 com os 505 arquivos reais):** o Pillow sozinho lê só 232 (46%); os 273 CMYK
  com transparência (5 e 6 canais) falham. `tifffile` + `imagecodecs` + `numpy` leram os 505, sem falha, em ~0,2 s por
  arquivo. Decisão: ler com `tifffile`, converter CMYK para RGB e achatar o alfa, e usar o Pillow para redimensionar e
  gravar `.webp`. Impacto: `numpy` aumenta o `.exe` (medir).
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
- **Finalizar pedido (integração com o Worker `pedido-terceiro-ca-dtf`, decisão de 2026-09-24):**
  - **Como o Worker funciona hoje (lido em 2026-09-24, só consulta):** um formulário dentro do Digisac cria a tarefa no
    ClickUp; Automations do ClickUp (etiquetas `dtf impresso` e `dtf pronto`, parâmetro `etapa`) chamam
    `/webhooks/clickup`, que grava no D1 e enfileira; o consumidor (`readyOrder.service.ts`) move a tarefa para
    FINALIZADO e a arquiva. Um cron diário apaga dados operacionais concluídos há mais de 30 dias.
  - **Ponto de ligação:** logo depois de `finalizeClickUpTask` em `readyOrder.service.ts`, em modo *best-effort* (falha
    da chamada é registrada em `integration_events` e **não** impede a finalização).
  - **De onde vem o código:** campo novo "Código do pedido do site" no formulário do Digisac, gravado na descrição da
    tarefa e numa coluna nova em `orders` (migration). Na finalização usa a coluna; se vazia, procura `DTF-XXXXX` na
    descrição da tarefa (regex do alfabeto do código; se houver mais de um, trata todos).
  - A chamada é por **service binding** com RPC (`WorkerEntrypoint`): o Worker do site expõe `finishOrder(code)` sem rota
    HTTP pública, então não há endpoint exposto nem token para esse trecho. O outro Worker só ganha um binding no
    `wrangler`; nenhum código dele é alterado além da chamada.
  - `finishOrder(code)`: apaga `uploads/<code>/` no R2, marca o pedido como concluído no D1 e devolve quantos arquivos
    apagou. Idempotente (chamar duas vezes não falha) e código inexistente devolve "não encontrado" sem erro.
  - Camadas de limpeza: 1) finalizar no ClickUp; 2) o Montador apaga do R2 depois de baixar a arte (SP6); 3) expiração
    automática do R2 como rede de segurança.

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

### SP5: painel de prévia de impressão

Spec: `docs/superpowers/specs/2026-09-24-painel-previa-impressao-design.md`. O cliente vê, no resumo do pedido, um painel
de 58 × 200 cm com as artes encaixadas na escala real (giro de 90°, espaço mínimo de 1/10 pol, quantidade N = N cópias),
em páginas navegáveis e com o comprimento usado. Algoritmo em TypeScript (MaxRects), reaproveitável no Worker.
O `layout` pode ir no pedido como campo opcional e informativo; a produção recalcula.

### SP7: login de clientes (proposto em 2026-09-24, a confirmar)

O **telefone (WhatsApp) é o identificador do cliente**. Sem verificar que a pessoa é dona do número, qualquer um poderia
ver ou refazer pedidos de outro, então o login confirma o número com um **código de uso único** (OTP).

- **Fluxo:** cliente informa o número → recebe código de 6 dígitos (validade curta, poucas tentativas) → sessão em cookie
  `HttpOnly; Secure; SameSite=Strict`. O login pode ficar só na hora de enviar o pedido, sem travar a navegação pelo catálogo.
- **Envio do código:** WhatsApp (o Digisac já é usado pela gráfica; confirmar se a API dele envia mensagem ativa) ou SMS
  como alternativa. Custo por mensagem a confirmar.
- **Dados (D1, regras do projeto):** `customers` (id, `phone` normalizado só dígitos com `55`+DDD, `name`, datas UTC,
  exclusão lógica), `login_codes` (só o hash do código, expiração, tentativas), `sessions`. `orders` ganha `customer_id`.
  O contrato do pedido continua com `customer.whatsapp` (agora sempre presente e normalizado).
- **Proteções:** Turnstile e limite de envios por número e por IP (evita gastar mensagens e spam), sem revelar se o número
  já existe, bloqueio temporário após tentativas erradas.
- **O que o cliente ganha:** dados preenchidos, histórico dos pedidos, refazer um pedido anterior e, no SP6, biblioteca
  das próprias artes.
- **Privacidade (LGPD):** aviso do uso do telefone e do nome, consulta e exclusão dos dados a pedido, retenção definida.
- **Montador:** pode listar clientes e pedidos por telefone; a integração de finalização continua pelo código do pedido.

### SP6: upload de arte do cliente

O cliente envia uma arte junto do pedido e **dita o tamanho** (largura ou altura em cm, proporção mantida, máx. 58 cm).
Aviso de responsabilidade com aceite registrado no pedido (data/hora e versão do texto): fundo, resolução ruim e afins são
do cliente. Limites de segurança: tipos aceitos (PNG, JPG, PDF), tamanho máximo por arquivo e artes por pedido. A arte
entra no encaixe do SP5 como mais um retângulo. Requer endpoint de envio no SP3.

**Armazenamento (decisão de 2026-09-24):** o R2 guarda só o que faz o site funcionar (`catalog.public.json` e prévias).
As artes dos clientes, mais pesadas, vão para o R2 **apenas como arquivo temporário** (prefixo `uploads/`, com regra de
ciclo de vida que apaga sozinha após poucos dias) e passam a viver num servidor local. Para não expor o servidor local
à internet, o Montador **busca** as artes pelo código do pedido (só conexão de saída), grava em disco e pede a remoção do
R2 (`uploads/` continua com a expiração automática como rede de segurança). O destino local (pasta do PC, NAS ou servidor)
fica atrás de uma interface simples, para trocar depois sem mexer no site.

## v2 (depois da base)

| Item | O que precisa existir antes |
|---|---|
| Preço por metro linear | SP5 pronto (comprimento usado) e a tabela de preço |
| PDF de impressão já montado | SP5 com arte em resolução real (o painel v1 é só prévia) |
| Caixa de pedidos do dono | Endpoint de listagem (`POST /api/admin/orders/list`, offset/limit) + tela protegida (Cloudflare Access) |
| Nome e número personalizados | Novo tipo de categoria (`custom_text`); campo aditivo `custom` no item do pedido (`{name, number}`); geração da arte por fonte |
| Pagamento online | Fora do plano; só se a operação mudar (o login de clientes agora é o SP7) |

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
| Servidor local das artes de clientes (pasta do PC, NAS ou servidor) e quantos dias o R2 as guarda | SP6 |
| Proteção da caixa de pedidos (Cloudflare Access vs senha) | v2 |
