// Segredos cadastrados com `wrangler secret put` (não aparecem no wrangler.jsonc, então não entram em `wrangler types`).
interface WorkerSecrets {
  ADMIN_TOKEN: string;
  READER_TOKEN: string;
  TURNSTILE_SECRET: string;
}

declare namespace Cloudflare {
  interface Env extends WorkerSecrets {}
}

interface Env extends WorkerSecrets {}
