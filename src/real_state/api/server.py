"""
FastAPI server for the PrimeLands RAG system.

Exposes endpoints so the Next.js frontend can send user queries
and receive answers from CAG / RAG / CRAG pipelines.

Run:
    uv run uvicorn real_state.api.server:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


from real_state.infrastructure.llm_provider import get_chat_llm, get_default_embeddings
from real_state.infrastructure.db.vector_db import QdrantStorage
from real_state.application.chat_service.rag_service import RagService
from real_state.application.chat_service.cag_service import CAGService
from real_state.application.chat_service.cag_cache import CAGCache
from real_state.application.chat_service.crag_service import CRAGService
from real_state.config import DATA_DIR


_qdrant: QdrantStorage | None = None
_rag: RagService | None = None
_cag: CAGService | None = None
_crag: CRAGService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize heavy services once at startup."""
    global _qdrant, _rag, _cag, _crag

    print("🚀 Initializing PrimeLands API services...")

    llm = get_chat_llm()
    _qdrant = QdrantStorage()

    _rag = RagService(llm=llm, retriever=_qdrant)

    embedder = get_default_embeddings()
    cache = CAGCache(cache_dir=DATA_DIR / "cache", embedder=embedder)
    _cag = CAGService(rag_service=_rag, cache=cache)

    _crag = CRAGService(retriever=_qdrant, llm=llm)

    print("✅ All services ready")
    yield
    print("👋 Shutting down")


app = FastAPI(
    title="PrimeLands RAG API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    mode: str = Field(default="cag", description="cag | rag | crag")
    strategy: Optional[str] = Field(
        default=None,
        description="Chunking strategy filter: child | fixed | sliding | semantic | late_chunk_base"
    )


class ChatResponse(BaseModel):
    answer: str
    mode_used: str
    strategy_used: Optional[str] = None
    evidence_urls: list[str] = []
    generation_time: float = 0.0
    cache_hit: Optional[bool] = None
    cache_source: Optional[str] = None
    similarity_score: Optional[float] = None
    matched_query: Optional[str] = None
    confidence_initial: Optional[float] = None
    confidence_final: Optional[float] = None
    correction_applied: Optional[bool] = None
    docs_used: Optional[int] = None


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "PrimeLands RAG API"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Process a user query through the selected pipeline.
    
    Modes:
      - cag:  Cache-Augmented Generation (checks FAQ + history cache first)
      - rag:  Standard RAG retrieval + generation
      - crag: Corrective RAG with confidence scoring
    
    Strategy filter (optional):
      child | fixed | sliding | semantic | late_chunk_base
      When set, only vectors with that chunking strategy are retrieved.
    """
    mode = req.mode.lower().strip()
    query = req.query.strip()

    if req.strategy:
        strategy = req.strategy.strip().lower()
    else:
        strategy = None

    try:
        if mode == "cag":
            result = _cag.generate(query, use_cache=True, verbose=False)
            return ChatResponse(
                answer=result["answer"],
                mode_used="cag",
                strategy_used=strategy,
                evidence_urls=result.get("evidence_urls", []),
                generation_time=result.get("generation_time", 0),
                cache_hit=result.get("cache_hit"),
                cache_source=result.get("cache_source"),
                similarity_score=result.get("similarity_score"),
                matched_query=result.get("matched_query"),
            )

        elif mode == "rag":
            if strategy:
                custom_qdrant = QdrantStorage()
                original_search = custom_qdrant.search_chunks
                def filtered_search(query: str, top_k: int = 4, **kwargs):
                    return original_search(query=query, top_k=top_k, strategy_filter=strategy, **kwargs)
                custom_qdrant.search_chunks = filtered_search
                rag = RagService(llm=get_chat_llm(), retriever=custom_qdrant)
            else:
                rag = _rag
            result = rag.generate(query)
            return ChatResponse(
                answer=result["answer"],
                mode_used="rag",
                strategy_used=strategy,
                evidence_urls=result.get("evidence_urls", []),
                generation_time=result.get("generation_time", 0),
                docs_used=result.get("num_docs"),
            )

        elif mode == "crag":
            if strategy:
                custom_qdrant = QdrantStorage()
                original_search = custom_qdrant.search_chunks
                def filtered_search_crag(query: str, top_k: int = 4, **kwargs):
                    return original_search(query=query, top_k=top_k, strategy_filter=strategy, **kwargs)
                custom_qdrant.search_chunks = filtered_search_crag
                crag = CRAGService(retriever=custom_qdrant, llm=get_chat_llm())
            else:
                crag = _crag
            result = crag.generate(query, verbose=False)
            return ChatResponse(
                answer=result["answer"],
                mode_used="crag",
                strategy_used=strategy,
                evidence_urls=result.get("evidence_urls", []),
                generation_time=result.get("generation_time", 0),
                confidence_initial=result.get("confidence_initial"),
                confidence_final=result.get("confidence_final"),
                correction_applied=result.get("correction_applied"),
                docs_used=result.get("docs_used"),
            )

        else:
            raise HTTPException(status_code=400, detail=f"Unknown mode: {mode}. Use cag, rag, or crag.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
def stats():
    """Return CAG cache stats."""
    if _cag:
        return _cag.cache_stats()
    return {"error": "CAG service not initialized"}

