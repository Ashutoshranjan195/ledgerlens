"""User Corrections & Few-Shot Feedback Memory for LedgerLens.

FINE-TUNING SUBSTITUTE:
Instead of running expensive parameter updates or paying cloud fine-tuning APIs,
user corrections are persisted in local SQLite and retrieved as dynamic
few-shot exemplars for subsequent inference runs.
Cost = $0.00. Privacy = 100%. Accuracy improves on their specific documents.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.store.db import get_db
from app.utils.logging import logger

def record_user_correction(
    document_id: str,
    corrected_vendor: str,
    corrected_category: str,
    corrected_total: float,
    user_note: str = ""
) -> str:
    """Save user modification and mark document as reviewed/approved."""
    db = get_db()
    corr_id = db.record_correction(
        document_id=document_id,
        corrected_vendor=corrected_vendor,
        corrected_category=corrected_category,
        corrected_total=corrected_total,
        user_note=user_note
    )
    logger.info("Recorded few-shot correction %s for doc %s", corr_id, document_id)
    return corr_id

def get_recent_corrections(limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieve the most recent corrections to inject into the agent prompt."""
    db = get_db()
    return db.get_few_shot_corrections(limit=limit)
