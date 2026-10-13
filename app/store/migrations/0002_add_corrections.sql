-- 0002_add_corrections.sql: Add User Corrections & Few-Shot Feedback Store

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

CREATE INDEX IF NOT EXISTS idx_corrections_vendor ON corrections(corrected_vendor);
