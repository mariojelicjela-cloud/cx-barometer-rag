from langchain_community.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings

COLLECTION_NAME = "cxbarometer_docs"

def get_vstore(db_url: str) -> PGVector:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    return PGVector(
        connection_string=db_url,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )