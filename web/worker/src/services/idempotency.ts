import { HttpError } from "../lib/errors";
import { sha256Hex } from "../lib/keys";
import type { NormalizedOrder } from "./order-validation";
import { createOrder, type CreateOrderInput, type CreatedOrder } from "./orders";

const KEY_PATTERN = /^[A-Za-z0-9_-]{16,64}$/;

export function parseIdempotencyKey(value: string | null | undefined): string {
  if (typeof value !== "string" || !KEY_PATTERN.test(value)) {
    throw new HttpError(400, "chave_idempotencia_invalida", "Informe o cabeçalho Idempotency-Key com 16 a 64 letras, números, _ ou -.");
  }
  return value;
}

/** Hash do pedido já normalizado: campos que o servidor ignora (token, código, data) não entram. */
export async function hashOrder(order: NormalizedOrder): Promise<string> {
  return sha256Hex(new TextEncoder().encode(JSON.stringify(order)));
}

export interface CreateOnceInput extends Omit<CreateOrderInput, "extraStatements"> {
  key: string;
}

export type CreatedOnce = CreatedOrder & { replayed: boolean };

interface StoredKey {
  request_hash: string;
  order_id: string;
}

async function replay(db: D1Database, key: string, requestHash: string): Promise<CreatedOnce | null> {
  const stored = await db.prepare("SELECT request_hash, order_id FROM idempotency_keys WHERE key = ?").bind(key).first<StoredKey>();
  if (!stored) return null;
  if (stored.request_hash !== requestHash) {
    throw new HttpError(409, "chave_idempotencia_em_uso", "Essa Idempotency-Key já foi usada com outro pedido.");
  }
  const order = await db.prepare("SELECT id, code, created_at FROM orders WHERE id = ?").bind(stored.order_id).first<{ id: string; code: string; created_at: string }>();
  if (!order) throw new HttpError(409, "chave_idempotencia_em_uso", "Essa Idempotency-Key já foi usada.");
  return { id: order.id, code: order.code, createdAt: order.created_at, replayed: true };
}

function isKeyCollision(error: unknown): boolean {
  const message = error instanceof Error ? `${error.message} ${(error.cause as Error | undefined)?.message ?? ""}` : String(error);
  return /UNIQUE constraint failed/i.test(message) && /idempotency_keys/i.test(message);
}

/**
 * Cria o pedido uma única vez por chave. A chave entra na mesma transação do pedido: se duas chamadas iguais chegarem
 * juntas, a segunda desfaz tudo (nenhum pedido duplicado) e então devolve o pedido da primeira.
 */
export async function createOrderOnce(db: D1Database, input: CreateOnceInput): Promise<CreatedOnce> {
  const requestHash = await hashOrder(input.order);
  const existing = await replay(db, input.key, requestHash);
  if (existing) return existing;

  const clock = input.clock ?? (() => new Date());
  const newId = input.newId ?? (() => crypto.randomUUID());
  const orderId = newId();
  const keyStatement = db
    .prepare("INSERT INTO idempotency_keys (key, request_hash, order_id, created_at) VALUES (?, ?, ?, ?)")
    .bind(input.key, requestHash, orderId, clock().toISOString());

  try {
    const created = await createOrder(db, { ...input, clock, newId: () => orderId, extraStatements: [keyStatement] });
    return { ...created, replayed: false };
  } catch (error) {
    if (!isKeyCollision(error)) throw error;
    const winner = await replay(db, input.key, requestHash);
    if (winner) return winner;
    throw error;
  }
}
