from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from app.settings import settings
from app.rag.retriever import get_retriever

class State(TypedDict, total=False):
    question: str
    customer_id: str | None
    retrieved: List[Dict[str, Any]]
    answer: str

def build_graph():
    llm = ChatOpenAI(model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2)
    retriever = get_retriever(settings.DATABASE_URL)

    def retrieve_node(state: State) -> State:
        docs = retriever.get_relevant_documents(state["question"])
        retrieved = [{"text": d.page_content, "meta": d.metadata} for d in docs]
        return {"retrieved": retrieved}

    def answer_node(state: State) -> State:
        ctx = []
        for i, r in enumerate(state.get("retrieved", []), 1):
            ctx.append(f"[RAG {i}] {r['text']}\nMETA: {r['meta']}")

        prompt = f"""You are CX Barometer assistant for a B2B call-center agent.
Answer grounded ONLY in the provided context. If context is insufficient, say what is missing.

QUESTION:
{state['question']}

CONTEXT:
{chr(10).join(ctx)}

OUTPUT:
- Sentiment (Green/Yellow/Red) + 1-line rationale
- Top 3 talking points for the agent
- Evidence bullets referencing [RAG #]
"""
        resp = llm.invoke(prompt)
        return {"answer": resp.content}

    g = StateGraph(State)
    g.add_node("retrieve", retrieve_node)
    g.add_node("generate", answer_node)
    g.set_entry_point("retrieve")
    g.add_edge("retrieve", "generate")
    g.add_edge("generate", END)
    return g.compile()