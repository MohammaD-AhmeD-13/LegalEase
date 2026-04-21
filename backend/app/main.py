from threading import Thread
import base64
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Literal, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.db import Base, engine, get_db
from backend.app.models import Chat, DocumentBadge, Message, Session as AuthSession, User
from backend.app.security import hash_password, verify_password
from backend.services.llm_service import (
    get_llm_service,
    get_llm_info,
    is_llm_ready,
    is_llm_enabled,
)
from backend.services.document_templates import (
    list_templates,
    render_template,
    render_html_document,
    render_pdf_from_html,
)
from backend.services.ocr_service import extract_text
from backend.services.retrieval_service import get_retrieval_service
from backend.services.risk_engine import analyze_risks
from backend.services.translation_service import translate_to_english, translate_to_urdu, translate_text

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
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
REFERRAL_SCORE_THRESHOLD = float(os.getenv("REFERRAL_SCORE_THRESHOLD", "0.2"))

EXPLICIT_REFERRAL_PATTERNS = [
    r"\bneed\s+(a\s+)?lawyer\b",
    r"\bneed\s+(an\s+)?expert\b",
    r"\bconsult\s+(a\s+)?lawyer\b",
    r"\bspeak\s+to\s+(a\s+)?lawyer\b",
    r"\bprofessional\s+help\b",
    r"\bescalate\b",
]

OUT_OF_SCOPE_PATTERNS = [
    r"outside\s+scope",
    r"cannot\s+advise",
    r"not\s+qualified",
    r"beyond\s+jurisdiction",
    r"consult\s+.*lawyer",
]

EXPERT_REFERRALS: Dict[str, Dict[str, str]] = {
    "Business / Corporate Law": {
        "name": "Ayesha Khan",
        "title": "Corporate Lawyer",
        "experience": "7 years",
        "domain": "Business / Corporate Law",
        "email": "ayesha.khan@legalease.pk",
        "photo_url": "",
    },
    "Contract Law": {
        "name": "Bilal Siddiqui",
        "title": "Contracts Specialist",
        "experience": "9 years",
        "domain": "Contract Law",
        "email": "bilal.siddiqui@legalease.pk",
        "photo_url": "",
    },
    "Tax Law": {
        "name": "Sara Malik",
        "title": "Tax & Compliance Counsel",
        "experience": "8 years",
        "domain": "Tax Law",
        "email": "sara.malik@legalease.pk",
        "photo_url": "",
    },
    "Employment / Labour Law": {
        "name": "Hassan Raza",
        "title": "Labour Law Advocate",
        "experience": "6 years",
        "domain": "Employment / Labour Law",
        "email": "hassan.raza@legalease.pk",
        "photo_url": "",
    },
    "General": {
        "name": "Amina Noor",
        "title": "Legal Advisor",
        "experience": "10 years",
        "domain": "General Legal",
        "email": "amina.noor@legalease.pk",
        "photo_url": "",
    },
}

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


class TranslatedMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    language: Optional[str]
    created_at: datetime
    translated_content: Optional[str] = None


class ChatResponse(BaseModel):
    id: str
    title: str
    updated_at: datetime


class RiskyClause(BaseModel):
    clause: str
    severity: Literal["High", "Medium", "Low"]
    reason: str


class ComplianceIssue(BaseModel):
    issue: str
    reason: str


class DocumentReviewResponse(BaseModel):
    risky_clauses: List[RiskyClause]
    compliance_issues: List[ComplianceIssue]
    recommendations: List[str]


class DocumentSummaryResponse(BaseModel):
    summary: str
    language: str


class TemplateField(BaseModel):
    key: str
    label: str
    required: bool
    placeholder: Optional[str] = None
    default: Optional[str] = None


class TemplateSummary(BaseModel):
    id: str
    name: str
    description: str
    fields: List[TemplateField]


class DocumentGenerateRequest(BaseModel):
    template_id: str = Field(..., min_length=2)
    fields: Dict[str, str]
    language: str = Field("en", pattern="^(en|ur)$")
    polish_with_llm: bool = False
    include_pdf: bool = False
    chat_id: Optional[str] = None


class DocumentGenerateResponse(BaseModel):
    title: str
    content: str
    language: str
    pdf_base64: Optional[str] = None
    filename: Optional[str] = None


class DocumentPdfRequest(BaseModel):
    title: str = Field(..., min_length=2)
    content: str = Field(..., min_length=1)


class DocumentPdfResponse(BaseModel):
    pdf_base64: str
    filename: str


class DocumentBadgeResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    chat_id: Optional[str] = None


def _contains_urdu(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))



def _format_history(history: Optional[List[ChatTurn]], max_turns: int = 4) -> str:
    if not history:
        return ""
    recent = history[-max_turns:]
    lines = []
    for turn in recent:
        label = "User" if turn.role == "user" else "Assistant"
        lines.append(f"{label}: {turn.content}")
    return "\n".join(lines)


def _clean_summary_output(text: str) -> str:
    lines = [line.strip() for line in (text or "").splitlines()]
    cleaned = []
    seen_summary = False
    for line in lines:
        if not line:
            cleaned.append("")
            continue
        if line.strip("-").strip() == "":
            continue
        lowered = line.lower()
        if lowered == "summary:":
            if seen_summary:
                continue
            seen_summary = True
        cleaned.append(line)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    return "\n".join(cleaned)


def _ensure_summary_heading(summary: str) -> str:
    trimmed = (summary or "").strip()
    if not trimmed:
        return "Summary:\nNo summary returned."
    lines = [line.strip() for line in trimmed.splitlines()]
    cleaned = []
    summary_seen = False
    for line in lines:
        if line.lower() == "summary:":
            if summary_seen:
                continue
            summary_seen = True
            cleaned.append("Summary:")
            continue
        cleaned.append(line)
    if not summary_seen:
        return f"Summary:\n{chr(10).join(cleaned).strip()}"
    return "\n".join(cleaned).strip()


def _format_review_message(filename: str, review: DocumentReviewResponse) -> str:
    lines = []
    lines.append(f"Document review: {filename}")
    lines.append("")
    lines.append("Risky clauses:")
    if review.risky_clauses:
        for index, item in enumerate(review.risky_clauses, start=1):
            severity = (item.severity or "Medium").upper()
            lines.append(f"{index}. [{severity}] {item.reason}")
            lines.append(f"   Clause: {item.clause}")
    else:
        lines.append("- No risky clauses found.")
    lines.append("")
    lines.append("Compliance issues:")
    if review.compliance_issues:
        for issue in review.compliance_issues:
            lines.append(f"- {issue.issue}: {issue.reason}")
    else:
        lines.append("- None flagged.")
    lines.append("")
    lines.append("Recommendations:")
    if review.recommendations:
        for item in review.recommendations:
            lines.append(f"- {item}")
    else:
        lines.append("- None provided.")
    return "\n".join(lines)


def _validate_upload(filename: str) -> None:
    if not filename:
        raise HTTPException(status_code=400, detail="File name is missing")
    lower = filename.lower()
    if not (lower.endswith(".pdf") or lower.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")


def _ensure_size_limit(size_bytes: int) -> None:
    limit = MAX_FILE_SIZE_MB * 1024 * 1024
    if size_bytes > limit:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit")


def _normalize_list(values: object) -> List[str]:
    if not isinstance(values, list):
        return []
    return [str(item) for item in values if item]


def _normalize_clauses(values: object) -> List[RiskyClause]:
    if not isinstance(values, list):
        return []
    normalized = []
    for item in values:
        if not isinstance(item, dict):
            continue
        severity = str(item.get("severity", "Medium")).capitalize()
        if severity not in {"High", "Medium", "Low"}:
            severity = "Medium"
        normalized.append(
            RiskyClause(
                clause=str(item.get("clause", "")).strip(),
                severity=severity,
                reason=str(item.get("reason", "")).strip(),
            )
        )
    return normalized


def _normalize_issues(values: object) -> List[ComplianceIssue]:
    if not isinstance(values, list):
        return []
    normalized = []
    for item in values:
        if not isinstance(item, dict):
            continue
        normalized.append(
            ComplianceIssue(
                issue=str(item.get("issue", "")).strip(),
                reason=str(item.get("reason", "")).strip(),
            )
        )
    return normalized


def _needs_referral(matches: List[dict], answer: str, query: str = "") -> bool:
    lowered_query = (query or "").lower()
    for pattern in EXPLICIT_REFERRAL_PATTERNS:
        if re.search(pattern, lowered_query):
            return True
    if not matches:
        return True
    top_score = matches[0].get("score") or 0.0
    if top_score < REFERRAL_SCORE_THRESHOLD:
        return True
    lowered = (answer or "").lower()
    if "don't have enough information" in lowered or "do not have enough information" in lowered:
        return True
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, lowered):
            return True
    return False


def _select_referral(matches: List[dict]) -> Dict[str, str]:
    domain_counts: Dict[str, int] = {}
    for item in matches:
        domain = str(item.get("domain") or "").strip()
        if not domain:
            continue
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    if domain_counts:
        best_domain = max(domain_counts.items(), key=lambda pair: pair[1])[0]
        if best_domain in EXPERT_REFERRALS:
            return EXPERT_REFERRALS[best_domain]
    return EXPERT_REFERRALS["General"]


def _referral_intro(language: str) -> str:
    if language == "ur":
        return "میں یہاں مکمل مدد نہیں کر سکتا، لیکن میں آپ کو ایک قانونی ماہر سے جوڑ سکتا ہوں۔"
    return "I'm not able to fully help here, but I can refer you to a legal expert."


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


def _serialize_translated_message(message: Message, translated_content: Optional[str]) -> TranslatedMessageResponse:
    return TranslatedMessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        language=message.language,
        created_at=message.created_at,
        translated_content=translated_content,
    )


def _serialize_document_badge(badge: DocumentBadge) -> DocumentBadgeResponse:
    return DocumentBadgeResponse(
        id=badge.id,
        title=badge.title,
        created_at=badge.created_at,
        chat_id=badge.chat_id,
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


@app.post("/documents/review", response_model=DocumentReviewResponse)
async def review_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    chat_id: Optional[str] = Form(None),
):
    _validate_upload(file.filename)
    data = await file.read()
    _ensure_size_limit(len(data))

    text = extract_text(file.filename, data)
    if not text:
        raise HTTPException(status_code=400, detail="Unable to extract text from the document")
    if not is_llm_enabled():
        raise HTTPException(status_code=503, detail="LLM is disabled")

    llm = get_llm_service()
    analysis = await analyze_risks(text, llm)
    response = DocumentReviewResponse(
        risky_clauses=_normalize_clauses(analysis.get("risky_clauses")),
        compliance_issues=_normalize_issues(analysis.get("compliance_issues")),
        recommendations=_normalize_list(analysis.get("recommendations")),
    )
    if chat_id:
        chat = (
            db.query(Chat)
            .filter(Chat.id == chat_id, Chat.user_id == current_user.id)
            .first()
        )
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        user_message = Message(
            chat_id=chat.id,
            role="user",
            content=f"Uploaded document: {file.filename}",
            language="en",
        )
        assistant_message = Message(
            chat_id=chat.id,
            role="assistant",
            content=_format_review_message(file.filename or "document", response),
            language="en",
        )
        if chat.title == "New chat":
            chat.title = f"Document Review: {(file.filename or 'document')[:60]}"
        chat.updated_at = datetime.utcnow()
        db.add_all([user_message, assistant_message, chat])
        db.commit()
    return response


@app.post("/documents/summarize", response_model=DocumentSummaryResponse)
async def summarize_document(
    file: UploadFile = File(...),
    language: str = Form("en"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    chat_id: Optional[str] = Form(None),
):
    _validate_upload(file.filename)
    data = await file.read()
    _ensure_size_limit(len(data))

    text = extract_text(file.filename, data)
    if not text:
        raise HTTPException(status_code=400, detail="Unable to extract text from the document")
    if language not in {"en", "ur"}:
        raise HTTPException(status_code=400, detail="Language must be 'en' or 'ur'")
    if not is_llm_enabled():
        raise HTTPException(status_code=503, detail="LLM is disabled")

    excerpt = text.strip()[:12000]
    prompt = (
        "You are a legal assistant for Pakistan. "
        "Explain the document below in simple, plain language for a non-expert. "
        "Focus on: parties, obligations, payments, deadlines, termination, penalties, and key risks. "
        "Do not provide legal advice. Use short paragraphs and '-' bullets. "
        "Format the response with these headings in order (no duplicates): "
        "Summary:, Key Clauses:, Key Risks:. "
        "Summary should be 2-4 sentences. "
        "Key Clauses and Key Risks should be bullet lists. "
        "Omit empty sections. End with a complete sentence (no truncation).\n\n"
        f"Document excerpt:\n{excerpt}"
    )
    llm = get_llm_service()
    summary = await llm.generate(prompt, max_new_tokens=384)

    response_language = language
    if language == "ur":
        summary = translate_to_urdu(summary)
        if not _contains_urdu(summary):
            response_language = "en"
    elif language == "en" and _contains_urdu(summary):
        summary = translate_to_english(summary)

    summary = _clean_summary_output(summary)
    response = DocumentSummaryResponse(summary=summary, language=response_language)
    if chat_id:
        chat = (
            db.query(Chat)
            .filter(Chat.id == chat_id, Chat.user_id == current_user.id)
            .first()
        )
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        user_message = Message(
            chat_id=chat.id,
            role="user",
            content=f"Summarize document: {file.filename}",
            language=language,
        )
        assistant_message = Message(
            chat_id=chat.id,
            role="assistant",
            content=_ensure_summary_heading(response.summary),
            language=response.language,
        )
        if chat.title == "New chat":
            chat.title = f"Document Summary: {(file.filename or 'document')[:60]}"
        chat.updated_at = datetime.utcnow()
        db.add_all([user_message, assistant_message, chat])
        db.commit()
    return response


@app.get("/documents/templates", response_model=List[TemplateSummary])
def get_document_templates(current_user: User = Depends(get_current_user)):
    return list_templates()


@app.get("/documents/badges", response_model=List[DocumentBadgeResponse])
def list_document_badges(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    badges = (
        db.query(DocumentBadge)
        .filter(DocumentBadge.user_id == current_user.id)
        .order_by(DocumentBadge.created_at.desc())
        .all()
    )
    return [_serialize_document_badge(badge) for badge in badges]


@app.post("/documents/generate", response_model=DocumentGenerateResponse)
async def generate_document(
    request: DocumentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        title, content = render_template(request.template_id, request.fields)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if request.polish_with_llm:
        if not is_llm_enabled():
            raise HTTPException(status_code=503, detail="LLM is disabled")
        llm = get_llm_service()
        polish_prompt = (
            "Improve clarity and consistency of the document below without adding, removing, or reordering clauses. "
            "Preserve headings and line breaks. Do not add legal advice. Respond ONLY in English.\n\n"
            f"Document:\n{content}"
        )
        content = await llm.generate(polish_prompt, max_new_tokens=512)

    response_language = "en" if request.language == "ur" else request.language

    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", title).strip("_") or "document"
    filename = f"{safe_name}.pdf"
    pdf_base64 = None
    if request.include_pdf:
        try:
            html = render_html_document(title, content)
            pdf_bytes = render_pdf_from_html(html)
            pdf_base64 = base64.b64encode(pdf_bytes).decode("ascii")
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    if request.chat_id:
        chat = (
            db.query(Chat)
            .filter(Chat.id == request.chat_id, Chat.user_id == current_user.id)
            .first()
        )
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        user_message = Message(
            chat_id=chat.id,
            role="user",
            content=f"Generate document: {title}",
            language=request.language,
        )
        assistant_message = Message(
            chat_id=chat.id,
            role="assistant",
            content=content,
            language=request.language,
        )
        if chat.title == "New chat":
            chat.title = title[:60]
        chat.updated_at = datetime.utcnow()
        badge = DocumentBadge(user_id=current_user.id, title=title, chat_id=request.chat_id)
        db.add_all([user_message, assistant_message, chat, badge])
        db.commit()
    else:
        badge = DocumentBadge(user_id=current_user.id, title=title, chat_id=request.chat_id)
        db.add(badge)
        db.commit()

    return DocumentGenerateResponse(
        title=title,
        content=content,
        language=response_language,
        pdf_base64=pdf_base64,
        filename=filename if pdf_base64 else None,
    )


@app.post("/documents/render/pdf", response_model=DocumentPdfResponse)
def render_document_pdf(
    request: DocumentPdfRequest,
    current_user: User = Depends(get_current_user),
):
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", request.title).strip("_") or "document"
    filename = f"{safe_name}.pdf"
    try:
        html = render_html_document(request.title, request.content)
        pdf_bytes = render_pdf_from_html(html)
        pdf_base64 = base64.b64encode(pdf_bytes).decode("ascii")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return DocumentPdfResponse(pdf_base64=pdf_base64, filename=filename)


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


@app.post("/chats/{chat_id}/translate")
def translate_chat_messages(
    chat_id: str,
    target: str = "ur",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if target not in {"ur", "en"}:
        raise HTTPException(status_code=400, detail="Target language must be 'ur' or 'en'")
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    translated_messages = []
    for message in messages:
        translated_content = None
        if message.role == "assistant":
            if target == "ur":
                if _contains_urdu(message.content):
                    translated_content = message.content
                else:
                    candidate = translate_text(message.content, "en", "ur")
                    translated_content = candidate if _contains_urdu(candidate) else None
            else:
                if not _contains_urdu(message.content):
                    translated_content = message.content
                else:
                    candidate = translate_text(message.content, "auto", "en")
                    translated_content = None if _contains_urdu(candidate) else candidate
        translated_messages.append(_serialize_translated_message(message, translated_content))
    return {
        "chat": _serialize_chat(chat),
        "messages": translated_messages,
        "target": target,
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

        response_language = request.language
        if request.language == "ur":
            answer = translate_to_urdu(answer)
            if not _contains_urdu(answer):
                response_language = "en"
        elif request.language == "en" and _contains_urdu(answer):
            answer = translate_to_english(answer)
        needs_referral = _needs_referral(matches, answer, request.query)
        referral_expert = _select_referral(matches) if needs_referral else None
        if needs_referral:
            intro_line = _referral_intro(request.language)
            if not (answer or "").strip():
                answer = intro_line
            else:
                answer = f"{intro_line}\n\n{answer.strip()}"
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
            "language": response_language,
            "chat_title": chat.title if chat is not None else None,
            "needs_referral": needs_referral,
            "referral_expert": referral_expert,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("RAG answer failed")
        detail = f"RAG answer failed: {type(exc).__name__}"
        if str(exc):
            detail = f"{detail}: {exc}"
        raise HTTPException(status_code=500, detail=detail) from exc
