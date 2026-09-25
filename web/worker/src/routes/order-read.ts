import { Hono, type Context } from "hono";
import { requireToken } from "../lib/auth";
import { HttpError } from "../lib/errors";
import { isValidOrderCode } from "../lib/order-code";
import { findOrderContract, markOrderImported } from "../services/orders";

export const orderReadRoutes = new Hono<{ Bindings: Env }>();

function codeFrom(context: Context): string {
  const code = context.req.query("code") ?? "";
  if (!isValidOrderCode(code)) throw new HttpError(400, "codigo_invalido", "Informe um código de pedido válido (DTF-XXXXX).");
  return code;
}

orderReadRoutes.get("/api/order", requireToken("reader"), async (context) => {
  const order = await findOrderContract(context.env.DB, codeFrom(context));
  if (!order) throw new HttpError(404, "pedido_nao_encontrado", "Pedido não encontrado.");
  return context.json(order);
});
orderReadRoutes.all("/api/order", (context) => context.body(null, 405, { Allow: "GET" }));

orderReadRoutes.post("/api/order/imported", requireToken("reader"), async (context) => {
  const state = await markOrderImported(context.env.DB, codeFrom(context));
  if (!state) throw new HttpError(404, "pedido_nao_encontrado", "Pedido não encontrado.");
  return context.json(state);
});
orderReadRoutes.all("/api/order/imported", (context) => context.body(null, 405, { Allow: "POST" }));
