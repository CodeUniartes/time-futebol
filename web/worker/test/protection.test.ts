import { env } from "cloudflare:workers";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { HttpError } from "../src/lib/errors";
import { clientKey, enforceRateLimit, hitRateLimit } from "../src/lib/rate-limit";
import { verifyTurnstile } from "../src/services/turnstile";

const SITEVERIFY = "https://challenges.cloudflare.com/turnstile/v0/siteverify";

function fakeFetch(body: unknown, status = 200) {
  return vi.fn(async (_url: RequestInfo | URL, _init?: RequestInit) => new Response(JSON.stringify(body), { status }));
}

describe("verifyTurnstile", () => {
  it("aceita quando a Cloudflare confirma, enviando segredo, token e IP", async () => {
    const fetchImpl = fakeFetch({ success: true });
    await expect(verifyTurnstile({ secret: "segredo", token: "tok", ip: "203.0.113.9", fetchImpl })).resolves.toBeUndefined();
    const [url, init] = fetchImpl.mock.calls[0]!;
    expect(url).toBe(SITEVERIFY);
    expect(init?.method).toBe("POST");
    const form = init?.body as URLSearchParams;
    expect(form.get("secret")).toBe("segredo");
    expect(form.get("response")).toBe("tok");
    expect(form.get("remoteip")).toBe("203.0.113.9");
  });

  it("recusa com 403 quando a verificação falha", async () => {
    const fetchImpl = fakeFetch({ success: false, "error-codes": ["invalid-input-response"] });
    await expect(verifyTurnstile({ secret: "s", token: "ruim", ip: "1.1.1.1", fetchImpl })).rejects.toMatchObject({
      status: 403,
      code: "verificacao_falhou",
    });
  });

  it("recusa sem token, sem chamar a Cloudflare", async () => {
    const fetchImpl = fakeFetch({ success: true });
    for (const token of [undefined, null, "", "   ", 42]) {
      await expect(verifyTurnstile({ secret: "s", token, ip: "1.1.1.1", fetchImpl })).rejects.toMatchObject({ status: 403 });
    }
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("recusa token gigante sem chamar a Cloudflare", async () => {
    const fetchImpl = fakeFetch({ success: true });
    await expect(verifyTurnstile({ secret: "s", token: "x".repeat(3000), ip: "1.1.1.1", fetchImpl })).rejects.toMatchObject({ status: 403 });
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("sem segredo configurado, falha fechada com 503", async () => {
    const fetchImpl = fakeFetch({ success: true });
    await expect(verifyTurnstile({ secret: "", token: "tok", ip: "1.1.1.1", fetchImpl })).rejects.toMatchObject({ status: 503 });
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("erro de rede ou resposta estranha vira 503, nunca libera", async () => {
    const broken = vi.fn(async () => {
      throw new Error("rede caiu");
    });
    await expect(verifyTurnstile({ secret: "s", token: "t", ip: "1.1.1.1", fetchImpl: broken })).rejects.toMatchObject({ status: 503, code: "verificacao_indisponivel" });
    await expect(verifyTurnstile({ secret: "s", token: "t", ip: "1.1.1.1", fetchImpl: fakeFetch({}, 500) })).rejects.toMatchObject({ status: 503 });
    await expect(verifyTurnstile({ secret: "s", token: "t", ip: "1.1.1.1", fetchImpl: fakeFetch("texto") })).rejects.toBeInstanceOf(HttpError);
  });
});

describe("limite de taxa", () => {
  beforeEach(async () => {
    await env.DB.prepare("DELETE FROM rate_limits").run();
  });

  const T0 = new Date("2026-09-25T12:00:00.000Z");
  const at = (seconds: number) => new Date(T0.getTime() + seconds * 1000);

  it("libera até o limite e bloqueia a partir da chamada seguinte", async () => {
    const results = [];
    for (let index = 0; index < 4; index += 1) results.push(await hitRateLimit(env.DB, { key: "a", limit: 3, windowSeconds: 600, now: at(index) }));
    expect(results.map((result) => result.allowed)).toEqual([true, true, true, false]);
    expect(results.map((result) => result.remaining)).toEqual([2, 1, 0, 0]);
  });

  it("informa quantos segundos faltam para a janela virar", async () => {
    await hitRateLimit(env.DB, { key: "a", limit: 1, windowSeconds: 600, now: at(0) });
    const blocked = await hitRateLimit(env.DB, { key: "a", limit: 1, windowSeconds: 600, now: at(100) });
    expect(blocked.allowed).toBe(false);
    expect(blocked.retryAfterSeconds).toBeGreaterThan(0);
    expect(blocked.retryAfterSeconds).toBeLessThanOrEqual(600);
  });

  it("nova janela zera a contagem", async () => {
    await hitRateLimit(env.DB, { key: "a", limit: 1, windowSeconds: 600, now: at(0) });
    expect((await hitRateLimit(env.DB, { key: "a", limit: 1, windowSeconds: 600, now: at(0) })).allowed).toBe(false);
    expect((await hitRateLimit(env.DB, { key: "a", limit: 1, windowSeconds: 600, now: at(601) })).allowed).toBe(true);
  });

  it("chaves diferentes não interferem", async () => {
    await hitRateLimit(env.DB, { key: "a", limit: 1, windowSeconds: 600, now: at(0) });
    expect((await hitRateLimit(env.DB, { key: "b", limit: 1, windowSeconds: 600, now: at(0) })).allowed).toBe(true);
  });

  it("chamadas simultâneas respeitam o limite", async () => {
    const results = await Promise.all(Array.from({ length: 10 }, () => hitRateLimit(env.DB, { key: "c", limit: 4, windowSeconds: 600, now: at(0) })));
    expect(results.filter((result) => result.allowed)).toHaveLength(4);
  });

  it("clientKey não guarda o IP em claro e é estável", async () => {
    const key = await clientKey("orders", "203.0.113.9");
    expect(key).toBe(await clientKey("orders", "203.0.113.9"));
    expect(key).not.toContain("203.0.113.9");
    expect(key).not.toBe(await clientKey("orders", "203.0.113.10"));
    expect(key).not.toBe(await clientKey("outra", "203.0.113.9"));
  });

  it("enforceRateLimit lança 429 com Retry-After", async () => {
    const options = { db: env.DB, scope: "orders", ip: "198.51.100.7", limit: 1, windowSeconds: 600 };
    await enforceRateLimit(options);
    try {
      await enforceRateLimit(options);
      throw new Error("não bloqueou");
    } catch (error) {
      expect(error).toBeInstanceOf(HttpError);
      const http = error as HttpError;
      expect(http.status).toBe(429);
      expect(http.code).toBe("muitas_tentativas");
      expect(Number(http.headers?.["Retry-After"])).toBeGreaterThan(0);
    }
  });
});
