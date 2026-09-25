import { env } from "cloudflare:workers";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import example from "../../../contracts/order.example.json";
import app from "../src/index";

const KEY = "chave-de-teste-0001";
let ipCounter = 0;

function turnstileReplies(success: boolean, status = 200) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async () => new Response(JSON.stringify({ success }), { status }));
}

function post(body: unknown, headers: Record<string, string> = {}, raw?: string) {
  const payload = raw ?? JSON.stringify({ ...(body as object), turnstile_token: "token-ok" });
  return app.request(
    "/api/orders",
    {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": KEY, "CF-Connecting-IP": `203.0.113.${ipCounter}`, ...headers },
      body: payload,
    },
    env,
  );
}

async function count(table: string) {
  return (await env.DB.prepare(`SELECT COUNT(*) AS n FROM ${table}`).first<{ n: number }>())!.n;
}

beforeEach(async () => {
  ipCounter += 1;
  await env.DB.batch(["orders", "order_items", "idempotency_keys", "rate_limits", "catalog_versions"].map((table) => env.DB.prepare(`DELETE FROM ${table}`)));
  turnstileReplies(true);
});

afterEach(() => vi.restoreAllMocks());

describe("POST /api/orders", () => {
  it("cria o pedido e devolve só o código e a data", async () => {
    const response = await post(example);
    expect(response.status).toBe(201);
    const body = (await response.json()) as { code: string; created_at: string };
    expect(Object.keys(body).sort()).toEqual(["code", "created_at"]);
    expect(body.code).toMatch(/^DTF-[2-9A-HJKMNP-Z]{5}$/);
    expect(body.created_at).toMatch(/Z$/);
    expect(await count("orders")).toBe(1);
    expect(await count("order_items")).toBe(1);
  });

  it("ignora o código e a data que o cliente mandar", async () => {
    const response = await post({ ...example, code: "DTF-ZZZZZ", created_at: "2020-01-01T00:00:00Z" });
    const body = (await response.json()) as { code: string; created_at: string };
    expect(body.code).not.toBe("DTF-ZZZZZ");
    expect(body.created_at.startsWith("2020")).toBe(false);
  });

  it("guarda a versão do catálogo publicada no momento", async () => {
    await env.DB.prepare("INSERT INTO catalog_versions (catalog_version, published_at, item_count) VALUES ('v-antiga', '2026-09-01T00:00:00Z', 1), ('v-nova', '2026-09-20T00:00:00Z', 5)").run();
    await post({ ...example, catalog_version: "inventada" });
    const row = await env.DB.prepare("SELECT catalog_version FROM orders").first<{ catalog_version: string }>();
    expect(row?.catalog_version).toBe("v-nova");
  });

  it("repetir a mesma chave e o mesmo pedido devolve o mesmo código com 200", async () => {
    const first = (await (await post(example)).json()) as { code: string };
    const again = await post(example);
    expect(again.status).toBe(200);
    expect(((await again.json()) as { code: string }).code).toBe(first.code);
    expect(await count("orders")).toBe(1);
  });

  it("repetir a chave com outro pedido dá 409", async () => {
    await post(example);
    const other = structuredClone(example);
    other.items[0]!.quantity = 5;
    const response = await post(other);
    expect(response.status).toBe(409);
    expect(((await response.json()) as { error: { code: string } }).error.code).toBe("chave_idempotencia_em_uso");
  });

  it.each([[{ "Idempotency-Key": "curta" }], [{ "Idempotency-Key": "" }]])("chave de idempotência inválida %j dá 400", async (headers) => {
    const response = await post(example, headers);
    expect(response.status).toBe(400);
    expect(((await response.json()) as { error: { code: string } }).error.code).toBe("chave_idempotencia_invalida");
  });

  it("sem o cabeçalho Idempotency-Key dá 400", async () => {
    const response = await app.request("/api/orders", { method: "POST", body: JSON.stringify({ ...example, turnstile_token: "t" }) }, env);
    expect(response.status).toBe(400);
  });

  it("JSON quebrado ou que não é objeto dá 400", async () => {
    for (const raw of ["{ nao é json", "[1,2]", '"texto"', "null"]) {
      const response = await post(example, {}, raw);
      expect(response.status).toBe(400);
      expect(((await response.json()) as { error: { code: string } }).error.code).toBe("json_invalido");
    }
  });

  it("pedido inválido dá 400 com os campos em details", async () => {
    const response = await post({ ...example, items: [], customer: {} });
    expect(response.status).toBe(400);
    const body = (await response.json()) as { error: { code: string; details: { field: string }[] } };
    expect(body.error.code).toBe("pedido_invalido");
    expect(body.error.details.map((detail) => detail.field)).toEqual(expect.arrayContaining(["items", "customer.name"]));
    expect(await count("orders")).toBe(0);
  });

  it("Turnstile recusado dá 403 e não cria pedido", async () => {
    vi.restoreAllMocks();
    turnstileReplies(false);
    const response = await post(example);
    expect(response.status).toBe(403);
    expect(await count("orders")).toBe(0);
  });

  it("sem token do Turnstile dá 403", async () => {
    const response = await post(example, {}, JSON.stringify(example));
    expect(response.status).toBe(403);
    expect(await count("orders")).toBe(0);
  });

  it("Turnstile fora do ar dá 503 e não cria pedido", async () => {
    vi.restoreAllMocks();
    turnstileReplies(true, 500);
    const response = await post(example);
    expect(response.status).toBe(503);
    expect(await count("orders")).toBe(0);
  });

  it("depois de 10 pedidos por hora o mesmo IP recebe 429 com Retry-After", async () => {
    for (let index = 0; index < 10; index += 1) {
      const response = await post(example, { "Idempotency-Key": `chave-de-teste-${String(index).padStart(4, "0")}` });
      expect(response.status).toBe(201);
    }
    const blocked = await post(example, { "Idempotency-Key": "chave-de-teste-9999" });
    expect(blocked.status).toBe(429);
    expect(Number(blocked.headers.get("Retry-After"))).toBeGreaterThan(0);
    const otherIp = await post(example, { "Idempotency-Key": "chave-de-teste-8888", "CF-Connecting-IP": "198.51.100.200" });
    expect(otherIp.status).toBe(201);
  });

  it("corpo acima de 256 KB dá 413", async () => {
    const response = await post(example, {}, JSON.stringify({ ...example, note: "x".repeat(300_000) }));
    expect(response.status).toBe(413);
  });

  it("outros métodos dão 405", async () => {
    for (const method of ["GET", "PUT", "DELETE"]) {
      const response = await app.request("/api/orders", { method }, env);
      expect(response.status).toBe(405);
    }
  });

  it("a resposta de erro não repete dados do cliente", async () => {
    const response = await post({ ...example, customer: { name: "Fulano Secreto", whatsapp: "123" } });
    expect(await response.text()).not.toContain("Fulano Secreto");
  });
});
