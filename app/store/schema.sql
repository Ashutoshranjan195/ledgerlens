-- Primary Schema Definition for LedgerLens Local Storage

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT,
    file_hash TEXT UNIQUE NOT NULL,
    file_type TEXT NOT NULL,         -- 'receipt' | 'invoice' | 'statement'
    vendor TEXT,
    doc_date TEXT,
    total_amount REAL,
    tax_amount REAL,
    currency TEXT DEFAULT 'USD',
    category TEXT,
    confidence REAL DEFAULT 1.0,
    needs_review INTEGER DEFAULT 0,  -- 0: Approved, 1: Flagged for review
    status TEXT DEFAULT 'processed', -- 'pending' | 'processed' | 'corrected'
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

CREATE TABLE IF NOT EXISTS corrections (
    id TEXT PRIMARY KEY,
    document_id TEXT REFERENCES documents(id) ON DELETE SET NULL,
    original_vendor TEXT,
    corrected_vendor TEXT,
    original_category TEXT,
    corrected_category TEXT,
    original_total REAL,
    corrected_total REAL,
    context_snippet TEXT,
    user_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_docs_review ON documents(needs_review);
CREATE INDEX IF NOT EXISTS idx_corrections_vendor ON corrections(corrected_vendor);
