from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="CX Barometer (Prototype)")

class AskRequest(BaseModel):
    question: str
    customer_id: str | None = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
async def ask(req: AskRequest):
    #  kasnije ovdje ubacimo LangGraph Agentic RAG
    return {
        "answer": f"Stub: received question='{req.question}' (customer_id={req.customer_id})",
    }