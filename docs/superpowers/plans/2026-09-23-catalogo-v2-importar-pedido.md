# Plano: catálogo v2 e importar pedido (SP1)

**Spec:** [`../specs/2026-09-23-catalogo-v2-importar-pedido-design.md`](../specs/2026-09-23-catalogo-v2-importar-pedido-design.md)
**Criado:** 2026-09-23 · **Status:** rascunho (aguardando revisão) · **Branch:** `feature/catalogo-v2-importar-pedido`

Convenção do projeto: planos ficam em `docs/superpowers/plans/` (não em `.planning/`). Teste antes do código em
`services/` e `utils/`; UI só orquestra e é verificada à mão.

## Componentes

| Componente | Tipo | Finalidade |
|---|---|---|
| `model_display_name` | função em `models/` | Rótulo `"<nome> · <ano>"` ou só `<nome>` |
| `CatalogService` (alterado) | service | Migração v1→v2, `season`/`active`, ID com ano, `updated_at` |
| `order_import_service` (novo) | service | `parse_site_order(dict, catalog) -> ImportedOrder`, `OrderImportError` |
| `contracts/*` (novos) | JSON Schema + exemplos | Contrato do pedido e rascunho do catálogo público |
| `OrderPanel` / `MainWindow` | UI | Menu com ano, botão **Importar Pedido** |
| `ConfigWindow` | UI | Campos **Ano** e **Ativa** |

## Arquivos

Novos:

| Arquivo | Finalidade |
|---|---|
| `src/services/order_import_service.py` | Parser do pedido do site |
| `contracts/order.schema.json`, `contracts/order.example.json` | Contrato do pedido v1 |
| `contracts/catalog.public.schema.json`, `contracts/catalog.public.example.json` | Rascunho do catálogo público |
| `contracts/README.md` | Regras de versionamento dos contratos |
| `tests/test_order_import_service.py` | Testes do parser |
| `tests/test_catalog_service.py` | Migração, ID com ano, `updated_at` |
| `tests/test_catalog_models.py` | `model_display_name` |
| `tests/test_contracts.py` | Exemplos válidos e aceitos pelo parser |
| `.github/workflows/tests.yml` | CI (Windows, Python 3.12) |

Alterados:

| Arquivo | O que muda |
|---|---|
| `src/models/catalog_models.py` | `SCHEMA_VERSION = 2`, `BLANK_CATALOG` v2, `model_display_name` |
| `src/services/catalog_service.py` | Migração em `load_catalog`; `add_model`/`update_model` com `season`/`active`; ID com ano; `save_catalog` grava `updated_at` |
| `src/ui/order_panel.py` | `model_map` por `model_display_name`; `import_order()` |
| `src/ui/main_window.py` | Botão **Importar Pedido**; botões da barra 130 → 116 px (linha 99) |
| `src/ui/config_window.py` | Campos Ano e Ativa; `model_map` por `model_display_name` |
| `.gitignore` | `config/site.json` |
| `CLAUDE.md`, `README.md` | Apontam para `docs/roadmap.md` e `contracts/` |

## Tarefas

Cada tarefa é um commit, no máximo 3 arquivos. "Testa" indica o teste que nasce antes do código.

### Fase 1: contrato e parser (sem dependências)

| # | Tarefa | Arquivos | Testa |
|---|---|---|---|
| 1 | Contrato do pedido: schema + exemplo | `contracts/order.schema.json`, `contracts/order.example.json` | Exemplo é JSON válido (fecha na tarefa 3) |
| 2 | `order_import_service`: `OrderImportError`, `ImportedOrder`, validação (JSON/objeto, `schema_version`, campos obrigatórios, `quantity` 1–999 sem bool/str) | `src/services/order_import_service.py`, `tests/test_order_import_service.py` | Pedido válido; versão 2; sem `code`/`customer.name`/`items`; item sem campo; quantidade 0, 1000, `true`, `"2"` |
| 3 | Mapeamento para o payload: Observação (`WhatsApp <n> · <nota>`, partes ausentes omitidas), `model_name` com ano, nomes ausentes usam o id, primeiro item vira time/modelo selecionados, campos extras ignorados, item fora do catálogo vira aviso (via `find_in_catalog`) | `src/services/order_import_service.py`, `tests/test_order_import_service.py`, `tests/test_contracts.py` | Observação com/sem WhatsApp e nota; ano no `model_name`; `custom` e `foo` ignorados e ausentes do payload; aviso lista o item; `order.example.json` aceito |

### Fase 2: schema v2 (depende só de `catalog_models`)

| # | Tarefa | Arquivos | Testa |
|---|---|---|---|
| 4 | `SCHEMA_VERSION = 2`, `BLANK_CATALOG` v2, `model_display_name` | `src/models/catalog_models.py`, `tests/test_catalog_models.py` | Com e sem ano; mesmo nome em anos diferentes gera rótulos distintos |
| 5 | Migração v1→v2 em `load_catalog` (em memória: `schema_version=2`, `active=True` onde faltar, `season` opcional, IDs intactos) | `src/services/catalog_service.py`, `tests/test_catalog_service.py` | Catálogo v1 carrega como v2 sem perder dados nem mudar IDs; v2 não é alterado |
| 6 | `add_model`/`update_model` aceitam `season`/`active`; ID novo = `slugify(nome + " " + ano)`, único no time | `src/services/catalog_service.py`, `tests/test_catalog_service.py` | `home_1_2026`; colisão vira `_2`; sem ano mantém o comportamento atual; `update_model` não muda o ID |
| 7 | `save_catalog` grava `updated_at` UTC com `Z` | `src/services/catalog_service.py`, `tests/test_catalog_service.py` | Termina em `Z`; muda a cada gravação (relógio injetável ou milissegundos) |

### Fase 3: contratos do catálogo público (depende da 1)

| # | Tarefa | Arquivos | Testa |
|---|---|---|---|
| 8 | Rascunho do catálogo público (item com `width_cm`/`height_cm` opcionais, para o SP5) + regras de versionamento, incluindo `layout` opcional no pedido | `contracts/catalog.public.schema.json`, `contracts/catalog.public.example.json`, `contracts/README.md` | `tests/test_contracts.py`: JSON válido, com `width_cm`/`height_cm` num item do exemplo, com `schema_version`, `catalog_version` e ao menos uma camisa com item |

### Fase 4: interface (depende das fases 1 e 2; sem testes automáticos)

| # | Tarefa | Arquivos | Verificação manual |
|---|---|---|---|
| 9 | Menu de camisas usa `model_display_name` (Pedido e Configurações) | `src/ui/order_panel.py`, `src/ui/config_window.py` | Duas camisas de mesmo nome e anos diferentes aparecem separadas; camisa sem ano mostra só o nome |
| 10 | Campos **Ano** (inteiro opcional, valida) e **Ativa (aparece no site)** em Configurações; passam para `add_model`/`update_model` | `src/ui/config_window.py` | Salvar, fechar, reabrir: valores permanecem; ano inválido mostra aviso |
| 11 | Botão **Importar Pedido**: seletor de arquivo → `parse_site_order` → confirma "Substituir o pedido atual?" se o carrinho tem itens → `load_order_payload` → mostra avisos; erros em `messagebox` sem travar. Barra 130 → 116 px | `src/ui/order_panel.py`, `src/ui/main_window.py` | Importar `contracts/order.example.json`; arquivo inválido; carrinho cheio pede confirmação; janela mínima 1180 px sem cortar botões |

### Fase 5: infraestrutura e docs (independentes, podem ir em qualquer momento)

| # | Tarefa | Arquivos |
|---|---|---|
| 12 | `.gitignore` ignora `config/site.json` | `.gitignore` |
| 13 | CI: `pytest` a cada push/PR (Windows, Python 3.12) | `.github/workflows/tests.yml` |
| 14 | `CLAUDE.md` e `README.md` apontam para `docs/roadmap.md` e `contracts/`; `CLAUDE.md` passa a citar `season`/`active` e o parser | `CLAUDE.md`, `README.md` |

## Paralelo vs sequencial

| Grupo paralelo | Tarefas | Por quê |
|---|---|---|
| A | 1→2→3 | Parser, só depende do contrato |
| B | 4→5→6→7 | Catálogo; todas tocam `catalog_service.py`, então em sequência |
| C | 12, 13 | Arquivos isolados |

| Sequencial | Depende de | Por quê |
|---|---|---|
| 8 | 1 | Reaproveita o padrão do contrato e `test_contracts.py` |
| 9, 10 | 4, 6 | Usam `model_display_name` e o `season`/`active` do service |
| 11 | 3, 9 | Usa o parser e o `model_map` novo |
| 14 | todas | Documenta o que foi feito |

Ordem recomendada (a da spec): 1–3, 4–7, 8, 9, 10, 11, 12–13, 14.

## Plano de testes (Gate 2)

- **Dados/serviços:** migração sem perda, ID com ano, `updated_at` (tarefas 4 a 7).
- **Regra de negócio:** validação e mapeamento do pedido, campos extras, aviso de item fora do catálogo (2 e 3).
- **Contratos:** exemplos válidos; o do pedido é aceito pelo parser; o do catálogo público tem os campos mínimos (3 e 8).
- **UI:** roteiro manual das tarefas 9 a 11, mais um pedido salvo antigo abrindo sem erro (compatibilidade).
- **Regressão:** `python -m pytest` verde antes de cada commit (hoje: 19 testes).

## Riscos

- `updated_at` em segundos empata em gravações seguidas: usar milissegundos ou relógio injetável no teste.
- `model_map` por rótulo: se dois rótulos ficarem iguais (mesmo nome, ambos sem ano), um sobrescreve o outro. Hoje já é assim; a tarefa 9 só resolve o caso com ano.
- `load_order_payload` só troca time/modelo se o `id` existir no catálogo local; o item fora do catálogo já cai no aviso.

## Gate 2

- [x] Segue a arquitetura existente (UI orquestra, lógica em `services/`)
- [x] Cada camada só chama a de baixo
- [x] Todos os arquivos, novos e alterados, listados
- [x] Tarefas pequenas (máx. 3 arquivos, um commit)
- [x] Dependências e paralelismo marcados
- [x] Testes de dados, regra e contratos planejados; UI com roteiro manual (o projeto não testa UI)
- [x] Casos de borda da spec cobertos
