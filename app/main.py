from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from app.rag.agent import build_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = None
    app.state.startup_error = None

    try:
        app.state.graph = build_graph()
    except Exception as e:
        app.state.graph = None
        app.state.startup_error = str(e)
        print(f"STARTUP ERROR: {app.state.startup_error}")

    yield


app = FastAPI(title="CX Barometer (Prototype)", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str
    customer_id: str | None = None


@app.get("/health")
def health(request: Request):
    graph = getattr(request.app.state, "graph", None)
    startup_error = getattr(request.app.state, "startup_error", None)

    return {
        "status": "ok" if graph is not None else "degraded",
        "graph_initialized": graph is not None,
        "startup_error": startup_error,
    }


@app.post("/ask")
async def ask(req: AskRequest, request: Request):
    graph: Any = getattr(request.app.state, "graph", None)
    startup_error = getattr(request.app.state, "startup_error", None)

    if graph is None:
        raise HTTPException(
            status_code=503,
            detail=f"Graph not initialized: {startup_error}",
        )

    try:
        out = await graph.ainvoke(
            {
                "question": req.question,
                "customer_id": req.customer_id,
            }
        )
        return {"answer": out.get("answer", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))