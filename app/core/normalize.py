"""Normalization engine for LedgerLens.
Ensures uniform date formats, sanitized float amounts, and standardized tax categories.
"""

from __future__ import annotations
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

SCHEDULE_C_STANDARD = [
    "Advertising",
    "Vehicle",
    "Contract Labor",
    "Insurance",
    "Legal & Professional",
    "Office Expense",
    "Supplies & Equipment",
    "Travel",
    "Meals (50%)",
    "Utilities",
    "Other"
]

def normalize_date(raw_date: Optional[str]) -> Optional[str]:
    """Parse various date representations into ISO 8601 (YYYY-MM-DD)."""
    if not raw_date:
        return None
    cleaned = raw_date.strip().replace("/", "-").replace(".", "-")

    # Match YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned):
        return cleaned

    formats = [
        "%Y-%m-%d",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%b %d %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%Y-%m-%d %H:%M:%S"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned.split("T")[0], fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Regex search for year, month, day patterns
    match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", raw_date)
    if match:
        y, m, d = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    match_us = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", raw_date)
    if match_us:
        m, d, y = match_us.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    return None

def normalize_amount(raw_val: Any) -> Optional[float]:
    """Convert string/number currency representations to a sanitized float rounded to 2 decimal places."""
    if raw_val is None:
        return None
    if isinstance(raw_val, (int, float)):
        return round(float(raw_val), 2)

    cleaned = str(raw_val).strip()
    # Strip symbols
    cleaned = re.sub(r"[^\d.,\-]", "", cleaned)
    if not cleaned:
        return None

    # Handle thousands comma vs decimal comma
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned and "." not in cleaned:
        # Check if comma represents decimal e.g. "49,99"
        if len(cleaned.split(",")[-1]) == 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")

    try:
        val = float(cleaned)
        return round(val, 2)
    except ValueError:
        return None

def normalize_category(raw_category: Optional[str]) -> str:
    """Map raw category to an official IRS Schedule C bucket."""
    if not raw_category:
        return "Supplies & Equipment"

    cleaned = raw_category.strip().title()
    for standard in SCHEDULE_C_STANDARD:
        if standard.lower() in cleaned.lower():
            return standard

    if "software" in cleaned.lower() or "subscription" in cleaned.lower() or "hosting" in cleaned.lower():
        return "Office Expense"
    if "food" in cleaned.lower() or "dining" in cleaned.lower() or "lunch" in cleaned.lower():
        return "Meals (50%)"
    if "hardware" in cleaned.lower() or "gear" in cleaned.lower() or "camera" in cleaned.lower():
        return "Supplies & Equipment"
    if "gas" in cleaned.lower() or "uber" in cleaned.lower() or "parking" in cleaned.lower():
        return "Vehicle"

    return "Supplies & Equipment"

def normalize_vendor(raw_vendor: Optional[str]) -> str:
    """Clean noisy store numbers and register prefixes from vendor names."""
    if not raw_vendor:
        return "Unknown Vendor"

    cleaned = raw_vendor.strip()
    # Remove common store noise like "#1249", "STORE 041", "REG 02"
    cleaned = re.sub(r"#\s*\d+", "", cleaned)
    cleaned = re.sub(r"(?i)\bstore\s+\d+\b", "", cleaned)
    cleaned = re.sub(r"(?i)\bregister\s+\d+\b", "", cleaned)
    cleaned = re.sub(r"(?i)\bterminal\s+\d+\b", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else "Unknown Vendor"

def normalize_extracted_fields(raw_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Execute all normalizations across raw extracted dictionary."""
    normalized = dict(raw_dict)
    normalized["vendor"] = normalize_vendor(raw_dict.get("vendor"))
    normalized["doc_date"] = normalize_date(raw_dict.get("doc_date"))
    normalized["total_amount"] = normalize_amount(raw_dict.get("total_amount"))
    normalized["subtotal"] = normalize_amount(raw_dict.get("subtotal"))
    normalized["tax_amount"] = normalize_amount(raw_dict.get("tax_amount")) or 0.0
    normalized["category"] = normalize_category(raw_dict.get("category"))
    normalized["currency"] = str(raw_dict.get("currency") or "USD").upper().strip()

    # Normalize line items if present
    items = raw_dict.get("line_items") or []
    norm_items = []
    for item in items:
        if isinstance(item, dict):
            norm_items.append({
                "description": str(item.get("description", "Item")).strip(),
                "quantity": normalize_amount(item.get("quantity")) or 1.0,
                "unit_price": normalize_amount(item.get("unit_price")) or 0.0,
                "total_price": normalize_amount(item.get("total_price")) or 0.0,
                "category": normalize_category(item.get("category") or normalized["category"]),
                "tax_deductible": bool(item.get("tax_deductible", True))
            })
    normalized["line_items"] = norm_items
    return normalized
