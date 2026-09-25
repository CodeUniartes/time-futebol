import { env } from "cloudflare:workers";
import { beforeEach, describe, expect, it } from "vitest";
import example from "../../../contracts/order.example.json";
import { createOrder } from "../src/services/orders";
import { validateOrder, type NormalizedOrder } from "../src/services/order-validation";

function normalized(overrides: Partial<NormalizedOrder> = {}): NormalizedOrder {
  const result = validateOrder(structuredClone(example));
  if (!result.ok) throw new Error("exemplo inválido");
  return { ...result.order, ...overrides };
}

const fixedNow = () => new Date("2026-09-25T13:45:10.123Z");

async function clean() {
  await env.DB.batch(
    ["orders", "order_items", "idempotency_keys"].map((table) => env.DB.prepare(`DELETE FROM ${table}`)),
  );
}

describe("createOrder", () => {
  beforeEach(clean);

  it("grava o pedido e os itens na mesma operação", async () => {
    const order = normalized({
      items: [
        ...normalized().items,
        { ...normalized().items[0]!, itemLabel: "7", quantity: 3, season: null, teamName: null },
      ],
    });
    const created = await createOrder(env.DB, { order, catalogVersion: "2026-09-20T10:00:00.000Z", clock: fixedNow });

    expect(created.code).toMatch(/^DTF-[2-9A-HJKMNP-Z]{5}$/);
    expect(created.createdAt).toBe("2026-09-25T13:45:10.123Z");

    const row = await env.DB.prepare("SELECT * FROM orders WHERE id = ?").bind(created.id).first<Record<string, unknown>>();
    expect(row).toMatchObject({
      code: created.code,
      status: "open",
      customer_name: "Fulano",
      customer_whatsapp: "5531999999999",
      note: "Entrega sexta",
      catalog_version: "2026-09-20T10:00:00.000Z",
      created_at: "2026-09-25T13:45:10.123Z",
      imported_at: null,
      finished_at: null,
      deleted_at: null,
    });

    const { results } = await env.DB.prepare("SELECT * FROM order_items WHERE order_id = ? ORDER BY position").bind(created.id).all<Record<string, unknown>>();
    expect(results).toHaveLength(2);
    expect(results[0]).toMatchObject({ position: 1, item_label: "10", quantity: 2, season: 2026, team_name: "Atletico Mineiro", model_id: "home_1_2026" });
    expect(results[1]).toMatchObject({ position: 2, item_label: "7", quantity: 3, season: null, team_name: null });
    expect(new Set(results.map((item) => item.id)).size).toBe(2);
  });

  it("guarda null quando não há WhatsApp, observação ou versão do catálogo", async () => {
    const created = await createOrder(env.DB, {
      order: normalized({ customerWhatsapp: null, note: null }),
      catalogVersion: null,
    });
    const row = await env.DB.prepare("SELECT customer_whatsapp, note, catalog_version FROM orders WHERE id = ?").bind(created.id).first();
    expect(row).toEqual({ customer_whatsapp: null, note: null, catalog_version: null });
  });

  it("grava pedidos com muitos itens (em blocos)", async () => {
    const base = normalized().items[0]!;
    const items = Array.from({ length: 250 }, (_, index) => ({ ...base, itemLabel: `item-${index}`, quantity: (index % 9) + 1 }));
    const created = await createOrder(env.DB, { order: normalized({ items }), catalogVersion: null });
    const count = await env.DB.prepare("SELECT COUNT(*) AS n, MIN(position) AS first, MAX(position) AS last FROM order_items WHERE order_id = ?").bind(created.id).first();
    expect(count).toEqual({ n: 250, first: 1, last: 250 });
  });

  it("texto com aspas, barras e acentos é gravado sem alteração", async () => {
    const base = normalized().items[0]!;
    const label = 'Ç "a" \\ b\nc';
    const created = await createOrder(env.DB, { order: normalized({ items: [{ ...base, itemLabel: label }] }), catalogVersion: null });
    const row = await env.DB.prepare("SELECT item_label FROM order_items WHERE order_id = ?").bind(created.id).first<{ item_label: string }>();
    expect(row?.item_label).toBe(label);
  });

  it("tenta outro código quando o sorteado já existe", async () => {
    const sequence = ["DTF-AAAAA", "DTF-AAAAA", "DTF-BBBBB"];
    const makeCode = () => sequence.shift()!;
    const first = await createOrder(env.DB, { order: normalized(), catalogVersion: null, makeCode });
    const second = await createOrder(env.DB, { order: normalized(), catalogVersion: null, makeCode });
    expect(first.code).toBe("DTF-AAAAA");
    expect(second.code).toBe("DTF-BBBBB");
    const { results } = await env.DB.prepare("SELECT COUNT(*) AS n FROM orders").all();
    expect(results[0]).toEqual({ n: 2 });
  });

  it("desiste depois de 5 colisões seguidas sem deixar pedido pela metade", async () => {
    await createOrder(env.DB, { order: normalized(), catalogVersion: null, makeCode: () => "DTF-AAAAA" });
    await expect(
      createOrder(env.DB, { order: normalized(), catalogVersion: null, makeCode: () => "DTF-AAAAA" }),
    ).rejects.toThrow();
    const orders = await env.DB.prepare("SELECT COUNT(*) AS n FROM orders").first();
    const items = await env.DB.prepare("SELECT COUNT(*) AS n FROM order_items").first();
    expect(orders).toEqual({ n: 1 });
    expect(items).toEqual({ n: 1 });
  });

  it("um erro em qualquer comando desfaz tudo (transação)", async () => {
    const failing = env.DB.prepare(
      "INSERT INTO idempotency_keys (key, request_hash, order_id, created_at) VALUES ('dup', 'h', 'x', '2026-09-25T00:00:00Z')",
    );
    await failing.run();
    await expect(
      createOrder(env.DB, { order: normalized(), catalogVersion: null, extraStatements: [failing] }),
    ).rejects.toThrow();
    const orders = await env.DB.prepare("SELECT COUNT(*) AS n FROM orders").first();
    expect(orders).toEqual({ n: 0 });
  });

  it("dois pedidos ao mesmo tempo recebem códigos diferentes", async () => {
    const results = await Promise.all(Array.from({ length: 8 }, () => createOrder(env.DB, { order: normalized(), catalogVersion: null })));
    expect(new Set(results.map((created) => created.code)).size).toBe(8);
  });
});
