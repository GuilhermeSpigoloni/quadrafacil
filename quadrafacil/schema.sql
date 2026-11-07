-- QuadraFácil - Esquema do banco de dados (SQLite)
-- Projeto Integrado - Análise e Desenvolvimento de Sistemas

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL,
    login       TEXT    NOT NULL UNIQUE,
    senha_hash  TEXT    NOT NULL,
    perfil      TEXT    NOT NULL CHECK (perfil IN ('ATENDENTE', 'GERENTE'))
);

CREATE TABLE IF NOT EXISTS cliente (
    id_cliente    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL,
    telefone      TEXT NOT NULL,
    email         TEXT,
    data_cadastro TEXT NOT NULL DEFAULT (date('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS quadra (
    id_quadra   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL UNIQUE,
    modalidade  TEXT    NOT NULL,
    valor_hora  REAL    NOT NULL CHECK (valor_hora >= 0),
    ativa       INTEGER NOT NULL DEFAULT 1 CHECK (ativa IN (0, 1))
);

CREATE TABLE IF NOT EXISTS reserva (
    id_reserva  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente  INTEGER NOT NULL REFERENCES cliente (id_cliente),
    id_quadra   INTEGER NOT NULL REFERENCES quadra  (id_quadra),
    id_usuario  INTEGER NOT NULL REFERENCES usuario (id_usuario),
    data        TEXT    NOT NULL,              -- AAAA-MM-DD
    hora_inicio TEXT    NOT NULL,              -- HH:MM
    hora_fim    TEXT    NOT NULL,              -- HH:MM
    valor_total REAL    NOT NULL CHECK (valor_total >= 0),
    status      TEXT    NOT NULL DEFAULT 'CONFIRMADA'
                CHECK (status IN ('CONFIRMADA', 'CANCELADA')),
    criada_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK (hora_fim > hora_inicio)
);

CREATE INDEX IF NOT EXISTS idx_reserva_quadra_data ON reserva (id_quadra, data);

-- Carga inicial: quadras da arena
INSERT OR IGNORE INTO quadra (nome, modalidade, valor_hora) VALUES
    ('Quadra 1 - Society', 'Futebol society', 120.00),
    ('Quadra 2 - Futsal', 'Futsal', 90.00),
    ('Quadra 3 - Areia', 'Vôlei de areia', 60.00);
