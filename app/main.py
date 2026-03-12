from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
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
        return {
            "answer": out.get("answer", ""),
            "retrieved": out.get("retrieved", []),
            "customer_signals": out.get("customer_signals", {}),
            "medallia_sentiment": out.get("medallia_sentiment", {}),
            "web_results": out.get("web_results", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
def ui(request: Request):
    graph: Any = getattr(request.app.state, "graph", None)
    startup_error = getattr(request.app.state, "startup_error", None)

    if graph is None:
        return HTMLResponse(
            content=f"Graph not initialized: {startup_error}",
            status_code=503,
        )

    return """
<!DOCTYPE html>
<html>
<head>
    <title>CX Barometer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background: #f6f6f8;
            max-width: 1200px;
            color: #222;
        }

        h1 {
            margin-bottom: 4px;
        }

        .subtitle {
            color: #777;
            margin-bottom: 20px;
        }

        label {
            font-weight: bold;
            display: block;
            margin-top: 10px;
            margin-bottom: 6px;
        }

        input,
        textarea {
            width: 100%;
            padding: 10px;
            margin-bottom: 14px;
            border-radius: 6px;
            border: 1px solid #ccc;
            font-size: 14px;
            box-sizing: border-box;
        }

        button {
            background: #e20074;
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
        }

        button:hover {
            opacity: 0.92;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }

        .card {
            background: white;
            border-radius: 10px;
            padding: 18px;
            border: 1px solid #e2e2e2;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }

        .card h2 {
            margin-top: 0;
            font-size: 18px;
            margin-bottom: 12px;
        }

        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 13px;
            margin: 0;
        }

        .sentiment {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            font-size: 22px;
            font-weight: bold;
            padding: 14px 18px;
            border-radius: 10px;
            margin-bottom: 20px;
            min-width: 220px;
        }

        .sentiment span:first-child {
            font-size: 28px;
        }

        .sentiment.green {
            background: #e8f7ec;
            color: #1f7a3a;
            border: 1px solid #b7e3c4;
        }

        .sentiment.yellow {
            background: #fff8e5;
            color: #8a6d1d;
            border: 1px solid #f5e1a4;
        }

        .sentiment.red {
            background: #fdecea;
            color: #a94442;
            border: 1px solid #f3b6b6;
        }

        .sentiment.unknown {
            background: #f3f3f3;
            color: #555;
            border: 1px solid #ddd;
        }

        .signal-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }

        .signal {
            background: #fafafa;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 10px;
            font-size: 13px;
        }

        .timeline {
            display: grid;
            gap: 10px;
        }

        .timeline-item {
            border-left: 4px solid #e20074;
            padding: 10px 12px;
            background: #fafafa;
            border-radius: 6px;
        }

        .timeline-title {
            font-weight: bold;
            margin-bottom: 4px;
        }

        .muted {
            color: #666;
            font-size: 13px;
        }

        @media (max-width: 900px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .signal-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <h1>CX Barometer</h1>
    <div class="subtitle">Agentic RAG demo for B2B Call Center</div>

    <label for="customer_id">Customer ID</label>
    <input id="customer_id" value="1001" />

    <label for="question">Question</label>
    <textarea id="question" rows="4">What is the customer sentiment and what should the agent focus on?</textarea>

    <button onclick="askQuestion()">Analyze Customer</button>

    <div class="card" style="margin-top: 20px;">
        <h2>Customer Sentiment</h2>
        <div id="sentiment-box" class="sentiment unknown">
            <span id="sentiment-emoji">⚪</span>
            <span id="sentiment-text">Sentiment: Unknown</span>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>Agent Recommendation</h2>
            <pre id="answer"></pre>
        </div>

        <div class="card">
            <h2>Customer Signals</h2>
            <div id="signals" class="signal-grid"></div>
        </div>

        <div class="card">
            <h2>Customer Timeline</h2>
            <div id="timeline" class="timeline"></div>
        </div>

        <div class="card">
            <h2>Medallia Sentiment</h2>
            <pre id="medallia"></pre>
        </div>

        <div class="card">
            <h2>Retrieved Context (RAG)</h2>
            <pre id="retrieved"></pre>
        </div>

        <div class="card">
            <h2>Web Results</h2>
            <pre id="web"></pre>
        </div>
    </div>

    <script>
        function extractSentiment(answerText) {
            if (!answerText) return "Unknown";

            const text = answerText.toLowerCase();

            if (text.includes("sentiment: red")) return "Red";
            if (text.includes("sentiment: yellow")) return "Yellow";
            if (text.includes("sentiment: green")) return "Green";

            return "Unknown";
        }

        function setSentiment(label) {
            const box = document.getElementById("sentiment-box");
            const emoji = document.getElementById("sentiment-emoji");
            const text = document.getElementById("sentiment-text");

            if (!box || !emoji || !text) return;

            box.className = "sentiment";

            if (label === "Red") {
                box.classList.add("red");
                emoji.textContent = "🔴";
                text.textContent = "Sentiment: RED";
            } else if (label === "Yellow") {
                box.classList.add("yellow");
                emoji.textContent = "🟡";
                text.textContent = "Sentiment: YELLOW";
            } else if (label === "Green") {
                box.classList.add("green");
                emoji.textContent = "🟢";
                text.textContent = "Sentiment: GREEN";
            } else {
                box.classList.add("unknown");
                emoji.textContent = "⚪";
                text.textContent = "Sentiment: UNKNOWN";
            }
        }

        function renderSignals(data) {
            const container = document.getElementById("signals");
            if (!container) return;

            container.innerHTML = "";

            const preferredOrder = [
                "company_name",
                "churn_risk",
                "churn_label",
                "medallia_score",
                "open_complaints",
                "recent_outages",
                "ftth_available",
                "network_quality_status",
                "billing_issue_open"
            ];

            preferredOrder.forEach((key) => {
                if (key in data) {
                    const div = document.createElement("div");
                    div.className = "signal";
                    div.innerHTML = "<b>" + key + "</b><br>" + String(data[key]);
                    container.appendChild(div);
                }
            });

            Object.keys(data).forEach((key) => {
                if (!preferredOrder.includes(key) && key !== "notes" && key !== "customer_id") {
                    const div = document.createElement("div");
                    div.className = "signal";
                    div.innerHTML = "<b>" + key + "</b><br>" + String(data[key]);
                    container.appendChild(div);
                }
            });
        }

        function renderTimeline(signals, medallia) {
            const container = document.getElementById("timeline");
            if (!container) return;

            container.innerHTML = "";

            const items = [];

            if (signals.company_name) {
                items.push({
                    title: "Customer",
                    text: signals.company_name
                });
            }

            if (signals.open_complaints !== undefined) {
                items.push({
                    title: "Complaints",
                    text: "Open complaints: " + signals.open_complaints
                });
            }

            if (signals.recent_outages !== undefined) {
                items.push({
                    title: "Recent Outages",
                    text: "Incidents in recent period: " + signals.recent_outages
                });
            }

            if (signals.billing_issue_open !== undefined) {
                items.push({
                    title: "Billing Status",
                    text: signals.billing_issue_open ? "Billing issue is still open" : "No open billing issue"
                });
            }

            if (signals.ftth_available !== undefined) {
                items.push({
                    title: "FTTH Availability",
                    text: signals.ftth_available ? "FTTH available" : "FTTH not yet available"
                });
            }

            if (medallia && medallia.sentiment_label) {
                items.push({
                    title: "Medallia Sentiment",
                    text: "Label: " + medallia.sentiment_label + " | Score: " + medallia.sentiment_score
                });
            }

            if (Array.isArray(signals.notes)) {
                signals.notes.forEach((note, index) => {
                    items.push({
                        title: "Key Note " + (index + 1),
                        text: note
                    });
                });
            }

            if (items.length === 0) {
                container.innerHTML = '<div class="muted">No timeline data available.</div>';
                return;
            }

            items.forEach((item) => {
                const div = document.createElement("div");
                div.className = "timeline-item";
                div.innerHTML =
                    '<div class="timeline-title">' + item.title + '</div>' +
                    '<div>' + item.text + '</div>';
                container.appendChild(div);
            });
        }

        async function askQuestion() {
            try {
                const question = document.getElementById("question").value;
                const customer_id = document.getElementById("customer_id").value;

                const response = await fetch("/ask", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        question: question,
                        customer_id: customer_id
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    alert("Request failed: " + JSON.stringify(data));
                    return;
                }

                const answerText = data.answer || "";
                const signals = data.customer_signals || {};
                const medallia = data.medallia_sentiment || {};
                const retrieved = data.retrieved || [];
                const webResults = data.web_results || [];

                document.getElementById("answer").innerText = answerText;
                document.getElementById("medallia").innerText = JSON.stringify(medallia, null, 2);
                document.getElementById("retrieved").innerText = JSON.stringify(retrieved, null, 2);
                document.getElementById("web").innerText = JSON.stringify(webResults, null, 2);

                renderSignals(signals);
                renderTimeline(signals, medallia);

                const sentiment = extractSentiment(answerText);
                setSentiment(sentiment);
            } catch (err) {
                console.error(err);
                alert("Frontend error: " + err);
            }
        }
    </script>
</body>
</html>
"""