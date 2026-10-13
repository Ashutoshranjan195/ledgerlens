"""Integration test for LedgerLens.
Executes the full pipeline loop end-to-end on bundled samples.
"""

from pathlib import Path
import pytest
from app.core.pipeline import get_pipeline
from app.core.corrections import record_user_correction
from app.core.output import export_documents_to_csv, export_documents_to_json
from app.store.db import get_db

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def test_full_pipeline_loop():
    pipeline = get_pipeline()
    db = get_db()

    # Use bundled sample
    sample_file = BASE_DIR / "samples" / "receipts" / "bh_photo_receipt.txt"
    assert sample_file.exists(), f"Sample file missing: {sample_file}"

    # 1. Process document
    result = pipeline.process_file(sample_file, force=True)
    assert result is not None
    assert "B&H PHOTO VIDEO" in result["vendor"]
    assert result["total_amount"] == 70.75
    assert result["category"] == "Supplies & Equipment"
    assert result["confidence"] >= 0.85

    # 2. Test user correction memory
    doc_id = result["id"]
    corr_id = record_user_correction(
        document_id=doc_id,
        corrected_vendor="B&H Photo NYC Flagship",
        corrected_category="Supplies & Equipment",
        corrected_total=70.75,
        user_note="Custom vendor naming override"
    )
    assert corr_id is not None

    few_shots = db.get_few_shot_corrections(limit=3)
    assert len(few_shots) > 0
    assert few_shots[0]["corrected_vendor"] == "B&H Photo NYC Flagship"

    # 3. Test export generation
    all_docs = db.get_all_documents()
    csv_str = export_documents_to_csv(all_docs)
    assert "doc_date,vendor,category" in csv_str
    assert "70.75" in csv_str

    json_str = export_documents_to_json(all_docs)
    assert "B&H Photo NYC Flagship" in json_str
