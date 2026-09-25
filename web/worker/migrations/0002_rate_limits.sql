-- Limite de taxa por janela fixa: uma linha por (chave, início da janela). A chave é o hash do IP, nunca o IP.
CREATE TABLE rate_limits (
  key TEXT NOT NULL,
  window_start INTEGER NOT NULL,
  count INTEGER NOT NULL,
  PRIMARY KEY (key, window_start)
);
CREATE INDEX idx_rate_limits_window ON rate_limits(window_start);
