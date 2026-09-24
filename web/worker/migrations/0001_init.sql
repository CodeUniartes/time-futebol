-- Regras do projeto: TEXT, sem chave estrangeira, datas em UTC (ISO 8601 com Z), exclusão lógica, índices parciais.

CREATE TABLE orders (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  customer_name TEXT NOT NULL,
  customer_whatsapp TEXT,
  customer_id TEXT,
  note TEXT,
  catalog_version TEXT,
  created_at TEXT NOT NULL,
  imported_at TEXT,
  finished_at TEXT,
  deleted_at TEXT
);
CREATE UNIQUE INDEX idx_orders_code_unique ON orders(code) WHERE deleted_at IS NULL;
CREATE INDEX idx_orders_status ON orders(status, created_at) WHERE deleted_at IS NULL;

CREATE TABLE order_items (
  id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL,
  position INTEGER NOT NULL,
  team_id TEXT NOT NULL,
  team_name TEXT,
  season INTEGER,
  model_id TEXT NOT NULL,
  model_name TEXT,
  category_id TEXT NOT NULL,
  category_name TEXT,
  item_label TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  deleted_at TEXT
);
CREATE INDEX idx_order_items_order_id ON order_items(order_id) WHERE deleted_at IS NULL;

CREATE TABLE idempotency_keys (
  key TEXT PRIMARY KEY,
  request_hash TEXT NOT NULL,
  order_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE catalog_versions (
  catalog_version TEXT PRIMARY KEY,
  published_at TEXT NOT NULL,
  item_count INTEGER NOT NULL
);

CREATE TABLE preview_files (
  key TEXT PRIMARY KEY,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  updated_at TEXT NOT NULL
);
