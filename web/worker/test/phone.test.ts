import { describe, expect, it } from "vitest";
import { normalizeWhatsapp } from "../src/lib/phone";

describe("normalizeWhatsapp", () => {
  it.each([
    ["(31) 99999-9999", "5531999999999"],
    ["+55 31 99999-9999", "5531999999999"],
    ["5531999999999", "5531999999999"],
    ["031999999999", "5531999999999"],
    ["31 99999 9999", "5531999999999"],
    ["  (11)91234-5678 ", "5511912345678"],
    ["55 (31) 3333-4444", "553133334444"],
    ["3133334444", "553133334444"],
    ["31 8888-7777", "553188887777"],
    ["553199999999", "553199999999"],
  ])("normaliza %s", (input, expected) => {
    expect(normalizeWhatsapp(input)).toBe(expected);
  });

  it.each([
    [""],
    ["   "],
    ["abc"],
    ["12345"],
    ["999999999"],
    ["(00) 99999-9999"],
    ["(10) 99999-9999"],
    ["(31) 19999-9999"],
    ["+1 415 555 2671"],
    ["55319999999991"],
  ])("recusa %s", (input) => {
    expect(normalizeWhatsapp(input)).toBeNull();
  });

  it("ignora letras e símbolos no meio do número", () => {
    expect(normalizeWhatsapp("tel: (31) 9.9999-9999 ok")).toBe("5531999999999");
  });

  it("não aceita valor que não é texto", () => {
    expect(normalizeWhatsapp(undefined as unknown as string)).toBeNull();
    expect(normalizeWhatsapp(31999999999 as unknown as string)).toBeNull();
  });
});
