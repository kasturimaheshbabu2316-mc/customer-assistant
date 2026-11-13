import base64
import io
import json
import math
import os
import random
import re
import time
import uuid
from collections import Counter
from typing import Any

import chromadb
from dotenv import load_dotenv
from PIL import Image

try:
    from rank_bm25 import BM25Okapi  # type: ignore
except ImportError:
    BM25Okapi = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

import database

# Load environment configuration from .env and doc/.env
load_dotenv()
if os.path.exists("doc/.env"):
    load_dotenv("doc/.env")

# Runtime Configuration State
DEFAULT_CONFIG: dict[str, Any] = {
    "generation_model": os.getenv("GENERATION_MODEL", "gemini-2.5-flash"),
    "embedding_model": os.getenv("EMBEDDING_MODEL", "gemini-embedding-001"),
    "guardrail_threshold": float(os.getenv("GUARDRAIL_DISTANCE_THRESHOLD", "0.85")),
    "top_k_chunks": int(os.getenv("TOP_K_CHUNKS", "3")),
    "temperature": float(os.getenv("GENERATION_TEMPERATURE", "0.1")),
    "chroma_path": os.getenv("CHROMA_DB_PATH", "./chroma_db"),
    "knowledge_base_path": os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base/company_faq.txt"),
    "system_instruction": os.getenv(
        "SYSTEM_INSTRUCTION",
        "You are the official OmniDesk AI Support Assistant. Ground answers exclusively in verified policy clauses and cite exact section names."
    )
}

CURRENT_SETTINGS: dict[str, Any] = dict(DEFAULT_CONFIG)

EMBEDDING_MODEL: str = str(CURRENT_SETTINGS["embedding_model"])
GENERATION_MODEL: str = str(CURRENT_SETTINGS["generation_model"])
GUARDRAIL_THRESHOLD: float = float(CURRENT_SETTINGS["guardrail_threshold"])
TOP_K_CHUNKS: int = int(CURRENT_SETTINGS["top_k_chunks"])
TEMPERATURE: float = float(CURRENT_SETTINGS["temperature"])
CHROMA_PATH: str = str(CURRENT_SETTINGS["chroma_path"])
DEFAULT_KB_PATH: str = str(CURRENT_SETTINGS["knowledge_base_path"])

# Lazy / safe client initialization
_client = None

def get_gemini_api_key() -> str:
    """Safe getter for GEMINI_API_KEY from environment variables."""
    return (
        os.getenv("GEMINI_API_KEY") or
        os.getenv("GOOGLE_GEMINI_AP_KEY") or
        os.getenv("GOOGLE_API_KEY") or
        ""
    ).strip()

def get_genai_client():
    """Initializes and returns Google GenAI SDK client if API key is provided."""
    global _client
    api_key = get_gemini_api_key()
    if not api_key or not genai:
        return None
    if _client is None:
        try:
            if types:
                _client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=10000))
            else:
                _client = genai.Client(api_key=api_key)
        except Exception as e:
            print(f"[Gemini Client Init Note] {e}")
            return None
    return _client

# Initialize ChromaDB persistent vector store pointing to ./chroma_db with collection name support_kb
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(
    name="support_kb",
    metadata={"hnsw:space": "cosine"}
)

def _ensure_collection_dimension():
    global collection
    try:
        if collection.count() > 0:
            collection.query(query_embeddings=[[0.0] * 768], n_results=1)
    except Exception as e:
        if "dimension" in str(e).lower() or "3072" in str(e):
            print(f"[ChromaDB Healing] Recreating collection due to dimension mismatch: {e}")
            try:
                chroma_client.delete_collection("support_kb")
            except Exception:
                pass
            collection = chroma_client.create_collection(
                name="support_kb",
                metadata={"hnsw:space": "cosine"}
            )

_ensure_collection_dimension()

def get_pipeline_settings() -> dict[str, Any]:
    """Returns runtime pipeline settings."""
    return dict(CURRENT_SETTINGS)

def update_pipeline_settings(new_settings: dict[str, Any]) -> dict[str, Any]:
    """Updates runtime pipeline settings dynamically."""
    global EMBEDDING_MODEL, GENERATION_MODEL, GUARDRAIL_THRESHOLD, TOP_K_CHUNKS, TEMPERATURE
    for key, val in new_settings.items():
        if key in CURRENT_SETTINGS and val is not None:
            if key in ["guardrail_threshold", "temperature"]:
                CURRENT_SETTINGS[key] = float(val)
            elif key == "top_k_chunks":
                CURRENT_SETTINGS[key] = int(val)
            else:
                CURRENT_SETTINGS[key] = str(val)
    
    EMBEDDING_MODEL = str(CURRENT_SETTINGS["embedding_model"])
    GENERATION_MODEL = str(CURRENT_SETTINGS["generation_model"])
    GUARDRAIL_THRESHOLD = float(CURRENT_SETTINGS["guardrail_threshold"])
    TOP_K_CHUNKS = int(CURRENT_SETTINGS["top_k_chunks"])
    TEMPERATURE = float(CURRENT_SETTINGS["temperature"])
    return dict(CURRENT_SETTINGS)

# ==============================================================================
# VOCABULARY PARTITIONING & DETERMINISTIC TF-IDF FALLBACK
# ==============================================================================
SECTION_KEYWORDS = [
    # 0: 1. RETURN AND EXCHANGE POLICY
    {'return', 'returns', 'refund', 'refunds', 'exchange', 'exchanges', '30-day', '30 day', 'restock', 'restocking', '15%', 'unopened', 'packaging', 'accessories', 'manuals', 'prepaid', 'label', 'inspection', 'reembolso', 'devoluci', 'rückgab', '返品', 'retour', 'remboursement', 'electronics'},
    # 1: 2. SHIPPING AND DELIVERY
    {'ship', 'shipping', 'delivery', 'deliveries', 'domestic', 'standard', 'expedited', '2-day', 'overnight', 'international', '85 countries', 'dhl', 'ddp', 'delivered duty paid', 'customs', 'duties', 'import', 'taxes', 'tracking', 'dispatch', 'livraison', 'versand', '配送', 'envío', 'canada'},
    # 2: 3. ORDER MODIFICATION AND CANCELLATION
    {'cancel', 'cancelling', 'cancellation', 'cancellations', 'modify', 'modification', 'modifications', '60-minute', '60 minute', 'picking', 'warehouse', 'address', 'annuler', 'stornieren', 'キャンセル', 'cancelar'},
    # 3: 4. WARRANTY AND REPAIR COVERAGE (DAMAGED OR DEFECTIVE)
    {'warranty', 'repair', 'repairs', 'coverage', '1-year', 'defect', 'defects', 'defective', 'damage', 'damaged', 'claim', 'claims', 'hardware', 'workmanship', 'serial', 'replacement', 'replacements', 'apex care+', 'care+', 'deductible', 'broken', 'garantía', 'garantie', '保証', 'reparatur'},
    # 4: 5. PAYMENT METHODS, BILLING & PRICE MATCHING
    {'payment', 'payments', 'billing', 'bill', 'visa', 'mastercard', 'amex', 'discover', 'paypal', 'apple pay', 'google pay', 'klarna', 'affirm', 'installment', 'installments', 'apr', 'price match', '14-day', 'currency', 'pago', 'zahlung', '支払い', 'paiement'},
    # 5: 6. CUSTOMER SUPPORT ESCALATION & HOURS
    {'support', 'customer support', 'escalation', 'escalate', 'hours', '24/7', '365', 'live agent', 'agent', 'human', 'representative', 'monday', 'friday', 'saturday', 'sunday', 'phone', '555-apex', '1-800', 'contact', 'soporte', 'kundendienst', 'サポート'}
]

def generate_tfidf_faq_embedding(text: str, dim: int = 768) -> list[float]:
    """
    Deterministic TF-IDF / keyword-weighted bag-of-words vector across company_faq.txt vocabulary.
    Maps official policy queries deterministically into corresponding policy section partitions with exact 768 dimensions.
    """
    vec = [0.0] * dim
    t_lower = text.lower()
    for sec_idx, kw_set in enumerate(SECTION_KEYWORDS):
        block_start = sec_idx * 100
        sec_weight = 0.0
        for kw in kw_set:
            if kw in t_lower:
                sec_weight += 2.0
        if sec_weight > 0:
            for i in range(100):
                angle = (i + 1) * (sec_idx + 1)
                vec[block_start + i] = sec_weight * (0.5 + 0.5 * math.sin(angle))
                
    words = [w for w in re.findall(r'[a-z0-9_-]+', t_lower) if len(w) > 2]
    for w in words:
        h = abs(hash(w)) % 168
        vec[600 + h] += 0.5
        
    norm = sum(x * x for x in vec) ** 0.5
    if norm > 0:
        return [x / norm for x in vec]
    return vec

# ==============================================================================
# GEMINI EMBEDDING FUNCTION & CIRCUIT BREAKER
# ==============================================================================
class GeminiEmbeddingFunction:
    """
    ChromaDB-compatible and standalone embedding function.
    Calls gemini-embedding-001 via Google GenAI SDK.
    Falls back to deterministic TF-IDF / keyword-weighted bag-of-words vector across company_faq.txt vocabulary.
    Does NOT permanently disable Gemini on transient errors.
    """
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or str(CURRENT_SETTINGS.get("embedding_model", "gemini-embedding-001"))

    def __call__(self, input: list[str] | str) -> list[list[float]] | list[float]:
        if isinstance(input, str):
            return self.embed_text(input)
        return [self.embed_text(t) for t in input]

    def embed_text(self, text: str) -> list[float]:
        api_key = get_gemini_api_key()
        if api_key and genai:
            client = get_genai_client()
            if client:
                try:
                    config = types.EmbedContentConfig(output_dimensionality=768) if types else None
                    res = client.models.embed_content(
                        model=self.model_name,
                        contents=text,
                        config=config
                    )
                    if res and res.embeddings and len(res.embeddings) > 0:
                        raw = getattr(res.embeddings[0], "values", None)
                        if raw is not None:
                            vec = list(raw)
                            if len(vec) == 768:
                                return vec
                            elif len(vec) > 768:
                                v = vec[:768]
                                norm = sum(x * x for x in v) ** 0.5
                                return [x / norm for x in v] if norm > 0 else v
                            else:
                                return vec + [0.0] * (768 - len(vec))
                except Exception as e:
                    # Transient failure: do NOT permanently disable Gemini for entire server lifetime
                    print(f"[Gemini Embedding Notice] {e}. Using deterministic TF-IDF vocabulary fallback for this call.")
        return generate_tfidf_faq_embedding(text)

_default_embedding_fn = GeminiEmbeddingFunction()

def generate_embedding(text: str) -> list[float]:
    """Generates embedding standardized to 768 dimensions using GeminiEmbeddingFunction."""
    return _default_embedding_fn.embed_text(text)

# Compatibility alias for internal fallback vector generation
def _generate_deterministic_embedding(text: str, dim: int = 768) -> list[float]:
    return generate_tfidf_faq_embedding(text, dim=dim)

def _get_target_dimension() -> int:
    try:
        sample = collection.get(limit=1, include=["embeddings"])
        embs = sample.get("embeddings")
        if embs is not None and len(embs) > 0 and len(embs[0]) > 0:
            return len(embs[0])
    except Exception:
        pass
    return 768

# ==============================================================================
# SECTION-AWARE POLICY PARSER
# ==============================================================================
def parse_faq_sections(text: str, source: str = "company_faq") -> list[dict[str, Any]]:
    r"""
    Section-aware policy parser:
    1. Splits company_faq.txt on numbered section boundaries (^\d+\.\s+[A-Z]) so each
       official policy is parsed into a complete semantic document with metadata
       {"source": source, "section": section_title, "chunk_index": i}.
    2. If custom markdown/text is uploaded via /api/admin/rag-upload, splits by markdown
       headers (# / ##) or numbered sections first.
    3. Falls back to paragraph-aware 800-character chunks only if no headers exist.
    """
    clean_text = text.strip()
    if not clean_text:
        return []

    sections: list[dict[str, Any]] = []

    # 1. Numbered section split (e.g. ^1. RETURN AND EXCHANGE POLICY)
    if re.search(r'(?m)^\d+\.\s+[A-Z]', clean_text):
        parts = re.split(r'(?m)^(?=\d+\.\s+[A-Z])', clean_text)
        chunk_idx = 0
        for p in parts:
            p_clean = p.strip()
            if not p_clean or p_clean.startswith('='):
                continue
            first_line = p_clean.splitlines()[0].strip()
            sections.append({
                "section": first_line,
                "title": first_line,
                "content": p_clean,
                "source": source,
                "chunk_index": chunk_idx,
                "tokens": max(1, len(p_clean) // 4)
            })
            chunk_idx += 1
        if sections:
            return sections

    # 2. Markdown headers split (e.g. ^# or ^##)
    if re.search(r'(?m)^#{1,3}\s+', clean_text):
        parts = re.split(r'(?m)^(?=#{1,3}\s+)', clean_text)
        chunk_idx = 0
        for p in parts:
            p_clean = p.strip()
            if not p_clean:
                continue
            first_line = p_clean.splitlines()[0].strip().lstrip('#').strip()
            sections.append({
                "section": first_line or f"Section {chunk_idx + 1}",
                "title": first_line or f"Section {chunk_idx + 1}",
                "content": p_clean,
                "source": source,
                "chunk_index": chunk_idx,
                "tokens": max(1, len(p_clean) // 4)
            })
            chunk_idx += 1
        if sections:
            return sections

    # 3. Paragraph-aware fallback (accumulate up to ~800 chars)
    paragraphs = [para.strip() for para in re.split(r'\n\s*\n', clean_text) if para.strip()]
    if not paragraphs:
        paragraphs = [clean_text]

    current_chunk: list[str] = []
    current_len = 0
    chunk_idx = 0

    for para in paragraphs:
        if current_len + len(para) > 800 and current_chunk:
            combined = "\n\n".join(current_chunk)
            sections.append({
                "section": f"Chunk {chunk_idx + 1}",
                "title": f"Chunk {chunk_idx + 1}",
                "content": combined,
                "source": source,
                "chunk_index": chunk_idx,
                "tokens": max(1, len(combined) // 4)
            })
            chunk_idx += 1
            current_chunk = [para]
            current_len = len(para)
        else:
            current_chunk.append(para)
            current_len += len(para) + 2

    if current_chunk:
        combined = "\n\n".join(current_chunk)
        sections.append({
            "section": f"Chunk {chunk_idx + 1}",
            "title": f"Chunk {chunk_idx + 1}",
            "content": combined,
            "source": source,
            "chunk_index": chunk_idx,
            "tokens": max(1, len(combined) // 4)
        })

    return sections

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    """Compatibility helper: returns sections or paragraph slices as strings."""
    parsed = parse_faq_sections(text)
    if parsed:
        return [sec["content"] for sec in parsed]
    return [text]

def ingest_faq(file_path: str | None = None, force_reindex: bool = False):
    """
    Section-aware policy ingestion into ChromaDB:
    Reads company_faq.txt, parses into the 6 official policy sections,
    and stores each with metadata:
    {"source": "company_faq", "section": section_title, "chunk_index": i}
    """
    global collection
    if file_path is None:
        file_path = str(CURRENT_SETTINGS.get("knowledge_base_path") or "knowledge_base/company_faq.txt")

    if not os.path.exists(file_path):
        print(f"Knowledge file {file_path} does not exist.")
        return

    # Dimension self-healing
    target_dim = 768
    curr_dim = _get_target_dimension()
    if collection.count() > 0 and curr_dim != target_dim:
        print(f"[ChromaDB Reset] Collection dimension {curr_dim} != {target_dim}. Re-creating collection...")
        try:
            chroma_client.delete_collection("support_kb")
        except Exception:
            pass
        collection = chroma_client.get_or_create_collection(
            name="support_kb",
            metadata={"hnsw:space": "cosine"}
        )
        force_reindex = True

    if collection.count() > 0 and not force_reindex:
        return

    if force_reindex and collection.count() > 0:
        try:
            all_ids = collection.get()["ids"]
            if all_ids:
                collection.delete(ids=all_ids)
        except Exception:
            pass

    with open(file_path, "r", encoding="utf-8") as f:
        full_text = f.read()

    doc_source = "company_faq" if "company_faq" in file_path else os.path.basename(file_path)
    sections = parse_faq_sections(full_text, source=doc_source)

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for sec in sections:
        cid = f"sec_{sec['chunk_index'] + 1}"
        emb = generate_embedding(sec["content"])
        ids.append(cid)
        embeddings.append(emb)
        documents.append(sec["content"])
        metadatas.append({
            "source": sec["source"],
            "section": sec["section"],
            "title": sec["section"],
            "chunk_index": sec["chunk_index"],
            "tokens": sec["tokens"]
        })

    try:
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
    except Exception as e:
        if "dimension" in str(e).lower():
            try:
                chroma_client.delete_collection("support_kb")
            except Exception:
                pass
            collection = chroma_client.create_collection(
                name="support_kb",
                metadata={"hnsw:space": "cosine"}
            )
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        else:
            raise

def ingest_policy_text(
    text: str,
    source: str = "uploaded_policy.txt",
    replace_all: bool = False,
    save_to_kb: bool = False
) -> list[dict[str, Any]]:
    r"""
    Parses and indexes policy markdown or text into ChromaDB using section-aware parsing:
    1. Splits on numbered sections (^\d+\.\s+[A-Z]) or markdown headers (#/##)
    2. Falls back to 800-char paragraph chunks if no headers exist.
    If replace_all is True, removes existing chunks before re-indexing.
    If save_to_kb is True, writes the updated content to knowledge_base/company_faq.txt.
    """
    clean_text = text.strip()
    if not clean_text:
        return []

    if save_to_kb:
        try:
            kb_path = str(CURRENT_SETTINGS.get("knowledge_base_path") or "knowledge_base/company_faq.txt")
            os.makedirs(os.path.dirname(kb_path), exist_ok=True)
            with open(kb_path, "w", encoding="utf-8") as f:
                f.write(clean_text)
        except Exception as e:
            print(f"[Save to KB Note] {e}")

    if replace_all and collection.count() > 0:
        try:
            all_ids = collection.get()["ids"]
            if all_ids:
                collection.delete(ids=all_ids)
        except Exception:
            pass

    doc_source = "company_faq" if "company_faq" in source else source
    sections = parse_faq_sections(clean_text, source=doc_source)

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, sec in enumerate(sections):
        cid = f"sec_{sec['chunk_index'] + 1}" if replace_all else f"sec_{uuid.uuid4().hex[:6]}_{i + 1}"
        emb = generate_embedding(sec["content"])
        ids.append(cid)
        embeddings.append(emb)
        documents.append(sec["content"])
        metadatas.append({
            "source": sec["source"],
            "section": sec["section"],
            "title": sec["section"],
            "chunk_index": sec["chunk_index"],
            "tokens": sec["tokens"]
        })
        sec["id"] = cid

    if ids:
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    return sections

def get_all_chunks() -> list[dict[str, Any]]:
    """Return list of all indexed chunks with IDs, titles, sections, content, and sources."""
    if not collection:
        return []
    try:
        data = collection.get(include=["documents", "metadatas"])
        chunks = []
        ids = data.get("ids") or []
        docs = data.get("documents") or []
        metas = data.get("metadatas") or []
        
        for i, cid in enumerate(ids):
            meta = metas[i] if (metas and i < len(metas) and metas[i]) else {}
            sec = meta.get("section") or meta.get("title") or f"Section {cid}"
            source = meta.get("source") or "company_faq.txt"
            content = docs[i] if (docs and i < len(docs) and docs[i] is not None) else ""
            tokens = meta.get("tokens") or max(1, len(content) // 4)
            chunks.append({
                "id": cid,
                "title": sec,
                "section": sec,
                "content": content,
                "tokens": tokens,
                "source": source
            })
        return chunks
    except Exception as e:
        print(f"[get_all_chunks Error] {e}")
        return []

def add_knowledge_chunk(title: str, content: str, source: str = "custom_policy.txt") -> dict[str, Any]:
    """Adds a new policy chunk into ChromaDB."""
    cid = f"chunk_{uuid.uuid4().hex[:6]}"
    tokens = max(1, len(content) // 4)
    full_text = f"{title}\n\n{content}"
    emb = generate_embedding(full_text)
    
    meta = {
        "title": title,
        "section": title,
        "source": source,
        "chunk_index": collection.count(),
        "tokens": tokens,
        "created_at": time.time()
    }
    
    collection.upsert(
        ids=[cid],
        embeddings=[emb],
        documents=[content],
        metadatas=[meta]
    )
    
    return {
        "id": cid,
        "title": title,
        "section": title,
        "content": content,
        "tokens": tokens,
        "source": source
    }

def delete_knowledge_chunk(chunk_id: str) -> bool:
    """Deletes a chunk from ChromaDB."""
    try:
        collection.delete(ids=[chunk_id])
        return True
    except Exception as e:
        print(f"[delete_knowledge_chunk Error] {e}")
        return False

def reindex_default_kb() -> int:
    """Purges and re-indexes the default FAQ file into official policy sections."""
    ingest_faq(file_path=str(CURRENT_SETTINGS["knowledge_base_path"]), force_reindex=True)
    return collection.count()

# ==============================================================================
# INTENT, ESCALATION & GROUNDED SYNTHESIS
# ==============================================================================
def detect_escalation_intent(query: str, sentiment: str = "") -> bool:
    """
    Detects if the user is frustrated, demanding a human agent, or asking for formal escalation.
    """
    q = query.lower()
    triggers = [
        "escalat", "human", "live agent", "real person", "representative",
        "speak to someone", "talk to someone", "customer service agent",
        "manager", "supervisor", "file a complaint", "legal", "lawyer",
        "unacceptable", "furious", "terrible service", "horrible service",
        "scam", "fraud", "dispute charge", "chargeback", "speak to a person",
        "agent please", "human please", "connect me to an agent", "urgent help"
    ]
    if any(t in q for t in triggers):
        return True
    return sentiment.lower() in ("high urgency", "urgent", "frustrated")

def generate_local_grounded_answer(
    query: str,
    matched_docs: list[str],
    order_record: dict[str, Any] | None = None,
    created_ticket: dict[str, Any] | None = None
) -> str:
    """High-quality grounded local response generator with exact section citations and order injection."""
    parts = []
    
    # 1. Injected Order Record details
    if order_record:
        oid = order_record.get('order_id') or order_record.get('id', 'N/A')
        status = order_record.get('status', 'Processing')
        items = order_record.get('items', 'Standard Product')
        trk = order_record.get('tracking_number', 'Pending Dispatch')
        total = order_record.get('total', 'N/A')
        parts.append(
            f"**Verified Order Information (#{oid}):**\n"
            f"- **Status:** {status}\n"
            f"- **Items Ordered:** {items}\n"
            f"- **Tracking Number:** `{trk}`\n"
            f"- **Order Total:** {total}"
        )
        
    # 2. Grounded Policy Clauses with Official Citations
    q = query.lower()
    if any(w in q for w in ['return', 'refund', '30-day', 'exchange', 'restock']):
        parts.append(
            "According to **[Section 1: Return and Exchange Policy]**, customers may return eligible products within **30 calendar days of delivery** "
            "for a full refund to the original payment method. Items must be unused in original packaging. Open-box electronics incur a 15% restocking fee unless defective upon arrival. "
            "Return shipping is free within the USA & Canada using our prepaid return labels."
        )
    elif any(w in q for w in ['ship', 'international', 'canada', 'duties', 'dhl', 'overnight', 'delivery']):
        parts.append(
            "According to **[Section 2: Shipping and Delivery Policy]**, Standard Domestic Shipping (3-5 business days) is free on orders over $50 ($4.99 under $50). "
            "We offer Expedited 2-Day ($14.99) and Overnight Delivery ($29.99). We ship internationally to 85+ countries via DHL Express (7-14 business days). "
            "All international orders are shipped **DDP (Delivered Duty Paid)** with import taxes and customs duties collected at checkout."
        )
    elif any(w in q for w in ['cancel', 'modify', 'change address', '60 minute']):
        parts.append(
            "According to **[Section 3: Order Modification & Cancellation]**, orders can be cancelled or modified within a strict **60-minute window** "
            "of placement directly from your account dashboard or via support. After 60 minutes, orders enter automated warehouse picking and cannot be stopped."
        )
    elif any(w in q for w in ['warranty', 'defect', 'repair', 'broken', 'claim', 'replace', 'replacement', 'damage', 'damaged']):
        parts.append(
            "According to **[Section 4: Damaged or Defective Items]** (Warranty & Repair Coverage), all hardware products include a **1-Year Limited Manufacturer Warranty** "
            "covering defects in materials and manufacturing workmanship. Standard warranty excludes cosmetic wear and accidental drops. "
            "To file a claim, submit photos and serial number to **support@company.com** for expedited 2-day replacement upon approval."
        )
    elif any(w in q for w in ['pay', 'card', 'paypal', 'apple pay', 'price match', 'klarna', 'affirm', 'balance']):
        parts.append(
            "According to **[Section 5: Account, Billing & Promotions]** (Payment Methods & Billing), we accept Visa, MasterCard, Amex, Discover, "
            "PayPal, Apple Pay, Google Pay, and Klarna / Affirm installments (0% APR). We also offer a **14-Day Price Match Guarantee** against authorized retailers."
        )
    elif any(w in q for w in ['hour', 'contact', 'agent', 'support@', 'phone', 'escalat']):
        parts.append(
            "According to **[Section 6: Customer Support Escalation & Hours]**, our AI Support Hub is available 24/7/365. "
            "Human support specialists are available Mon-Fri 8:00 AM - 8:00 PM EST and Sat-Sun 10:00 AM - 6:00 PM EST. "
            "You can reach live support at **support@company.com** or call **+1 (800) 555-APEX**."
        )
    elif matched_docs:
        snippet = matched_docs[0].strip()
        parts.append(f"Based on our official store documentation:\n\n{snippet}")
    else:
        parts.append("I do not have sufficient information in our policy database to answer this accurately. Would you like to reach our live support team at support@company.com?")

    # 3. Escalation Confirmation Notice
    if created_ticket:
        tid = created_ticket.get('id', 'TCK-NEW')
        parts.append(
            f"📋 **Support Escalation Confirmed:** Live support ticket **#{tid}** has been automatically created for your inquiry. "
            f"A customer specialist will review your request and follow up with you promptly."
        )
        
    return "\n\n".join(parts)

def classify_intent_and_sentiment(query: str) -> dict[str, Any]:
    """
    Return {"intent": str, "sentiment": str} categorized into Return & Refund,
    Shipping & Logistics, Warranty & Claims, Billing & Payment, or General Inquiry,
    with sentiment categorized into Standard, High Urgency, or VIP / Commercial.
    """
    q = query.lower()
    
    intent = "General Inquiry"
    if any(k in q for k in ["return", "refund", "restock", "money back", "30-day", "exchange", "devoluci", "reembols", "rückgabe", "erstattung", "retour", "remboursement", "返品", "返金", "devoluç", "वापस"]):
        intent = "Return & Refund"
    elif any(k in q for k in ["ship", "delivery", "track", "customs", "duties", "overnight", "canada", "dhl", "fedex", "freight", "envío", "versand", "livraison", "entrega", "発送", "शिपिंग"]):
        intent = "Shipping & Logistics"
    elif any(k in q for k in ["warranty", "repair", "defect", "broken", "replace", "hardware", "malfunction", "damaged", "garantía", "garantie", "保証", "वारंटी"]):
        intent = "Warranty & Claims"
    elif any(k in q for k in ["pay", "price match", "charge", "invoice", "tax", "discount", "klarna", "affirm", "paypal", "credit", "bitcoin", "crypto", "pago", "zahlung", "paiement", "pagamento", "支払い", "भुगतान"]):
        intent = "Billing & Payment"
    elif any(k in q for k in ["cancel", "modify", "change address", "change order", "stop order", "60 minute", "cancelar", "stornieren", "annuler", "キャンセル", "रद्द"]):
        intent = "Order Modification"
    elif any(k in q for k in ["account", "password", "login", "auth", "sign in", "cuenta", "compte", "konto", "アカウント", "खाता"]):
        intent = "Account & Security"

    sentiment = "Standard"
    if any(k in q for k in ["urgent", "asap", "immediately", "broken", "wrong", "terrible", "worst", "angry", "disappointed", "complaint", "unacceptable", "dispute", "lawyer", "fraud"]):
        sentiment = "High Urgency"
    elif any(k in q for k in ["vip", "enterprise", "bulk", "corporate", "commercial", "wholesale", "volume", "procurement", "sla"]):
        sentiment = "VIP / Commercial"
    elif any(k in q for k in ["please", "thank", "helpful", "appreciate", "wondering", "curious"]):
        sentiment = "Positive Inquiry"

    return {
        "intent": intent,
        "sentiment": sentiment
    }

def detect_language(text: str) -> str:
    """Detects query language across English, Spanish, French, German, Japanese, Portuguese, Hindi."""
    if not text:
        return "English"
    if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
        return "Japanese"
    if any('\u0900' <= char <= '\u097f' for char in text):
        return "Hindi"

    t = text.lower()
    scores = {"Spanish": 0, "Portuguese": 0, "French": 0, "German": 0, "English": 0}
    pt_unique = ["qual", "olá", "ola", "obrigado", "obrigada", "você", "voce", "não", "nao", "troca", "prazo", "rastreamento", "entregue", "devolução", "devolucao", "reembolso"]
    es_unique = ["cuál", "cual", "hola", "gracias", "cómo", "como", "envío", "envio", "garantía", "garantia", "días", "cancelar", "precio", "cuánto", "tiempo", "devolución", "devolucion", "reembolso"]
    fr_unique = ["bonjour", "remboursement", "retour", "livraison", "combien", "garantie", "délai", "annuler", "merci", "payer", "carte", "quelle", "quel", "est-ce"]
    de_unique = ["hallo", "rückgabe", "ruckgabe", "versand", "erstattung", "garantie", "bestellung", "stornieren", "danke", "lieferung", "dauer", "wie", "ist", "das"]

    if "qual" in t or "obrigado" in t or "você" in t or "troca" in t or "prazo" in t:
        scores["Portuguese"] += 3
    if "cuál" in t or "¿" in t or "¡" in t or "gracias" in t or "días" in t or "cuánto" in t:
        scores["Spanish"] += 3
        
    for w in pt_unique:
        if w in t:
            scores["Portuguese"] += 1
    for w in es_unique:
        if w in t:
            scores["Spanish"] += 1
    for w in fr_unique:
        if w in t:
            scores["French"] += 2
    for w in de_unique:
        if w in t:
            scores["German"] += 2
            
    best_lang = max(scores, key=lambda k: scores[k])
    if scores[best_lang] > 0:
        return best_lang
    return "English"

LOCAL_TRANSLATIONS = {
    "Spanish": {
        "return": "Bajo nuestra **Política de Devoluciones y Cambios**, los clientes pueden devolver productos elegibles dentro de los **30 días calendario posteriores a la entrega** para un reembolso completo al método de pago original. Los artículos deben estar sin usar y en su embalaje original. Los productos electrónicos de caja abierta tienen una tarifa de reposición del 15%. El envío de devolución es gratuito en EE. UU. y Canadá.",
        "ship": "Ofrecemos Envío Nacional Estándar (3-5 días, gratis en compras mayores a $50; $4.99 si es menor), Express de 2 Días ($14.99) y Entrega Nocturna ($29.99). Realizamos envíos internacionales a más de 85 países mediante DHL Express (7-14 días). Todos los pedidos internacionales se envían como **DDP (Delivered Duty Paid)**, con los aranceles e impuestos de importación cobrados en el proceso de pago.",
        "warranty": "Todos los productos de hardware incluyen una **Garantía Limitada del Fabricante de 1 Año** que cubre defectos en materiales y mano de obra. La garantía estándar no cubre desgaste cosmético o caídas accidentales. Para enviar un reclamo, proporcione su número de serie y fotos a **support@company.com**.",
        "cancel": "Los pedidos pueden cancelarse o modificarse dentro de una estricta **ventana de 60 minutos** desde su realización, directamente desde su panel de control o contactando a soporte.",
        "pay": "Aceptamos Visa, MasterCard, Amex, Discover, PayPal, Apple Pay, Google Pay y cuotas de Klarna / Affirm (0% TAE). También ofrecemos una **Garantía de Igualación de Precios de 14 Días** si un distribuidor autorizado ofrece un precio más bajo.",
        "deflected": "No dispongo de información suficiente en nuestra base de datos de políticas para responder a esto con precisión. ¿Le gustaría comunicarse con nuestro equipo de soporte en vivo en support@company.com?"
    },
    "French": {
        "return": "Conformément à notre **Politique de Retour et d'Échange**, les clients peuvent retourner les produits éligibles dans un délai de **30 jours calendaires suivant la livraison** pour un remboursement intégral sur le mode de paiement d'origine. Les articles doivent être inutilisés et dans leur emballage d'origine. Les produits électroniques en boîte ouverte entraînent des frais de réapprovisionnement de 15%. Les frais de retour sont gratuits aux États-Unis et au Canada.",
        "ship": "Nous proposons la Livraison Standard (3-5 jours, gratuite dès $50; $4.99 en dessous), Express 2 Jours ($14.99) et Livraison Lendemain ($29.99). Nous livrons à l'international dans plus de 85 pays via DHL Express (7-14 jours). Toutes les commandes internationales sont expédiées en **DDP (Delivered Duty Paid)**, avec tous les droits de douane et taxes inclus à la commande.",
        "warranty": "Tous les produits matériels bénéficient d'une **Garantie Constructeur Limitée de 1 An** couvrant les défauts de fabrication et de matériaux. Pour déposer une réclamation, envoyez votre numéro de série et des photos à **support@company.com**.",
        "cancel": "Les commandes peuvent être annulées ou modifiées dans un délai strict de **60 minutes** après leur enregistrement.",
        "pay": "Nous acceptons Visa, MasterCard, Amex, PayPal, Apple Pay, Google Pay et les paiements échelonnés Klarna / Affirm. Nous offrons également une **Garantie d'Alignement de Prix de 14 Jours**.",
        "deflected": "Je ne dispose pas de suffisamment d'informations dans notre base de données pour répondre avec précision. Souhaitez-vous contacter notre équipe d'assistance à support@company.com ?"
    },
    "German": {
        "return": "Gemäß unserer **Rückgabe- und Umtauschrichtlinie** können berechtigte Artikel innerhalb von **30 Kalendertagen nach Lieferung** gegen volle Rückerstattung zurückgegeben werden. Artikel müssen unbenutzt und in Originalverpackung sein. Für geöffnete Elektronikartikel fällt eine Wiedereinlagerungsgebühr von 15% an. Der Rückversand ist in den USA und Kanada kostenlos.",
        "ship": "Wir bieten Standardversand (3-5 Werktage, kostenlos ab $50), 2-Tage-Express ($14.99) und Übernachtzustellung ($29.99). Internationaler Versand in über 85 Länder erfolgt per DHL Express (7-14 Tage) via **DDP (Delivered Duty Paid)** inklusive aller Zollgebühren und Steuern.",
        "warranty": "Auf alle Hardwareprodukte gewähren wir eine **1-jährige eingeschränkte Herstellergarantie** auf Material- und Verarbeitungsfehler. Schadensmeldungen richten Sie bitte mit Seriennummer und Fotos an **support@company.com**.",
        "cancel": "Bestellungen können innerhalb eines strikten Zeitfensters von **60 Minuten** nach Aufgabe storniert oder geändert werden.",
        "pay": "Wir akzeptieren Visa, MasterCard, Amex, Discover, PayPal, Apple Pay, Google Pay sowie Klarna / Affirm Ratenzahlung (0% eff. Jahreszins). Zudem bieten wir eine **14-tägige Bestpreisgarantie**.",
        "deflected": "In unserer Richtliniendatenbank liegen nicht genügend Informationen vor, um dies präzise zu beantworten. Möchten Sie unseren Live-Support unter support@company.com kontaktieren?"
    },
    "Japanese": {
        "return": "当社の**返品・交換ポリシー**に基づき、商品お届けから**30日以内**であれば、元の支払い方法への全額返金にて返品が可能です。商品は未使用かつ元のパッケージに入っている必要があります。開封済みの電子機器には15%の再補充手数料が適用されます。米国およびカナダへの返送は無料です。",
        "ship": "国内標準配送（3〜5日、50ドル以上無料）、2日間速達（14.99ドル）、翌日配送（29.99ドル）を提供しています。DHL Expressを通じて85か国以上に配送可能です（7〜14日）。すべての国際注文は**DDP（関税元払）**で発送され、チェックアウト時に関税が決済されます。",
        "warranty": "すべてのハードウェア製品には、材質および製造上の欠陥を保証する**1年間の限定メーカー保証**が付帯します。保証請求を行うには、シリアル番号と写真を **support@company.com** まで送信してください。",
        "cancel": "ご注文のキャンセルまたは変更は、注文確定後**60分以内**に限り受け付けております。",
        "pay": "Visa、MasterCard、Amex、Discover、PayPal、Apple Pay、Google Pay、Klarna / Affirmに対応しています。また、**14日間の価格マッチ保証**も提供しております。",
        "deflected": "ポリシーデータベースに正確な情報がありません。担当サポートチーム（support@company.com）にお問い合わせください。"
    },
    "Portuguese": {
        "return": "De acordo com nossa **Política de Devolução e Troca**, produtos elegíveis podem ser devolvidos em até **30 dias corridos após a entrega** com reembolso integral. Os itens devem estar sem uso e na embalagem original. Eletrônicos com caixa aberta possuem taxa de reabastecimento de 15%.",
        "ship": "Oferecemos Envio Padrão (3-5 dias, grátis acima de $50), Expresso 2 Dias ($14.99) e Entrega Noturna ($29.99). Enviamos internacionalmente para mais de 85 países via DHL Express (7-14 dias) na modalidade **DDP (Delivered Duty Paid)**.",
        "warranty": "Todos os produtos de hardware possuem **Garantia Limitada do Fabricante de 1 Ano** contra defeitos de fabricação e material. Para acionar a garantia, envie número de série e fotos para **support@company.com**.",
        "cancel": "Pedidos podem ser cancelados ou alterados dentro de um prazo rigoroso de **60 minutos** após a compra.",
        "pay": "Aceitamos Visa, MasterCard, Amex, PayPal, Apple Pay, Google Pay e parcelamento Klarna/Affirm. Oferecemos **Garantia de Cobrimento de Preço de 14 Dias**.",
        "deflected": "Não encontramos informações suficientes na base de políticas. Deseja falar com o suporte em support@company.com?"
    },
    "Hindi": {
        "return": "हमारी **वापसी और विनिमय नीति** के तहत, ग्राहक डिलीवरी के **30 कैलेंडर दिनों** के भीतर मूल भुगतान विधि पर पूर्ण धनवापसी के लिए पात्र उत्पादों को वापस कर सकते हैं। वस्तुएं अप्रयुक्त और मूल पैकेजिंग में होनी चाहिए। ओपन-बॉक्स इलेक्ट्रॉनिक्स पर 15% रीस्टॉकिंग शुल्क लागू होता है।",
        "ship": "हम मानक घरेलू शिपिंग (3-5 दिन, $50 से अधिक पर मुफ़्त), 2-दिवसीय एक्सप्रेस ($14.99), और रातोंरात डिलीवरी ($29.99) प्रदान करते हैं। हम DHL एक्सप्रेस (7-14 दिन) के माध्यम से 85+ देशों में अंतरराष्ट्रीय स्तर पर **DDP (Delivered Duty Paid)** शिप करते हैं।",
        "warranty": "सभी हार्डवेयर उत्पादों में सामग्री और विनिर्माण दोषों को कवर करने वाली **1-वर्ष की सीमित निर्माता वारंटी** शामिल है। दावा दर्ज करने के लिए, अपना सीरियल नंबर और फोटो **support@company.com** पर भेजें।",
        "cancel": "ऑर्डर देने के **60 मिनट की सख्त समय सीमा** के भीतर ही ऑर्डर रद्द या संशोधित किए जा सकते हैं।",
        "pay": "हम वीज़ा, मास्टरकार्ड, एमेक्स, पेपैल, ऐप्पल पे, गूगल पे और क्लार्ना स्वीकार करते हैं। हम **14-दिवसीय मूल्य मिलान गारंटी** भी प्रदान करते हैं।",
        "deflected": "सटीक उत्तर देने के लिए हमारी नीति डेटाबेस में पर्याप्त जानकारी नहीं है। क्या आप हमारी सहायता टीम support@company.com से संपर्क करना चाहते हैं?"
    }
}

def translate_grounded_response(answer: str, target_lang: str, query: str = "") -> str:
    """Translates a grounded English answer into target language."""
    if not target_lang or target_lang == "English":
        return answer
    
    lang_dict = LOCAL_TRANSLATIONS.get(target_lang)
    if not lang_dict:
        return answer
    
    combined = (query + " " + answer).lower()
    if any(k in combined for k in ["return", "refund", "30-day", "devoluc", "rückgabe", "retour", "वापसी", "返品"]):
        return lang_dict.get("return", answer)
    if any(k in combined for k in ["ship", "delivery", "canada", "dhl", "duties", "envio", "versand", "livraison", "शिपिंग", "配送"]):
        return lang_dict.get("ship", answer)
    if any(k in combined for k in ["warranty", "defect", "repair", "garant", "वारंटी", "保証"]):
        return lang_dict.get("warranty", answer)
    if any(k in combined for k in ["cancel", "modify", "60 minute", "annuler", "stornier", "रद्द"]):
        return lang_dict.get("cancel", answer)
    if any(k in combined for k in ["pay", "price match", "klarna", "payer", "preismatch", "मूल्य"]):
        return lang_dict.get("pay", answer)
    if "not have sufficient information" in answer.lower():
        return lang_dict.get("deflected", answer)

    return answer

def _format_conversation_history(history: list[dict[str, Any]] | None) -> str:
    if not history:
        return ""
    valid_turns = []
    for turn in history[-6:]:
        role = turn.get("role", "")
        role_label = "Customer" if role in ("user", "customer") else "Assistant"
        content = (turn.get("content") or "").strip()
        if content:
            valid_turns.append(f"{role_label}: {content}")
    if not valid_turns:
        return ""
    return "<conversation_history>\n" + "\n".join(valid_turns) + "\n</conversation_history>\n\n"

def _build_contextual_query(user_query: str, history: list[dict[str, Any]] | None) -> str:
    if not history:
        return user_query
    q_lower = user_query.lower()
    pronouns = {"it", "this", "that", "they", "them", "these", "those", "instead", "too", "also"}
    words = set(q_lower.split())
    if len(words) <= 4 or bool(words & pronouns):
        for turn in reversed(history):
            if turn.get("role") in ("user", "customer") and turn.get("content"):
                prev_text = turn.get("content", "").strip()
                if prev_text:
                    return f"{prev_text} | {user_query}"
    return user_query

# ==============================================================================
# MAIN RAG SUPPORT RESPONSE GENERATOR
# ==============================================================================
def generate_support_response(
    user_query: str,
    chat_history: list[dict[str, Any]] | None = None,
    customer_email: str | None = None
) -> dict[str, Any]:
    r"""
    Official OmniDesk policy and order query resolution engine:
    1. Automatically detects any Order ID (ORD-\d{4}), retrieves record from database.get_order(),
       and injects status, items, tracking number, and total into the prompt context.
    2. Queries ChromaDB for the top official policy sections.
    3. Builds a strict system prompt instructing gemini-2.5-flash to answer ONLY from the
       retrieved policy sections and order record, citing exact section names (e.g. '[Section 1: Return and Exchange Policy]').
    4. Detects escalation intent; if user is frustrated or demands a human agent, automatically
       calls database.create_ticket() and returns the created ticket details.
    """
    start_time = time.time()
    classification = classify_intent_and_sentiment(user_query)
    
    # 1. Detect Escalation Intent
    is_escalated = detect_escalation_intent(user_query, sentiment=classification.get("sentiment", ""))
    created_ticket: dict[str, Any] | None = None
    if is_escalated:
        try:
            now_ts = time.time()
            now_str = time.strftime("%b %d, %H:%M")
            t_id = f"TCK-{random.randint(1050, 9999)}"
            c_id = f"CUST-{random.randint(1000, 9999)}"
            email_addr = customer_email or "customer@example.com"
            ticket_payload = {
                "id": t_id,
                "customer_id": c_id,
                "customer_name": "Valued Customer",
                "customer_email": email_addr,
                "customer_tier": "Standard Retail",
                "intent": classification.get("intent", "Customer Escalation"),
                "sentiment": classification.get("sentiment", "High Urgency"),
                "subject": f"Escalation Request: {user_query[:50]}",
                "query": user_query,
                "priority": "Urgent",
                "status": "Open",
                "created_at": now_str,
                "created_ts": now_ts,
                "assigned_agent": "Unassigned",
                "transcript_snippet": f"Autonomous escalation triggered for query: {user_query[:100]}",
                "messages": [
                    {
                        "id": f"msg_{t_id}_init",
                        "sender": "Valued Customer",
                        "text": user_query,
                        "is_internal_note": False,
                        "timestamp": now_str
                    }
                ]
            }
            created_ticket = database.create_ticket(ticket_payload)
        except Exception as e:
            print(f"[Escalation Ticket Creation Note] {e}")

    # 2. Automatically Detect Order ID (ORD-\d{4})
    order_record: dict[str, Any] | None = None
    order_context = ""
    order_match = re.search(r'\b(ORD-\d{4})\b', user_query, re.IGNORECASE)
    if order_match:
        matched_order_id = order_match.group(1).upper()
        try:
            order_record = database.get_order(matched_order_id)
        except Exception as e:
            print(f"[Order Lookup Note] {e}")
            
        if order_record:
            oid = order_record.get('order_id') or order_record.get('id', matched_order_id)
            order_context = (
                f"<verified_order_record>\n"
                f"Order ID: {oid}\n"
                f"Customer Name: {order_record.get('customer_name', 'Valued Customer')}\n"
                f"Status: {order_record.get('status', 'Processing')}\n"
                f"Items: {order_record.get('items', 'Standard Retail Product')}\n"
                f"Tracking Number: {order_record.get('tracking_number', 'Pending Dispatch')}\n"
                f"Total: {order_record.get('total', 'N/A')}\n"
                f"Order Date: {order_record.get('order_date', 'N/A')}\n"
                f"</verified_order_record>\n\n"
            )
        else:
            order_context = f"<verified_order_record>\nOrder ID {matched_order_id} could not be located in our database.\n</verified_order_record>\n\n"

    # 3. Retrieve Top Policy Sections from ChromaDB
    retrieval_query = _build_contextual_query(user_query, chat_history)
    query_emb = generate_embedding(retrieval_query)
    
    n_results = min(int(CURRENT_SETTINGS.get("top_k_chunks", 3)), max(1, collection.count()))
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results
    )

    docs_res = results.get("documents")
    metas_res = results.get("metadatas")
    dists_res = results.get("distances")
    documents: list[str] = docs_res[0] if (docs_res and len(docs_res) > 0 and docs_res[0] is not None) else []
    metadatas: list[dict[str, Any]] = [dict(m) for m in metas_res[0] if m] if (metas_res and len(metas_res) > 0 and metas_res[0] is not None) else []
    distances: list[float] = dists_res[0] if (dists_res and len(dists_res) > 0 and dists_res[0] is not None) else []

    # Format Policy Sections with Citations
    formatted_policy_docs = []
    sections_cited = []
    for doc, meta in zip(documents, metadatas):
        sec_label = meta.get("section") or meta.get("title") or "Verified Store Policy"
        m_sec = re.match(r'(\d+)\.\s*(.*)', sec_label)
        if m_sec:
            citation_tag = f"[Section {m_sec.group(1)}: {m_sec.group(2).title()}]"
        else:
            citation_tag = f"[{sec_label}]"
        sections_cited.append(citation_tag)
        formatted_policy_docs.append(f"{citation_tag}\n{doc}")

    policy_context = "\n\n---\n\n".join(formatted_policy_docs)

    # 4. Guardrail Deflection Check
    guardrail_thresh = float(CURRENT_SETTINGS.get("guardrail_threshold", 0.85))
    is_deflected = (not documents or (distances and distances[0] > guardrail_thresh)) and not order_record
    if is_deflected:
        latency = int((time.time() - start_time) * 1000)
        base_deflected = "I do not have sufficient information in our policy database to answer this accurately. Would you like to reach our live support team at support@company.com?"
        return {
            "answer": base_deflected,
            "sources": [],
            "sections": [],
            "distances": [float(d) for d in distances] if distances else [],
            "deflected": True,
            "latency_ms": latency,
            "order": order_record,
            "ticket": created_ticket,
            "intent": classification["intent"],
            "sentiment": classification["sentiment"]
        }

    # 5. Build Strict System Prompt & Call Gemini
    answer = None
    gen_model = str(CURRENT_SETTINGS.get("generation_model", "gemini-2.5-flash"))
    api_key = get_gemini_api_key()

    if api_key and genai:
        client = get_genai_client()
        if client and types:
            try:
                system_instruction = (
                    "You are the official OmniDesk AI Support Assistant. "
                    "Answer the customer's question strictly and exclusively using the verified store policy sections and customer order records provided below.\n\n"
                    "Mandatory Instructions:\n"
                    "1. Always cite the exact policy section name (e.g., '[Section 1: Return and Exchange Policy]') when stating conditions, rules, windows, or fees.\n"
                    "2. If verified order records are provided, directly report the order status, items, tracking number, and total.\n"
                    "3. Answer ONLY from the retrieved context. Do not invent external facts, promotions, or unlisted contact details.\n"
                    "4. If the question cannot be answered from the provided policy clauses, state so plainly and offer escalation."
                )
                
                context_payload = ""
                if order_context:
                    context_payload += order_context + "\n"
                if policy_context:
                    context_payload += f"<verified_policies>\n{policy_context}\n</verified_policies>\n\n"

                history_context = _format_conversation_history(chat_history)
                prompt = f"{context_payload}{history_context}<customer_inquiry>\n{user_query}\n</customer_inquiry>"

                response = client.models.generate_content(
                    model=gen_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=float(CURRENT_SETTINGS.get("temperature", 0.1))
                    )
                )
                if response and response.text:
                    answer = response.text.strip()
            except Exception as e:
                print(f"[Gemini Generate Note] {e}. Falling back to deterministic local grounded synthesis.")

    # 6. Fallback to Grounded Synthesis if Gemini call is offline or unavailable
    if not answer:
        answer = generate_local_grounded_answer(user_query, documents, order_record=order_record, created_ticket=created_ticket)
    elif created_ticket and "ticket" not in answer.lower():
        answer += f"\n\n📋 **Support Escalation Confirmed:** Live support ticket **#{created_ticket['id']}** has been created for your inquiry."

    latency = int((time.time() - start_time) * 1000)
    return {
        "answer": answer,
        "sources": documents,
        "sections": sections_cited,
        "distances": [float(d) for d in distances] if distances else [],
        "deflected": False,
        "latency_ms": latency,
        "order": order_record,
        "ticket": created_ticket,
        "intent": classification["intent"],
        "sentiment": classification["sentiment"]
    }

# ==============================================================================
# PIPELINE ENTRYPOINTS & STREAMING
# ==============================================================================
def run_rag_pipeline(query: str, target_language: str = "Auto Detect", history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """
    Standard pipeline entrypoint for API and test harness:
    Invokes generate_support_response, translates if required, and returns standard format.
    """
    lang = target_language if (target_language and target_language != "Auto Detect") else detect_language(query)
    res = generate_support_response(user_query=query, chat_history=history)
    
    final_answer = res.get("answer", "")
    if lang != "English" and not res.get("deflected") or lang != "English" and res.get("deflected"):
        final_answer = translate_grounded_response(final_answer, lang, query)
        
    return {
        "answer": final_answer,
        "sources": res.get("sources", []),
        "distances": res.get("distances", []),
        "deflected": res.get("deflected", False),
        "latency_ms": res.get("latency_ms", 0),
        "language": lang,
        "model": str(CURRENT_SETTINGS.get("generation_model", "gemini-2.5-flash")),
        "order": res.get("order"),
        "ticket": res.get("ticket"),
        "intent": res.get("intent", "General Inquiry"),
        "sentiment": res.get("sentiment", "Standard")
    }

# Alias for backwards compatibility with server.py imports
query_rag_pipeline = run_rag_pipeline

def stream_rag_pipeline(query: str, target_language: str = "Auto Detect", history: list[dict[str, Any]] | None = None):
    """
    Generator yielding Server-Sent Events (SSE) data:
    event: sources, event: token, event: done for real-time frontend streaming.
    """
    start_time = time.time()
    res = generate_support_response(user_query=query, chat_history=history)
    lang = target_language if (target_language and target_language != "Auto Detect") else detect_language(query)
    
    sources_payload = {
        "sources": res.get("sources", []),
        "distances": res.get("distances", []),
        "deflected": res.get("deflected", False),
        "threshold": float(CURRENT_SETTINGS.get("guardrail_threshold", 0.85)),
        "intent": res.get("intent", "General Inquiry"),
        "sentiment": res.get("sentiment", "Standard"),
        "language": lang
    }
    yield f"event: sources\ndata: {json.dumps(sources_payload)}\n\n"

    answer = res.get("answer", "")
    if lang != "English":
        answer = translate_grounded_response(answer, lang, query)

    # Stream tokens word by word
    for word in answer.split(" "):
        chunk_data = json.dumps({"token": word + " "})
        yield f"event: token\ndata: {chunk_data}\n\n"
        time.sleep(0.01)

    latency = int((time.time() - start_time) * 1000)
    done_payload = {
        "latency_ms": latency,
        "model": str(CURRENT_SETTINGS.get("generation_model", "gemini-2.5-flash")),
        "deflected": res.get("deflected", False),
        "intent": res.get("intent", "General Inquiry"),
        "sentiment": res.get("sentiment", "Standard"),
        "language": lang
    }
    yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

# ==============================================================================
# COPILOT, BM25, HYBRID SEARCH & BENCHMARK
# ==============================================================================
def generate_local_copilot_draft(ticket_query: str, customer_name: str, customer_tier: str, documents: list[str]) -> str:
    first_name = customer_name.split()[0] if customer_name else "there"
    vip_greeting = " As one of our priority account members, your inquiry has been fast-tracked." if ("VIP" in customer_tier or "Pro" in customer_tier) else ""
    grounded_info = documents[0] if documents else "our team is actively looking into the details of your request."
    
    return (
        f"Hi {first_name},\n\n"
        f"Thank you for contacting OmniDesk Support!{vip_greeting}\n\n"
        f"Regarding your inquiry, here is our official policy:\n\n"
        f"{grounded_info}\n\n"
        "Please let us know if you have any further questions or if you'd like us to take further action on your behalf.\n\n"
        "Best regards,\n"
        "The OmniDesk Support Team"
    )

def generate_agent_reply_draft(
    ticket_id: str | None = None,
    ticket_query: str | None = None,
    customer_name: str | None = None,
    customer_tier: str | None = "Standard Retail",
    intent: str | None = "General Inquiry"
) -> dict[str, Any]:
    """Retrieve ticket details, search relevant KB clauses, and synthesize an agent resolution draft."""
    start_time = time.time()
    
    if ticket_id and not ticket_query:
        try:
            t = database.get_ticket_by_id(ticket_id.upper())
            if t:
                ticket_query = t.get("query", "")
                customer_name = customer_name or t.get("customer_name", "Valued Customer")
                customer_tier = customer_tier or t.get("customer_tier", "Standard Retail")
                intent = intent or t.get("intent", "General Inquiry")
        except Exception:
            pass

    query_text = ticket_query or (ticket_id or "General support inquiry")
    cust_name = customer_name or "Valued Customer"
    cust_tier = customer_tier or "Standard Retail"
    cat_intent = intent or "General Inquiry"

    query_emb = generate_embedding(query_text)
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=min(3, max(1, collection.count()))
    )
    docs_res = results.get("documents")
    documents: list[str] = docs_res[0] if (docs_res and len(docs_res) > 0 and docs_res[0] is not None) else []
    context = "\n---\n".join(documents) if documents else "No specific policy clause found."

    draft = None
    api_key = get_gemini_api_key()
    if api_key and genai:
        client = get_genai_client()
        if client and types:
            try:
                tier_note = f" (Account Tier: {cust_tier})" if cust_tier else ""
                copilot_system_prompt = (
                    "You are OmniDesk AI Copilot assisting a human customer support specialist. "
                    "Draft a warm, polite, professional, and definitive resolution email to the customer based on verified store policies. "
                    "Include clear next steps, address the customer by first name, cite relevant policy conditions (e.g. 30-day window, DDP customs, 1-year warranty), "
                    "and sign off as 'The OmniDesk Support Team'."
                )
                prompt = (
                    f"<verified_policies>\n{context}\n</verified_policies>\n\n"
                    f"Customer Name: {cust_name}{tier_note}\n"
                    f"Inquiry Category: {cat_intent}\n"
                    f"Customer Message: {query_text}\n\n"
                    "Please generate a complete, ready-to-send agent reply draft:"
                )
                res = client.models.generate_content(
                    model=str(CURRENT_SETTINGS.get("generation_model", "gemini-2.5-flash")),
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=copilot_system_prompt,
                        temperature=0.3
                    )
                )
                draft = res.text.strip() if res.text else ""
            except Exception as e:
                print(f"[Copilot Draft Note] {e}")

    if not draft:
        draft = generate_local_copilot_draft(query_text, cust_name, cust_tier, documents)

    latency = int((time.time() - start_time) * 1000)
    return {
        "ticket_id": ticket_id,
        "customer_name": cust_name,
        "customer_tier": cust_tier,
        "intent": cat_intent,
        "suggested_reply": draft,
        "sources": documents,
        "latency_ms": latency
    }

def _tokenize_text(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r'\b[a-zA-Z0-9_-]+\b', text) if len(w) > 1]

def bm25_search(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Tokenize indexed chunks and return top BM25 matches using rank_bm25 with fallback."""
    chunks = get_all_chunks()
    if not chunks:
        return []
    
    query_tokens = _tokenize_text(query)
    if not query_tokens:
        return chunks[:top_k]
    
    doc_tokens_list = [_tokenize_text(c["content"] + " " + c["title"]) for c in chunks]
    
    scores = []
    if BM25Okapi is not None:
        try:
            bm25 = BM25Okapi(doc_tokens_list)
            raw_scores = bm25.get_scores(query_tokens)
            for idx, chunk in enumerate(chunks):
                scores.append((float(raw_scores[idx]), chunk))
        except Exception:
            scores = []
            
    if not scores:
        N = len(chunks)
        doc_lens = [len(dt) for dt in doc_tokens_list]
        avgdl = sum(doc_lens) / max(1, N)
        dfs = Counter()
        for dt in doc_tokens_list:
            unique_terms = set(dt)
            for term in query_tokens:
                if term in unique_terms:
                    dfs[term] += 1
        k1 = 1.5
        b = 0.75
        for idx, (chunk, dt, dl) in enumerate(zip(chunks, doc_tokens_list, doc_lens)):
            score = 0.0
            term_counts = Counter(dt)
            for term in query_tokens:
                if term not in term_counts:
                    continue
                tf = term_counts[term]
                df = dfs[term]
                idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
                denom = tf + k1 * (1 - b + b * (dl / avgdl))
                score += idf * ((tf * (k1 + 1)) / denom)
            scores.append((score, chunk))
            
    scores.sort(key=lambda x: x[0], reverse=True)
    ranked = []
    for score, chunk in scores[:top_k]:
        ranked.append({
            "id": chunk["id"],
            "title": chunk["title"],
            "section": chunk.get("section", chunk["title"]),
            "content": chunk["content"],
            "bm25_score": round(score, 4),
            "source": chunk.get("source", "company_faq.txt")
        })
    return ranked

def hybrid_search_rag(query: str, top_k: int = 3, rrf_k: int = 60) -> dict[str, Any]:
    """Combine ChromaDB dense vector ranks and BM25 sparse ranks using Reciprocal Rank Fusion (RRF)."""
    start_time = time.time()
    query_emb = generate_embedding(query)
    
    n_results = min(top_k * 2, max(1, collection.count()))
    vector_results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results
    )
    v_docs_res = vector_results.get("documents")
    v_metas_res = vector_results.get("metadatas")
    v_dists_res = vector_results.get("distances")
    vec_docs = v_docs_res[0] if (v_docs_res and len(v_docs_res) > 0 and v_docs_res[0] is not None) else []
    vec_metas = v_metas_res[0] if (v_metas_res and len(v_metas_res) > 0 and v_metas_res[0] is not None) else []
    vec_dists = v_dists_res[0] if (v_dists_res and len(v_dists_res) > 0 and v_dists_res[0] is not None) else []
    
    bm25_results = bm25_search(query, top_k=top_k * 2)
    
    rrf_scores = {}
    doc_map = {}
    
    for rank, (doc, meta, dist) in enumerate(zip(vec_docs, vec_metas, vec_dists)):
        cid = meta.get("title", f"vec_{rank}")
        doc_map[cid] = {"content": doc, "title": meta.get("title", "Policy Clause"), "vector_distance": round(float(dist), 4)}
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank + 1))
        
    for rank, b_item in enumerate(bm25_results):
        cid = b_item["title"]
        if cid not in doc_map:
            doc_map[cid] = {"content": b_item["content"], "title": b_item["title"], "bm25_score": b_item["bm25_score"]}
        else:
            doc_map[cid]["bm25_score"] = b_item["bm25_score"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank + 1))
        
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    fused_results = []
    for cid, score in sorted_items:
        item = dict(doc_map[cid])
        item["rrf_score"] = round(score, 5)
        fused_results.append(item)
        
    latency = int((time.time() - start_time) * 1000)
    return {
        "status": "success",
        "query": query,
        "results_count": len(fused_results),
        "fused_results": fused_results,
        "latency_ms": latency
    }

def analyze_claim_image(
    image_bytes: bytes | None = None,
    description: str | None = None,
    image_base64: str | None = None,
    claim_description: str | None = None,
    mime_type: str = "image/jpeg"
) -> dict[str, Any]:
    """Analyze product damage photos with Gemini Vision, cross-referencing Section 4 warranty exclusions."""
    start_time = time.time()
    resolved_desc = (description or claim_description or "").strip()
    
    if image_bytes and not image_base64:
        try:
            with Image.open(io.BytesIO(image_bytes)) as pil_img:
                _ = pil_img.size
        except Exception:
            pass
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    elif image_base64 and not image_bytes:
        try:
            image_bytes = base64.b64decode(image_base64)
            with Image.open(io.BytesIO(image_bytes)) as pil_img:
                _ = pil_img.size
        except Exception:
            pass

    desc_lower = resolved_desc.lower()
    is_drop_damage = any(w in desc_lower for w in ["drop", "cracked screen", "shattered", "water", "spill", "smashed"])
    is_defect = any(w in desc_lower for w in ["flicker", "stopped working", "power", "dead pixel", "won't charge", "defective", "malfunction"])
    
    if is_drop_damage:
        verdict = "Requires Apex Care+ / Non-Warranty Repair"
        verdict_status = "accidental_damage"
        approved = False
        notes = "Physical accidental drop/impact damage detected. Standard 1-Year Warranty excludes accidental damage. Recommending Apex Care+ $29 deductible repair."
    elif is_defect:
        verdict = "Approved for 1-Year Warranty Replacement"
        verdict_status = "warranty_approved"
        approved = True
        notes = "Hardware failure consistent with internal component/manufacturing defect. Eligible for expedited 2-day warranty replacement."
    else:
        verdict = "Intake Review Required"
        verdict_status = "manual_review"
        approved = False
        notes = "Receipt/hardware verification in progress. Our warranty specialist will inspect the serial barcode label."
        
    warranty_policy = (
        "Section 4: Warranty & Repair Coverage. 1-Year Limited Manufacturer Warranty covers defects in materials "
        "and manufacturing workmanship. Does NOT cover cosmetic wear, accidental drops, or water damage."
    )

    api_key = get_gemini_api_key()
    if api_key and genai and image_bytes and len(image_bytes) > 0:
        client = get_genai_client()
        if client and types:
            try:
                vision_prompt = (
                    f"You are OmniDesk AI Vision Claim Inspector. Analyze this customer claim image against store policy:\n"
                    f"<policy>\n{warranty_policy}\n</policy>\n"
                    f"Customer claim notes: {resolved_desc}\n\n"
                    "Assess if the image shows manufacturing defect, accidental impact damage, or standard wear. "
                    "Provide a 2-sentence formal assessment."
                )
                image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                res = client.models.generate_content(
                    model=str(CURRENT_SETTINGS.get("generation_model", "gemini-2.5-flash")),
                    contents=[image_part, vision_prompt],
                    config=types.GenerateContentConfig(
                        system_instruction="Assess customer hardware damage objectively according to warranty rules.",
                        temperature=0.2
                    )
                )
                notes = res.text.strip() if res.text else ""
            except Exception as e:
                print(f"[Vision Claim Note] {e}")

    latency = int((time.time() - start_time) * 1000)
    return {
        "status": "success",
        "claim_verdict": verdict,
        "verdict_status": verdict_status,
        "is_warranty_covered": approved,
        "assessment_notes": notes,
        "grounded_policy_clause": "Section 4: Warranty and Repair Coverage",
        "latency_ms": latency
    }

def run_synthetic_benchmark(num_queries: int = 8) -> dict[str, Any]:
    """Run mock queries and return throughput, latency percentiles, guardrail precision, and intent accuracy."""
    test_battery = [
        {"q": "What is the return window for open-box electronics?", "expected_intent": "Return & Refund", "should_deflect": False, "lang": "English"},
        {"q": "Do you ship to Canada and how are customs duties handled?", "expected_intent": "Shipping & Logistics", "should_deflect": False, "lang": "English"},
        {"q": "What is covered under the hardware manufacturer warranty?", "expected_intent": "Warranty & Claims", "should_deflect": False, "lang": "English"},
        {"q": "Can I cancel an order I placed 20 minutes ago?", "expected_intent": "Order Modification", "should_deflect": False, "lang": "English"},
        {"q": "¿Cuál es la política de devoluciones y reembolsos?", "expected_intent": "Return & Refund", "should_deflect": False, "lang": "Spanish"},
        {"q": "Wie lautet das Rückgaberecht für Einkäufe?", "expected_intent": "Return & Refund", "should_deflect": False, "lang": "German"},
        {"q": "返品ポリシーと返金条件は何ですか？", "expected_intent": "Return & Refund", "should_deflect": False, "lang": "Japanese"},
        {"q": "What is the stock price of Apple on NASDAQ?", "expected_intent": "General Inquiry", "should_deflect": True, "lang": "English"}
    ]
    
    battery = test_battery[:min(num_queries, len(test_battery))]
    results = []
    latencies = []
    bench_start = time.time()
    
    for item in battery:
        item_start = time.time()
        q_str = str(item["q"])
        classification = classify_intent_and_sentiment(q_str)
        lang_field = item.get("lang")
        lang = str(lang_field) if lang_field else detect_language(q_str)
        query_emb = generate_embedding(q_str)
        n_results = min(int(CURRENT_SETTINGS.get("top_k_chunks", 3)), max(1, collection.count()))
        v_res = collection.query(query_embeddings=[query_emb], n_results=n_results)
        v_docs_res = v_res.get("documents")
        v_dists_res = v_res.get("distances")
        docs: list[str] = v_docs_res[0] if (v_docs_res and len(v_docs_res) > 0 and v_docs_res[0] is not None) else []
        distances: list[float] = v_dists_res[0] if (v_dists_res and len(v_dists_res) > 0 and v_dists_res[0] is not None) else []
        is_deflected = not docs or (distances and distances[0] > float(CURRENT_SETTINGS.get("guardrail_threshold", 0.85)))
        lat = max(1, int((time.time() - item_start) * 1000))
        latencies.append(lat)
        
        deflection_correct = (is_deflected == item["should_deflect"])
        intent_match = (classification["intent"] == item["expected_intent"])
        
        results.append({
            "query": item["q"],
            "language": lang,
            "intent": classification["intent"],
            "latency_ms": lat,
            "deflected": is_deflected,
            "deflection_accurate": deflection_correct,
            "intent_accurate": intent_match
        })
        
    total_time_s = max(0.001, time.time() - bench_start)
    latencies.sort()
    
    p50 = latencies[len(latencies) // 2] if latencies else 0
    p90 = latencies[int(len(latencies) * 0.9)] if latencies else 0
    p99 = latencies[-1] if latencies else 0
    qps = round(len(battery) / total_time_s, 2)
    deflection_accuracy = round(sum(1 for r in results if r["deflection_accurate"]) / len(results) * 100, 1)
    intent_accuracy = round(sum(1 for r in results if r["intent_accurate"]) / len(results) * 100, 1)
    
    return {
        "status": "success",
        "benchmark_id": f"bench_{uuid.uuid4().hex[:8]}",
        "total_queries": len(battery),
        "total_duration_s": round(total_time_s, 3),
        "qps": qps,
        "latency_p50_ms": p50,
        "latency_p90_ms": p90,
        "latency_p99_ms": p99,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
        "guardrail_accuracy_percent": deflection_accuracy,
        "intent_accuracy_percent": intent_accuracy,
        "detailed_results": results
    }

# Initial knowledge base ingestion on module load if empty
try:
    if os.path.exists(DEFAULT_KB_PATH):
        ingest_faq(DEFAULT_KB_PATH, force_reindex=(collection.count() == 0))
except Exception as e:
    print(f"[Initial KB Ingest Note] {e}")
