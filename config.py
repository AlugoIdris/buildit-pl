import os

def get_secret(key, fallback=None):
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        return os.getenv(key, fallback)

OPENAI_API_KEY      = get_secret("OPENAI_API_KEY")
CHROMA_PERSIST_DIR  = get_secret("CHROMA_PERSIST_DIR", "./chroma_store")
KNOWLEDGE_BASE_DIR  = "./knowledge_base"
LLM_MODEL_DEFAULT   = "gpt-4o-mini"
LLM_MODEL_PREMIUM   = "gpt-4o"
EMBEDDING_MODEL     = "text-embedding-3-small"
CHUNK_SIZE          = 800
CHUNK_OVERLAP       = 100
TOP_K_RESULTS       = 5
