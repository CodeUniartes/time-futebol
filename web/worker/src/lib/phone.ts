const COUNTRY_CODE = "55";
const MIN_DDD = 11;

/**
 * Número brasileiro só com dígitos, no formato 55 + DDD + número (12 ou 13 dígitos), ou null se não for válido.
 * Celular tem 9 dígitos e começa com 9; fixo tem 8 dígitos e começa com 2 a 5; número antigo de celular
 * sem o nono dígito (começa com 6 a 9) também é aceito, sem inventar o dígito que falta.
 */
export function normalizeWhatsapp(input: string): string | null {
  if (typeof input !== "string") return null;
  let digits = input.replace(/[^0-9]/g, "");
  if (digits.startsWith("0")) digits = digits.replace(/^0+/, "");
  if (digits.startsWith(COUNTRY_CODE) && (digits.length === 12 || digits.length === 13)) {
    digits = digits.slice(COUNTRY_CODE.length);
  }
  if (digits.length !== 10 && digits.length !== 11) return null;

  const ddd = Number(digits.slice(0, 2));
  const subscriber = digits.slice(2);
  if (ddd < MIN_DDD) return null;
  if (subscriber.length === 9 && subscriber[0] !== "9") return null;
  if (subscriber.length === 8 && !/^[2-9]/.test(subscriber)) return null;
  return COUNTRY_CODE + digits;
}
