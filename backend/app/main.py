from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.services.llm_service import get_llm_service
from backend.services.retrieval_service import get_retrieval_service

app = FastAPI(title="LegalEase")


@app.on_event("startup")
def load_llm() -> None:
    get_llm_service()


@app.on_event("startup")
def load_rag_index() -> None:
    get_retrieval_service()

@app.get("/")
def health_check():
    return {"status": "LegalEase backend running"}


@app.get("/llm/ready")
def llm_ready():
    return {"status": "loaded"}


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_k: int = Field(5, ge=1, le=20)
    max_new_tokens: int = Field(256, ge=32, le=1024)


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
