"""Tools inspectable and executable by the LedgerLens agent layer.
Every tool is deterministic, local, and pure Python.
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional

SCHEDULE_C_CATEGORIES = {
    "Advertising": ["facebook ads", "google ads", "domain", "hosting", "flyer", "squarespace", "godaddy", "meta"],
    "Vehicle": ["gas", "fuel", "parking", "toll", "uber", "lyft", "auto repair", "chevron", "shell", "taxi", "cab", "meter", "pump"],
    "Commissions": ["referral fee", "agent commission"],
    "Contract Labor": ["upwork", "fiverr", "freelance assistant", "videographer hire", "retouching", "contract labor", "contract"],
    "Insurance": ["insurance", "equipment insurance", "business liability", "lemonade", "policy", "marine", "broker"],
    "Legal & Professional": ["attorney", "accountant", "cpa", "tax prep", "legalzoom", "tax services", "cpa tax"],
    "Office Expense": ["notion", "adobe", "google workspace", "google cloud", "dropbox", "software", "slack", "zoom", "apple cloud", "creative cloud"],
    "Supplies & Equipment": ["b&h", "camera", "lens", "sd card", "tripod", "printer paper", "ink", "staples", "best buy", "home depot", "apple store", "fedex", "target", "amazon", "studio", "hdmi", "cables", "prints", "batteries"],
    "Travel": ["hotel", "airbnb", "delta", "united", "flight", "amtrak", "airline", "lodging", "marriott", "air lines", "room rate"],
    "Meals (50%)": ["coffee", "starbucks", "cafe", "restaurant", "lunch meeting", "diner", "bistro", "panera", "chipotle", "working lunch", "pour over", "roaster", "croissant", "bowl", "burrito", "tea", "food"],
    "Utilities": ["internet", "mobile bill", "verizon", "t-mobile", "electric", "comcast", "utilities", "wireless", "broadband"],
    "Other": []
}

def validate_math(subtotal: Optional[float], tax: Optional[float], total: Optional[float]) -> Dict[str, Any]:
    """Validate arithmetic: does subtotal + tax equal total within 2 cents?"""
    if total is None:
        return {"valid": False, "discrepancy": 0.0, "message": "Total is missing"}

    if subtotal is not None and tax is not None:
        expected = round(subtotal + tax, 2)
        diff = round(abs(expected - total), 2)
        if diff <= 0.03:
            return {"valid": True, "discrepancy": diff, "message": "Math matches"}
        return {"valid": False, "discrepancy": diff, "message": f"Discrepancy: {subtotal} + {tax} != {total}"}

    return {"valid": True, "discrepancy": 0.0, "message": "Partial math fields"}

def lookup_schedule_c_category(vendor: str, text: str) -> str:
    """Classify expense into standard IRS Schedule C categories based on vendor and items."""
    combined = f"{vendor} {text}".lower()
    for category, keywords in SCHEDULE_C_CATEGORIES.items():
        for kw in keywords:
            if kw in combined:
                return category
    return "Supplies & Equipment"  # default solopreneur catch-all

def detect_currency_symbol(text: str) -> str:
    """Map detected currency symbols to ISO codes."""
    if "€" in text or "EUR" in text:
        return "EUR"
    if "£" in text or "GBP" in text:
        return "GBP"
    if "CAD" in text:
        return "CAD"
    return "USD"

def format_few_shot_context(corrections: List[Dict[str, Any]]) -> str:
    """Format previous user corrections into compact few-shot prompt text."""
    if not corrections:
        return "No user corrections on file yet."

    lines = ["Here are examples of how the user previously corrected mistakes on their receipts:"]
    for c in corrections:
        lines.append(
            f"- Vendor recognized as '{c.get('original_vendor')}' was corrected to '{c.get('corrected_vendor')}'. "
            f"Category assigned: '{c.get('corrected_category')}'. Verified Total: ${c.get('corrected_total', 0.0):.2f}"
        )
    return "\n".join(lines)
