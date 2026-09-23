# Catálogo v2 e importação de pedido (sub-projeto 1)

Data: 2026-09-23 · Status: aguardando revisão · Tamanho estimado: S/M (~1 dia)

## Contexto

Projeto maior: site onde clientes de DTF de camisa de time montam o pedido e o dono da gráfica o importa no Montador
de Pedido Futebol. Decisões gerais estão na memória do projeto (`project_site-pedidos-dtf`). O projeto se divide em 4
sub-projetos, cada um com spec, plano e código próprios:

1. **Este:** núcleo no Montador (catálogo v2, contrato do pedido, importar pedido de arquivo `.json`).
2. Publicar catálogo (prévias `.webp` + `catalog.json` no R2).
3. API (Worker + D1).
4. Site do cliente.

## Objetivo e critério de sucesso

O dono abre o Montador, clica em **Importar Pedido**, escolhe um `.json` no formato do contrato e o carrinho aparece
preenchido, pronto para **Validar arquivos** e **Gerar pasta de produção**. Funciona 100% offline, sem site.

## Decisões

| Tema | Decisão |
|---|---|
| Ano | Campo `season` (int, opcional) da camisa. Não é um nível novo da árvore. |
| ID da camisa | Novas camisas: `slugify(nome + " " + ano)` (ex.: `home_1_2026`), único dentro do time. IDs existentes não mudam. |
| Versão da camisa | Nome livre (Home 1, Home 2, Home 3...). |
| `active` | Campo da camisa (padrão `true`). Só vai controlar o que o site publica (sub-projeto 2). O Montador mostra todas as camisas, ativas ou não, para poder produzir pedidos antigos. |
| Schema do catálogo | `schema_version` sobe de 1 para 2. |
| Carrinho | `CartItem` **não muda**. Ano é só informativo. |
| Preço/metragem | Fora da v1 inteira do projeto. |

## Contrato do pedido (v1)

Arquivos: `contracts/order.schema.json` (JSON Schema) e `contracts/order.example.json`. O site (sub-projeto 4) usará o
mesmo arquivo. A fonte de verdade do que é aceito é o `order_import_service`; um teste garante que o exemplo é aceito.

```json
{
  "schema_version": 1,
  "code": "DTF-7K3F",
  "created_at": "2026-09-23T14:05:00Z",
  "customer": { "name": "Fulano", "whatsapp": "31999999999" },
  "note": "Entrega sexta",
  "catalog_version": "2026-09-20T10:00:00Z",
  "items": [
    {
      "team_id": "atletico_mineiro", "team_name": "Atletico Mineiro",
      "season": 2026,
      "model_id": "home_1_2026", "model_name": "Home 1",
      "category_id": "numero_costas", "category_name": "Número Costas",
      "item_label": "10", "quantity": 2
    }
  ]
}
```

Datas em UTC (`Z`). `note`, `customer.whatsapp`, `catalog_version`, `season` e os campos `*_name` são opcionais;
sem `*_name`, usa-se o respectivo `*_id`.

### Mapeamento para o Montador

| Contrato | Montador |
|---|---|
| `code` | Pedido nº |
| `customer.name` | Cliente |
| `customer.whatsapp` + `note` | Observação: `WhatsApp <número> · <nota>` (partes ausentes são omitidas) |
| `items` | Carrinho. `model_name` vira `"<model_name> · <season>"` quando há `season`. |
| primeiro item | `selected_team_id` e `selected_model_id` do payload |

O resultado é o mesmo payload que `OrderPanel.load_order_payload` já consome (`order`, `selected_team_id`,
`selected_model_id`, `items`).

### Validação (erro bloqueia a importação)

- Não é JSON válido / não é objeto.
- `schema_version` diferente de 1.
- Faltando: `code`, `customer.name`, `items` (lista não vazia), e por item `team_id`, `model_id`, `category_id`,
  `item_label` (não vazio).
- `quantity` não inteiro (booleano não vale) ou fora de 1 a 999.

Item que não existe no catálogo local **não bloqueia**: gera aviso, entra no carrinho e cai no
`arquivos_faltando.txt` na geração.

## Componentes

| # | Arquivo | Mudança | Depende de |
|---|---|---|---|
| 1 | `src/models/catalog_models.py` | `SCHEMA_VERSION = 2`; `season`/`active` na camisa; `model_display_name(model)` = `"<nome> · <ano>"` ou só `<nome>` sem ano | - |
| 2 | `src/services/catalog_service.py` | Migração v1→v2 em `load_catalog` (em memória; grava na próxima gravação); `add_model`/`update_model` aceitam `season`/`active`; ID novo inclui o ano | 1 |
| 3 | `src/services/order_import_service.py` (novo) | `parse_site_order(data, catalog) -> ImportedOrder(payload, warnings)`; `OrderImportError` com mensagem em português | 1 |
| 4 | `contracts/order.schema.json`, `contracts/order.example.json` | Contrato acima | - |
| 5 | `src/ui/config_window.py` | Campos **Ano** e **Ativa (aparece no site)** no cadastro da camisa | 2 |
| 6 | `src/ui/order_panel.py`, `src/ui/main_window.py` | Menu de camisas usa `model_display_name` (evita colisão de nome entre anos); botão **Importar Pedido** (seletor de arquivo → confirma se o carrinho tem itens → `load_order_payload` → mostra avisos); botões da barra de 130 para 116 px para caber na largura mínima 1180 | 2, 3 |

Ponto de atenção: hoje o menu de camisas é montado como `{nome: id}`; sem o ano no rótulo, duas camisas de mesmo nome
e anos diferentes se sobrescreveriam.

## Mensagens de erro (janela, sem travar o app)

| Situação | Mensagem |
|---|---|
| Não é JSON | "Arquivo inválido: não é um pedido do site." |
| Versão desconhecida | "Versão de pedido não suportada. Atualize o Montador." |
| Campo faltando | "Pedido incompleto: falta `<campo>`." |
| Quantidade inválida | "Quantidade inválida no item `<item>`." |
| Itens fora do catálogo | Importa e avisa listando os itens. |
| Carrinho com itens | "Substituir o pedido atual?" |

## Compatibilidade

Catálogo v1 e pedidos salvos atuais abrem sem alteração: camisas sem `season` mostram só o nome; IDs existentes ficam.

## Testes (escritos antes do código)

- Migração: catálogo v1 carrega como v2 sem perder dados nem mudar IDs.
- `model_display_name` com e sem ano; duas camisas de mesmo nome e anos diferentes têm rótulos distintos.
- ID novo com ano é único dentro do time.
- Importação: pedido válido; `order.example.json` válido; mapeamento de Observação (com e sem WhatsApp/nota);
  `model_name` com ano; versão desconhecida; JSON inválido; campo faltando; quantidade 0, 1000, `true`, `"2"`;
  item fora do catálogo vira aviso.
- Interface: verificação manual (não há testes de UI no projeto).

## Fora do escopo

Buscar pedido pela internet, publicar catálogo/prévias, Worker/D1, site, preço, área de impressão, nomes personalizados.

## Ordem de entrega

1. Contrato + `order_import_service` + testes.
2. Schema v2 + migração + testes.
3. Menu de camisas com ano.
4. Campos Ano/Ativa em Configurações.
5. Botão Importar Pedido.
6. Atualizar `CLAUDE.md` e `README.md`.
