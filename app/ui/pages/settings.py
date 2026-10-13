"""Settings and Privacy Control Page for LedgerLens.
Allows model profile swapping, offline status checks, and data purging.
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
from app.config import get_config
from app.store.db import get_db
from app.update.orchestrator import get_orchestrator
from app.utils.crypto import verify_offline_license

def render_settings():
    st.markdown("## ⚙️ Settings & Privacy Controls")

    config_mgr = get_config()
    cfg = config_mgr.app_config

    st.markdown("### 🧠 Local Model Profile")
    st.markdown("Switch profiles instantly without touching code. Runs locally on your hardware.")

    profiles = ["fast", "balanced", "best"]
    current_profile = cfg.profile if cfg.profile in profiles else "balanced"
    new_profile = st.radio(
        "Active Model Profile",
        profiles,
        index=profiles.index(current_profile),
        format_func=lambda p: {
            "fast": "⚡ Fast (llama3.2:3b — 8 GB RAM Floor)",
            "balanced": "⚖️ Balanced (qwen2.5:7b-vl — 16 GB RAM Recommended)",
            "best": "🏆 Best (qwen2.5:32b-vl — 32 GB+ RAM Studio Grade)"
        }[p]
    )

    if new_profile != current_profile:
        config_mgr.set_profile(new_profile)
        st.success(f"Switched model profile to {new_profile}!")

    st.markdown("---")
    st.markdown("### 🔒 Offline & Privacy Guarantees")
    st.markdown("""
    - **Offline Status:** ✅ 100% Offline (Zero cloud telemetry)
    - **Model Weights:** Loaded from local Ollama / embedded fallback
    - **Database:** Local SQLite storage at `~/.local/share/ledgerlens/ledgerlens.db`
    """)

    st.markdown("---")
    st.markdown("### 🔄 Auto-Update Subsystem")
    if st.button("🔍 Check for Updates (app update --all)"):
        orchestrator = get_orchestrator()
        with st.spinner("Running 5 update channels..."):
            res = orchestrator.update_all()
        st.success("Update check completed! Recorded to logs/updates.log.")

    st.markdown("---")
    st.markdown("### 🔑 Offline Commercial License")
    st.markdown("Free tier allows 30 documents/month. Paste an Ed25519-signed offline license key for unlimited processing.")
    license_input = st.text_input("License Key", value=cfg.license_key or "", placeholder="PAYLOAD.ED25519_SIGNATURE")
    if license_input:
        status = verify_offline_license(license_input)
        if status["valid"]:
            st.success(f"✅ Verified Offline Perpetual License: {status['payload']}")
        else:
            st.warning(f"Free Tier Active: {status['reason']}")

    st.markdown("---")
    st.markdown("### 🗑️ Data Sovereignty: Delete All My Data")
    st.markdown("Hard delete all processed documents, extracted line items, and few-shot correction memory.")
    if st.button("🚨 Purge All Data Forever", type="secondary"):
        db = get_db()
        db.purge_all_data()
        st.error("All local user data has been permanently deleted.")
        st.rerun()
