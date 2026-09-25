import { describe, expect, it } from "vitest";
import example from "../../../contracts/order.example.json";
import { HttpError } from "../src/lib/errors";
import { MAX_ITEMS, parseOrderRequest, validateOrder } from "../src/services/order-validation";

const clone = () => structuredClone(example) as Record<string, any>;

function detailsOf(body: unknown) {
  const result = validateOrder(body);
  if (result.ok) throw new Error("era para ser inválido");
  return result.details;
}

describe("pedido válido", () => {
  it("aceita o exemplo do contrato e devolve os dados normalizados", () => {
    const result = validateOrder(clone());
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.order.customerName).toBe("Fulano");
    expect(result.order.customerWhatsapp).toBe("5531999999999");
    expect(result.order.note).toBe("Entrega sexta");
    expect(result.order.items).toEqual([
      {
        teamId: "atletico_mineiro",
        teamName: "Atletico Mineiro",
        season: 2026,
        modelId: "home_1_2026",
        modelName: "Home 1",
        categoryId: "numero_costas",
        categoryName: "Número Costas",
        itemLabel: "10",
        quantity: 2,
      },
    ]);
  });

  it("ignora o que é do servidor (code, created_at, catalog_version) e campos desconhecidos", () => {
    const body = clone();
    body.turnstile_token = "abc";
    body.foo = "bar";
    body.items[0].custom = { name: "X" };
    const result = validateOrder(body);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(JSON.stringify(result.order)).not.toContain("DTF-7K3F");
    expect(JSON.stringify(result.order)).not.toContain("2026-09-23T14:05:00Z");
    expect(Object.keys(result.order.items[0]!)).not.toContain("custom");
    expect(Object.keys(result.order)).not.toContain("foo");
  });

  it("campos opcionais ausentes viram null", () => {
    const body = clone();
    delete body.note;
    delete body.customer.whatsapp;
    delete body.items[0].team_name;
    delete body.items[0].season;
    const result = validateOrder(body);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.order.note).toBeNull();
    expect(result.order.customerWhatsapp).toBeNull();
    expect(result.order.items[0]!.teamName).toBeNull();
    expect(result.order.items[0]!.season).toBeNull();
  });

  it("o espaço em volta dos textos é removido", () => {
    const body = clone();
    body.customer.name = "  Fulano  ";
    body.items[0].item_label = " 10 ";
    const result = validateOrder(body);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.order.customerName).toBe("Fulano");
    expect(result.order.items[0]!.itemLabel).toBe("10");
  });

  it("aceita o WhatsApp em vários formatos e guarda normalizado", () => {
    for (const raw of ["(31) 99999-9999", "+55 31 99999-9999", "31999999999"]) {
      const body = clone();
      body.customer.whatsapp = raw;
      const result = validateOrder(body);
      expect(result.ok && result.order.customerWhatsapp).toBe("5531999999999");
    }
  });
});

describe("pedido inválido (mensagens em português)", () => {
  it("não é um objeto", () => {
    for (const body of [null, "texto", 3, [], undefined]) {
      expect(detailsOf(body)[0]).toMatchObject({ message: expect.stringContaining("objeto") });
    }
  });

  it("campos obrigatórios ausentes, com o caminho de cada um", () => {
    const body = clone();
    delete body.customer.name;
    delete body.items[0].team_id;
    const details = detailsOf(body);
    expect(details).toEqual(
      expect.arrayContaining([
        { field: "customer.name", message: "Campo obrigatório." },
        { field: "items[1].team_id", message: "Campo obrigatório." },
      ]),
    );
  });

  it("schema_version diferente de 1", () => {
    const body = clone();
    body.schema_version = 2;
    expect(detailsOf(body)).toEqual(expect.arrayContaining([{ field: "schema_version", message: "Versão de pedido não suportada." }]));
  });

  it("itens vazios ou ausentes", () => {
    const empty = clone();
    empty.items = [];
    expect(detailsOf(empty)).toEqual(expect.arrayContaining([{ field: "items", message: "Informe pelo menos um item." }]));
    const missing = clone();
    delete missing.items;
    expect(detailsOf(missing)[0]!.field).toBe("items");
  });

  it.each([0, 1000, -1, 1.5, "2", true, null])("quantidade %j", (quantity) => {
    const body = clone();
    body.items[0].quantity = quantity;
    expect(detailsOf(body)).toEqual(
      expect.arrayContaining([expect.objectContaining({ field: "items[1].quantity" })]),
    );
  });

  it("mensagem de quantidade fora do limite cita o intervalo", () => {
    const body = clone();
    body.items[0].quantity = 1000;
    expect(detailsOf(body)).toEqual(
      expect.arrayContaining([{ field: "items[1].quantity", message: "A quantidade deve ficar entre 1 e 999." }]),
    );
  });

  it(`passa de ${MAX_ITEMS} itens`, () => {
    const body = clone();
    body.items = Array.from({ length: MAX_ITEMS + 1 }, (_, index) => ({ ...example.items[0], item_label: String(index) }));
    expect(detailsOf(body)).toEqual(expect.arrayContaining([{ field: "items", message: `No máximo ${MAX_ITEMS} itens por pedido.` }]));
  });

  it("aceita exatamente o máximo de itens", () => {
    const body = clone();
    body.items = Array.from({ length: MAX_ITEMS }, (_, index) => ({ ...example.items[0], item_label: String(index) }));
    expect(validateOrder(body).ok).toBe(true);
  });

  it("nome vazio, só com espaços ou grande demais", () => {
    for (const name of ["", "   ", "a".repeat(121)]) {
      const body = clone();
      body.customer.name = name;
      expect(detailsOf(body)).toEqual(expect.arrayContaining([expect.objectContaining({ field: "customer.name" })]));
    }
  });

  it("observação e rótulo grandes demais", () => {
    const body = clone();
    body.note = "n".repeat(501);
    body.items[0].item_label = "x".repeat(61);
    const details = detailsOf(body);
    expect(details).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ field: "note" }),
        expect.objectContaining({ field: "items[1].item_label" }),
      ]),
    );
  });

  it("WhatsApp informado mas inválido", () => {
    const body = clone();
    body.customer.whatsapp = "12345";
    expect(detailsOf(body)).toEqual(expect.arrayContaining([{ field: "customer.whatsapp", message: "Número de WhatsApp inválido." }]));
  });

  it("caracteres de controle são recusados", () => {
    const body = clone();
    body.note = "linha1" + String.fromCharCode(0) + "linha2";
    expect(detailsOf(body)).toEqual(expect.arrayContaining([expect.objectContaining({ field: "note" })]));
  });

  it("acumula todos os erros, não só o primeiro", () => {
    const body = clone();
    body.customer.name = "";
    body.items[0].quantity = 0;
    delete body.items[0].model_id;
    expect(detailsOf(body).length).toBeGreaterThanOrEqual(3);
  });
});

describe("parseOrderRequest", () => {
  it("devolve o pedido normalizado", () => {
    expect(parseOrderRequest(clone()).customerName).toBe("Fulano");
  });

  it("lança HttpError 400 com details", () => {
    try {
      parseOrderRequest({});
      throw new Error("não lançou");
    } catch (error) {
      expect(error).toBeInstanceOf(HttpError);
      const http = error as HttpError;
      expect(http.status).toBe(400);
      expect(http.code).toBe("pedido_invalido");
      expect(http.details!.length).toBeGreaterThan(0);
    }
  });
});
