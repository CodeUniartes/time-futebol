/** Versão do catálogo publicada por último (guardada em cada pedido para saber de qual catálogo ele saiu). */
export async function latestCatalogVersion(db: D1Database): Promise<string | null> {
  const row = await db
    .prepare("SELECT catalog_version FROM catalog_versions ORDER BY published_at DESC LIMIT 1")
    .first<{ catalog_version: string }>();
  return row?.catalog_version ?? null;
}
