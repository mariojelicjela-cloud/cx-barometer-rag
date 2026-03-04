from fastapi import FastAPI
from pydantic import BaseModel
from app.rag.agent import build_graph

graph = build_graph()

app = FastAPI(title="CX Barometer (Prototype)")

class AskRequest(BaseModel):
    question: str
    customer_id: str | None = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
async def ask(req: AskRequest):
    out = await graph.ainvoke({"question": req.question, "customer_id": req.customer_id})
    return {"answer": out.get("answer", "")}