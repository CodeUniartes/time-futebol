import { Hono } from "hono";
import { describe, expect, it } from "vitest";
import { bearerToken, requireToken, tokensMatch } from "../src/lib/auth";
import { useErrorHandling } from "../src/lib/errors";

type TestEnv = { ADMIN_TOKEN?: string; READER_TOKEN?: string };
const ENV: TestEnv = { ADMIN_TOKEN: "admin-secret-1234567890", READER_TOKEN: "reader-secret-1234567890" };

function buildApp() {
  const app = new Hono<{ Bindings: TestEnv }>();
  useErrorHandling(app);
  app.get("/admin", requireToken("admin"), (context) => context.json({ ok: "admin" }));
  app.get("/reader", requireToken("reader"), (context) => context.json({ ok: "reader" }));
  return app;
}

const withToken = (token: string) => ({ headers: { Authorization: `Bearer ${token}` } });

describe("bearerToken", () => {
  it("extrai o token do cabeçalho", () => {
    expect(bearerToken(new Request("https://x.test", withToken("abc")))).toBe("abc");
  });

  it("ignora o prefixo em qualquer caixa e recusa formatos errados", () => {
    expect(bearerToken(new Request("https://x.test", { headers: { Authorization: "bearer abc" } }))).toBe("abc");
    expect(bearerToken(new Request("https://x.test", { headers: { Authorization: "Basic abc" } }))).toBeNull();
    expect(bearerToken(new Request("https://x.test", { headers: { Authorization: "Bearer " } }))).toBeNull();
    expect(bearerToken(new Request("https://x.test"))).toBeNull();
  });
});

describe("tokensMatch", () => {
  it("compara valor igual e diferente, inclusive de tamanhos distintos", async () => {
    expect(await tokensMatch("igual", "igual")).toBe(true);
    expect(await tokensMatch("igual", "outro")).toBe(false);
    expect(await tokensMatch("curto", "muito mais comprido que o outro")).toBe(false);
    expect(await tokensMatch("", "")).toBe(false);
  });
});

describe("requireToken", () => {
  it("aceita o token certo em cada rota", async () => {
    const app = buildApp();
    expect((await app.request("/admin", withToken(ENV.ADMIN_TOKEN!), ENV)).status).toBe(200);
    expect((await app.request("/reader", withToken(ENV.READER_TOKEN!), ENV)).status).toBe(200);
  });

  it("recusa sem token, com token errado e com o token da outra rota", async () => {
    const app = buildApp();
    for (const init of [{}, withToken("errado"), withToken(ENV.READER_TOKEN!)]) {
      const response = await app.request("/admin", init, ENV);
      expect(response.status).toBe(401);
      expect(response.headers.get("www-authenticate")).toBe("Bearer");
      expect((await response.json()) as object).toMatchObject({ error: { code: "nao_autorizado", status: 401 } });
    }
    expect((await app.request("/reader", withToken(ENV.ADMIN_TOKEN!), ENV)).status).toBe(401);
  });

  it("a mensagem não revela qual token era esperado", async () => {
    const response = await buildApp().request("/admin", withToken("errado"), ENV);
    const text = await response.text();
    expect(text).not.toContain(ENV.ADMIN_TOKEN!);
    expect(text.toLowerCase()).not.toContain("reader");
  });

  it("sem segredo configurado, recusa tudo (nunca libera)", async () => {
    const app = buildApp();
    expect((await app.request("/admin", withToken("qualquer"), {})).status).toBe(401);
    expect((await app.request("/admin", withToken(""), { ADMIN_TOKEN: "" })).status).toBe(401);
    expect((await app.request("/admin", {}, { ADMIN_TOKEN: "" })).status).toBe(401);
  });
});
