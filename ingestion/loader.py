import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import config

def load_documents(source_dir):
    loader = DirectoryLoader(source_dir, glob="**/*.pdf",
                             loader_cls=PyPDFLoader, show_progress=True)
    docs = loader.load()
    print(f"Loaded {len(docs)} pages.")
    return docs

def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "]
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")
    return chunks

def build_vector_store(chunks):
    embeddings = OpenAIEmbeddings(model=config.EMBEDDING_MODEL,
                                   openai_api_key=config.OPENAI_API_KEY)
    vs = Chroma.from_documents(documents=chunks, embedding=embeddings,
                                persist_directory=config.CHROMA_PERSIST_DIR)
    print(f"Vector store saved to: {config.CHROMA_PERSIST_DIR}")
    return vs

def load_vector_store():
    """Load existing store, or auto-build it from knowledge_base/ PDFs."""
    embeddings = OpenAIEmbeddings(model=config.EMBEDDING_MODEL,
                                   openai_api_key=config.OPENAI_API_KEY)
    store_exists = os.path.exists(config.CHROMA_PERSIST_DIR) and \
                   len(os.listdir(config.CHROMA_PERSIST_DIR)) > 0
    if not store_exists:
        print("No vector store found — building from knowledge_base/...")
        docs   = load_documents(config.KNOWLEDGE_BASE_DIR)
        chunks = chunk_documents(docs)
        return build_vector_store(chunks)
    return Chroma(persist_directory=config.CHROMA_PERSIST_DIR,
                  embedding_function=embeddings)

if __name__ == "__main__":
    docs   = load_documents(config.KNOWLEDGE_BASE_DIR)
    chunks = chunk_documents(docs)
    build_vector_store(chunks)
