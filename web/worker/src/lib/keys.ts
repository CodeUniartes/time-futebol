export const PREVIEW_PREFIX = "previews/";
export const CATALOG_KEY = "catalog/catalog.public.json";
const MAX_KEY_LENGTH = 300;
// Só o que o Montador gera (slug em minúsculas). A lista de permitidos já barra barra invertida, %, espaço e quebra de linha.
const SAFE_PREVIEW_KEY = /^previews\/[a-z0-9_.\-/]+\.webp$/;

export function isSafePreviewKey(key: string): boolean {
  if (typeof key !== "string" || key.length > MAX_KEY_LENGTH || !SAFE_PREVIEW_KEY.test(key)) return false;
  const parts = key.split("/");
  return parts.every((part) => part.length > 0 && part !== "." && part !== "..") && !key.endsWith("/.webp");
}

export async function sha256Hex(data: ArrayBuffer | Uint8Array): Promise<string> {
  const bytes = data instanceof Uint8Array ? data : new Uint8Array(data);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function isSha256Hex(value: string): boolean {
  return typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
}
