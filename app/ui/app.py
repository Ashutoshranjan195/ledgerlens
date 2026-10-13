"""LedgerLens Local-First Web Interface (Streamlit).
Drag-and-drop receipts & invoices, verify confidence, and export tax CSVs.
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import tempfile

from app.core.pipeline import get_pipeline
from app.core.output import export_documents_to_csv, export_documents_to_json, generate_printable_summary_markdown
from app.store.db import get_db
from app.config import get_config
from app.ui.pages.onboarding import render_onboarding
from app.ui.pages.review_queue import render_review_queue
from app.ui.pages.settings import render_settings

st.set_page_config(
    page_title="LedgerLens — Local Expense Ledger",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_dashboard():
    st.title("🧾 LedgerLens")
    st.caption("Local-First • 100% Offline • Zero Marginal Cost Expense Ledger")

    db = get_db()
    pipeline = get_pipeline()
    config_mgr = get_config()

    # Drag and Drop Uploader
    st.markdown("### 📥 Drag & Drop Receipts or Invoices")
    uploaded_files = st.file_uploader(
        "Drop photos (PNG, JPG) or PDF invoices here",
        type=["png", "jpg", "jpeg", "pdf", "txt"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button(f"⚡ Process {len(uploaded_files)} File(s) Locally", type="primary"):
            progress_bar = st.progress(0)
            processed_count = 0
            with st.spinner("Extracting with local open-weight model..."):
                for idx, uf in enumerate(uploaded_files):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uf.name).suffix) as tmp:
                        tmp.write(uf.getvalue())
                        tmp_path = Path(tmp.name)
                    
                    try:
                        pipeline.process_file(tmp_path, force=True)
                        processed_count += 1
                    finally:
                        if tmp_path.exists():
                            tmp_path.unlink()
                    progress_bar.progress((idx + 1) / len(uploaded_files))
            st.success(f"Processed {processed_count} documents with local pipeline!")
            st.rerun()

    # Metrics Summary
    all_docs = db.get_all_documents()
    total_spend = sum(float(d.get("total_amount") or 0.0) for d in all_docs)
    review_needed = sum(1 for d in all_docs if d.get("needs_review"))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Expenses", f"${total_spend:,.2f}")
    m2.metric("Documents Ingested", len(all_docs))
    m3.metric("Review Queue", review_needed, delta="-needs attention" if review_needed else None)
    m4.metric("Active Model", config_mgr.get_active_profile().name)

    st.markdown("---")

    # Document Table & Actions
    if all_docs:
        st.subheader("📑 Document Ledger")
        
        # Action Buttons
        col_csv, col_json, _ = st.columns([1, 1, 3])
        with col_csv:
            csv_data = export_documents_to_csv(all_docs)
            st.download_button(
                "📥 Export Schedule C CSV",
                data=csv_data,
                file_name="ledgerlens_schedule_c_expenses.csv",
                mime="text/csv"
            )
        with col_json:
            json_data = export_documents_to_json(all_docs)
            st.download_button(
                "📥 Export Audit JSON",
                data=json_data,
                file_name="ledgerlens_audit_ledger.json",
                mime="application/json"
            )

        table_rows = []
        for d in all_docs:
            table_rows.append({
                "Date": d.get("doc_date") or "N/A",
                "Vendor": d.get("vendor") or "Unknown",
                "Category": d.get("category") or "Supplies & Equipment",
                "Total ($)": f"${float(d.get('total_amount') or 0.0):.2f}",
                "Confidence": f"{float(d.get('confidence') or 1.0)*100:.0f}%",
                "Status": "⚠️ Review Required" if d.get("needs_review") else "✅ Verified",
                "Filename": d.get("filename")
            })
        st.dataframe(table_rows, use_container_width=True)
    else:
        st.info("No documents processed yet. Drop your first receipt above or visit the Onboarding page for a 60-second win.")

def main():
    config_mgr = get_config()
    st.sidebar.markdown(f"### ⚙️ LedgerLens v{config_mgr.app_config.version}")
    st.sidebar.markdown(f"**Profile:** `{config_mgr.app_config.profile}`")
    st.sidebar.markdown("**Network:** ✈️ `Airplane Mode Ready`")

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard & Ingest", "Review Queue", "60s Onboarding", "Settings & Privacy"]
    )

    if page == "Dashboard & Ingest":
        render_dashboard()
    elif page == "Review Queue":
        render_review_queue()
    elif page == "60s Onboarding":
        render_onboarding()
    elif page == "Settings & Privacy":
        render_settings()

if __name__ == "__main__":
    main()
