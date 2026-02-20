import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from rag.pipeline import is_complex_query, ask
from ingestion.loader import load_vector_store
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from rag.prompts import SYSTEM_PROMPT, USER_TEMPLATE
from utils.cost_tracker import get_total_cost
from utils.session_manager import get_session_id, load_history, save_message, clear_session
from document_analysis.extractor import extract_text
from document_analysis.analyzer import analyze_document
from document_analysis.report_generator import generate_pdf_report
import config

st.set_page_config(page_title="BuildIt PL", page_icon="🏗️", layout="centered")

# ── Cache the vector store and chain ─────────────────────────────────────────
@st.cache_resource
def get_retriever():
    vs = load_vector_store()
    return vs.as_retriever(search_type="similarity", search_kwargs={"k": config.TOP_K_RESULTS})

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

@st.cache_resource
def get_chain(premium: bool):
    retriever = get_retriever()
    model = config.LLM_MODEL_PREMIUM if premium else config.LLM_MODEL_DEFAULT
    llm = ChatOpenAI(model=model, openai_api_key=config.OPENAI_API_KEY, temperature=0.2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_TEMPLATE)
    ])
    
    # Modern LCEL chain
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return (chain, retriever, model)

# ── Header ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🏗️ BuildIt PL")
    st.caption("Your AI guide to construction & renovation in Poland — for expats, by expats.")
with col2:
    st.metric("API cost", f"${get_total_cost():.4f}")

st.markdown("---")

# ── Session ────────────────────────────────────────────────────────────────
session_id = get_session_id()
if "messages" not in st.session_state:
    st.session_state.messages = load_history(session_id)

# ── FIX 2: Active tab tracked in session state (not Streamlit tabs) ─────────
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "chat"

col_t1, col_t2 = st.columns(2)
if col_t1.button("💬 Chat Assistant",  use_container_width=True,
                  type="primary" if st.session_state.active_tab == "chat" else "secondary"):
    st.session_state.active_tab = "chat"
if col_t2.button("📄 Document Analyzer", use_container_width=True,
                  type="primary" if st.session_state.active_tab == "docs" else "secondary"):
    st.session_state.active_tab = "docs"

st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════
# CHAT VIEW
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.active_tab == "chat":

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
            if cols[i % 2].button(q, use_container_width=True, key=f"s{i}"):
                st.session_state.pending_input = q
                st.rerun()

    # Display full chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # FIX: chat_input at TOP LEVEL (not inside any tab/column/expander)
    user_input = st.chat_input("Ask about permits, contractors, renovation steps...")

    # Handle starter button input
    if "pending_input" in st.session_state:
        user_input = st.session_state.pop("pending_input")

    if user_input:
        # Save & display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        save_message(session_id, "user", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate & display assistant response
        with st.chat_message("assistant"):
            premium     = is_complex_query(user_input)
            model_label = "gpt-4o" if premium else "gpt-4o-mini"
            with st.spinner(f"[{model_label}] Checking Polish construction law..."):
                chain_tuple = get_chain(premium)
                response     = ask(chain_tuple, user_input, chain_tuple[2])
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
# DOCUMENT ANALYZER VIEW
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "docs":
    st.subheader("📄 Contract & Document Analyzer")
    st.caption("Upload a Polish construction contract, purchase agreement, or permit letter.")
    st.markdown("---")

    uploaded_file = st.file_uploader("Upload your document (PDF)", type=["pdf"])

    if uploaded_file:
        st.success(f"✅ Uploaded: **{uploaded_file.name}**")

        if st.button("🔍 Analyze Document", type="primary", use_container_width=True):
            with st.spinner("Extracting text..."):
                try:
                    doc_text = extract_text(uploaded_file)
                except Exception as e:
                    st.error(f"Could not read file: {e}")
                    st.stop()

            bar = st.progress(0)
            with st.spinner("Summarizing..."):        bar.progress(25)
            with st.spinner("Identifying risks..."):  bar.progress(50)
            with st.spinner("Checking completeness..."):
                report = analyze_document(doc_text, uploaded_file.name)
                bar.progress(100)

            st.markdown("---")
            score = report["risk_score"]
            emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(score, "🟡")
            st.markdown(f"### Overall Risk: {emoji} **{score}** — {report['total_risks']} issue(s) found")

            with st.expander("📋 Document Summary", expanded=True):
                st.markdown(report["summary"])

            with st.expander(f"⚠️ Risks ({report['total_risks']})", expanded=True):
                for level, risks, e in [("HIGH", report["risks_high"], "🔴"),
                                         ("MEDIUM", report["risks_medium"], "🟡"),
                                         ("LOW", report["risks_low"], "🟢")]:
                    for r in risks:
                        st.markdown(f"{e} **[{level}]** {r['description']}")
                        if r.get("explanation"):
                            st.caption(f"→ {r['explanation']}")

            with st.expander(f"📝 Missing Items ({len(report['missing_items'])})", expanded=True):
                for i, item in enumerate(report["missing_items"], 1):
                    st.markdown(f"{i}. {item}")

            pdf_bytes = generate_pdf_report(report)
            st.download_button("⬇️ Download PDF Report", data=pdf_bytes,
                file_name=f"buildit_{uploaded_file.name}", mime="application/pdf",
                use_container_width=True, type="primary")
            st.caption("⚠️ AI-generated for informational purposes only. Consult a licensed Polish attorney before signing.")

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏗️ BuildIt PL")
    st.markdown("---")
    st.caption(f"Session: `{session_id[:8]}...`")
    st.caption(f"Messages: {len(st.session_state.get('messages', []))}")
    if st.button("🗑️ Clear chat", use_container_width=True):
        clear_session(session_id)
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("Built with LangChain · LangGraph · ChromaDB · GPT-4o · Streamlit")
