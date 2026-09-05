from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from rag_engine import (
    run_rag_pipeline,
    ingest_faq,
    collection,
    EMBEDDING_MODEL,
    GENERATION_MODEL,
    GUARDRAIL_THRESHOLD,
    DEFAULT_KB_PATH
)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if os.path.exists(DEFAULT_KB_PATH):
            ingest_faq(DEFAULT_KB_PATH)
            print(f"Knowledge base ({DEFAULT_KB_PATH}) ingested successfully.")
        else:
            print(f"{DEFAULT_KB_PATH} not found, skipping startup ingestion.")
    except Exception as e:
        print(f"Startup ingestion note: {e}")
    yield

app = FastAPI(title="OmniDesk Customer Support RAG Agent API", lifespan=lifespan)

# Enable CORS for web frontends (index.html & app.html)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "OmniDesk RAG Backend",
        "vector_count": collection.count() if collection else 0
    }

@app.get("/api/info")
def get_info():
    count = 0
    try:
        count = collection.count()
    except Exception:
        pass
    return {
        "status": "online",
        "collection_name": "support_kb",
        "document_chunks": count,
        "embedding_model": EMBEDDING_MODEL,
        "generation_model": GENERATION_MODEL,
        "guardrail_threshold": GUARDRAIL_THRESHOLD
    }

@app.post("/ask", response_model=QueryResponse)
def ask(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        return run_rag_pipeline(req.query)
    except Exception as e:
        print(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount current directory as static files if accessed directly via backend
if os.path.exists("."):
    try:
        app.mount("/static", StaticFiles(directory=".", html=True), name="static")
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)