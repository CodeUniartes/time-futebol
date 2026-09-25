import { generateOrderCode } from "../lib/order-code";
import type { NormalizedItem, NormalizedOrder } from "./order-validation";

const MAX_CODE_ATTEMPTS = 5;
const ITEMS_PER_STATEMENT = 100;

export interface CreateOrderInput {
  order: NormalizedOrder;
  catalogVersion: string | null;
  clock?: () => Date;
  makeCode?: () => string;
  newId?: () => string;
  /** Comandos que precisam entrar na mesma transação do pedido (ex.: a chave de idempotência). */
  extraStatements?: D1PreparedStatement[];
}

export interface CreatedOrder {
  id: string;
  code: string;
  createdAt: string;
}

const INSERT_ORDER = `INSERT INTO orders
  (id, code, status, customer_name, customer_whatsapp, note, catalog_version, created_at)
  VALUES (?1, ?2, 'open', ?3, ?4, ?5, ?6, ?7)`;

// Um comando só insere um bloco de itens: os itens vão como um JSON e o SQLite os abre com json_each.
const INSERT_ITEMS = `INSERT INTO order_items
  (id, order_id, position, team_id, team_name, season, model_id, model_name, category_id, category_name, item_label, quantity)
  SELECT lower(hex(randomblob(16))), ?1,
    json_extract(value, '$.position'), json_extract(value, '$.team_id'), json_extract(value, '$.team_name'),
    json_extract(value, '$.season'), json_extract(value, '$.model_id'), json_extract(value, '$.model_name'),
    json_extract(value, '$.category_id'), json_extract(value, '$.category_name'),
    json_extract(value, '$.item_label'), json_extract(value, '$.quantity')
  FROM json_each(?2)`;

function itemRows(items: NormalizedItem[], firstPosition: number) {
  return items.map((item, index) => ({
    position: firstPosition + index,
    team_id: item.teamId,
    team_name: item.teamName,
    season: item.season,
    model_id: item.modelId,
    model_name: item.modelName,
    category_id: item.categoryId,
    category_name: item.categoryName,
    item_label: item.itemLabel,
    quantity: item.quantity,
  }));
}

export function isOrderCodeCollision(error: unknown): boolean {
  const message = error instanceof Error ? `${error.message} ${(error.cause as Error | undefined)?.message ?? ""}` : String(error);
  return /UNIQUE constraint failed/i.test(message) && /orders\.code|idx_orders_code_unique/i.test(message);
}

/** Cria o pedido e os itens numa única transação (batch do D1). Colisão de código sorteia outro, até 5 vezes. */
export async function createOrder(db: D1Database, input: CreateOrderInput): Promise<CreatedOrder> {
  const clock = input.clock ?? (() => new Date());
  const makeCode = input.makeCode ?? generateOrderCode;
  const newId = input.newId ?? (() => crypto.randomUUID());
  const { order } = input;

  let lastError: unknown;
  for (let attempt = 0; attempt < MAX_CODE_ATTEMPTS; attempt += 1) {
    const id = newId();
    const code = makeCode();
    const createdAt = clock().toISOString();
    const statements: D1PreparedStatement[] = [
      db.prepare(INSERT_ORDER).bind(id, code, order.customerName, order.customerWhatsapp, order.note, input.catalogVersion, createdAt),
    ];
    for (let start = 0; start < order.items.length; start += ITEMS_PER_STATEMENT) {
      const chunk = order.items.slice(start, start + ITEMS_PER_STATEMENT);
      statements.push(db.prepare(INSERT_ITEMS).bind(id, JSON.stringify(itemRows(chunk, start + 1))));
    }
    statements.push(...(input.extraStatements ?? []));
    try {
      await db.batch(statements);
      return { id, code, createdAt };
    } catch (error) {
      if (!isOrderCodeCollision(error)) throw error;
      lastError = error;
    }
  }
  throw new Error("Não foi possível gerar um código de pedido único.", { cause: lastError });
}

interface OrderRow {
  id: string;
  code: string;
  status: string;
  customer_name: string;
  customer_whatsapp: string | null;
  note: string | null;
  catalog_version: string | null;
  created_at: string;
}

interface ItemRow {
  team_id: string;
  team_name: string | null;
  season: number | null;
  model_id: string;
  model_name: string | null;
  category_id: string;
  category_name: string | null;
  item_label: string;
  quantity: number;
}

const OPTIONAL_ITEM_FIELDS = ["team_name", "season", "model_name", "category_name"] as const;

/** Pedido no formato de contracts/order.schema.json: campos opcionais vazios saem do JSON (o contrato não aceita null). */
export async function findOrderContract(db: D1Database, code: string): Promise<Record<string, unknown> | null> {
  const order = await db
    .prepare("SELECT id, code, status, customer_name, customer_whatsapp, note, catalog_version, created_at FROM orders WHERE code = ? AND deleted_at IS NULL")
    .bind(code)
    .first<OrderRow>();
  if (!order) return null;

  const { results } = await db
    .prepare(
      `SELECT team_id, team_name, season, model_id, model_name, category_id, category_name, item_label, quantity
       FROM order_items WHERE order_id = ? AND deleted_at IS NULL ORDER BY position`,
    )
    .bind(order.id)
    .all<ItemRow>();

  const customer: Record<string, unknown> = { name: order.customer_name };
  if (order.customer_whatsapp) customer.whatsapp = order.customer_whatsapp;

  const contract: Record<string, unknown> = {
    schema_version: 1,
    code: order.code,
    created_at: order.created_at,
    customer,
  };
  if (order.note) contract.note = order.note;
  if (order.catalog_version) contract.catalog_version = order.catalog_version;
  contract.items = results.map((row) => {
    const item: Record<string, unknown> = {
      team_id: row.team_id,
      model_id: row.model_id,
      category_id: row.category_id,
      item_label: row.item_label,
      quantity: row.quantity,
    };
    for (const field of OPTIONAL_ITEM_FIELDS) if (row[field] !== null && row[field] !== undefined) item[field] = row[field];
    return item;
  });
  return contract;
}

export interface ImportedState {
  code: string;
  status: string;
  imported_at: string | null;
}

/** open -> imported (guarda a primeira hora). Pedido já importado ou finalizado não muda de novo. */
export async function markOrderImported(db: D1Database, code: string, now: Date = new Date()): Promise<ImportedState | null> {
  const updated = await db
    .prepare(
      `UPDATE orders SET status = 'imported', imported_at = COALESCE(imported_at, ?2)
       WHERE code = ?1 AND deleted_at IS NULL AND status IN ('open', 'imported')
       RETURNING code, status, imported_at`,
    )
    .bind(code, now.toISOString())
    .first<ImportedState>();
  if (updated) return updated;
  return db
    .prepare("SELECT code, status, imported_at FROM orders WHERE code = ? AND deleted_at IS NULL")
    .bind(code)
    .first<ImportedState>();
}
