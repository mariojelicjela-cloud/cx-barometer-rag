from pathlib import Path
from app.settings import settings
from app.rag.vectordb import get_vstore
from app.rag.chunking import split_unstructured

def run():
    vstore = get_vstore(settings.DATABASE_URL)

    seed_dir = Path("data/seed")
    seed_dir.mkdir(parents=True, exist_ok=True)

    docs = []
    for p in list(seed_dir.glob("*.md")) + list(seed_dir.glob("*.txt")):
        text = p.read_text(encoding="utf-8")
        docs.extend(split_unstructured(text, {"source": p.suffix.lstrip("."), "path": str(p)}))

    if not docs:
        print("No seed docs found in data/seed.")
        return

    vstore.add_texts([d.text for d in docs], metadatas=[d.metadata for d in docs])
    print(f"Ingested {len(docs)} chunks into pgvector.")

if __name__ == "__main__":
    run()