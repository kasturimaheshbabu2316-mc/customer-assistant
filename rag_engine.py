import os
import chromadb
from dotenv import load_dotenv

# Load environment configuration from .env and doc/.env
load_dotenv()
if os.path.exists("doc/.env"):
    load_dotenv("doc/.env")

# Configuration Variables
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gemini-3-flash")
GUARDRAIL_THRESHOLD = float(os.getenv("GUARDRAIL_DISTANCE_THRESHOLD", "1.2"))
TOP_K_CHUNKS = int(os.getenv("TOP_K_CHUNKS", "2"))
TEMPERATURE = float(os.getenv("GENERATION_TEMPERATURE", "0.1"))
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
DEFAULT_KB_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base/company_faq.txt")

# Lazy / safe client initialization
_client = None

def get_genai_client():
    global _client
    if _client is None:
        from google import genai
        api_key = (
            os.getenv("GEMINI_API_KEY") or
            os.getenv("GOOGLE_GEMINI_AP_KEY") or
            os.getenv("GOOGLE_API_KEY")
        )
        _client = genai.Client(api_key=api_key)
    return _client

# Initialize ChromaDB persistent vector store
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="support_kb")

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start += chunk_size - overlap
    return chunks

def ingest_faq(file_path: str = None):
    if file_path is None:
        file_path = DEFAULT_KB_PATH

    if not os.path.exists(file_path):
        print(f"Knowledge file {file_path} does not exist.")
        return

    if collection.count() > 0:
        print(f"Collection already contains {collection.count()} chunks. Ready.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        full_text = f.read()

    chunks = chunk_text(full_text)
    client = get_genai_client()
    
    print(f"Ingesting {len(chunks)} chunks into ChromaDB...")
    for idx, chunk in enumerate(chunks):
        try:
            emb_res = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=chunk
            )
            embedding = emb_res.embeddings[0].values
            collection.add(
                ids=[f"chunk_{idx}"],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source": file_path, "chunk_id": idx}]
            )
        except Exception as e:
            print(f"Error embedding chunk {idx}: {e}")
    print(f"Ingestion complete. Total items in DB: {collection.count()}")

def run_rag_pipeline(user_query: str) -> dict:
    client = get_genai_client()
    from google.genai import types

    # 1. Embed query
    query_emb = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=user_query
    ).embeddings[0].values

    # 2. Retrieve top matches
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=TOP_K_CHUNKS
    )

    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

    # Guardrail: Distance check (cosine/L2 threshold to stop empty inference)
    if not documents or (distances and distances[0] > GUARDRAIL_THRESHOLD):
        return {
            "answer": "I do not have sufficient information in our policy database to answer this accurately. Would you like to reach our live support team at support@company.com?",
            "sources": []
        }

    context = "\n---\n".join(documents)

    # 3. Grounded generation using gemini model
    system_instruction = (
        "You are an empathetic, concise Customer Support Assistant. "
        "Strict Rule: Rely ONLY on the facts explicitly mentioned in the provided <context>. "
        "Do not extrapolate, assume, or fabricate any rules, dates, or prices. "
        "If the answer is not explicitly written in the context, output: "
        "'I am sorry, but our documentation does not cover that. Please contact support@company.com.'"
    )

    prompt = f"""
    <context>
    {context}
    </context>

    Customer Query: {user_query}
    """

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=TEMPERATURE,
        )
    )

    return {
        "answer": response.text.strip(),
        "sources": documents
    }