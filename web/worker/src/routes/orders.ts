import { Hono } from "hono";
import { HttpError, limitBody } from "../lib/errors";
import { enforceRateLimit } from "../lib/rate-limit";
import { latestCatalogVersion } from "../services/catalog-version";
import { createOrderOnce, parseIdempotencyKey } from "../services/idempotency";
import { parseOrderRequest } from "../services/order-validation";
import { verifyTurnstile } from "../services/turnstile";

export const MAX_ORDER_BODY_BYTES = 256 * 1024;
export const ORDERS_PER_WINDOW = 10;
export const ORDERS_WINDOW_SECONDS = 3600;

export const orderRoutes = new Hono<{ Bindings: Env }>();

orderRoutes.post("/api/orders", limitBody(MAX_ORDER_BODY_BYTES), async (context) => {
  const key = parseIdempotencyKey(context.req.header("Idempotency-Key"));

  let body: unknown;
  try {
    body = await context.req.json();
  } catch {
    throw new HttpError(400, "json_invalido", "O corpo do pedido não é um JSON válido.");
  }
  if (typeof body !== "object" || body === null || Array.isArray(body)) {
    throw new HttpError(400, "json_invalido", "O corpo do pedido precisa ser um objeto JSON.");
  }

  const ip = context.req.header("CF-Connecting-IP") ?? "desconhecido";
  await enforceRateLimit({ db: context.env.DB, scope: "orders", ip, limit: ORDERS_PER_WINDOW, windowSeconds: ORDERS_WINDOW_SECONDS });
  await verifyTurnstile({ secret: context.env.TURNSTILE_SECRET, token: (body as { turnstile_token?: unknown }).turnstile_token, ip });

  const order = parseOrderRequest(body);
  const created = await createOrderOnce(context.env.DB, {
    key,
    order,
    catalogVersion: await latestCatalogVersion(context.env.DB),
  });
  return context.json({ code: created.code, created_at: created.createdAt }, created.replayed ? 200 : 201);
});

orderRoutes.all("/api/orders", (context) => context.body(null, 405, { Allow: "POST" }));
