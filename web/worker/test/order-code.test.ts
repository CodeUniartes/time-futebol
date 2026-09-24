import { describe, expect, it } from "vitest";
import { ORDER_CODE_ALPHABET, generateOrderCode, isValidOrderCode } from "../src/lib/order-code";

const fromBytes = (bytes: number[]) => {
  let position = 0;
  return (count: number) => {
    const out = new Uint8Array(count);
    for (let index = 0; index < count; index += 1) out[index] = bytes[position++ % bytes.length]!;
    return out;
  };
};

describe("alfabeto", () => {
  it("tem 31 símbolos, sem 0, O, 1, I e L", () => {
    expect(ORDER_CODE_ALPHABET).toHaveLength(31);
    expect(new Set(ORDER_CODE_ALPHABET).size).toBe(31);
    for (const banned of ["0", "O", "1", "I", "L"]) expect(ORDER_CODE_ALPHABET).not.toContain(banned);
  });
});

describe("generateOrderCode", () => {
  it("segue o formato DTF-XXXXX", () => {
    for (let index = 0; index < 200; index += 1) expect(generateOrderCode()).toMatch(/^DTF-[2-9A-HJKMNP-Z]{5}$/);
  });

  it("mapeia bytes em símbolos na ordem do alfabeto", () => {
    expect(generateOrderCode(fromBytes([0, 1, 2, 3, 4]))).toBe("DTF-23456");
  });

  it("rejeita bytes que causariam viés (>= 248) e sorteia de novo", () => {
    const code = generateOrderCode(fromBytes([255, 250, 248, 0, 1, 2, 3, 4]));
    expect(code).toBe("DTF-23456");
  });

  it("dá a volta no alfabeto com bytes abaixo de 248", () => {
    expect(generateOrderCode(fromBytes([31, 32, 62, 247, 30]))).toBe(`DTF-${ORDER_CODE_ALPHABET[0]}${ORDER_CODE_ALPHABET[1]}${ORDER_CODE_ALPHABET[0]}${ORDER_CODE_ALPHABET[30]}${ORDER_CODE_ALPHABET[30]}`);
  });

  it("distribui os símbolos de forma parecida (sem viés grosseiro)", () => {
    const counts = new Map<string, number>();
    for (let index = 0; index < 6000; index += 1) {
      for (const symbol of generateOrderCode().slice(4)) counts.set(symbol, (counts.get(symbol) ?? 0) + 1);
    }
    const expected = (6000 * 5) / 31;
    expect(counts.size).toBe(31);
    for (const count of counts.values()) expect(Math.abs(count - expected) / expected).toBeLessThan(0.2);
  });

  it("gera códigos diferentes", () => {
    expect(new Set(Array.from({ length: 500 }, () => generateOrderCode())).size).toBeGreaterThan(495);
  });
});

describe("isValidOrderCode", () => {
  it("aceita códigos válidos e recusa o resto", () => {
    expect(isValidOrderCode("DTF-7K3F2")).toBe(true);
    for (const bad of ["DTF-7K3F", "DTF-7K3F22", "dtf-7k3f2", "DTF-0K3F2", "DTF-7K3FI", "XYZ-7K3F2", "", "DTF-7K3F2 "]) {
      expect(isValidOrderCode(bad)).toBe(false);
    }
  });
});
