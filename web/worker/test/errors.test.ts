import { Hono } from "hono";
import { describe, expect, it, vi } from "vitest";
import { HttpError, limitBody, useErrorHandling } from "../src/lib/errors";

function buildApp() {
  const app = new Hono();
  useErrorHandling(app);
  app.get("/http-error", () => {
    throw new HttpError(422, "dados_invalidos", "Pedido inválido.", [{ field: "items", message: "obrigatório" }]);
  });
  app.get("/crash", () => {
    throw new Error("SELECT * FROM orders: senha=abc123");
  });
  app.post("/echo", limitBody(20), async (context) => context.json({ size: (await context.req.text()).length }));
  return app;
}

describe("formato de erro", () => {
  it("HttpError vira o corpo da spec", async () => {
    const response = await buildApp().request("/http-error");
    expect(response.status).toBe(422);
    expect(response.headers.get("content-type")).toContain("application/json");
    expect(await response.json()).toEqual({
      error: {
        code: "dados_invalidos",
        message: "Pedido inválido.",
        status: 422,
        details: [{ field: "items", message: "obrigatório" }],
      },
    });
  });

  it("erro inesperado vira 500 genérico, sem vazar texto interno", async () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    const response = await buildApp().request("/crash");
    const text = await response.text();
    expect(response.status).toBe(500);
    expect(JSON.parse(text).error).toMatchObject({ code: "erro_interno", status: 500, message: "Erro interno. Tente novamente." });
    expect(text).not.toContain("SELECT");
    expect(text).not.toContain("abc123");
    expect(JSON.stringify(spy.mock.calls)).not.toContain("abc123");
    spy.mockRestore();
  });

  it("rota inexistente é 404 no mesmo formato", async () => {
    const response = await buildApp().request("/nao-existe");
    expect(response.status).toBe(404);
    expect((await response.json()) as object).toMatchObject({ error: { code: "nao_encontrado", status: 404 } });
  });

  it("erro sem details omite o campo", async () => {
    const app = new Hono();
    useErrorHandling(app);
    app.get("/x", () => {
      throw new HttpError(401, "nao_autorizado", "Não autorizado.");
    });
    const body = (await (await app.request("/x")).json()) as { error: Record<string, unknown> };
    expect("details" in body.error).toBe(false);
  });
});

describe("limite de corpo", () => {
  it("aceita corpo dentro do limite", async () => {
    const response = await buildApp().request("/echo", { method: "POST", body: "12345" });
    expect(response.status).toBe(200);
  });

  it("recusa com 413 quando o Content-Length passa do limite", async () => {
    const response = await buildApp().request("/echo", { method: "POST", body: "x".repeat(50) });
    expect(response.status).toBe(413);
    expect((await response.json()) as object).toMatchObject({ error: { code: "corpo_grande_demais", status: 413 } });
  });

  it("recusa corpo em fluxo (sem Content-Length) que passa do limite", async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode("x".repeat(15)));
        controller.enqueue(new TextEncoder().encode("y".repeat(15)));
        controller.close();
      },
    });
    const response = await buildApp().request("/echo", {
      method: "POST",
      body: stream,
      // @ts-expect-error duplex é necessário para corpo em fluxo
      duplex: "half",
    });
    expect(response.status).toBe(413);
  });
});
