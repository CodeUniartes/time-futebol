import { SELF } from "cloudflare:test";
import { describe, expect, it } from "vitest";

describe("GET /api/health", () => {
  it("responde ok em JSON", async () => {
    const response = await SELF.fetch("https://site.test/api/health");
    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("application/json");
    expect(await response.json()).toEqual({ ok: true });
  });

  it("não aceita outros métodos", async () => {
    const response = await SELF.fetch("https://site.test/api/health", { method: "POST" });
    expect(response.status).toBe(405);
  });
});
