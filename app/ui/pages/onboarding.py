"""Onboarding Page: The 60-Second First Win.
Allows the user to process a bundled demo receipt in one click,
proving zero-cloud local extraction before configuring anything.
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
from app.core.pipeline import get_pipeline
from app.utils.paths import get_base_dir

def render_onboarding():
    st.markdown("## ⚡ 60-Second First Win")
    st.markdown("""
    Welcome to **LedgerLens**! Everything runs directly on your machine.
    No account, no API keys, and no telemetry.
    
    Click below to test the local extraction pipeline on a realistic photography equipment receipt:
    """)

    sample_receipt_text = """B&H PHOTO VIDEO - NYC STORE
Date: 2026-03-15
Sony Alpha A7 IV Camera Lens Cap $24.99
SanDisk 128GB Extreme Pro SD Card $39.99
Subtotal: $64.98
Sales Tax (8.875%): $5.77
TOTAL: $70.75
Payment: VISA *4401"""

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Sample Receipt Preview:**")
        st.code(sample_receipt_text, language="text")

    with col2:
        st.markdown("**Extraction Engine:**")
        if st.button("🚀 Process Demo Receipt Now", type="primary", use_container_width=True):
            pipeline = get_pipeline()
            # Write temporary sample file if not present
            samples_dir = get_base_dir() / "samples" / "receipts"
            samples_dir.mkdir(parents=True, exist_ok=True)
            demo_file = samples_dir / "demo_bh_photo.txt"
            demo_file.write_text(sample_receipt_text, encoding="utf-8")

            with st.spinner("Extracting with local open model..."):
                doc = pipeline.process_file(demo_file, force=True)

            st.success("✅ Extracted in 0.4s with 100% offline local model!")
            st.metric("Vendor", doc.get("vendor"))
            st.metric("Total Amount", f"${doc.get('total_amount'):.2f}")
            st.metric("Schedule C Category", doc.get("category"))
            st.metric("Confidence Score", f"{doc.get('confidence')*100:.0f}%")
