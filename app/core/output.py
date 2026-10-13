"""Output and Export Writers for LedgerLens.
Generates tax-ready CSV, audit-proof JSON, and formatted printable summaries.
"""

from __future__ import annotations
import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def export_documents_to_csv(documents: List[Dict[str, Any]], target_file: Optional[Union[str, Path]] = None) -> str:
    """Generate a tax-ready CSV formatted for IRS Schedule C reporting."""
    fieldnames = [
        "doc_date",
        "vendor",
        "category",
        "total_amount",
        "tax_amount",
        "currency",
        "status",
        "confidence",
        "filename"
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for doc in documents:
        row = {
            "doc_date": doc.get("doc_date") or "",
            "vendor": doc.get("vendor") or "",
            "category": doc.get("category") or "",
            "total_amount": f"{doc.get('total_amount', 0.0):.2f}" if doc.get("total_amount") is not None else "0.00",
            "tax_amount": f"{doc.get('tax_amount', 0.0):.2f}" if doc.get("tax_amount") is not None else "0.00",
            "currency": doc.get("currency") or "USD",
            "status": doc.get("status") or "processed",
            "confidence": f"{doc.get('confidence', 1.0):.2f}",
            "filename": doc.get("filename") or ""
        }
        writer.writerow(row)

    content = output.getvalue()
    if target_file:
        Path(target_file).parent.mkdir(parents=True, exist_ok=True)
        Path(target_file).write_text(content, encoding="utf-8")
    return content

def export_documents_to_json(documents: List[Dict[str, Any]], target_file: Optional[Union[str, Path]] = None) -> str:
    """Generate structured audit-proof JSON containing full metadata and confidence scores."""
    content = json.dumps(documents, indent=2, default=str)
    if target_file:
        Path(target_file).parent.mkdir(parents=True, exist_ok=True)
        Path(target_file).write_text(content, encoding="utf-8")
    return content

def generate_printable_summary_markdown(documents: List[Dict[str, Any]]) -> str:
    """Produce a clean Markdown report grouped by tax category with totals."""
    categories: Dict[str, float] = {}
    grand_total = 0.0

    for doc in documents:
        cat = doc.get("category") or "Uncategorized"
        amt = float(doc.get("total_amount") or 0.0)
        categories[cat] = categories.get(cat, 0.0) + amt
        grand_total += amt

    lines = [
        "# LedgerLens Tax & Expense Summary",
        f"**Total Documents:** {len(documents)}  ",
        f"**Total Deductible Expenses:** ${grand_total:,.2f}  ",
        "",
        "## Category Breakdown (IRS Schedule C)",
        "",
        "| Category | Total Amount | % of Total |",
        "| :--- | :--- | :--- |"
    ]

    for cat, amt in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        pct = (amt / grand_total * 100) if grand_total > 0 else 0.0
        lines.append(f"| {cat} | ${amt:,.2f} | {pct:.1f}% |")

    lines.append("")
    lines.append("## Itemized Audit Ledger")
    lines.append("")
    lines.append("| Date | Vendor | Category | Total | Review Status |")
    lines.append("| :--- | :--- | :--- | :--- | :--- |")

    for doc in documents:
        d = doc.get("doc_date") or "N/A"
        v = doc.get("vendor") or "N/A"
        c = doc.get("category") or "N/A"
        t = f"${float(doc.get('total_amount') or 0.0):,.2f}"
        status = "[Needs Review]" if doc.get("needs_review") else "[Verified]"
        lines.append(f"| {d} | {v} | {c} | {t} | {status} |")

    return "\n".join(lines)
