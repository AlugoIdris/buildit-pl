"""
LangGraph analysis pipeline with 4 nodes:
  summarize -> identify_risks -> check_completeness -> compile_report
"""
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import config

class AnalysisState(TypedDict):
    document_text: str
    document_name: str
    summary: str
    risks: List[dict]
    missing_items: List[str]
    report: dict

def _llm():
    return ChatOpenAI(model=config.LLM_MODEL_PREMIUM,
                      openai_api_key=config.OPENAI_API_KEY,
                      temperature=0.1)

# ── Node 1: Summarize ─────────────────────────────────────────────────────
def summarize_document(state: AnalysisState) -> AnalysisState:
    prompt = f"""You are a legal assistant helping a foreigner understand a Polish construction or real estate document.

Summarize this document in plain English (3-5 sentences):
- What type of document is it?
- Who are the parties?
- What is the core agreement or obligation?

DOCUMENT:
{state["document_text"]}
"""
    response = _llm().invoke(prompt)
    state["summary"] = response.content
    return state

# ── Node 2: Identify Risks ────────────────────────────────────────────────
def identify_risks(state: AnalysisState) -> AnalysisState:
    prompt = f"""You are a legal risk analyst reviewing a Polish construction/real estate document for a foreign client.

Identify risky, unusual, or unfair clauses. For each risk:
- Describe the clause briefly
- Explain why it is risky for the client
- Rate severity: HIGH / MEDIUM / LOW

Format each risk as:
RISK: <description>
WHY: <explanation>
SEVERITY: <HIGH|MEDIUM|LOW>

DOCUMENT:
{state["document_text"]}
"""
    response = _llm().invoke(prompt)
    raw = response.content
    risks = []
    blocks = [b.strip() for b in raw.split("\n\n") if "RISK:" in b]
    for block in blocks:
        lines = {l.split(":")[0].strip(): ":".join(l.split(":")[1:]).strip()
                 for l in block.split("\n") if ":" in l}
        risks.append({
            "description": lines.get("RISK", ""),
            "explanation":  lines.get("WHY", ""),
            "severity":     lines.get("SEVERITY", "MEDIUM").upper()
        })
    state["risks"] = risks if risks else [{"description": raw, "explanation": "", "severity": "MEDIUM"}]
    return state

# ── Node 3: Check Completeness ────────────────────────────────────────────
def check_completeness(state: AnalysisState) -> AnalysisState:
    prompt = f"""You are reviewing a Polish construction contract for a foreigner.

List items that are MISSING or UNCLEAR that a proper construction contract should include.
Examples: payment schedule, warranty period, penalty clauses, completion date, 
          materials specification, dispute resolution, contractor license number.

Return a plain numbered list of missing items only.

DOCUMENT:
{state["document_text"]}
"""
    response = _llm().invoke(prompt)
    raw = response.content
    items = [
        line.lstrip("0123456789.-) ").strip()
        for line in raw.split("\n")
        if line.strip() and line.strip()[0].isdigit() or line.strip().startswith("-")
    ]
    state["missing_items"] = items if items else [raw]
    return state

# ── Node 4: Compile Report ────────────────────────────────────────────────
def compile_report(state: AnalysisState) -> AnalysisState:
    high   = [r for r in state["risks"] if r["severity"] == "HIGH"]
    medium = [r for r in state["risks"] if r["severity"] == "MEDIUM"]
    low    = [r for r in state["risks"] if r["severity"] == "LOW"]
    state["report"] = {
        "document_name":  state["document_name"],
        "summary":        state["summary"],
        "risks_high":     high,
        "risks_medium":   medium,
        "risks_low":      low,
        "missing_items":  state["missing_items"],
        "total_risks":    len(state["risks"]),
        "risk_score":     "HIGH" if high else ("MEDIUM" if medium else "LOW"),
    }
    return state

# ── Build graph ───────────────────────────────────────────────────────────
def build_analysis_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("summarize",    summarize_document)
    graph.add_node("risks",        identify_risks)
    graph.add_node("completeness", check_completeness)
    graph.add_node("compile",      compile_report)
    graph.set_entry_point("summarize")
    graph.add_edge("summarize",    "risks")
    graph.add_edge("risks",        "completeness")
    graph.add_edge("completeness", "compile")
    graph.add_edge("compile",      END)
    return graph.compile()

def analyze_document(document_text: str, document_name: str) -> dict:
    app = build_analysis_graph()
    result = app.invoke({
        "document_text": document_text,
        "document_name": document_name,
        "summary": "", "risks": [], "missing_items": [], "report": {}
    })
    return result["report"]
