import { env } from "cloudflare:workers";
import { beforeEach, describe, expect, it } from "vitest";
import example from "../../../contracts/order.example.json";
import app from "../src/index";
import { createOrder } from "../src/services/orders";
import { validateOrder } from "../src/services/order-validation";

const reader = { Authorization: `Bearer ${env.READER_TOKEN}` };
const admin = { Authorization: `Bearer ${env.ADMIN_TOKEN}` };
const get = (path: string, headers: Record<string, string> = reader) => app.request(path, { headers }, env);
const post = (path: string, headers: Record<string, string> = reader) => app.request(path, { method: "POST", headers }, env);

async function seed(overrides: { whatsapp?: string | null; note?: string | null; catalogVersion?: string | null; items?: number } = {}) {
  const base = validateOrder(structuredClone(example));
  if (!base.ok) throw new Error("exemplo inválido");
  const items = Array.from({ length: overrides.items ?? 1 }, (_, index) => ({ ...base.order.items[0]!, itemLabel: String(10 + index), quantity: index + 1 }));
  return createOrder(env.DB, {
    order: {
      ...base.order,
      customerWhatsapp: overrides.whatsapp === undefined ? base.order.customerWhatsapp : overrides.whatsapp,
      note: overrides.note === undefined ? base.order.note : overrides.note,
      items,
    },
    catalogVersion: overrides.catalogVersion === undefined ? "2026-09-20T10:00:00.000Z" : overrides.catalogVersion,
  });
}

beforeEach(async () => {
  await env.DB.batch(["orders", "order_items", "idempotency_keys"].map((table) => env.DB.prepare(`DELETE FROM ${table}`)));
});

describe("GET /api/order", () => {
  it("devolve o pedido no formato do contrato, aceito pelo mesmo validador", async () => {
    const created = await seed({ items: 3 });
    const response = await get(`/api/order?code=${created.code}`);
    expect(response.status).toBe(200);
    const body = (await response.json()) as Record<string, any>;
    expect(body).toMatchObject({
      schema_version: 1,
      code: created.code,
      created_at: created.createdAt,
      customer: { name: "Fulano", whatsapp: "5531999999999" },
      note: "Entrega sexta",
      catalog_version: "2026-09-20T10:00:00.000Z",
    });
    expect(body.items.map((item: any) => [item.item_label, item.quantity])).toEqual([["10", 1], ["11", 2], ["12", 3]]);
    expect(body.items[0]).toMatchObject({
      team_id: "atletico_mineiro",
      team_name: "Atletico Mineiro",
      season: 2026,
      model_id: "home_1_2026",
      model_name: "Home 1",
      category_id: "numero_costas",
      category_name: "Número Costas",
    });
    expect(validateOrder(body).ok).toBe(true);
  });

  it("omite os campos opcionais que estão vazios (o contrato não aceita null)", async () => {
    const created = await seed({ whatsapp: null, note: null, catalogVersion: null });
    const body = (await (await get(`/api/order?code=${created.code}`)).json()) as Record<string, any>;
    expect("note" in body).toBe(false);
    expect("catalog_version" in body).toBe(false);
    expect("whatsapp" in body.customer).toBe(false);
  });

  it("sem token ou com token errado dá 401; o de administrador não vale aqui", async () => {
    const created = await seed();
    for (const headers of [{}, { Authorization: "Bearer errado" }, admin]) {
      expect((await get(`/api/order?code=${created.code}`, headers)).status).toBe(401);
    }
  });

  it("código com formato inválido dá 400; ausente também", async () => {
    for (const path of ["/api/order?code=abc", "/api/order?code=DTF-0O1IL", "/api/order", "/api/order?code="]) {
      const response = await get(path);
      expect(response.status).toBe(400);
      expect(((await response.json()) as { error: { code: string } }).error.code).toBe("codigo_invalido");
    }
  });

  it("código que não existe dá 404", async () => {
    expect((await get("/api/order?code=DTF-ZZZZZ")).status).toBe(404);
  });

  it("pedido com exclusão lógica dá 404", async () => {
    const created = await seed();
    await env.DB.prepare("UPDATE orders SET deleted_at = '2026-09-25T00:00:00Z' WHERE id = ?").bind(created.id).run();
    expect((await get(`/api/order?code=${created.code}`)).status).toBe(404);
  });

  it("ler o pedido não muda o estado dele", async () => {
    const created = await seed();
    await get(`/api/order?code=${created.code}`);
    const row = await env.DB.prepare("SELECT status, imported_at FROM orders WHERE id = ?").bind(created.id).first();
    expect(row).toEqual({ status: "open", imported_at: null });
  });

  it("só aceita GET", async () => {
    expect((await post("/api/order?code=DTF-ZZZZZ", reader)).status).toBe(405);
  });
});

describe("POST /api/order/imported", () => {
  it("marca o pedido como importado e guarda a hora", async () => {
    const created = await seed();
    const response = await post(`/api/order/imported?code=${created.code}`);
    expect(response.status).toBe(200);
    const body = (await response.json()) as { code: string; status: string; imported_at: string };
    expect(body).toMatchObject({ code: created.code, status: "imported" });
    expect(body.imported_at).toMatch(/Z$/);
  });

  it("é idempotente: importar de novo mantém a primeira hora", async () => {
    const created = await seed();
    const first = (await (await post(`/api/order/imported?code=${created.code}`)).json()) as { imported_at: string };
    const second = (await (await post(`/api/order/imported?code=${created.code}`)).json()) as { imported_at: string; status: string };
    expect(second.imported_at).toBe(first.imported_at);
    expect(second.status).toBe("imported");
  });

  it("não volta um pedido finalizado para importado", async () => {
    const created = await seed();
    await env.DB.prepare("UPDATE orders SET status = 'finished', finished_at = '2026-09-25T00:00:00Z' WHERE id = ?").bind(created.id).run();
    const body = (await (await post(`/api/order/imported?code=${created.code}`)).json()) as { status: string };
    expect(body.status).toBe("finished");
  });

  it("exige o token de leitura, valida o código e devolve 404 se não existir", async () => {
    const created = await seed();
    expect((await post(`/api/order/imported?code=${created.code}`, {})).status).toBe(401);
    expect((await post(`/api/order/imported?code=${created.code}`, admin)).status).toBe(401);
    expect((await post("/api/order/imported?code=xx")).status).toBe(400);
    expect((await post("/api/order/imported?code=DTF-ZZZZZ")).status).toBe(404);
  });

  it("só aceita POST", async () => {
    expect((await get("/api/order/imported?code=DTF-ZZZZZ")).status).toBe(405);
  });
});
