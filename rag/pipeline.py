from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from ingestion.loader import load_vector_store
from rag.prompts import SYSTEM_PROMPT, USER_TEMPLATE
from utils.cost_tracker import log_usage, get_total_cost
import config

COMPLEX_KEYWORDS = ["permit", "legal", "law", "regulation", "article", "penalty", "fine", "court"]

def is_complex_query(question):
    return any(kw in question.lower() for kw in COMPLEX_KEYWORDS)

def build_rag_chain(premium=False):
    vector_store = load_vector_store()
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": config.TOP_K_RESULTS})
    model = config.LLM_MODEL_PREMIUM if premium else config.LLM_MODEL_DEFAULT
    llm = ChatOpenAI(model=model, openai_api_key=config.OPENAI_API_KEY, temperature=0.2)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(USER_TEMPLATE)
    ])
    chain = RetrievalQA.from_chain_type(
        llm=llm, retriever=retriever, chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}, return_source_documents=True
    )
    return chain, model

def ask(chain, question, model):
    result = chain.invoke({"query": question})
    answer = result["result"]
    sources = list({doc.metadata.get("source", "Unknown") for doc in result["source_documents"]})
    input_est = len(question) // 4
    output_est = len(answer) // 4
    cost = log_usage(model, input_est, output_est, question)
    return {"answer": answer, "sources": sources, "model_used": model,
            "query_cost_usd": round(cost, 5), "total_cost_usd": get_total_cost()}
