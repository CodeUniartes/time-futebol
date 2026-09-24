import type { Context, Hono } from "hono";
import { bodyLimit } from "hono/body-limit";
import type { ContentfulStatusCode } from "hono/utils/http-status";

export interface ErrorDetail {
  field?: string;
  message: string;
}

export class HttpError extends Error {
  constructor(
    readonly status: ContentfulStatusCode,
    readonly code: string,
    message: string,
    readonly details?: ErrorDetail[],
  ) {
    super(message);
    this.name = "HttpError";
  }
}

export function errorResponse(context: Context, error: HttpError): Response {
  const body: { code: string; message: string; status: number; details?: ErrorDetail[] } = {
    code: error.code,
    message: error.message,
    status: error.status,
  };
  if (error.details) body.details = error.details;
  return context.json({ error: body }, error.status);
}

/** Formato único de erro da API; erro inesperado nunca devolve nem registra o texto original (pode ter dado pessoal). */
export function useErrorHandling(app: Hono<any>): void {
  app.onError((error, context) => {
    if (error instanceof HttpError) return errorResponse(context, error);
    console.error(JSON.stringify({ event: "unhandled_error", name: error.name, path: new URL(context.req.url).pathname }));
    return errorResponse(context, new HttpError(500, "erro_interno", "Erro interno. Tente novamente."));
  });
  app.notFound((context) => errorResponse(context, new HttpError(404, "nao_encontrado", "Recurso não encontrado.")));
}

export function limitBody(maxBytes: number) {
  return bodyLimit({
    maxSize: maxBytes,
    onError: (context) =>
      errorResponse(context, new HttpError(413, "corpo_grande_demais", "O envio passou do tamanho máximo permitido.")),
  });
}
