// Segredos cadastrados com `wrangler secret put` (não aparecem no wrangler.jsonc, então não entram em `wrangler types`).
declare namespace Cloudflare {
  interface Env {
    ADMIN_TOKEN: string;
    READER_TOKEN: string;
    TURNSTILE_SECRET: string;
  }
}
