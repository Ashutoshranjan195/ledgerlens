"""Core Processing Pipeline for LedgerLens.

LAYERING ENFORCEMENT:
- May NOT import from app/ui/** or app/update/**.
- May NOT import requests, httpx, or openai.
- Implements: extract -> normalize -> model pass -> validate -> output.
"""

from __future__ import annotations
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.core.extract import extract_document
from app.core.infer import get_inference_engine
from app.core.normalize import normalize_extracted_fields
from app.core.validate import validate_extraction
from app.agent.harness import InspectableAgentHarness
from app.store.db import get_db
from app.config import get_config
from app.utils.logging import logger

class LedgerPipeline:
    """The central offline document processing pipeline."""

    def __init__(self) -> None:
        self.db = get_db()
        self.config_manager = get_config()
        self.inference_engine = get_inference_engine()
        self.agent_harness = InspectableAgentHarness(
            infer_fn=self.inference_engine.generate
        )

    def process_file(
        self,
        file_path: Union[str, Path],
        force: bool = False
    ) -> Dict[str, Any]:
        """Execute end-to-end extraction pipeline on a single document."""
        path = Path(file_path)
        logger.info("Pipeline processing file: %s", path.name)

        # 1. Extraction (local OCR / PDF / image parsing)
        extracted = extract_document(path)
        file_hash = str(extracted["file_hash"])

        # Check deduplication in local DB
        if not force:
            existing = self.db.get_document_by_hash(file_hash)
            if existing:
                logger.info("Found existing document record with hash %s", file_hash)
                return existing

        # 2. Retrieve dynamic few-shot corrections from local SQLite memory
        few_shots = self.db.get_few_shot_corrections(limit=4)

        # 3. Model Pass via Inspectable Agent Harness
        agent_trace = self.agent_harness.execute(
            raw_text=str(extracted["extracted_text"]),
            image_base64=str(extracted["image_base64"]) if extracted["image_base64"] else None,
            few_shots=few_shots
        )
        raw_output = agent_trace.final_output

        # 4. Normalization (dates, floats, IRS Schedule C categories)
        normalized = normalize_extracted_fields(raw_output)

        # 5. Validation & Confidence Scoring
        conf_threshold = self.config_manager.app_config.confidence_threshold
        confidence, needs_review, review_reasons = validate_extraction(
            normalized,
            confidence_threshold=conf_threshold
        )

        active_model = self.config_manager.get_active_model_name()
        doc_id = str(uuid.uuid4())

        doc_record = {
            "id": doc_id,
            "filename": path.name,
            "file_path": str(path.resolve()),
            "file_hash": file_hash,
            "file_type": "invoice" if "invoice" in path.name.lower() else "receipt",
            "vendor": normalized.get("vendor", "Unknown Vendor"),
            "doc_date": normalized.get("doc_date"),
            "total_amount": normalized.get("total_amount"),
            "tax_amount": normalized.get("tax_amount", 0.0),
            "currency": normalized.get("currency", "USD"),
            "category": normalized.get("category", "Supplies & Equipment"),
            "confidence": confidence,
            "needs_review": 1 if needs_review else 0,
            "status": "pending_review" if needs_review else "processed",
            "raw_text": str(extracted["extracted_text"])[:2000],
            "model_used": active_model
        }

        # 6. Store in local SQLite
        self.db.insert_document(
            doc_data=doc_record,
            line_items=normalized.get("line_items")
        )

        doc_record["review_reasons"] = review_reasons
        doc_record["line_items"] = normalized.get("line_items", [])
        return doc_record

    def process_batch(self, file_paths: List[Union[str, Path]]) -> List[Dict[str, Any]]:
        """Process multiple files sequentially with local zero-marginal cost."""
        results = []
        for p in file_paths:
            try:
                res = self.process_file(p)
                results.append(res)
            except Exception as e:
                logger.error("Failed to process file %s: %s", p, e)
                results.append({
                    "filename": Path(p).name,
                    "error": str(e),
                    "needs_review": 1,
                    "status": "error"
                })
        return results

_GLOBAL_PIPELINE: Optional[LedgerPipeline] = None

def get_pipeline() -> LedgerPipeline:
    global _GLOBAL_PIPELINE
    if _GLOBAL_PIPELINE is None:
        _GLOBAL_PIPELINE = LedgerPipeline()
    return _GLOBAL_PIPELINE
