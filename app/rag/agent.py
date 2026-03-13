from typing import TypedDict, List, Dict, Any, cast

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from app.settings import settings
from app.rag.retriever import get_retriever
from app.tools.web_search import tavily_search
from app.tools.customer_signals import get_customer_signals

from app.tools.medallia_sentiment import score_medallia_sentiment


class State(TypedDict, total=False):
    question: str
    customer_id: str | None
    retrieved: List[Dict[str, Any]]
    customer_signals: Dict[str, Any]
    medallia_sentiment: Dict[str, Any]
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

    def _question(state: State) -> str:
        q = state.get("question")
        if not q:
            raise ValueError("Missing required 'question' in state")
        return cast(str, q)

    def retrieve_node(state: State) -> State:
        retriever = get_retriever(settings.DATABASE_URL, state.get("customer_id"))
        docs = retriever.get_relevant_documents(_question(state))
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

            company = ""
            signals = state.get("customer_signals", {})

            if signals and "company_name" in signals:
                company = signals["company_name"]

            query = f"{company} Grindhouse j.d.o.o. company Croatia news Poslovna Hrvatska business profile"

            results = tavily_search(query)

            return {"web_results": results}

        return {"web_results": []}

    def medallia_sentiment_node(state: State) -> State:
        customer_id = state.get("customer_id")
        if not customer_id:
            return {"medallia_sentiment": {"error": "No customer_id provided"}}

        sentiment = score_medallia_sentiment(customer_id)
        return {"medallia_sentiment": sentiment}

    def answer_node(state: State) -> State:
        ctx: list[str] = []

        for i, r in enumerate(state.get("retrieved", []), 1):
            ctx.append(f"[RAG {i}] {r['text']}\nMETA: {r['meta']}")

        signals = state.get("customer_signals", {})
        if signals:
            ctx.append(f"[SIGNALS] {signals}")

        medallia_sentiment = state.get("medallia_sentiment", {})
        if medallia_sentiment:
            ctx.append(f"[MEDALLIA_SENTIMENT] {medallia_sentiment}")

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
3. Medallia sentiment scoring
4. Public web context (if available)

Answer grounded ONLY in the provided context. If context is insufficient, say what is missing.

QUESTION:
{_question(state)}

CONTEXT:
{chr(10).join(ctx)}

OUTPUT FORMAT (strict):
Sentiment: <Green|Yellow|Red>

Customer Risk Summary:
<short summary>

Top Talking Points:
1.
2.
3.

Evidence:
- bullets referencing [RAG #], [SIGNALS], [MEDALLIA_SENTIMENT], and if used [WEB #]
"""

        resp = llm.invoke(prompt)
        answer_text = resp.content if isinstance(resp.content, str) else str(resp.content)
        return {"answer": answer_text}

    g = StateGraph(State)

    g.add_node("retrieve", retrieve_node)
    g.add_node("load_customer_signals", customer_signals_node)
    g.add_node("score_medallia_sentiment", medallia_sentiment_node)
    g.add_node("web_search", web_node)
    g.add_node("generate", answer_node)

    g.set_entry_point("retrieve")

    g.add_edge("retrieve", "load_customer_signals")
    g.add_edge("load_customer_signals", "score_medallia_sentiment")
    g.add_edge("load_customer_signals", "web_search")
    g.add_edge("web_search", "generate")
    g.add_edge("generate", END)

    return g.compile()