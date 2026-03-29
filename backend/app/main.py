from threading import Thread
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.db import Base, engine, get_db
from backend.app.models import Chat, Message, Session as AuthSession, User
from backend.app.security import hash_password, verify_password
from backend.services.llm_service import (
    get_llm_service,
    get_llm_info,
    is_llm_ready,
    is_llm_enabled,
)
from backend.services.retrieval_service import get_retrieval_service

try:  # Optional local env loading
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

app = FastAPI(title="LegalEase")
logger = logging.getLogger("uvicorn.error")

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "legalease_session")
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "168"))
HISTORY_LIMIT = 6

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5177",
        "http://localhost:5178",
        "http://127.0.0.1:5178",
        "http://localhost:5179",
        "http://127.0.0.1:5179",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    error_id = secrets.token_hex(6)
    logger.exception("Unhandled error %s on %s %s", error_id, request.method, request.url.path)
    return Response(
        content=f"Internal Server Error (id={error_id}): {type(exc).__name__}: {exc}",
        status_code=500,
        media_type="text/plain",
    )


@app.on_event("startup")
def load_llm() -> None:
    if not is_llm_enabled():
        raise RuntimeError("LLM is disabled. Set LLM_ENABLED=1.")
    if os.getenv("LLM_PRELOAD", "1") != "1":
        raise RuntimeError("LLM_PRELOAD=0 prevents LLM startup.")
    get_llm_service()


@app.on_event("startup")
def load_rag_index() -> None:
    if os.getenv("RAG_PRELOAD", "1") != "1":
        raise RuntimeError("RAG_PRELOAD=0 prevents RAG startup.")
    service = get_retrieval_service()
    service.preload()


@app.on_event("startup")
def init_database() -> None:
    Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check():
    return {"status": "LegalEase backend running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database unavailable: {exc}") from exc


@app.get("/llm/ready")
def llm_ready():
    if not is_llm_enabled():
        return {"status": "disabled"}
    return {"status": "loaded" if is_llm_ready() else "loading"}


@app.get("/llm/info")
def llm_info():
    return get_llm_info()


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_k: int = Field(2, ge=1, le=10)
    max_new_tokens: int = Field(96, ge=32, le=512)
    language: str = Field("en", pattern="^(en|ur)$")
    history: Optional[List[ChatTurn]] = None
    chat_id: Optional[str] = None


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class ChatCreateRequest(BaseModel):
    title: Optional[str] = "New chat"


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    language: Optional[str]
    created_at: datetime


class ChatResponse(BaseModel):
    id: str
    title: str
    updated_at: datetime


def _contains_urdu(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))


async def _translate_to_urdu(llm, english_text: str, max_new_tokens: int) -> str:
    translate_prompt = (
        "Translate the answer below into clear, natural Urdu. "
        "Use Urdu script only, no English or Roman Urdu. "
        "Keep it short (4-6 sentences) and easy to read.\n\n"
        f"Answer:\n{english_text}"
    )
    urdu = await llm.generate(translate_prompt, max_new_tokens=max_new_tokens)
    if _contains_urdu(urdu):
        return urdu

    stricter_prompt = (
        "صرف اردو میں جواب دیں۔ انگریزی یا رومن اردو استعمال نہ کریں۔ "
        "جواب مختصر اور واضح رکھیں (زیادہ سے زیادہ 5 جملے).\n\n"
        f"Answer:\n{english_text}"
    )
    return await llm.generate(stricter_prompt, max_new_tokens=max_new_tokens)


def _format_history(history: Optional[List[ChatTurn]], max_turns: int = 4) -> str:
    if not history:
        return ""
    recent = history[-max_turns:]
    lines = []
    for turn in recent:
        label = "User" if turn.role == "user" else "Assistant"
        lines.append(f"{label}: {turn.content}")
    return "\n".join(lines)


def _create_session(db: Session, user_id: str) -> str:
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)
    db.add(AuthSession(id=session_id, user_id=user_id, expires_at=expires_at))
    db.commit()
    return session_id


def _get_user_for_session(db: Session, session_id: str) -> Optional[User]:
    session = db.query(AuthSession).filter(AuthSession.id == session_id).first()
    if session is None:
        return None
    if session.expires_at <= datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        return None
    return db.query(User).filter(User.id == session.user_id).first()


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None
    return _get_user_for_session(db, session_id)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user_optional(request, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def _serialize_chat(chat: Chat) -> ChatResponse:
    return ChatResponse(id=chat.id, title=chat.title, updated_at=chat.updated_at)


def _serialize_message(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        language=message.language,
        created_at=message.created_at,
    )


def _load_chat_history(db: Session, chat_id: str, limit: int = HISTORY_LIMIT) -> List[ChatTurn]:
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    messages.reverse()
    return [ChatTurn(role=message.role, content=message.content) for message in messages]


@app.post("/auth/signup")
def signup(request: SignupRequest, response: Response, db: Session = Depends(get_db)):
    try:
        existing = db.query(User).filter(User.email == request.email).first()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = User(name=request.name, email=request.email, password_hash=hash_password(request.password))
        db.add(user)
        db.commit()
        db.refresh(user)

        session_id = _create_session(db, user.id)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            samesite="lax",
        )
        return {"user": {"id": user.id, "name": user.name, "email": user.email}}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Signup failed")
        detail = f"Signup failed: {type(exc).__name__}"
        if str(exc):
            detail = f"{detail}: {exc}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from exc


@app.post("/auth/login")
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    session_id = _create_session(db, user.id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return {"user": {"id": user.id, "name": user.name, "email": user.email}}


@app.post("/auth/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        db.query(AuthSession).filter(AuthSession.id == session_id).delete()
        db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"status": "ok"}


@app.get("/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {"user": {"id": current_user.id, "name": current_user.name, "email": current_user.email}}


@app.get("/chats")
def list_chats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id)
        .order_by(Chat.updated_at.desc())
        .all()
    )
    return {"chats": [_serialize_chat(chat) for chat in chats]}


@app.post("/chats")
def create_chat(
    request: ChatCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = Chat(user_id=current_user.id, title=request.title or "New chat")
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return {"chat": _serialize_chat(chat)}


@app.get("/chats/{chat_id}")
def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return {
        "chat": _serialize_chat(chat),
        "messages": [_serialize_message(message) for message in messages],
    }


@app.delete("/chats/{chat_id}")
def delete_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    db.delete(chat)
    db.commit()
    return {"status": "deleted"}


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
async def rag_answer(
    request: RagQueryRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    try:
        if not is_llm_enabled():
            raise HTTPException(status_code=503, detail="LLM is disabled")
        chat = None
        history = request.history
        if request.chat_id:
            if current_user is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
            chat = (
                db.query(Chat)
                .filter(Chat.id == request.chat_id, Chat.user_id == current_user.id)
                .first()
            )
            if chat is None:
                raise HTTPException(status_code=404, detail="Chat not found")
            history = _load_chat_history(db, request.chat_id)

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
        history_block = _format_history(history)
        history_prompt = ""
        if history_block:
            history_prompt = f"Conversation so far:\n{history_block}\n\n"
        base_prompt = (
            "Answer the question using ONLY the context below. "
            "If the context does not contain the answer, say you don't have enough information. "
            "Do not provide legal advice. "
            "Respond ONLY in English. Do not use Urdu.\n\n"
            f"{history_prompt}Question: {request.query}\n\nContext:\n{context}"
        )

        llm = get_llm_service()
        answer = await llm.generate(base_prompt, max_new_tokens=request.max_new_tokens)

        if request.language == "ur":
            answer = await _translate_to_urdu(llm, answer, request.max_new_tokens)
        elif request.language == "en" and _contains_urdu(answer):
            translate_prompt = (
                "Translate the answer below into English. "
                "Respond ONLY in English. Do not use Urdu.\n\n"
                f"Answer:\n{answer}"
            )
            answer = await llm.generate(translate_prompt, max_new_tokens=request.max_new_tokens)
        if chat is not None:
            user_message = Message(
                chat_id=chat.id,
                role="user",
                content=request.query,
                language=request.language,
            )
            assistant_message = Message(
                chat_id=chat.id,
                role="assistant",
                content=answer,
                language=request.language,
            )
            if chat.title == "New chat":
                chat.title = request.query[:60]
            chat.updated_at = datetime.utcnow()
            db.add_all([user_message, assistant_message, chat])
            db.commit()
        return {
            "answer": answer,
            "sources": matches,
            "language": request.language,
            "chat_title": chat.title if chat is not None else None,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("RAG answer failed")
        detail = f"RAG answer failed: {type(exc).__name__}"
        if str(exc):
            detail = f"{detail}: {exc}"
        raise HTTPException(status_code=500, detail=detail) from exc
