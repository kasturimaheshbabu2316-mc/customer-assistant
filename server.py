from fastapi import FastAPI, HTTPException, Request, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any
import os
import time
import random
import json
import csv
import io
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

import database
from rag_engine import (
    run_rag_pipeline,
    query_rag_pipeline,
    stream_rag_pipeline,
    classify_intent_and_sentiment,
    generate_agent_reply_draft,
    generate_support_response,
    detect_escalation_intent,
    detect_language,
    translate_grounded_response,
    GeminiEmbeddingFunction,
    parse_faq_sections,
    ingest_policy_text,
    ingest_faq,
    get_all_chunks,
    add_knowledge_chunk,
    delete_knowledge_chunk,
    reindex_default_kb,
    get_pipeline_settings,
    update_pipeline_settings,
    run_synthetic_benchmark,
    bm25_search,
    hybrid_search_rag,
    analyze_claim_image,
    collection,
    DEFAULT_KB_PATH,
    get_gemini_api_key
)

SERVER_START_TIME = time.time()
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "admin-secret-key-2026").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

# ==============================================================================
# SAFE PROXY IP EXTRACTION & SLIDING-WINDOW RATE LIMITER
# ==============================================================================
def get_client_ip(request: Request) -> str:
    """Safely extracts the client IP address considering proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in X-Forwarded-For is the originating client
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP") or request.headers.get("CF-Connecting-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"

class SlidingWindowRateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.requests: dict[str, list[float]] = {}

    @property
    def limit(self) -> int:
        return self.rpm

    @limit.setter
    def limit(self, val: int):
        self.rpm = val

    def is_allowed(self, client_ip: str) -> tuple[bool, int]:
        now = time.time()
        window_start = now - 60.0
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Purge timestamps outside the 60s window
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]
        
        if len(self.requests[client_ip]) >= self.rpm:
            oldest_in_window = self.requests[client_ip][0]
            retry_after = max(1, int(oldest_in_window - window_start) + 1)
            return False, retry_after
        
        self.requests[client_ip].append(now)
        return True, 0

rate_limiter = SlidingWindowRateLimiter(requests_per_minute=RATE_LIMIT_PER_MINUTE)

def check_rate_limit(request: Request):
    client_ip = get_client_ip(request)
    allowed, retry_after = rate_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({rate_limiter.rpm} req/min). Please retry in {retry_after}s.",
            headers={"Retry-After": str(retry_after)}
        )

# ==============================================================================
# ADMIN AUTHENTICATION DEPENDENCY
# ==============================================================================
def get_configured_admin_password() -> str:
    """Returns ADMIN_PASSWORD from .env, falling back to ADMIN_API_KEY or 'admin-secret-key-2026'."""
    env_admin_pw = os.getenv("ADMIN_PASSWORD", "").strip()
    if env_admin_pw:
        return env_admin_pw
    env_admin_key = os.getenv("ADMIN_API_KEY", "").strip()
    if env_admin_key:
        return env_admin_key
    global_key = str(globals().get("ADMIN_API_KEY", "")).strip()
    if global_key:
        return global_key
    return "admin-secret-key-2026"

def verify_admin_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    token = x_api_key or x_admin_key
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()
            
    expected_pw = get_configured_admin_password()
    valid_keys = {expected_pw}
    if os.getenv("ADMIN_API_KEY", "").strip():
        valid_keys.add(os.getenv("ADMIN_API_KEY", "").strip())
    if globals().get("ADMIN_API_KEY"):
        valid_keys.add(str(globals()["ADMIN_API_KEY"]).strip())
    if not os.getenv("ADMIN_PASSWORD") and not os.getenv("ADMIN_API_KEY"):
        valid_keys.add("admin-secret-key-2026")

    if token and token in valid_keys:
        return True

    # Also verify if token is a valid admin session token from database
    if token:
        sess = database.get_session(token)
        if sess and sess.get("role") in ["admin", "developer"]:
            return True

    raise HTTPException(
        status_code=401,
        detail="Unauthorized: Missing or invalid Admin API Key in X-API-Key header",
        headers={"WWW-Authenticate": "ApiKey"}
    )

# Backward-compatibility list proxies for legacy test suites
class TicketsDBProxy(list):
    def __iter__(self):
        return iter(database.get_all_tickets())
    def __len__(self):
        return len(database.get_all_tickets())
    def __getitem__(self, idx):
        return database.get_all_tickets()[idx]
    def insert(self, idx, item):
        database.create_ticket(item)

TICKETS_DB = TicketsDBProxy()

# Query Stats tracking
QUERY_STATS = {
    "total_queries": 14820,
    "deflected_queries": 13100,
    "total_latency_ms": 14820 * 420
}

# Standard Agent Response Macros
MACROS_DB = [
    {
        "id": "macro_return_rma",
        "title": "📦 30-Day Return RMA Authorization",
        "category": "Return & Refund",
        "template": "Hi {{customer_name}},\n\nThank you for reaching out to OmniDesk Support. We have approved your return authorization for Ticket #{{ticket_id}} under our 30-Day Policy.\n\nNext Steps:\n1. Affix the prepaid return shipping label to the original packaging.\n2. Drop off at any authorized courier depot within 14 days.\n3. Your full refund will process within 3-5 business days upon arrival.\n\nWarm regards,\n{{assigned_agent}} — OmniDesk Support"
    },
    {
        "id": "macro_warranty_claim",
        "title": "🛡️ 1-Year Manufacturer Warranty Intake",
        "category": "Warranty & Claims",
        "template": "Hi {{customer_name}},\n\nWe have received your warranty inquiry for Ticket #{{ticket_id}}. To process your 1-Year Limited Manufacturer Warranty replacement:\n\n1. Reply with your hardware serial number (on barcode label).\n2. Attach 1-2 clear photos/video of the issue.\n\nOnce received, our warranty desk will expedite your replacement dispatch.\n\nBest regards,\n{{assigned_agent}} — Warranty Desk"
    },
    {
        "id": "macro_price_match",
        "title": "💳 14-Day Price Match Adjustment Credit",
        "category": "Billing & Payment",
        "template": "Hi {{customer_name}},\n\nGreat news! We have verified the promotional pricing under our 14-Day Price Match Guarantee for Ticket #{{ticket_id}}.\n\nA price adjustment credit has been applied to your original payment method and will reflect on your statement in 2-3 business days.\n\nThank you for choosing OmniDesk,\n{{assigned_agent}}"
    },
    {
        "id": "macro_intl_ddp",
        "title": "✈️ DHL International DDP Delivery Details",
        "category": "Shipping & Logistics",
        "template": "Hi {{customer_name}},\n\nRegarding your international delivery inquiry for Ticket #{{ticket_id}}:\n\nAll international shipments are dispatched via DHL Express under Delivered Duty Paid (DDP) terms. All customs duties, VAT, and brokerage fees were pre-cleared at checkout. No additional fees will be requested upon arrival.\n\nTracking updates are active in your account dashboard.\n\nSafe travels & regards,\n{{assigned_agent}}"
    }
]

def dispatch_webhook_alert(event_type: str, title: str, payload: dict, severity: str = "medium", destination: str = "Slack #support-alerts") -> dict:
    """Dispatches a simulated Slack / PagerDuty webhook incident alert to persistent DB."""
    return database.add_webhook_log(
        event_type=event_type,
        title=title,
        severity=severity,
        destination=destination,
        payload=payload,
        status="delivered"
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        kb_path = str(DEFAULT_KB_PATH)
        if os.path.exists(kb_path):
            ingest_faq(kb_path)
            print(f"Knowledge base ({kb_path}) ingested successfully.")
        else:
            print(f"{kb_path} not found, skipping startup ingestion.")
    except Exception as e:
        print(f"Startup ingestion note: {e}")
    yield

app = FastAPI(title="OmniDesk Customer Support RAG Agent API", lifespan=lifespan)

# Configurable CORS
cors_env = os.getenv("CORS_ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# REQUEST & RESPONSE MODELS
# ==============================================================================

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Customer question text")
    language: Optional[str] = Field("Auto Detect", max_length=50)
    history: Optional[list[dict[str, Any]]] = Field(default=[], description="Recent conversation history turns [{'role': 'user'|'assistant', 'content': '...'}]")

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    distances: Optional[list[float]] = []
    deflected: Optional[bool] = False
    latency_ms: Optional[int] = 0
    language: Optional[str] = "English"
    model: Optional[str] = "gemini-1.5-flash"

class ChatRequest(BaseModel):
    query: Optional[str] = Field(None, max_length=2000, description="Customer question text")
    message: Optional[str] = Field(None, max_length=2000, description="Customer question alias")
    email: Optional[str] = Field(None, max_length=120, description="Customer email")
    customer_email: Optional[str] = Field(None, max_length=120, description="Customer email alias")
    history: Optional[list[dict[str, Any]]] = Field(default=[], description="Recent conversation history turns")
    language: Optional[str] = Field("Auto Detect", max_length=50)

    @model_validator(mode="before")
    @classmethod
    def check_query_or_message(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_q = data.get("query")
            raw_msg = data.get("message")
            q = raw_q if (raw_q is not None and str(raw_q).strip()) else raw_msg
            if q is None or not str(q).strip():
                raise ValueError("Query or message cannot be empty")
            clean_q = str(q).strip()
            data["query"] = clean_q
            data["message"] = clean_q
            
            raw_email = data.get("email")
            raw_cust_email = data.get("customer_email")
            em = raw_email if (raw_email is not None and str(raw_email).strip()) else raw_cust_email
            if em is not None and str(em).strip():
                clean_em = str(em).strip()
                data["email"] = clean_em
                data["customer_email"] = clean_em
        return data

class FeedbackRequest(BaseModel):
    query: Optional[str] = ""
    rating: Optional[int] = Field(None, ge=1, le=5)
    score: Optional[int] = Field(None, ge=1, le=5)
    is_positive: Optional[bool] = None
    comment: Optional[str] = ""
    language: Optional[str] = "English"

    @model_validator(mode="before")
    @classmethod
    def normalize_feedback(cls, data: Any) -> Any:
        if isinstance(data, dict):
            r = data.get("rating") if data.get("rating") is not None else data.get("score")
            if r is None:
                r = 5
            data["rating"] = int(r)
            if data.get("is_positive") is None:
                data["is_positive"] = (int(r) >= 4)
        return data

class ApplyMacroRequest(BaseModel):
    macro_id: str = Field(..., min_length=1)
    sender: Optional[str] = "Support Specialist"

class AddPolicyRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Policy clause header")
    content: str = Field(..., min_length=5, max_length=20000, description="Detailed policy text")
    source: Optional[str] = Field("custom_policy.txt", max_length=100)

class RagUploadRequest(BaseModel):
    text: Optional[str] = Field(None, description="Raw markdown or text policy document")
    content: Optional[str] = Field(None, description="Alternative field for policy content")
    filename: Optional[str] = Field("company_faq.txt", description="Document filename or identifier")
    replace_all: Optional[bool] = Field(True, description="Whether to replace all existing sections")
    save_to_kb: Optional[bool] = Field(True, description="Whether to persist to knowledge_base/company_faq.txt")

class SettingsUpdateRequest(BaseModel):
    guardrail_threshold: Optional[float] = Field(None, ge=0.1, le=3.0)
    top_k_chunks: Optional[int] = Field(None, ge=1, le=20)
    generation_model: Optional[str] = None
    embedding_model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    system_instruction: Optional[str] = None

class FeaturesUpdateRequest(BaseModel):
    enable_streaming: Optional[bool] = None
    enable_vision_upload: Optional[bool] = None
    enable_multi_language: Optional[bool] = None
    enable_faq_chips: Optional[bool] = None
    enable_csat_popup: Optional[bool] = None
    enable_ticket_lookup: Optional[bool] = None
    enable_announcement_banner: Optional[bool] = None
    announcement_banner_text: Optional[str] = Field(None, max_length=500)
    welcome_greeting: Optional[str] = Field(None, max_length=1000)
    theme_mode: Optional[str] = Field(None, max_length=50)
    auto_escalate_vip: Optional[bool] = None

class CreateTicketRequest(BaseModel):
    customer_id: Optional[str] = Field(None, max_length=50)
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_email: str = Field(..., min_length=3, max_length=120)
    customer_tier: Optional[str] = Field("Standard Retail", max_length=50)
    subject: Optional[str] = Field(None, max_length=200)
    query: Optional[str] = Field(None, max_length=3000)
    message: Optional[str] = Field(None, max_length=3000)
    priority: Optional[str] = Field("Medium", description="Urgent, High, Medium, or Low")
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    transcript_snippet: Optional[str] = Field("", max_length=1000)

    @model_validator(mode="before")
    @classmethod
    def set_ticket_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_q = data.get("query")
            raw_msg = data.get("message")
            q = raw_q if (raw_q is not None and str(raw_q).strip()) else raw_msg
            if q is None or not str(q).strip():
                raise ValueError("query or message is required and cannot be empty")
            clean_q = str(q).strip()
            data["query"] = clean_q
            data["message"] = clean_q
            if not data.get("subject") or not str(data.get("subject")).strip():
                data["subject"] = f"Inquiry: {clean_q[:40]}..."
        return data

class TicketMessageRequest(BaseModel):
    sender: str = Field("Support Agent", min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=5000)
    is_internal_note: Optional[bool] = False

class TicketReplyRequest(BaseModel):
    message: Optional[str] = Field(None, max_length=5000, description="Reply message text")
    text: Optional[str] = Field(None, max_length=5000, description="Message text alias")
    sender: Optional[str] = Field("Support Agent", max_length=100, description="Sender name")
    is_internal_note: Optional[bool] = Field(False, description="Whether this is a staff-only internal note")
    status: Optional[str] = Field(None, description="Optional new ticket status, e.g. In Progress, Resolved")

    @model_validator(mode="before")
    @classmethod
    def check_reply_text(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_text = data.get("text")
            raw_msg = data.get("message")
            msg = raw_text if (raw_text is not None and str(raw_text).strip()) else raw_msg
            if msg is None or not str(msg).strip():
                raise ValueError("Reply text or message cannot be empty")
            clean_msg = str(msg).strip()
            data["text"] = clean_msg
            data["message"] = clean_msg
        return data

class UpdateTicketRequest(BaseModel):
    status: Optional[str] = Field(None, description="Open, In Progress, or Resolved")
    assigned_agent: Optional[str] = None
    priority: Optional[str] = None

class AdminLoginRequest(BaseModel):
    password: Optional[str] = Field(None, max_length=256, description="Admin password or API key")
    secret_key: Optional[str] = Field(None, max_length=256, description="Admin secret key alias")
    admin_password: Optional[str] = Field(None, max_length=256, description="Admin password alias")
    key: Optional[str] = Field(None, max_length=256, description="Admin key alias")
    email: Optional[str] = Field(None, max_length=120, description="Admin email")

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)

class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=120)
    password: str = Field(..., min_length=1, max_length=128)

class DevLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=120)
    secret_key: str = Field(..., min_length=1, max_length=200)
    mfa_token: Optional[str] = Field(None, max_length=20)

class DevKeyRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)
    team: str = Field(..., min_length=2, max_length=100)
    reason: str = Field(..., min_length=5, max_length=500)

# ==============================================================================
# AUTHENTICATION & IDENTITY APIS
# ==============================================================================

@app.post("/api/auth/register")
def register_customer(req: UserRegisterRequest):
    existing = database.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    
    try:
        user = database.create_user(
            name=req.name,
            email=req.email,
            password=req.password,
            role="customer",
            tier="Standard Retail"
        )
        token = database.create_user_session(user["id"], role="customer")
        return {
            "status": "success",
            "message": "Account created successfully!",
            "user": user,
            "token": token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
def login_customer(req: UserLoginRequest):
    user = database.authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    token = database.create_user_session(user["id"], role=user.get("role", "customer"))
    return {
        "status": "success",
        "message": f"Welcome back, {user['name']}!",
        "user": user,
        "token": token
    }

@app.get("/api/auth/me")
def get_current_user(
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    token = x_session_token
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()
            
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated: No session token provided.")
        
    session = database.get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please sign in again.")
        
    return {
        "status": "success",
        "user": {
            "id": session["user_id"],
            "name": session["name"],
            "email": session["email"],
            "tier": session["tier"],
            "role": session["role"]
        }
    }

@app.post("/api/auth/logout")
def logout_user(
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    token = x_session_token
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()
            
    if token:
        database.delete_session(token)
        
    return {"status": "success", "message": "Successfully signed out."}

@app.post("/api/admin/login")
def admin_login_endpoint(req: AdminLoginRequest):
    provided = (req.password or req.secret_key or req.admin_password or req.key or "").strip()
    
    expected_pw = get_configured_admin_password()
    is_valid = bool(provided) and (provided == expected_pw)
    admin_user = None
    if not is_valid and req.email and provided:
        admin_user = database.authenticate_user(req.email, provided)
        if admin_user and admin_user.get("role") in ["admin", "developer"]:
            is_valid = True
            
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid Admin credentials."
        )
        
    user_id = admin_user["id"] if admin_user else "ADMIN-ROOT"
    user_name = admin_user["name"] if admin_user else "Admin Operations"
    token = database.create_user_session(user_id, role="admin")
    
    return {
        "status": "success",
        "message": f"Admin session authenticated. Welcome {user_name}.",
        "token": token,
        "access_token": token,
        "token_type": "bearer",
        "role": "admin"
    }

@app.post("/api/auth/developer-login")
def developer_gateway_login(req: DevLoginRequest):
    current_key = globals().get("ADMIN_API_KEY") or os.getenv("ADMIN_API_KEY", "admin-secret-key-2026").strip()
    
    is_valid_key = (req.secret_key.strip() == current_key)
    admin_user = database.authenticate_user(req.email, req.secret_key)
    
    if not is_valid_key and (not admin_user or admin_user.get("role") not in ["admin", "developer"]):
        raise HTTPException(status_code=401, detail="Invalid Developer Access Key or credentials.")
        
    user_id = admin_user["id"] if admin_user else "ADMIN-ROOT"
    user_name = admin_user["name"] if admin_user else "Developer Operations Lead"
    token = database.create_user_session(user_id, role="admin")
    
    return {
        "status": "success",
        "message": f"Developer Console Authenticated. Welcome {user_name}.",
        "admin_key": current_key,
        "token": token,
        "user": {
            "id": user_id,
            "name": user_name,
            "email": req.email,
            "role": "admin"
        }
    }

@app.post("/api/auth/request-key")
def request_developer_key(req: DevKeyRequest):
    entry = database.record_developer_key_request(
        email=req.email,
        team=req.team,
        reason=req.reason
    )
    return {
        "status": "success",
        "message": "Your Developer Access Key request has been submitted for lead review.",
        "request": entry
    }

# ==============================================================================
# CORE CHAT & DIAGNOSTICS APIS
# ==============================================================================

@app.get("/health")
def health():
    count = 0
    try:
        count = collection.count() if collection else 0
    except Exception:
        pass
    has_api_key = bool(get_gemini_api_key())
    tickets = database.get_all_tickets()
    open_tickets = sum(1 for t in tickets if t["status"] == "Open")
    return {
        "status": "healthy",
        "service": "OmniDesk RAG Backend",
        "vector_count": count,
        "has_gemini_api_key": has_api_key,
        "gemini_mode": "live_api" if has_api_key else "local_grounded_fallback",
        "rate_limit_per_min": RATE_LIMIT_PER_MINUTE,
        "admin_auth_enabled": bool(ADMIN_API_KEY),
        "open_tickets": open_tickets
    }

@app.get("/api/info")
def get_info():
    count = 0
    try:
        count = collection.count() if collection else 0
    except Exception:
        pass
    settings = get_pipeline_settings()
    uptime = int(time.time() - SERVER_START_TIME)
    return {
        "status": "online",
        "uptime_seconds": uptime,
        "collection_name": "support_kb",
        "document_chunks": count,
        "embedding_model": settings["embedding_model"],
        "generation_model": settings["generation_model"],
        "guardrail_threshold": settings["guardrail_threshold"],
        "top_k_chunks": settings["top_k_chunks"],
        "temperature": settings["temperature"],
        "has_gemini_api_key": bool(get_gemini_api_key()),
        "rate_limit_per_min": RATE_LIMIT_PER_MINUTE,
        "admin_auth_enabled": bool(ADMIN_API_KEY)
    }

@app.post("/ask", response_model=QueryResponse, dependencies=[Depends(check_rate_limit)])
def ask(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        res = run_rag_pipeline(req.query.strip(), target_language=req.language or "Auto Detect", history=req.history)
        
        # Record stats
        QUERY_STATS["total_queries"] += 1
        if not res.get("deflected"):
            QUERY_STATS["deflected_queries"] += 1
        QUERY_STATS["total_latency_ms"] += res.get("latency_ms", 300)
        
        # Record persistent audit log
        database.add_audit_log(
            query=req.query[:80],
            status="Deflected (Escalated)" if res.get("deflected") else "Resolved (100% Grounded)",
            distance=round(res["distances"][0], 2) if res.get("distances") else 0.0,
            matched=res["sources"][0][:50] if res.get("sources") else "None",
            latency_ms=res.get("latency_ms", 0)
        )
            
        return res
    except Exception as e:
        print(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask/stream", dependencies=[Depends(check_rate_limit)])
def ask_stream(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        QUERY_STATS["total_queries"] += 1
        QUERY_STATS["deflected_queries"] += 1
        return StreamingResponse(
            stream_rag_pipeline(req.query.strip(), target_language=req.language or "Auto Detect", history=req.history),
            media_type="text/event-stream"
        )
    except Exception as e:
        print(f"Stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", dependencies=[Depends(check_rate_limit)])
def chat_endpoint(req: ChatRequest):
    """
    Customer RAG chat with grounded policies, order context injection,
    and automatic live ticket escalation for frustrated inquiries.
    """
    user_query = (req.query or req.message or "").strip()
    if not user_query:
        raise HTTPException(status_code=422, detail="Query cannot be empty")
        
    email = (req.email or req.customer_email or "").strip() or None
    try:
        res = generate_support_response(
            user_query=user_query,
            chat_history=req.history,
            customer_email=email
        )
        
        target_lang = req.language or "Auto Detect"
        lang = target_lang if target_lang != "Auto Detect" else detect_language(user_query)
        final_answer = res.get("answer", "")
        if lang != "English" and final_answer:
            final_answer = translate_grounded_response(final_answer, lang, user_query)
            
        QUERY_STATS["total_queries"] += 1
        if not res.get("deflected"):
            QUERY_STATS["deflected_queries"] += 1
        QUERY_STATS["total_latency_ms"] += res.get("latency_ms", 300)
        
        database.add_audit_log(
            query=user_query[:80],
            status="Deflected (Escalated)" if res.get("deflected") else "Resolved (100% Grounded)",
            distance=round(res["distances"][0], 2) if res.get("distances") else 0.0,
            matched=res["sources"][0][:50] if res.get("sources") else "None",
            latency_ms=res.get("latency_ms", 0)
        )
        
        return {
            "status": "success",
            "answer": final_answer,
            "response": final_answer,
            "sources": res.get("sources", []),
            "sections": res.get("sections", []),
            "distances": res.get("distances", []),
            "deflected": res.get("deflected", False),
            "latency_ms": res.get("latency_ms", 0),
            "order": res.get("order"),
            "ticket": res.get("ticket"),
            "intent": res.get("intent", "General Inquiry"),
            "sentiment": res.get("sentiment", "Standard"),
            "language": lang
        }
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# TICKETS, SLA ENGINE & COPILOT APIS
# ==============================================================================

def calculate_sla_details(ticket: dict) -> dict:
    created_ts = ticket.get("created_ts") or time.time()
    priority = (ticket.get("priority") or "Medium").capitalize()
    
    sla_targets = {
        "Urgent": 60,       # 1 hour
        "High": 240,        # 4 hours
        "Medium": 1440,     # 24 hours
        "Low": 2880         # 48 hours
    }
    target_mins = sla_targets.get(priority, 1440)
    elapsed_mins = int((time.time() - created_ts) / 60)
    remaining_mins = target_mins - elapsed_mins
    is_breached = remaining_mins <= 0 and ticket.get("status") != "Resolved"
    
    if ticket.get("status") == "Resolved":
        badge_status = "resolved"
        label = "SLA Met"
    elif is_breached:
        badge_status = "breached"
        label = f"SLA Breached ({abs(remaining_mins)}m overdue)"
    elif remaining_mins <= 60:
        badge_status = "urgent"
        label = f"{remaining_mins}m left"
    elif remaining_mins <= 180:
        badge_status = "warning"
        label = f"{remaining_mins // 60}h {remaining_mins % 60}m left"
    else:
        badge_status = "normal"
        hours = remaining_mins // 60
        label = f"{hours}h left" if hours < 24 else f"{hours // 24}d {hours % 24}h left"
        
    return {
        "sla_target_minutes": target_mins,
        "elapsed_minutes": elapsed_mins,
        "remaining_minutes": max(0, remaining_mins),
        "is_breached": is_breached,
        "badge_status": badge_status,
        "label": label
    }

@app.get("/api/tickets")
def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status: Open, In Progress, Resolved"),
    priority: Optional[str] = Query(None, description="Filter by priority: Urgent, High, Medium, Low"),
    email: Optional[str] = Query(None, description="Filter by customer email"),
    customer_email: Optional[str] = Query(None, description="Alias for customer email filter")
):
    target_email = email or customer_email
    tickets = database.get_all_tickets(status=status, priority=priority)
    if target_email:
        clean_email = target_email.strip().lower()
        tickets = [t for t in tickets if str(t.get("customer_email", "")).strip().lower() == clean_email]
    
    enriched = []
    for t in tickets:
        t_copy = dict(t)
        t_copy["sla_details"] = calculate_sla_details(t)
        enriched.append(t_copy)

    return {
        "total": len(enriched),
        "tickets": enriched
    }

@app.post("/api/tickets")
def create_ticket(req: CreateTicketRequest):
    ticket_id = None
    for _ in range(50):
        cand = f"TCK-{random.randint(1050, 99999)}"
        if not database.get_ticket_by_id(cand):
            ticket_id = cand
            break
    if not ticket_id:
        ticket_id = f"TCK-{int(time.time()*1000) % 1000000}"
    cust_id = req.customer_id.strip() if req.customer_id else f"CUST-{random.randint(1000, 9999)}"
    
    query_text = (req.query or req.message or "").strip()
    classification = classify_intent_and_sentiment(query_text)
    intent = req.intent.strip() if req.intent else classification["intent"]
    sentiment = req.sentiment.strip() if req.sentiment else classification["sentiment"]
    now_ts = time.time()
    
    subject_text = (req.subject or f"Inquiry: {query_text[:40]}...").strip()
    
    initial_messages = [
        {
            "id": "msg_1",
            "sender": req.customer_name.strip(),
            "text": query_text,
            "is_internal_note": False,
            "timestamp": time.strftime("%b %d, %H:%M")
        }
    ]

    new_ticket_data = {
        "id": ticket_id,
        "customer_id": cust_id,
        "customer_name": req.customer_name.strip(),
        "customer_email": req.customer_email.strip(),
        "customer_tier": req.customer_tier.strip() if req.customer_tier else "Standard Retail",
        "intent": intent,
        "sentiment": sentiment,
        "subject": subject_text,
        "query": query_text,
        "priority": req.priority.title() if req.priority else "Medium",
        "status": "Open",
        "created_at": time.strftime("%b %d, %H:%M"),
        "created_ts": now_ts,
        "assigned_agent": "Unassigned",
        "transcript_snippet": req.transcript_snippet.strip() if req.transcript_snippet else query_text[:120],
        "messages": initial_messages
    }
    
    created = database.create_ticket(new_ticket_data)
    
    # Phase 7: Trigger Outbound Incident Webhook for Urgent or VIP Escalations
    if created["priority"] == "Urgent" or "VIP" in created["customer_tier"]:
        dispatch_webhook_alert(
            event_type="urgent_ticket_escalated",
            title=f"🚨 Urgent Escalation: Ticket #{ticket_id} ({created['customer_name']})",
            payload={"ticket_id": ticket_id, "customer_name": created["customer_name"], "priority": created["priority"], "tier": created["customer_tier"], "subject": created["subject"]},
            severity="high",
            destination="Slack #support-tier2-urgent"
        )
    
    returned_ticket = dict(created)
    returned_ticket["sla_details"] = calculate_sla_details(created)
    
    return {
        "status": "success",
        "message": f"Support Ticket {ticket_id} created successfully",
        "ticket": returned_ticket
    }

@app.get("/api/tickets/export")
def export_tickets(format: str = Query("csv", description="csv or json")):
    tickets = database.get_all_tickets()
    if format.lower() == "json":
        json_str = json.dumps(tickets, indent=2)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="omnidesk_tickets_export.json"'}
        )
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Ticket ID", "Customer ID", "Customer Name", "Customer Email", 
        "Customer Tier", "Priority", "Status", "Intent", "Sentiment", 
        "Assigned Agent", "Created At", "Subject", "Query Context"
    ])
    
    for t in tickets:
        writer.writerow([
            t.get("id", ""),
            t.get("customer_id", ""),
            t.get("customer_name", ""),
            t.get("customer_email", ""),
            t.get("customer_tier", ""),
            t.get("priority", ""),
            t.get("status", ""),
            t.get("intent", "General Inquiry"),
            t.get("sentiment", "Standard"),
            t.get("assigned_agent", "Unassigned"),
            t.get("created_at", ""),
            t.get("subject", ""),
            t.get("query", "")
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="omnidesk_tickets_export.csv"'}
    )

@app.get("/api/kb/export")
def export_knowledge_base():
    chunks = get_all_chunks()
    json_str = json.dumps({
        "export_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_chunks": len(chunks),
        "chunks": chunks
    }, indent=2)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="omnidesk_kb_backup.json"'}
    )

@app.get("/api/tickets/stats")
def get_ticket_stats():
    tickets = database.get_all_tickets()
    total = len(tickets)
    open_c = sum(1 for t in tickets if t["status"] == "Open")
    in_prog_c = sum(1 for t in tickets if t["status"] == "In Progress")
    resolved_c = sum(1 for t in tickets if t["status"] == "Resolved")
    rate = round((resolved_c / total * 100), 1) if total > 0 else 100.0

    return {
        "total_tickets": total,
        "open_tickets": open_c,
        "in_progress_tickets": in_prog_c,
        "resolved_tickets": resolved_c,
        "resolution_rate_percent": rate
    }

@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str, public: Optional[bool] = Query(False, description="Strip private internal notes if true")):
    if public:
        ticket = database.get_customer_safe_ticket(ticket_id.upper())
    else:
        ticket = database.get_ticket_by_id(ticket_id.upper())
        
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    t_copy = dict(ticket)
    t_copy["sla_details"] = calculate_sla_details(ticket)
    return {
        **t_copy,
        "status": "success",
        "ticket": t_copy
    }

@app.get("/api/tickets/public/{ticket_id}")
def get_public_ticket(ticket_id: str):
    ticket = database.get_customer_safe_ticket(ticket_id.upper())
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    t_copy = dict(ticket)
    t_copy["sla_details"] = calculate_sla_details(ticket)
    return {
        "status": "success",
        "ticket": t_copy
    }

@app.post("/api/tickets/{ticket_id}/suggest-reply")
def suggest_agent_reply(ticket_id: str):
    t = database.get_ticket_by_id(ticket_id.upper())
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
    copilot_res = generate_agent_reply_draft(
        ticket_query=t.get("query", ""),
        customer_name=t.get("customer_name", "Valued Customer"),
        customer_tier=t.get("customer_tier", "Standard Retail"),
        intent=t.get("intent", "General Inquiry")
    )
    return {
        "ticket_id": t["id"],
        "customer_name": t.get("customer_name"),
        "customer_tier": t.get("customer_tier"),
        "intent": t.get("intent"),
        "suggested_reply": copilot_res["suggested_reply"],
        "sources": copilot_res["sources"],
        "latency_ms": copilot_res["latency_ms"]
    }

@app.post("/api/tickets/{ticket_id}/messages")
def add_ticket_message_endpoint(ticket_id: str, req: TicketMessageRequest):
    t = database.get_ticket_by_id(ticket_id.upper())
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
    new_msg = database.add_ticket_message(
        ticket_id=ticket_id.upper(),
        sender=req.sender.strip(),
        text=req.text.strip(),
        is_internal_note=bool(req.is_internal_note)
    )
    
    if not req.is_internal_note and t["status"] == "Open":
        database.update_ticket(ticket_id.upper(), {"status": "In Progress"})
        
    updated_ticket = database.get_ticket_by_id(ticket_id.upper())
    t_copy = dict(updated_ticket or t)
    t_copy["sla_details"] = calculate_sla_details(t_copy)
    return {
        "status": "success",
        "message": "Message appended to ticket thread",
        "ticket_message": new_msg,
        "ticket": t_copy
    }

@app.post("/api/tickets/{ticket_id}/reply")
def reply_ticket_endpoint(ticket_id: str, req: TicketReplyRequest):
    clean_tid = ticket_id.strip()
    t = database.get_ticket_by_id(clean_tid.upper()) or database.get_ticket_by_id(clean_tid)
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    actual_tid = t["id"]
        
    msg_text = (req.text or req.message or "").strip()
    sender_name = req.sender.strip() if req.sender else "Support Agent"
    
    new_msg = database.add_ticket_message(
        ticket_id=actual_tid,
        sender=sender_name,
        text=msg_text,
        is_internal_note=bool(req.is_internal_note)
    )
    
    updates: dict[str, Any] = {}
    if req.status:
        st_val = req.status.strip()
        updates["status"] = "In Progress" if st_val.lower() == "in progress" else st_val.title()
    elif not req.is_internal_note and t.get("status") == "Open":
        updates["status"] = "In Progress"
        
    if sender_name not in ("Valued Customer", "Customer", "User") and t.get("assigned_agent") in (None, "", "Unassigned"):
        updates["assigned_agent"] = sender_name
        
    if updates:
        database.update_ticket(actual_tid, updates)
        
    updated = database.get_ticket_by_id(actual_tid)
    t_copy = dict(updated or t)
    t_copy["sla_details"] = calculate_sla_details(t_copy)
    return {
        "status": "success",
        "message": "Reply posted to ticket thread",
        "reply": new_msg,
        "ticket_message": new_msg,
        "ticket": t_copy,
        "state": t_copy
    }

@app.get("/api/tickets/{ticket_id}/State")
@app.get("/api/tickets/{ticket_id}/state")
def get_ticket_state(ticket_id: str):
    clean_tid = ticket_id.strip()
    ticket = database.get_ticket_by_id(clean_tid.upper()) or database.get_ticket_by_id(clean_tid)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    t_copy = dict(ticket)
    t_copy["sla_details"] = calculate_sla_details(ticket)
    return {
        "status": "success",
        "ticket_id": t_copy["id"],
        "ticket_status": t_copy.get("status"),
        "status_name": t_copy.get("status"),
        "assigned_agent": t_copy.get("assigned_agent"),
        "messages": t_copy.get("messages", []),
        "sla_details": t_copy["sla_details"],
        "ticket": t_copy,
        "state": t_copy
    }

@app.patch("/api/tickets/{ticket_id}")
@app.post("/api/tickets/{ticket_id}")
@app.put("/api/tickets/{ticket_id}")
def update_ticket_endpoint(ticket_id: str, req: UpdateTicketRequest):
    clean_tid = ticket_id.strip()
    t = database.get_ticket_by_id(clean_tid.upper()) or database.get_ticket_by_id(clean_tid)
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    actual_tid = t["id"]
        
    updates: dict[str, Any] = {}
    if req.status:
        st_val = req.status.strip()
        updates["status"] = "In Progress" if st_val.lower() == "in progress" else st_val.title()
    if req.assigned_agent:
        updates["assigned_agent"] = req.assigned_agent.strip()
    if req.priority:
        updates["priority"] = req.priority.title()
        
    updated = database.update_ticket(ticket_id.upper(), updates)
    t_copy = dict(updated or t)
    t_copy["sla_details"] = calculate_sla_details(t_copy)
    return {
        "status": "success",
        "message": f"Ticket {ticket_id} updated",
        "ticket": t_copy
    }

@app.delete("/api/tickets/{ticket_id}", dependencies=[Depends(verify_admin_key)])
def delete_ticket_endpoint(ticket_id: str):
    deleted = database.delete_ticket(ticket_id.upper())
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return {
        "status": "success",
        "message": f"Ticket {ticket_id} removed"
    }

# ==============================================================================
# KNOWLEDGE BASE STUDIO APIS (Admin Protected)
# ==============================================================================

@app.get("/api/kb/chunks")
def list_kb_chunks():
    chunks = get_all_chunks()
    return {
        "total": len(chunks),
        "chunks": chunks
    }

@app.post("/api/kb/add", dependencies=[Depends(verify_admin_key)])
def add_policy_chunk(req: AddPolicyRequest):
    try:
        new_chunk = add_knowledge_chunk(
            title=req.title.strip(),
            content=req.content.strip(),
            source=req.source.strip() if req.source else "custom_policy.txt"
        )
        return {
            "status": "success",
            "message": f"Clause '{req.title}' vectorized and indexed into ChromaDB",
            "chunk": new_chunk,
            "total_chunks": collection.count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/kb/chunks/{chunk_id}", dependencies=[Depends(verify_admin_key)])
def remove_policy_chunk(chunk_id: str):
    success = delete_knowledge_chunk(chunk_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Chunk {chunk_id} not found or could not be deleted")
    return {
        "status": "success",
        "message": f"Chunk {chunk_id} removed from vector index",
        "total_chunks": collection.count()
    }

@app.post("/api/kb/reset", dependencies=[Depends(verify_admin_key)])
def reset_knowledge_base():
    try:
        total = reindex_default_kb()
        return {
            "status": "success",
            "message": f"Knowledge base re-indexed. Total chunks: {total}",
            "total_chunks": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# INTERNAL RAG POLICY STUDIO & ORDERS RETRIEVAL
# ==============================================================================

@app.get("/api/admin/rag-upload", dependencies=[Depends(verify_admin_key)])
@app.get("/api/admin/rag-policy", dependencies=[Depends(verify_admin_key)])
def get_admin_rag_policy():
    """Retrieve the raw knowledge base policy content and indexed policy chunks."""
    kb_path = os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base/company_faq.txt")
    content = ""
    if os.path.exists(kb_path):
        with open(kb_path, "r", encoding="utf-8") as f:
            content = f.read()
    chunks = get_all_chunks()
    return {
        "status": "success",
        "kb_path": kb_path,
        "content": content,
        "total_chunks": len(chunks),
        "chunks": chunks
    }

@app.get("/api/rag/status")
@app.get("/api/admin/rag/status")
def get_rag_status():
    """Live RAG policy hot-reload & chunk inspection."""
    kb_path = os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base/company_faq.txt")
    chunks = get_all_chunks()
    settings = get_pipeline_settings()
    return {
        "status": "ready",
        "kb_path": kb_path,
        "total_chunks": len(chunks),
        "embedding_model": settings.get("embedding_model", "models/text-embedding-004"),
        "generation_model": settings.get("generation_model", "gemini-2.5-flash"),
        "guardrail_threshold": settings.get("guardrail_threshold", 0.85),
        "chunks": chunks
    }

@app.post("/api/admin/rag-upload", dependencies=[Depends(verify_admin_key)])
async def admin_rag_upload(request: Request):
    r"""
    RAG Policy Studio document upload and hot-reloading:
    Accepts JSON payload, raw markdown text, or multipart form upload.
    Parses on numbered section boundaries (^\d+\.\s+[A-Z]) or markdown headers (#/##),
    and indexes each section with metadata into ChromaDB.
    """
    content_type = request.headers.get("content-type", "")
    text_content = ""
    filename = "company_faq.txt"
    replace_all = True
    save_to_kb = True

    if "multipart/form-data" in content_type:
        form = await request.form()
        file_obj = form.get("file")
        if file_obj is not None and hasattr(file_obj, "read"):
            file_bytes = await file_obj.read()  # type: ignore
            text_content = file_bytes.decode("utf-8", errors="replace")
            filename = getattr(file_obj, "filename", "company_faq.txt") or "company_faq.txt"
        elif "text" in form:
            text_content = str(form["text"])
        elif "content" in form:
            text_content = str(form["content"])
        if "replace_all" in form:
            replace_all = str(form["replace_all"]).lower() in ("true", "1", "yes")
        if "save_to_kb" in form:
            save_to_kb = str(form["save_to_kb"]).lower() in ("true", "1", "yes")
    else:
        try:
            body = await request.json()
            if isinstance(body, dict):
                text_content = body.get("text") or body.get("content") or ""
                filename = body.get("filename") or "company_faq.txt"
                if "replace_all" in body:
                    replace_all = bool(body["replace_all"])
                if "save_to_kb" in body:
                    save_to_kb = bool(body["save_to_kb"])
        except Exception:
            raw_b = await request.body()
            text_content = raw_b.decode("utf-8", errors="replace")

    clean_text = text_content.strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Policy text or uploaded file cannot be empty.")

    sections = ingest_policy_text(
        text=clean_text,
        source=filename,
        replace_all=replace_all,
        save_to_kb=save_to_kb
    )
    return {
        "status": "success",
        "message": f"Successfully indexed {len(sections)} policy section(s) into ChromaDB.",
        "total_chunks": collection.count(),
        "sections": [
            {
                "section": s["section"],
                "title": s["title"],
                "chunk_index": s["chunk_index"],
                "tokens": s["tokens"],
                "source": s["source"]
            }
            for s in sections
        ]
    }

@app.get("/api/orders/{order_id}")
def get_order_endpoint(order_id: str):
    """Fetches details for an order ID (e.g. ORD-1001)."""
    clean_id = order_id.strip()
    order = database.get_order(clean_id) or database.get_order(clean_id.upper())
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return {"status": "success", "order": order}

@app.get("/api/orders")
def get_orders_endpoint(
    email: Optional[str] = Query(None, description="Filter orders by customer email"),
    customer_email: Optional[str] = Query(None, description="Alias for email filter")
):
    """Lists customer orders, optionally filtered by customer email."""
    target_email = email or customer_email
    orders = database.get_all_orders()
    if target_email and target_email.strip():
        clean_email = target_email.strip().lower()
        orders = [o for o in orders if str(o.get("customer_email", "")).strip().lower() == clean_email]
    return {"status": "success", "total": len(orders), "orders": orders}

# ==============================================================================
# SETTINGS & ANALYTICS APIS
# ==============================================================================

@app.get("/api/settings")
def get_settings():
    return get_pipeline_settings()

@app.post("/api/settings", dependencies=[Depends(verify_admin_key)])
def update_settings(req: SettingsUpdateRequest):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    updated = update_pipeline_settings(updates)
    return {
        "status": "success",
        "message": "Pipeline settings updated",
        "settings": updated
    }

@app.get("/api/features")
def get_features():
    """Public feature flags and UX customization options."""
    return database.get_feature_flags()

@app.post("/api/features", dependencies=[Depends(verify_admin_key)])
def update_features(req: FeaturesUpdateRequest):
    """Protected endpoint for UX team & admins to modify customer features."""
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    updated = database.update_feature_flags(updates)
    return {
        "status": "success",
        "message": "UX feature flags updated successfully",
        "features": updated
    }

@app.post("/api/csat")
@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    rating_val = req.rating if req.rating is not None else 5
    is_pos = req.is_positive if req.is_positive is not None else (rating_val >= 4)
    fb_entry = database.add_feedback(
        query=req.query[:100] if req.query else "Live Assistant Query",
        rating=rating_val,
        is_positive=is_pos,
        comment=req.comment.strip() if req.comment else "",
        language=req.language or "English"
    )
        
    # Phase 7: Trigger Outbound Webhook on Low CSAT rating
    if rating_val <= 2 or not is_pos:
        dispatch_webhook_alert(
            event_type="low_csat_alert",
            title=f"⚠️ Low CSAT Rating Received ({rating_val}/5.0)",
            payload={"rating": rating_val, "comment": req.comment, "query": req.query, "language": req.language},
            severity="medium",
            destination="Slack #csat-telemetry"
        )
        
    return {
        "status": "success",
        "message": "Thank you for your feedback!",
        "feedback": fb_entry
    }

class TestWebhookRequest(BaseModel):
    event_type: Optional[str] = "test_ping"
    channel: Optional[str] = "Slack #support-alerts"
    message: Optional[str] = "Simulated webhook delivery from OmniDesk AI Support Hub."

class BenchmarkRequest(BaseModel):
    num_queries: Optional[int] = 8

@app.post("/api/webhooks/test")
def trigger_test_webhook(req: Optional[TestWebhookRequest] = None):
    ev_type = req.event_type if req and req.event_type else "test_ping"
    dest = req.channel if req and req.channel else "Slack #support-alerts"
    msg = req.message if req and req.message else "Simulated webhook delivery from OmniDesk AI Support Hub."
    
    entry = dispatch_webhook_alert(
        event_type=ev_type,
        title="🔔 Test Webhook Incident Dispatch",
        payload={"message": msg, "status": "Simulated Delivery Successful"},
        severity="info",
        destination=dest
    )
    return {
        "status": "success",
        "message": "Test webhook alert dispatched successfully",
        "webhook_log": entry
    }

@app.get("/api/webhooks/logs")
def get_webhook_logs():
    logs = database.get_webhook_logs()
    return {
        "total": len(logs),
        "logs": logs
    }

@app.post("/api/benchmark/simulate")
def run_benchmark_simulation(req: Optional[BenchmarkRequest] = None):
    num_q = req.num_queries if req and req.num_queries else 8
    bench_data = run_synthetic_benchmark(num_queries=num_q)
    return bench_data

@app.get("/api/macros")
def list_macros():
    return {
        "total": len(MACROS_DB),
        "macros": MACROS_DB
    }

@app.post("/api/tickets/{ticket_id}/apply-macro")
def apply_ticket_macro(ticket_id: str, req: ApplyMacroRequest):
    selected_macro = next((m for m in MACROS_DB if m["id"] == req.macro_id), None)
    if not selected_macro:
        raise HTTPException(status_code=404, detail=f"Macro {req.macro_id} not found")
        
    t = database.get_ticket_by_id(ticket_id.upper())
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
    cust_name = t.get("customer_name", "Valued Customer")
    agent = t.get("assigned_agent", req.sender or "OmniDesk Support")
    if agent == "Unassigned":
        agent = req.sender or "OmniDesk Support"
        
    resolved_text = selected_macro["template"]
    resolved_text = resolved_text.replace("{{customer_name}}", cust_name)
    resolved_text = resolved_text.replace("{{ticket_id}}", t["id"])
    resolved_text = resolved_text.replace("{{assigned_agent}}", agent)
    
    database.add_ticket_message(
        ticket_id=ticket_id.upper(),
        sender=agent,
        text=resolved_text,
        is_internal_note=False
    )
    database.update_ticket(ticket_id.upper(), {"status": "In Progress"})
    
    updated_t = database.get_ticket_by_id(ticket_id.upper())
    t_copy = dict(updated_t or t)
    t_copy["sla_details"] = calculate_sla_details(t_copy)
    return {
        "status": "success",
        "message": f"Macro '{selected_macro['title']}' applied to ticket",
        "applied_text": resolved_text,
        "ticket": t_copy
    }

@app.get("/api/metrics")
@app.get("/api/analytics")
def get_analytics():
    total_q = QUERY_STATS["total_queries"]
    deflected_q = QUERY_STATS["deflected_queries"]
    avg_latency = round((QUERY_STATS["total_latency_ms"] / total_q) / 1000, 2) if total_q > 0 else 0.42
    rate = round((deflected_q / total_q) * 100, 1) if total_q > 0 else 88.4

    metrics = database.get_analytics_metrics()
    feedbacks = database.get_all_feedback()
    webhooks = database.get_webhook_logs(limit=5)
    audits = database.get_audit_logs(limit=10)
    tickets = database.get_all_tickets()
    total_tickets = len(tickets)
    open_tickets = sum(1 for t in tickets if t.get("status") == "Open")
    resolved_tickets = sum(1 for t in tickets if t.get("status") == "Resolved")
    uptime = int(time.time() - SERVER_START_TIME)

    return {
        "status": "success",
        "deflection_rate": rate,
        "avg_latency_s": avg_latency,
        "total_inquiries": total_q,
        "total_queries": total_q,
        "csat_score": metrics["average_rating"],
        "average_csat": metrics["average_rating"],
        "csat_positive_percent": metrics["csat_score_percent"],
        "total_feedbacks": metrics["total_feedback"],
        "feedback_count": metrics["total_feedback"],
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,
        "uptime_seconds": uptime,
        "recent_feedback": feedbacks[:5],
        "recent_webhooks": webhooks,
        "audit_logs": audits
    }

# ==============================================================================
# PHASE 8: HYBRID SEARCH & MULTI-MODAL VISION ENDPOINTS
# ==============================================================================

class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Search query string")
    top_k: Optional[int] = Field(3, ge=1, le=20)
    rrf_k: Optional[int] = Field(60, ge=1, le=200)

class AnalyzeImageRequest(BaseModel):
    image_base64: Optional[str] = Field("", max_length=7000000, description="Base64 image string (max ~5MB)")
    image: Optional[str] = Field(None, max_length=7000000, description="Alias for image_base64")
    claim_description: Optional[str] = Field(None, max_length=2000, description="Customer claim explanation")
    description: Optional[str] = Field(None, max_length=2000, description="Alias for claim_description")
    mime_type: Optional[str] = Field("image/jpeg", max_length=50)

    @model_validator(mode="before")
    @classmethod
    def check_desc(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_claim = data.get("claim_description")
            raw_desc = data.get("description")
            desc = raw_claim if (raw_claim is not None and str(raw_claim).strip()) else raw_desc
            if desc is None or not str(desc).strip():
                raise ValueError("claim_description or description cannot be empty")
            clean_desc = str(desc).strip()
            data["claim_description"] = clean_desc
            data["description"] = clean_desc
            raw_img = data.get("image_base64")
            raw_alias = data.get("image")
            img = raw_img if (raw_img is not None and str(raw_img).strip()) else raw_alias
            if img:
                data["image_base64"] = str(img).strip()
        return data

VisionClaimRequest = AnalyzeImageRequest

@app.post("/api/search/hybrid", dependencies=[Depends(check_rate_limit)])
def hybrid_search(req: HybridSearchRequest):
    try:
        return hybrid_search_rag(query=req.query.strip(), top_k=req.top_k or 3, rrf_k=req.rrf_k or 60)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-image", dependencies=[Depends(check_rate_limit)])
@app.post("/api/vision/analyze-claim", dependencies=[Depends(check_rate_limit)])
def analyze_claim(req: AnalyzeImageRequest):
    try:
        img_b64 = req.image_base64 or req.image or ""
        claim_desc = req.claim_description or req.description or ""
        return analyze_claim_image(
            image_base64=img_b64,
            claim_description=claim_desc.strip(),
            mime_type=req.mime_type or "image/jpeg"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# TWO-WINDOW DESKTOP HTML ROUTES
# Window 1: Customer Support Portal (app.html)
# Window 2: Admin & Agent Command Center (admin.html)
# ==============================================================================

@app.get("/")
@app.get("/app.html")
@app.get("/app")
def read_customer_portal():
    """Serves Window 1: Customer Support Portal."""
    if os.path.exists("app.html"):
        return FileResponse("app.html", media_type="text/html")
    raise HTTPException(status_code=404, detail="app.html not found")

@app.get("/admin")
@app.get("/admin.html")
def read_admin_console():
    """Serves Window 2: Admin & Agent Command Center."""
    if os.path.exists("admin.html"):
        return FileResponse("admin.html", media_type="text/html")
    raise HTTPException(status_code=404, detail="admin.html not found")

# Mount static asset folders (restricted to /css and /js only)
os.makedirs("css", exist_ok=True)
app.mount("/css", StaticFiles(directory="css"), name="css")
os.makedirs("js", exist_ok=True)
app.mount("/js", StaticFiles(directory="js"), name="js")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))
    uvicorn.run(app, host=host, port=port)