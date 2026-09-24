import { Hono } from "hono";

const app = new Hono<{ Bindings: Env }>();

app.get("/api/health", (context) => context.json({ ok: true }));
app.all("/api/health", (context) => context.body(null, 405, { Allow: "GET" }));

export default app;
