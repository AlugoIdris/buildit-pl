from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ingestion.loader import load_vector_store
from rag.prompts import SYSTEM_PROMPT, USER_TEMPLATE
from utils.cost_tracker import log_usage, get_total_cost
import config

COMPLEX_KEYWORDS = ["permit", "legal", "law", "regulation", "article", "penalty", "fine", "court"]

def is_complex_query(question):
    return any(kw in question.lower() for kw in COMPLEX_KEYWORDS)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def build_rag_chain(premium=False):
    vector_store = load_vector_store()
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": config.TOP_K_RESULTS})
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

def ask(chain_tuple, question, model):
    chain, retriever, _ = chain_tuple
    
    # Get the answer
    answer = chain.invoke(question)
    
    # Get source documents separately
    source_docs = retriever.get_relevant_documents(question)
    sources = list({doc.metadata.get("source", "Unknown") for doc in source_docs})
    
    input_est = len(question) // 4
    output_est = len(answer) // 4
    cost = log_usage(model, input_est, output_est, question)
    return {"answer": answer, "sources": sources, "model_used": model,
            "query_cost_usd": round(cost, 5), "total_cost_usd": get_total_cost()}
