import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from rag.pipeline import build_rag_chain, ask, is_complex_query
from utils.cost_tracker import get_total_cost
from utils.session_manager import get_session_id, load_history, save_message, clear_session
from document_analysis.extractor import extract_text
from document_analysis.analyzer import analyze_document
from document_analysis.report_generator import generate_pdf_report

st.set_page_config(page_title="BuildIt PL", page_icon="🏗️", layout="centered")

# ── Header ────────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🏗️ BuildIt PL")
    st.caption("Your AI guide to construction & renovation in Poland — for expats, by expats.")
with col2:
    st.metric("API cost", f"${get_total_cost():.4f}")

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────
tab_chat, tab_docs = st.tabs(["💬 Chat Assistant", "📄 Document Analyzer"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════════════════════════════════════════
with tab_chat:
    session_id = get_session_id()
    if "messages" not in st.session_state:
        st.session_state.messages = load_history(session_id)

    STARTERS = [
        "What permits do I need to build a 120m² house in Masovia?",
        "Can I renovate without a permit if changes are internal only?",
        "What is MPZP and why does it matter for my plot?",
        "How long does a building permit take in Poland?",
    ]

    if len(st.session_state.messages) == 1:
        st.markdown("**Try a question:**")
        cols = st.columns(2)
        for i, q in enumerate(STARTERS):
            if cols[i % 2].button(q, use_container_width=True, key=f"starter_{i}"):
                st.session_state.starter_question = q

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask about permits, contractors, renovation steps...")
    if "starter_question" in st.session_state:
        user_input = st.session_state.pop("starter_question")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        save_message(session_id, "user", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            premium     = is_complex_query(user_input)
            model_label = "gpt-4o" if premium else "gpt-4o-mini"
            with st.spinner(f"Checking Polish construction law... [{model_label}]"):
                chain_tuple = build_rag_chain(premium=premium)
                _, _, model = chain_tuple
                response     = ask(chain_tuple, user_input, model)
                answer       = response["answer"]
                st.markdown(answer)
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    if response["sources"]:
                        with st.expander("📄 Sources"):
                            for s in response["sources"]:
                                st.markdown(f"- {s}")
                with col_b:
                    st.caption(f"🤖 `{model_label}` 💰 ${response['query_cost_usd']:.5f}")
                st.session_state.messages.append({"role": "assistant", "content": answer})
                save_message(session_id, "assistant", answer)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — DOCUMENT ANALYZER
# ════════════════════════════════════════════════════════════════════════════
with tab_docs:
    st.subheader("📄 Contract & Document Analyzer")
    st.caption(
        "Upload a Polish construction contract, purchase agreement, or permit letter. "
        "BuildIt will summarize it in plain English, flag risky clauses, and identify missing items."
    )
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Upload your document (PDF)",
        type=["pdf"],
        help="Max ~20 pages. Longer documents will be truncated."
    )

    if uploaded_file:
        st.success(f"✅ Uploaded: **{uploaded_file.name}**")

        if st.button("🔍 Analyze Document", type="primary", use_container_width=True):
            with st.spinner("Extracting text..."):
                try:
                    doc_text = extract_text(uploaded_file)
                except Exception as e:
                    st.error(f"Could not read file: {e}")
                    st.stop()

            progress = st.progress(0, text="Running analysis pipeline...")

            with st.spinner("Step 1/4 — Summarizing document..."):
                progress.progress(25, text="Summarizing...")

            with st.spinner("Step 2/4 — Identifying risky clauses..."):
                progress.progress(50, text="Identifying risks...")

            with st.spinner("Step 3/4 — Checking completeness..."):
                progress.progress(75, text="Checking completeness...")

                report = analyze_document(doc_text, uploaded_file.name)

            progress.progress(100, text="Generating report...")

            st.markdown("---")

            # ── Risk Score ────────────────────────────────────────────────
            score = report["risk_score"]
            color = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(score, "🟡")
            st.markdown(f"### Overall Risk: {color} **{score}**  —  {report['total_risks']} issue(s) found")

            # ── Summary ───────────────────────────────────────────────────
            with st.expander("📋 Document Summary", expanded=True):
                st.markdown(report["summary"])

            # ── Risks ─────────────────────────────────────────────────────
            with st.expander(f"⚠️ Risk Analysis ({report['total_risks']} items)", expanded=True):
                for level, risks, emoji in [
                    ("HIGH",   report["risks_high"],   "🔴"),
                    ("MEDIUM", report["risks_medium"], "🟡"),
                    ("LOW",    report["risks_low"],    "🟢"),
                ]:
                    for r in risks:
                        st.markdown(f"{emoji} **[{level}]** {r['description']}")
                        if r.get("explanation"):
                            st.caption(f"→ {r['explanation']}")
                if not report["total_risks"]:
                    st.success("No significant risks identified.")

            # ── Missing Items ─────────────────────────────────────────────
            with st.expander(f"📝 Missing / Unclear Items ({len(report['missing_items'])})", expanded=True):
                for i, item in enumerate(report["missing_items"], 1):
                    st.markdown(f"{i}. {item}")

            # ── Download PDF Report ───────────────────────────────────────
            st.markdown("---")
            pdf_bytes = generate_pdf_report(report)
            st.download_button(
                label="⬇️ Download Full PDF Report",
                data=pdf_bytes,
                file_name=f"buildit_analysis_{uploaded_file.name.replace('.pdf','')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )

            st.caption(
                "⚠️ Disclaimer: AI-generated analysis for informational purposes only. "
                "Always consult a licensed Polish attorney before signing."
            )

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏗️ BuildIt PL")
    st.markdown("AI assistant for expats navigating construction in Poland.")
    st.markdown("---")
    session_id = get_session_id()
    st.caption(f"Session: `{session_id[:8]}...`")
    st.caption(f"Messages: {len(st.session_state.get('messages', []))}")
    if st.button("🗑️ Clear chat", use_container_width=True):
        clear_session(session_id)
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.markdown("**Features**")
    st.caption("💬 Chat: construction Q&A")
    st.caption("📄 Analyzer: contract risk scanner")
    st.markdown("---")
    st.caption("Built with LangChain · LangGraph · ChromaDB · GPT-4o · Streamlit")
