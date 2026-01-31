from threading import Thread

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.services.llm_service import get_llm_service, is_llm_ready
from backend.services.retrieval_service import get_retrieval_service

app = FastAPI(title="LegalEase")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def load_llm() -> None:
    Thread(target=get_llm_service, daemon=True).start()


@app.on_event("startup")
def load_rag_index() -> None:
    get_retrieval_service()

@app.get("/")
def health_check():
    return {"status": "LegalEase backend running"}


@app.get("/llm/ready")
def llm_ready():
    return {"status": "loaded" if is_llm_ready() else "loading"}


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_k: int = Field(3, ge=1, le=20)
    max_new_tokens: int = Field(128, ge=32, le=512)


@app.post("/rag/build")
def rag_build_index():
    retriever = get_retrieval_service()
    try:
        return retriever.build_index()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/rag/search")
def rag_search(request: RagQueryRequest):
    retriever = get_retrieval_service()
    try:
        matches = retriever.search(request.query, top_k=request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"query": request.query, "results": matches}


@app.post("/rag/answer")
def rag_answer(request: RagQueryRequest):
    retriever = get_retrieval_service()
    try:
        matches = retriever.search(request.query, top_k=request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    context_blocks = []
    for idx, item in enumerate(matches, start=1):
        context_blocks.append(
            f"[{idx}] {item.get('text')}\nSource: {item.get('law_name')} §{item.get('section_id')} ({item.get('chunk_id')})"
        )

    context = "\n\n".join(context_blocks)
    prompt = (
        "Answer the question using ONLY the context below. "
        "If the context does not contain the answer, say you don't have enough information. "
        "Do not provide legal advice.\n\n"
        f"Question: {request.query}\n\nContext:\n{context}"
    )

    llm = get_llm_service()
    answer = llm.generate(prompt, max_new_tokens=request.max_new_tokens)
    return {"answer": answer, "sources": matches}
