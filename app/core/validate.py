"""Validation and Confidence Scoring Engine for LedgerLens.

RULE: The model NEVER silently guesses on low confidence.
Any document that violates mathematical consistency, lacks clear vendor attribution,
or has ambiguous totals is proactively flagged for the Review Queue.
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple

def validate_extraction(data: Dict[str, Any], confidence_threshold: float = 0.85) -> Tuple[float, bool, List[str]]:
    """Evaluate extraction quality, computing a confidence score and 'needs review' flag.

    Returns:
        (confidence_score, needs_review, review_reasons)
    """
    reasons: List[str] = []
    score = 1.0

    vendor = data.get("vendor")
    total_amount = data.get("total_amount")
    subtotal = data.get("subtotal")
    tax_amount = data.get("tax_amount")
    doc_date = data.get("doc_date")
    category = data.get("category")

    # 1. Total checks (most critical financial field)
    if total_amount is None:
        score -= 0.50
        reasons.append("Critical: Total amount is missing.")
    elif total_amount <= 0.0:
        score -= 0.40
        reasons.append(f"Critical: Total amount is non-positive (${total_amount}).")
    elif total_amount > 50000.0:
        score -= 0.15
        reasons.append(f"Notice: Unusually large transaction amount (${total_amount:,.2f}).")

    # 2. Arithmetic validation
    if total_amount is not None and subtotal is not None and tax_amount is not None:
        expected = round(subtotal + tax_amount, 2)
        diff = round(abs(expected - total_amount), 2)
        if diff > 0.03:
            score -= 0.25
            reasons.append(f"Math discrepancy: Subtotal (${subtotal}) + Tax (${tax_amount}) != Total (${total_amount}). Diff: ${diff}")

    # 3. Vendor validation
    if not vendor or str(vendor).strip().lower() in ("unknown vendor", "unknown", "receipt", "invoice", "store"):
        score -= 0.30
        reasons.append("Vendor name is missing or ambiguous.")
    elif len(str(vendor).strip()) < 2:
        score -= 0.20
        reasons.append("Vendor name is too short to be definitive.")

    # 4. Date validation
    if not doc_date:
        score -= 0.20
        reasons.append("Document date could not be established.")

    # 5. Category validation
    if not category or category in ("Other", "Unknown"):
        score -= 0.10
        reasons.append("Tax category could not be definitively matched.")

    # Bound score between 0.0 and 1.0
    final_score = max(0.0, min(1.0, round(score, 2)))
    needs_review = (final_score < confidence_threshold) or bool(reasons)

    return final_score, needs_review, reasons
