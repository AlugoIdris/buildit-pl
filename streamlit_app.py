import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from rag.pipeline import build_rag_chain, ask, is_complex_query
from utils.cost_tracker import get_total_cost
from utils.session_manager import get_session_id, load_history, save_message, clear_session

st.set_page_config(page_title="BuildIt PL", page_icon="🏗️", layout="centered")

# ── Header ────────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🏗️ BuildIt PL")
    st.caption("Your AI guide to construction & renovation in Poland — for expats, by expats.")
with col2:
    st.metric("Total cost", f"${get_total_cost():.4f}")

st.markdown("---")

# ── Session ───────────────────────────────────────────────────────────────
session_id = get_session_id()

if "messages" not in st.session_state:
    st.session_state.messages = load_history(session_id)

# ── Starter suggestions (shown only on fresh session) ─────────────────────
STARTERS = [
    "What permits do I need to build a 120m² house in Masovia?",
    "Can I renovate without a permit if changes are internal only?",
    "What is MPZP and why does it matter for my plot?",
    "How long does a building permit take in Poland?",
]

if len(st.session_state.messages) == 1:
    st.markdown("**Try one of these to get started:**")
    cols = st.columns(2)
    for i, q in enumerate(STARTERS):
        if cols[i % 2].button(q, use_container_width=True):
            st.session_state.starter_question = q

# ── Chat history ──────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input: typed or starter button ───────────────────────────────────────
user_input = st.chat_input("Ask about permits, contractors, renovation steps...")
if "starter_question" in st.session_state:
    user_input = st.session_state.pop("starter_question")

# ── Response ──────────────────────────────────────────────────────────────
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_message(session_id, "user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        premium      = is_complex_query(user_input)
        model_label  = "gpt-4o" if premium else "gpt-4o-mini"
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
                st.caption(f"🤖 `{model_label}`  💰 ${response['query_cost_usd']:.5f}")

            st.session_state.messages.append({"role": "assistant", "content": answer})
            save_message(session_id, "assistant", answer)

# ── Sidebar: session info & reset ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏗️ BuildIt PL")
    st.markdown("AI assistant for expats navigating construction in Poland.")
    st.markdown("---")
    st.caption(f"Session ID: `{session_id[:8]}...`")
    st.caption(f"Messages: {len(st.session_state.messages)}")
    if st.button("🗑️ Clear my chat", use_container_width=True):
        clear_session(session_id)
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.markdown("**About**")
    st.caption("Built with LangChain · ChromaDB · GPT-4o-mini · Streamlit")
    st.caption("Knowledge base: Polish Construction Law (Prawo Budowlane)")
