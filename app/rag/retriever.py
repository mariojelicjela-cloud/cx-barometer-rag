from app.rag.vectordb import get_vstore


def _customer_filter(customer_id: str | None) -> dict | None:
    if not customer_id:
        return None
    # pgvector LangChain uses metadata dicts; "filter" applies server-side when supported.
    return {"customer_id": str(customer_id)}


def get_retriever(db_url: str, customer_id: str | None = None):
    vstore = get_vstore(db_url)
    f = _customer_filter(customer_id)
    search_kwargs = {"k": 5}
    if f is not None:
        search_kwargs["filter"] = f
    return vstore.as_retriever(search_kwargs=search_kwargs)