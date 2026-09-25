import { Validator } from "@cfworker/json-schema";
import orderSchema from "../../../../contracts/order.schema.json";
import { HttpError, type ErrorDetail } from "../lib/errors";
import { normalizeWhatsapp } from "../lib/phone";

export const MAX_ITEMS = 300;
const MAX_NAME = 120;
const MAX_NOTE = 500;
const MAX_LABEL = 60;
const MAX_ID = 100;
const MAX_QUANTITY = 999;

export interface NormalizedItem {
  teamId: string;
  teamName: string | null;
  season: number | null;
  modelId: string;
  modelName: string | null;
  categoryId: string;
  categoryName: string | null;
  itemLabel: string;
  quantity: number;
}

export interface NormalizedOrder {
  customerName: string;
  customerWhatsapp: string | null;
  note: string | null;
  items: NormalizedItem[];
}

export type ValidationResult = { ok: true; order: NormalizedOrder } | { ok: false; details: ErrorDetail[] };

// O contrato do pedido é o mesmo arquivo usado pelo Montador (contracts/order.schema.json).
const validator = new Validator(orderSchema as never, "2020-12", false);
const LEAF_KEYWORDS = new Set(["required", "type", "minimum", "maximum", "minLength", "minItems", "const", "enum"]);

type Loose = Record<string, unknown>;
const isObject = (value: unknown): value is Loose => typeof value === "object" && value !== null && !Array.isArray(value);
const hasControlCharacter = (text: string) => Array.from(text).some((char) => char.charCodeAt(0) < 32 || char.charCodeAt(0) === 127);

function fieldPath(instanceLocation: string, extra?: string): string {
  const parts = instanceLocation.replace(/^#\/?/, "").split("/").filter(Boolean);
  let path = "";
  for (const part of parts) {
    path += /^[0-9]+$/.test(part) ? `[${Number(part) + 1}]` : path ? `.${part}` : part;
  }
  if (extra) path += path ? `.${extra}` : extra;
  return path;
}

function schemaMessage(keyword: string, path: string): string {
  if (keyword === "required") return "Campo obrigatório.";
  if (keyword === "type") return "Tipo de valor inválido.";
  if (keyword === "minimum" || keyword === "maximum") {
    return path.endsWith("quantity") ? `A quantidade deve ficar entre 1 e ${MAX_QUANTITY}.` : "Valor fora do limite permitido.";
  }
  if (keyword === "minLength") return "Não pode ficar vazio.";
  if (keyword === "minItems") return "Informe pelo menos um item.";
  if (keyword === "const" && path === "schema_version") return "Versão de pedido não suportada.";
  return "Valor inválido.";
}

function schemaDetails(body: unknown): ErrorDetail[] {
  const details: ErrorDetail[] = [];
  const result = validator.validate(body);
  for (const error of result.errors) {
    if (!LEAF_KEYWORDS.has(error.keyword)) continue;
    if (error.keyword === "required") {
      const name = /"([^"]+)"/.exec(error.error)?.[1];
      details.push({ field: fieldPath(error.instanceLocation, name), message: "Campo obrigatório." });
      continue;
    }
    const field = fieldPath(error.instanceLocation);
    details.push({ field, message: schemaMessage(error.keyword, field) });
  }
  return details;
}

function text(value: unknown): string | null {
  return typeof value === "string" ? value.trim() : null;
}

function checkText(details: ErrorDetail[], field: string, value: unknown, max: number, required: boolean): string | null {
  if (value === undefined || value === null) return null;
  const trimmed = text(value);
  if (trimmed === null) return null; // o esquema já apontou o tipo
  if (hasControlCharacter(trimmed)) details.push({ field, message: "Contém caracteres não permitidos." });
  else if (required && trimmed.length === 0) details.push({ field, message: "Não pode ficar vazio." });
  else if (trimmed.length > max) details.push({ field, message: `Use no máximo ${max} caracteres.` });
  return trimmed;
}

/** Valida o corpo de POST /api/orders. O servidor decide code, created_at e catalog_version: o que vier deles é ignorado. */
export function validateOrder(body: unknown): ValidationResult {
  if (!isObject(body)) return { ok: false, details: [{ field: "", message: "O pedido precisa ser um objeto JSON." }] };

  const details = schemaDetails(body);
  const customer = isObject(body.customer) ? body.customer : {};
  const rawItems = Array.isArray(body.items) ? body.items : [];

  const customerName = checkText(details, "customer.name", customer.name, MAX_NAME, true);
  const note = checkText(details, "note", body.note, MAX_NOTE, false);
  let whatsapp: string | null = null;
  const rawWhatsapp = text(customer.whatsapp);
  if (rawWhatsapp) {
    whatsapp = normalizeWhatsapp(rawWhatsapp);
    if (!whatsapp) details.push({ field: "customer.whatsapp", message: "Número de WhatsApp inválido." });
  }
  if (rawItems.length === 0) details.push({ field: "items", message: "Informe pelo menos um item." });
  if (rawItems.length > MAX_ITEMS) details.push({ field: "items", message: `No máximo ${MAX_ITEMS} itens por pedido.` });

  const items: NormalizedItem[] = [];
  rawItems.slice(0, MAX_ITEMS).forEach((raw, index) => {
    const item = isObject(raw) ? raw : {};
    const at = (name: string) => `items[${index + 1}].${name}`;
    const teamId = checkText(details, at("team_id"), item.team_id, MAX_ID, true);
    const modelId = checkText(details, at("model_id"), item.model_id, MAX_ID, true);
    const categoryId = checkText(details, at("category_id"), item.category_id, MAX_ID, true);
    const itemLabel = checkText(details, at("item_label"), item.item_label, MAX_LABEL, true);
    const teamName = checkText(details, at("team_name"), item.team_name, MAX_NAME, false);
    const modelName = checkText(details, at("model_name"), item.model_name, MAX_NAME, false);
    const categoryName = checkText(details, at("category_name"), item.category_name, MAX_NAME, false);
    const season = typeof item.season === "number" && Number.isInteger(item.season) ? item.season : null;
    const quantity = typeof item.quantity === "number" ? item.quantity : 0;
    items.push({
      teamId: teamId ?? "",
      teamName: teamName || null,
      season,
      modelId: modelId ?? "",
      modelName: modelName || null,
      categoryId: categoryId ?? "",
      categoryName: categoryName || null,
      itemLabel: itemLabel ?? "",
      quantity,
    });
  });

  if (details.length > 0) return { ok: false, details: dedupe(details) };
  return { ok: true, order: { customerName: customerName ?? "", customerWhatsapp: whatsapp, note: note || null, items } };
}

function dedupe(details: ErrorDetail[]): ErrorDetail[] {
  const seen = new Set<string>();
  return details.filter((detail) => {
    const key = `${detail.field}|${detail.message}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function parseOrderRequest(body: unknown): NormalizedOrder {
  const result = validateOrder(body);
  if (!result.ok) throw new HttpError(400, "pedido_invalido", "O pedido tem campos inválidos.", result.details);
  return result.order;
}
