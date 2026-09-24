import { Hono } from "hono";
import { useErrorHandling } from "./lib/errors";

const app = new Hono<{ Bindings: Env }>();
useErrorHandling(app);

app.get("/api/health", (context) => context.json({ ok: true }));
app.all("/api/health", (context) => context.body(null, 405, { Allow: "GET" }));

export default app;
