import { HttpError } from "../lib/errors";

const SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify";
const MAX_TOKEN_LENGTH = 2048;

export interface TurnstileInput {
  secret: string | undefined;
  token: unknown;
  ip: string;
  fetchImpl?: typeof fetch;
}

/** Confirma o desafio do Turnstile. Qualquer dúvida (sem segredo, rede, resposta estranha) recusa: nunca libera por engano. */
export async function verifyTurnstile({ secret, token, ip, fetchImpl }: TurnstileInput): Promise<void> {
  if (!secret) throw new HttpError(503, "verificacao_indisponivel", "Verificação de segurança indisponível. Tente mais tarde.");
  if (typeof token !== "string" || token.trim().length === 0 || token.length > MAX_TOKEN_LENGTH) {
    throw new HttpError(403, "verificacao_falhou", "Não foi possível confirmar que você não é um robô. Recarregue a página e tente de novo.");
  }

  const form = new URLSearchParams({ secret, response: token, remoteip: ip });
  let outcome: unknown;
  try {
    const response = await (fetchImpl ?? fetch)(SITEVERIFY_URL, { method: "POST", body: form });
    if (!response.ok) throw new Error(`siteverify ${response.status}`);
    outcome = await response.json();
  } catch {
    throw new HttpError(503, "verificacao_indisponivel", "Verificação de segurança indisponível. Tente mais tarde.");
  }

  const success = typeof outcome === "object" && outcome !== null && (outcome as { success?: unknown }).success;
  if (success === true) return;
  if (typeof outcome !== "object" || outcome === null) {
    throw new HttpError(503, "verificacao_indisponivel", "Verificação de segurança indisponível. Tente mais tarde.");
  }
  throw new HttpError(403, "verificacao_falhou", "Não foi possível confirmar que você não é um robô. Recarregue a página e tente de novo.");
}
