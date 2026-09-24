import { describe, expect, it } from "vitest";
import { isSha256Hex, isSafePreviewKey, sha256Hex } from "../src/lib/keys";

describe("isSafePreviewKey", () => {
  it("aceita as chaves geradas pelo Montador", () => {
    for (const key of [
      "previews/galo/home_1_2026/numero_costas/10.webp",
      "previews/galo/home_1_2026/camisa_completa/todos_os_arquivos.webp",
      "previews/cruzeiro/azul-2026/logos/logo_a_b_2.webp",
    ]) {
      expect(isSafePreviewKey(key)).toBe(true);
    }
  });

  it("recusa outro prefixo, outra extensão e o catálogo", () => {
    for (const key of [
      "catalog/catalog.public.json",
      "uploads/DTF-7K3F2/arte.webp",
      "previews/galo/10.png",
      "previews/galo/10.webp.exe",
      "preview/galo/10.webp",
      "previews/",
      "previews/.webp",
    ]) {
      expect(isSafePreviewKey(key)).toBe(false);
    }
  });

  it("recusa tentativas de sair da pasta", () => {
    for (const key of [
      "previews/../catalog/catalog.public.json.webp",
      "previews/galo/../../x.webp",
      "previews/galo/./10.webp",
      "/previews/galo/10.webp",
      "previews//galo/10.webp",
      "previews/galo%2F..%2Fx.webp",
      "previews/galo\\..\\x.webp",
      "previews/galo/10.webp\n",
    ]) {
      expect(isSafePreviewKey(key)).toBe(false);
    }
  });

  it("recusa maiúsculas, espaços, acentos e chaves enormes", () => {
    for (const key of ["previews/Galo/10.webp", "previews/galo/1 0.webp", "previews/galo/açaí.webp", `previews/${"a/".repeat(200)}x.webp`]) {
      expect(isSafePreviewKey(key)).toBe(false);
    }
  });

  it("recusa valores que não são texto", () => {
    expect(isSafePreviewKey(undefined as unknown as string)).toBe(false);
    expect(isSafePreviewKey(null as unknown as string)).toBe(false);
  });
});

describe("sha256", () => {
  it("calcula o hash conhecido de um texto", async () => {
    expect(await sha256Hex(new TextEncoder().encode("abc"))).toBe(
      "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    );
  });

  it("valida o formato do hash", () => {
    expect(isSha256Hex("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")).toBe(true);
    for (const bad of ["", "abc", "Z".repeat(64), "BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD"]) {
      expect(isSha256Hex(bad)).toBe(false);
    }
  });
});
