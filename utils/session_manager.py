"""
Per-user session manager.
Uses st.session_state for runtime isolation (each browser tab = unique state).
Persists chat history to SQLite in /tmp (survives page refreshes within a deployment).
"""
import sqlite3, uuid, os
import streamlit as st

DB_PATH = "/tmp/buildit_sessions.db"

def _init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            session_id TEXT,
            role TEXT,
            content TEXT,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()

def get_session_id() -> str:
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
    return st.session_state["session_id"]

def load_history(session_id: str) -> list:
    _init_db()
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT role, content FROM messages WHERE session_id=? ORDER BY ts",
        (session_id,)
    ).fetchall()
    con.close()
    if not rows:
        return [{
            "role": "assistant",
            "content": (
                "Hi! I am **BuildIt**, your AI assistant for construction "
                "and renovation in Poland.\n\n"
                "Ask me anything — permits, timelines, contractor tips, renovation steps."
            )
        }]
    return [{"role": r, "content": c} for r, c in rows]

def save_message(session_id: str, role: str, content: str):
    _init_db()
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?,?,?)",
        (session_id, role, content)
    )
    con.commit()
    con.close()

def clear_session(session_id: str):
    _init_db()
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    con.commit()
    con.close()
