"""Review Queue Page for LedgerLens.
Presents low-confidence documents that need human approval.
Saves user edits as few-shot exemplars to improve future local extractions.
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
from app.store.db import get_db
from app.core.corrections import record_user_correction
from app.core.normalize import SCHEDULE_C_STANDARD

def render_review_queue():
    st.markdown("## ⚠️ Review Queue")
    st.markdown("""
    **Rule:** The model never silently guesses on low confidence.
    Review flagged documents below, adjust fields if necessary, and approve.
    Your corrections are saved locally to improve subsequent extractions automatically.
    """)

    db = get_db()
    flagged_docs = db.get_review_queue()

    if not flagged_docs:
        st.success("🎉 All documents verified! Zero items currently in the review queue.")
        return

    st.info(f"**{len(flagged_docs)} document(s)** requiring your review.")

    for doc in flagged_docs:
        with st.expander(f"📄 {doc.get('filename')} — ${doc.get('total_amount', 0.0):.2f} (Confidence: {doc.get('confidence', 0)*100:.0f}%)", expanded=True):
            st.markdown(f"**Detected raw text:**")
            st.code(doc.get("raw_text", "")[:350], language="text")

            col1, col2, col3 = st.columns(3)
            with col1:
                new_vendor = st.text_input("Vendor Name", value=doc.get("vendor") or "", key=f"vendor_{doc['id']}")
            with col2:
                current_cat = doc.get("category") or "Supplies & Equipment"
                cat_index = SCHEDULE_C_STANDARD.index(current_cat) if current_cat in SCHEDULE_C_STANDARD else 0
                new_cat = st.selectbox("IRS Schedule C Category", SCHEDULE_C_STANDARD, index=cat_index, key=f"cat_{doc['id']}")
            with col3:
                new_total = st.number_input("Verified Total ($)", value=float(doc.get("total_amount") or 0.0), step=0.50, key=f"tot_{doc['id']}")

            user_note = st.text_input("Optional memory note for local agent", value="", placeholder="e.g. Always categorize this studio rental under Supplies & Equipment", key=f"note_{doc['id']}")

            if st.button("✅ Approve & Save to Memory", key=f"btn_{doc['id']}", type="primary"):
                record_user_correction(
                    document_id=doc["id"],
                    corrected_vendor=new_vendor,
                    corrected_category=new_cat,
                    corrected_total=new_total,
                    user_note=user_note
                )
                st.success(f"Approved! Stored correction in local memory.")
                st.rerun()
