# Contratos

Formatos JSON compartilhados entre o Montador (Python), o Worker (API) e o site. Cada arquivo `.schema.json` é o
contrato; o `.example.json` ao lado é um exemplo válido, e os testes (`tests/test_contracts.py`) garantem que os dois
andam juntos.

| Contrato | Quem gera | Quem lê |
|---|---|---|
| `order.schema.json` | Site (via API) | Montador (`order_import_service`) |
| `catalog.public.schema.json` (rascunho) | Montador (publicar catálogo) | Site |

## Regras de versionamento

- Todo contrato tem `schema_version` (inteiro).
- **Campo novo opcional** mantém a mesma `schema_version`.
- **Qualquer mudança que quebre leitores antigos** (campo obrigatório novo, campo renomeado ou removido, mudança de tipo
  ou de significado) cria uma versão nova.
- **Quem lê ignora campos desconhecidos.** É isso que permite ao site evoluir (por exemplo, `custom` num item do pedido)
  sem quebrar um Montador antigo.
- Datas em UTC, no formato ISO 8601 com `Z`.

## Campos opcionais já reservados

- `order.layout`: painel de impressão calculado no site (páginas e posições das artes). Só informativo; a produção
  recalcula. Ver `docs/superpowers/specs/2026-09-24-painel-previa-impressao-design.md`.
- `catalog.public` `items[].width_cm` e `height_cm`: tamanho real da área com tinta, usado pelo painel.
