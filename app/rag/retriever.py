from app.rag.vectordb import get_vstore

def get_retriever(db_url: str):
    vstore = get_vstore(db_url)
    return vstore.as_retriever(search_kwargs={"k": 5})