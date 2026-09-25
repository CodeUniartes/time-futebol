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
