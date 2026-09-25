import { env } from "cloudflare:workers";
import { beforeEach, describe, expect, it } from "vitest";
import example from "../../../contracts/order.example.json";
import { HttpError } from "../src/lib/errors";
import { createOrderOnce, hashOrder, parseIdempotencyKey } from "../src/services/idempotency";
import { validateOrder, type NormalizedOrder } from "../src/services/order-validation";

function normalized(mutate?: (body: Record<string, any>) => void): NormalizedOrder {
  const body = structuredClone(example) as Record<string, any>;
  mutate?.(body);
  const result = validateOrder(body);
  if (!result.ok) throw new Error("pedido de teste inválido");
  return result.order;
}

const KEY = "chave-de-teste-0001";

async function counts() {
  const orders = await env.DB.prepare("SELECT COUNT(*) AS n FROM orders").first<{ n: number }>();
  const keys = await env.DB.prepare("SELECT COUNT(*) AS n FROM idempotency_keys").first<{ n: number }>();
  return { orders: orders!.n, keys: keys!.n };
}

beforeEach(async () => {
  await env.DB.batch(["orders", "order_items", "idempotency_keys"].map((table) => env.DB.prepare(`DELETE FROM ${table}`)));
});

describe("parseIdempotencyKey", () => {
  it("aceita de 16 a 64 caracteres seguros", () => {
    expect(parseIdempotencyKey("a".repeat(16))).toBe("a".repeat(16));
    expect(parseIdempotencyKey("A1_-".repeat(16))).toHaveLength(64);
  });

  it("recusa ausente, curta, longa ou com caracteres estranhos", () => {
    for (const bad of [null, undefined, "", "curta", "a".repeat(65), "com espaço 1234567890", "acentuação-123456789", "a".repeat(15) + "/"]) {
      expect(() => parseIdempotencyKey(bad as string)).toThrowError(HttpError);
    }
    try {
      parseIdempotencyKey(null);
    } catch (error) {
      expect((error as HttpError).status).toBe(400);
      expect((error as HttpError).code).toBe("chave_idempotencia_invalida");
    }
  });
});

describe("hashOrder", () => {
  it("é estável e muda quando o pedido muda", async () => {
    expect(await hashOrder(normalized())).toBe(await hashOrder(normalized()));
    expect(await hashOrder(normalized())).toMatch(/^[0-9a-f]{64}$/);
    expect(await hashOrder(normalized())).not.toBe(await hashOrder(normalized((body) => (body.items[0].quantity = 3))));
  });

  it("não muda com campos que o servidor ignora", async () => {
    const other = normalized((body) => {
      body.turnstile_token = "outro";
      body.code = "DTF-XXXXX";
      body.created_at = "2020-01-01T00:00:00Z";
    });
    expect(await hashOrder(other)).toBe(await hashOrder(normalized()));
  });
});

describe("createOrderOnce", () => {
  it("primeira chamada cria o pedido", async () => {
    const created = await createOrderOnce(env.DB, { key: KEY, order: normalized(), catalogVersion: null });
    expect(created.replayed).toBe(false);
    expect(await counts()).toEqual({ orders: 1, keys: 1 });
  });

  it("mesma chave e mesmo pedido devolvem o mesmo código, sem criar outro", async () => {
    const first = await createOrderOnce(env.DB, { key: KEY, order: normalized(), catalogVersion: null });
    const second = await createOrderOnce(env.DB, { key: KEY, order: normalized(), catalogVersion: null });
    expect(second).toMatchObject({ id: first.id, code: first.code, createdAt: first.createdAt, replayed: true });
    expect(await counts()).toEqual({ orders: 1, keys: 1 });
  });

  it("mesma chave com outro pedido dá 409", async () => {
    await createOrderOnce(env.DB, { key: KEY, order: normalized(), catalogVersion: null });
    const changed = normalized((body) => (body.items[0].quantity = 9));
    await expect(createOrderOnce(env.DB, { key: KEY, order: changed, catalogVersion: null })).rejects.toMatchObject({
      status: 409,
      code: "chave_idempotencia_em_uso",
    });
    expect(await counts()).toEqual({ orders: 1, keys: 1 });
  });

  it("chaves diferentes criam pedidos diferentes", async () => {
    const a = await createOrderOnce(env.DB, { key: "chave-de-teste-000A", order: normalized(), catalogVersion: null });
    const b = await createOrderOnce(env.DB, { key: "chave-de-teste-000B", order: normalized(), catalogVersion: null });
    expect(a.code).not.toBe(b.code);
    expect(await counts()).toEqual({ orders: 2, keys: 2 });
  });

  it("chamadas simultâneas com a mesma chave criam um único pedido", async () => {
    const results = await Promise.all(Array.from({ length: 6 }, () => createOrderOnce(env.DB, { key: KEY, order: normalized(), catalogVersion: null })));
    expect(new Set(results.map((result) => result.code)).size).toBe(1);
    expect(results.filter((result) => !result.replayed)).toHaveLength(1);
    expect(await counts()).toEqual({ orders: 1, keys: 1 });
    const items = await env.DB.prepare("SELECT COUNT(*) AS n FROM order_items").first<{ n: number }>();
    expect(items!.n).toBe(1);
  });

  it("simultâneas com a mesma chave e pedidos diferentes: um vence e os outros dão 409", async () => {
    const outcomes = await Promise.allSettled(
      [1, 2, 3].map((quantity) =>
        createOrderOnce(env.DB, { key: KEY, order: normalized((body) => (body.items[0].quantity = quantity)), catalogVersion: null }),
      ),
    );
    expect(outcomes.filter((outcome) => outcome.status === "fulfilled")).toHaveLength(1);
    for (const outcome of outcomes) {
      if (outcome.status === "rejected") expect(outcome.reason).toMatchObject({ status: 409 });
    }
    expect(await counts()).toEqual({ orders: 1, keys: 1 });
  });
});
