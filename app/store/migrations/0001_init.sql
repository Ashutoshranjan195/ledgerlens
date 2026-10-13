-- 0001_init.sql: Initial Schema

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT,
    file_hash TEXT UNIQUE NOT NULL,
    file_type TEXT NOT NULL,
    vendor TEXT,
    doc_date TEXT,
    total_amount REAL,
    tax_amount REAL,
    currency TEXT DEFAULT 'USD',
    category TEXT,
    confidence REAL DEFAULT 1.0,
    needs_review INTEGER DEFAULT 0,
    status TEXT DEFAULT 'processed',
    raw_text TEXT,
    model_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS line_items (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity REAL DEFAULT 1.0,
    unit_price REAL,
    total_price REAL NOT NULL,
    category TEXT,
    tax_deductible INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_docs_review ON documents(needs_review);
