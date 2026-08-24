-- Database schema for managing businesses and their associated data in a SQLite database.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    sheets_folder_id TEXT NOT NULL,
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