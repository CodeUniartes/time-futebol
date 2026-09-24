export const ORDER_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ";
export const ORDER_CODE_LENGTH = 5;
const PREFIX = "DTF-";
// Maior múltiplo de 31 abaixo de 256: bytes a partir daqui são descartados para o sorteio não ter viés.
const UNBIASED_LIMIT = 248;

export type RandomBytes = (count: number) => Uint8Array;

const systemRandom: RandomBytes = (count) => crypto.getRandomValues(new Uint8Array(count));

export function generateOrderCode(randomBytes: RandomBytes = systemRandom): string {
  let symbols = "";
  while (symbols.length < ORDER_CODE_LENGTH) {
    for (const byte of randomBytes(ORDER_CODE_LENGTH * 2)) {
      if (byte >= UNBIASED_LIMIT) continue;
      symbols += ORDER_CODE_ALPHABET[byte % ORDER_CODE_ALPHABET.length];
      if (symbols.length === ORDER_CODE_LENGTH) break;
    }
  }
  return PREFIX + symbols;
}

const ORDER_CODE_PATTERN = new RegExp(`^${PREFIX}[${ORDER_CODE_ALPHABET}]{${ORDER_CODE_LENGTH}}$`);

export function isValidOrderCode(value: string): boolean {
  return ORDER_CODE_PATTERN.test(value);
}
