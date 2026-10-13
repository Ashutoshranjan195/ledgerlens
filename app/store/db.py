"""Database manager for LedgerLens.
Encapsulates SQLite connection, automatic migrations, transactions, and few-shot memory.
"""

from __future__ import annotations
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.utils.paths import get_db_path, get_base_dir
from app.utils.logging import logger
from app.store.backup import backup_database

class Database:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or get_db_path()
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Establish a connection with foreign keys and row factory enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self) -> None:
        """Run all pending forward migrations."""
        self.run_migrations()

    def run_migrations(self) -> int:
        """Execute forward-only migrations from app/store/migrations/."""
        migrations_dir = get_base_dir() / "app" / "store" / "migrations"
        if not migrations_dir.exists():
            return 0

        # Backup DB prior to running migrations if DB already exists
        if self.db_path.exists() and self.db_path.stat().st_size > 0:
            backup_database(label="pre_migration")

        conn = self.get_connection()
        applied_count = 0
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor = conn.cursor()
                cursor.execute("SELECT version FROM schema_migrations ORDER BY version ASC;")
                applied_versions = {row["version"] for row in cursor.fetchall()}

                migration_files = sorted(migrations_dir.glob("*.sql"))
                for mf in migration_files:
                    prefix = mf.name.split("_")[0]
                    if not prefix.isdigit():
                        continue
                    version = int(prefix)
                    if version not in applied_versions:
                        logger.info("Applying database migration %d: %s", version, mf.name)
                        sql_script = mf.read_text(encoding="utf-8")
                        conn.executescript(sql_script)
                        conn.execute(
                            "INSERT INTO schema_migrations (version) VALUES (?);",
                            (version,)
                        )
                        applied_count += 1
            return applied_count
        finally:
            conn.close()

    def insert_document(self, doc_data: Dict[str, Any], line_items: Optional[List[Dict[str, Any]]] = None) -> str:
        """Insert or replace a processed receipt or invoice with line items."""
        doc_id = doc_data.get("id") or str(uuid.uuid4())
        conn = self.get_connection()
        try:
            with conn:
                conn.execute("""
                    INSERT OR REPLACE INTO documents (
                        id, filename, file_path, file_hash, file_type, vendor,
                        doc_date, total_amount, tax_amount, currency, category,
                        confidence, needs_review, status, raw_text, model_used, updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
                    );
                """, (
                    doc_id,
                    doc_data.get("filename", ""),
                    doc_data.get("file_path", ""),
                    doc_data["file_hash"],
                    doc_data.get("file_type", "receipt"),
                    doc_data.get("vendor"),
                    doc_data.get("doc_date"),
                    doc_data.get("total_amount"),
                    doc_data.get("tax_amount"),
                    doc_data.get("currency", "USD"),
                    doc_data.get("category"),
                    doc_data.get("confidence", 1.0),
                    1 if doc_data.get("needs_review") else 0,
                    doc_data.get("status", "processed"),
                    doc_data.get("raw_text", ""),
                    doc_data.get("model_used", "")
                ))

                if line_items:
                    conn.execute("DELETE FROM line_items WHERE document_id = ?;", (doc_id,))
                    for item in line_items:
                        item_id = item.get("id") or str(uuid.uuid4())
                        conn.execute("""
                            INSERT INTO line_items (
                                id, document_id, description, quantity,
                                unit_price, total_price, category, tax_deductible
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """, (
                            item_id,
                            doc_id,
                            item.get("description", "Item"),
                            item.get("quantity", 1.0),
                            item.get("unit_price", 0.0),
                            item.get("total_price", 0.0),
                            item.get("category"),
                            1 if item.get("tax_deductible", True) else 0
                        ))
            return doc_id
        finally:
            conn.close()

    def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE file_hash = ?;", (file_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_documents(self, limit: int = 500) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY created_at DESC LIMIT ?;", (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_review_queue(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE needs_review = 1 ORDER BY created_at DESC;")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def record_correction(
        self,
        document_id: str,
        corrected_vendor: str,
        corrected_category: str,
        corrected_total: float,
        user_note: str = ""
    ) -> str:
        """Store user correction and update the document, creating a few-shot feedback memory."""
        corr_id = str(uuid.uuid4())
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documents WHERE id = ?;", (document_id,))
                doc = cursor.fetchone()
                if not doc:
                    raise ValueError(f"Document {document_id} not found")

                orig_vendor = doc["vendor"]
                orig_cat = doc["category"]
                orig_total = doc["total_amount"]
                raw_snippet = (doc["raw_text"] or "")[:250]

                # Record correction event
                conn.execute("""
                    INSERT INTO corrections (
                        id, document_id, original_vendor, corrected_vendor,
                        original_category, corrected_category, original_total,
                        corrected_total, context_snippet, user_note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    corr_id,
                    document_id,
                    orig_vendor,
                    corrected_vendor,
                    orig_cat,
                    corrected_category,
                    orig_total,
                    corrected_total,
                    raw_snippet,
                    user_note
                ))

                # Update the target document to approved/corrected status
                conn.execute("""
                    UPDATE documents SET
                        vendor = ?,
                        category = ?,
                        total_amount = ?,
                        needs_review = 0,
                        status = 'corrected',
                        confidence = 1.0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?;
                """, (corrected_vendor, corrected_category, corrected_total, document_id))

            logger.info("Recorded correction %s for doc %s", corr_id, document_id)
            return corr_id
        finally:
            conn.close()

    def get_few_shot_corrections(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve recent corrections to feed back into model prompts."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM corrections
                ORDER BY created_at DESC
                LIMIT ?;
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def purge_all_data(self) -> None:
        """Hard delete all user documents, line items, and corrections."""
        conn = self.get_connection()
        try:
            with conn:
                conn.execute("DELETE FROM line_items;")
                conn.execute("DELETE FROM corrections;")
                conn.execute("DELETE FROM documents;")
            logger.info("Purged all user records from database")
        finally:
            conn.close()

_GLOBAL_DB: Optional[Database] = None

def get_db() -> Database:
    global _GLOBAL_DB
    if _GLOBAL_DB is None:
        _GLOBAL_DB = Database()
    return _GLOBAL_DB
