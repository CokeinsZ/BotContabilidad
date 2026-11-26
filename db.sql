-- Database schema for managing businesses and their associated data in a SQLite database.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    sheets_folder_id TEXT NOT NULL,
    workers_folder_id TEXT,
    state TEXT NOT NULL DEFAULT 'active'
        CHECK (state IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS business_administrators (
    id INTEGER PRIMARY KEY,
    business_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'active'
        CHECK (state IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (business_id) REFERENCES businesses(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS business_bold_api_keys (
    id INTEGER PRIMARY KEY,
    business_id INTEGER NOT NULL,
    api_key TEXT NOT NULL,

    FOREIGN KEY (business_id) REFERENCES businesses(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS business_bold_payments (
    id INTEGER PRIMARY KEY,
    business_id INTEGER NOT NULL,
    payment_id TEXT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    state TEXT NOT NULL DEFAULT 'rejected'
        CHECK (state IN ('approved', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (business_id) REFERENCES businesses(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- ----------------------------------------------------------------------
-- App móvil
-- Los tiempos de estas tablas son segundos Unix (UTC) en INTEGER: se comparan
-- en Python sin depender del formato de fecha de SQLite.
-- El historial del chat NO se guarda aquí: vive en cada teléfono.
-- ----------------------------------------------------------------------

-- Vinculación de la app desde WhatsApp: la app muestra un código y el
-- administrador se lo envía al bot ("VINCULAR 482913").
CREATE TABLE IF NOT EXISTS app_pairings (
    id TEXT PRIMARY KEY,                       -- secreto aleatorio que solo conoce la app
    code TEXT NOT NULL,                        -- 6 dígitos que viajan por WhatsApp
    device_name TEXT,
    administrator_id INTEGER,                  -- se llena al confirmar desde WhatsApp
    state TEXT NOT NULL DEFAULT 'pending'
        CHECK (state IN ('pending', 'confirmed', 'consumed')),
    expires_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL,

    FOREIGN KEY (administrator_id) REFERENCES business_administrators(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_app_pairings_code ON app_pairings(code, state);

-- Sesiones de la app: una por dispositivo vinculado. El refresh token se
-- guarda como SHA-256, nunca en claro, y rota en cada uso.
CREATE TABLE IF NOT EXISTS app_sessions (
    id INTEGER PRIMARY KEY,
    administrator_id INTEGER NOT NULL,
    refresh_token_hash TEXT NOT NULL UNIQUE,
    device_name TEXT,
    created_at INTEGER NOT NULL,
    last_used_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    revoked_at INTEGER,

    FOREIGN KEY (administrator_id) REFERENCES business_administrators(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_app_sessions_admin ON app_sessions(administrator_id);
