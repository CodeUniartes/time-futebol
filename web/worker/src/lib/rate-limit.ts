import { HttpError } from "./errors";
import { sha256Hex } from "./keys";

export interface HitInput {
  key: string;
  limit: number;
  windowSeconds: number;
  now?: Date;
}

export interface HitResult {
  allowed: boolean;
  remaining: number;
  retryAfterSeconds: number;
}

/**
 * Janela fixa: cada chamada soma 1 na linha (chave, início da janela) numa única instrução atômica.
 * A ordem de chegada decide quem passa, então chamadas simultâneas nunca ultrapassam o limite.
 */
export async function hitRateLimit(db: D1Database, { key, limit, windowSeconds, now = new Date() }: HitInput): Promise<HitResult> {
  const nowSeconds = Math.floor(now.getTime() / 1000);
  const windowStart = nowSeconds - (nowSeconds % windowSeconds);
  const row = await db
    .prepare(
      `INSERT INTO rate_limits (key, window_start, count) VALUES (?1, ?2, 1)
       ON CONFLICT(key, window_start) DO UPDATE SET count = count + 1
       RETURNING count`,
    )
    .bind(key, windowStart)
    .first<{ count: number }>();
  const count = row?.count ?? limit + 1;
  return {
    allowed: count <= limit,
    remaining: Math.max(0, limit - count),
    retryAfterSeconds: windowStart + windowSeconds - nowSeconds,
  };
}

/** Chave por cliente sem guardar o IP em claro (dado pessoal): só o hash, separado por finalidade. */
export async function clientKey(scope: string, ip: string): Promise<string> {
  return `${scope}:${(await sha256Hex(new TextEncoder().encode(`${scope}|${ip}`))).slice(0, 32)}`;
}

export interface EnforceInput {
  db: D1Database;
  scope: string;
  ip: string;
  limit: number;
  windowSeconds: number;
  now?: Date;
}

export async function enforceRateLimit({ db, scope, ip, limit, windowSeconds, now }: EnforceInput): Promise<void> {
  const result = await hitRateLimit(db, { key: await clientKey(scope, ip), limit, windowSeconds, now });
  if (!result.allowed) {
    throw new HttpError(429, "muitas_tentativas", "Muitas tentativas em pouco tempo. Aguarde um pouco e tente de novo.", undefined, {
      "Retry-After": String(result.retryAfterSeconds),
    });
  }
}
