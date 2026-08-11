-- ============================================================
-- PRINTS NoxTec — Multi-Painel
-- Domínio: dashboard.dashapi.com.br
-- Schema SQLite
-- ============================================================

-- ============================================================
-- PAINÉIS (multi-projeto)
-- Cada painel é um produto da NoxTec
-- ============================================================
CREATE TABLE IF NOT EXISTS paineis (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT UNIQUE NOT NULL,  -- validacao-documentos, disparador, etc
    nome            TEXT NOT NULL,         -- "Validação Documentos"
    descricao       TEXT,
    icone           TEXT,                  -- emoji ou url
    cor_primaria    TEXT DEFAULT '#4F46E5',
    ativo           INTEGER DEFAULT 1,
    criado_em       DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- USUÁRIOS
-- ============================================================
CREATE TABLE IF NOT EXISTS painel_usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT UNIQUE NOT NULL,
    senha_hash  TEXT NOT NULL,
    nome        TEXT NOT NULL,
    nivel       TEXT DEFAULT 'viewer',  -- admin | operador | viewer
    ativo       INTEGER DEFAULT 1,
    criado_em   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- PERMISSÕES (usuário pode acessar N painéis)
-- ============================================================
CREATE TABLE IF NOT EXISTS painel_permissoes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL,
    painel_id   INTEGER NOT NULL,
    nivel       TEXT DEFAULT 'viewer',  -- admin | operador | viewer
    UNIQUE(usuario_id, painel_id),
    FOREIGN KEY (usuario_id) REFERENCES painel_usuarios(id),
    FOREIGN KEY (painel_id)   REFERENCES paineis(id)
);

-- ============================================================
-- EXECUÇÕES — Validação Documentos
-- ============================================================
CREATE TABLE IF NOT EXISTS wd_execucoes (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id           TEXT UNIQUE NOT NULL,
    workflow_id            TEXT,
    workflow_nome          TEXT,
    status                 TEXT NOT NULL,
    iniciado_em            DATETIME,
    finalizado_em          DATETIME,
    duracao_ms             INTEGER,
    total_documentos       INTEGER DEFAULT 0,
    documentos_aprovados   INTEGER DEFAULT 0,
    documentos_rejeitados  INTEGER DEFAULT 0,
    documentos_pendentes   INTEGER DEFAULT 0,
    metadados              TEXT,
    erro_mensagem          TEXT,
    erro_node              TEXT,
    nodes_executados       TEXT,
    dados_originais        TEXT,
    created_at             DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wd_metricas_dia (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    data                DATE UNIQUE NOT NULL,
    total_execucoes     INTEGER DEFAULT 0,
    total_sucesso       INTEGER DEFAULT 0,
    total_erro          INTEGER DEFAULT 0,
    total_documentos    INTEGER DEFAULT 0,
    docs_aprovados      INTEGER DEFAULT 0,
    docs_rejeitados     INTEGER DEFAULT 0,
    tempo_medio_ms      INTEGER DEFAULT 0,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wd_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id    TEXT,
    nivel           TEXT DEFAULT 'info',
    mensagem        TEXT,
    node_nome       TEXT,
    contexto        TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- ÍNDICES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_execucoes_status ON wd_execucoes(status);
CREATE INDEX IF NOT EXISTS idx_execucoes_data   ON wd_execucoes(finalizado_em);
CREATE INDEX IF NOT EXISTS idx_metricas_data    ON wd_metricas_dia(data);
CREATE INDEX IF NOT EXISTS idx_logs_execution   ON wd_logs(execution_id);
CREATE INDEX IF NOT EXISTS idx_permissoes_user  ON painel_permissoes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_permissoes_painel ON painel_permissoes(painel_id);

-- ============================================================
-- SEED — Painéis iniciais da NoxTec
-- ============================================================
INSERT OR IGNORE INTO paineis (slug, nome, descricao, icone, cor_primaria) VALUES
    ('validacao-documentos', 'Validação Documentos', 'Análise e validação automática de documentos', '📄', '#4F46E5'),
    ('disparador',           'Disparador',           'Central de disparos WhatsApp',                  '📨', '#10B981');
