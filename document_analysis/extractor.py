"""
Extracts text from uploaded PDF or DOCX files.
Cleans and truncates to fit within LLM context window.
"""
import fitz  # PyMuPDF
import io

MAX_CHARS = 12000  # ~3000 tokens — safe for gpt-4o context

def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for page in doc:
        pages.append(page.get_text())
    raw = "\n".join(pages).strip()
    return raw[:MAX_CHARS] + ("\n\n[Document truncated for analysis...]" if len(raw) > MAX_CHARS else "")

def extract_text(uploaded_file) -> str:
    """Main entry point — handles file object from st.file_uploader."""
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {uploaded_file.name}. Upload a PDF.")
