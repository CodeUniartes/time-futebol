import { env } from "cloudflare:workers";
import { describe, expect, it } from "vitest";

async function columnsOf(table: string): Promise<string[]> {
  const { results } = await env.DB.prepare(`PRAGMA table_info(${table})`).all<{ name: string }>();
  return results.map((row) => row.name);
}

async function indexesOf(table: string): Promise<string[]> {
  const { results } = await env.DB.prepare(`PRAGMA index_list(${table})`).all<{ name: string }>();
  return results.map((row) => row.name);
}

describe("migração 0001", () => {
  it("cria as tabelas", async () => {
    const { results } = await env.DB.prepare(
      "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' AND name != 'd1_migrations'",
    ).all<{ name: string }>();
    expect(results.map((row) => row.name).sort()).toEqual([
      "catalog_versions",
      "idempotency_keys",
      "order_items",
      "orders",
      "preview_files",
      "rate_limits",
    ]);
  });

  it("orders tem as colunas da spec, com exclusão lógica", async () => {
    expect(await columnsOf("orders")).toEqual(
      expect.arrayContaining([
        "id", "code", "status", "customer_name", "customer_whatsapp", "customer_id", "note",
        "catalog_version", "created_at", "imported_at", "finished_at", "deleted_at",
      ]),
    );
  });

  it("order_items guarda posição e exclusão lógica", async () => {
    expect(await columnsOf("order_items")).toEqual(
      expect.arrayContaining(["id", "order_id", "position", "item_label", "quantity", "deleted_at"]),
    );
  });

  it("código do pedido é único entre os não excluídos", async () => {
    const insert = (id: string, deletedAt: string | null) =>
      env.DB.prepare(
        "INSERT INTO orders (id, code, customer_name, created_at, deleted_at) VALUES (?, 'DTF-AAAAA', 'Fulano', '2026-09-24T12:00:00Z', ?)",
      )
        .bind(id, deletedAt)
        .run();

    await insert("1", null);
    await expect(insert("2", null)).rejects.toThrow();
    await expect(insert("3", "2026-09-25T00:00:00Z")).resolves.toBeTruthy();
  });

  it("status começa como open", async () => {
    await env.DB.prepare(
      "INSERT INTO orders (id, code, customer_name, created_at) VALUES ('s1', 'DTF-BBBBB', 'Fulano', '2026-09-24T12:00:00Z')",
    ).run();
    const row = await env.DB.prepare("SELECT status FROM orders WHERE id = 's1'").first<{ status: string }>();
    expect(row?.status).toBe("open");
  });

  it("tem os índices de consulta", async () => {
    expect(await indexesOf("orders")).toEqual(expect.arrayContaining(["idx_orders_code_unique", "idx_orders_status"]));
    expect(await indexesOf("order_items")).toContain("idx_order_items_order_id");
  });

  it("não usa chaves estrangeiras", async () => {
    for (const table of ["orders", "order_items", "idempotency_keys", "catalog_versions", "preview_files"]) {
      const { results } = await env.DB.prepare(`PRAGMA foreign_key_list(${table})`).all();
      expect(results).toEqual([]);
    }
  });

  it("chave de idempotência é única", async () => {
    const insert = () =>
      env.DB.prepare(
        "INSERT INTO idempotency_keys (key, request_hash, order_id, created_at) VALUES ('k1', 'h', 'o', '2026-09-24T12:00:00Z')",
      ).run();
    await insert();
    await expect(insert()).rejects.toThrow();
  });
});
