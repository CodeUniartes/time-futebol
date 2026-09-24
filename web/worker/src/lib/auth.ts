import type { MiddlewareHandler } from "hono";
import { HttpError } from "./errors";

type TokenKind = "admin" | "reader";
type TokenEnv = { ADMIN_TOKEN?: string; READER_TOKEN?: string };

const SECRET_NAME: Record<TokenKind, keyof TokenEnv> = { admin: "ADMIN_TOKEN", reader: "READER_TOKEN" };
const encoder = new TextEncoder();

export function bearerToken(request: Request): string | null {
  const header = request.headers.get("Authorization") ?? "";
  const match = /^bearer\s+(\S+)\s*$/i.exec(header);
  return match?.[1] ?? null;
}

async function digest(value: string): Promise<Uint8Array> {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", encoder.encode(value)));
}

/** Compara em tempo constante: os dois lados viram hash de mesmo tamanho antes de comparar. */
export async function tokensMatch(received: string, expected: string): Promise<boolean> {
  if (!received || !expected) return false;
  const [left, right] = await Promise.all([digest(received), digest(expected)]);
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) difference |= left[index]! ^ right[index]!;
  return difference === 0;
}

/** Exige o token da categoria; qualquer falha vira o mesmo 401, sem dizer o que faltou ou qual token valia. */
export function requireToken(kind: TokenKind): MiddlewareHandler<{ Bindings: TokenEnv }> {
  return async (context, next) => {
    const expected = context.env?.[SECRET_NAME[kind]] ?? "";
    const received = bearerToken(context.req.raw);
    if (!received || !(await tokensMatch(received, expected))) {
      context.header("WWW-Authenticate", "Bearer");
      throw new HttpError(401, "nao_autorizado", "Acesso não autorizado.");
    }
    await next();
  };
}
