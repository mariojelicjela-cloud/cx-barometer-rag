# CX Barometer

CX Barometer is an Agentic RAG prototype for B2B call-center agents.

It combines:
- customer interaction history
- complaints and support context
- structured customer signals
- Medallia-style survey feedback
- public web search

The goal is to provide agents with an instant sentiment and risk view before or during customer interaction.

## Stack

- FastAPI
- LangGraph
- OpenAI
- PGVector / PostgreSQL
- Tavily
- Python

## Features

- Agentic RAG workflow
- Customer-specific retrieval
- Structured customer signals
- Medallia sentiment scoring
- Web search integration
- Evaluation baseline
- Retriever upgrade comparison
- Minimal dashboard UI

## Run locally

1. Start Postgres / pgvector
docker compose -f docker/docker-compose.yml up -d

2. Ingest seed data
python -m app.ingest

3. Run the app
uvicorn app.main:app --reload --port 8000

4. Open in browser
http://127.0.0.1:8000/


Full project write-up is available in:
docs/certification.md