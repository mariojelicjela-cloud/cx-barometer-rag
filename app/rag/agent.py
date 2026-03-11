from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from app.settings import settings
from app.rag.retriever import get_retriever
from app.tools.web_search import tavily_search
from app.tools.customer_signals import get_customer_signals


class State(TypedDict, total=False):
    question: str
    customer_id: str | None
    retrieved: List[Dict[str, Any]]
    customer_signals: Dict[str, Any]
    web_results: List[Dict[str, Any]]
    answer: str


def should_use_web_search(question: str) -> bool:
    q = question.lower()
    triggers = [
        "news",
        "media",
        "public",
        "press",
        "article",
        "announcement",
        "objava",
        "mediji",
        "javno",
    ]
    return any(word in q for word in triggers)


def build_graph():
    llm = ChatOpenAI(
        model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.2,
    )
    retriever = get_retriever(settings.DATABASE_URL)

    def retrieve_node(state: State) -> State:
        docs = retriever.get_relevant_documents(state["question"])
        retrieved = [{"text": d.page_content, "meta": d.metadata} for d in docs]
        return {"retrieved": retrieved}

    def customer_signals_node(state: State) -> State:
        customer_id = state.get("customer_id")
        if not customer_id:
            return {"customer_signals": {"error": "No customer_id provided"}}

        signals = get_customer_signals(customer_id)
        return {"customer_signals": signals}

    def web_node(state: State) -> State:
        if should_use_web_search(state["question"]):
            results = tavily_search(state["question"])
            return {"web_results": results}
        return {"web_results": []}

    def answer_node(state: State) -> State:
        ctx = []

        for i, r in enumerate(state.get("retrieved", []), 1):
            ctx.append(f"[RAG {i}] {r['text']}\nMETA: {r['meta']}")

        signals = state.get("customer_signals", {})
        if signals:
            ctx.append(f"[SIGNALS] {signals}")

        for i, w in enumerate(state.get("web_results", []), 1):
            ctx.append(
                f"[WEB {i}] {w['title']}\n"
                f"URL: {w['url']}\n"
                f"CONTENT: {w['content']}"
            )

        prompt = f"""You are CX Barometer assistant for a B2B call-center agent.

Your job is to combine:
1. Retrieved customer interaction context
2. Structured customer signals
3. Public web context (if available)

Answer grounded ONLY in the provided context. If context is insufficient, say what is missing.

QUESTION:
{state['question']}

CONTEXT:
{chr(10).join(ctx)}

OUTPUT:
- Sentiment (Green/Yellow/Red) + 1-line rationale
- Customer risk summary
- Top 3 talking points for the agent
- Evidence bullets referencing [RAG #], [SIGNALS], and if used [WEB #]
"""

        resp = llm.invoke(prompt)
        return {"answer": resp.content}

    g = StateGraph(State)

    g.add_node("retrieve", retrieve_node)
    g.add_node("load_customer_signals", customer_signals_node)
    g.add_node("web_search", web_node)
    g.add_node("generate", answer_node)

    g.set_entry_point("retrieve")

    g.add_edge("retrieve", "load_customer_signals")
    g.add_edge("load_customer_signals", "web_search")
    g.add_edge("web_search", "generate")
    g.add_edge("generate", END)

    return g.compile()