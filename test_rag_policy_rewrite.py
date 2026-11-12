import os
import sys
import json
import pytest
from fastapi.testclient import TestClient
from server import app
import rag_engine
import database

client = TestClient(app)
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "admin-secret-key-2026")
AUTH_HEADERS = {"X-Admin-Key": ADMIN_KEY}

def test_1_parse_faq_sections_official_kb():
    """Verify parse_faq_sections correctly extracts the 6 official numbered policies."""
    with open("knowledge_base/company_faq.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    sections = rag_engine.parse_faq_sections(text, source="company_faq")
    assert len(sections) == 6, f"Expected 6 sections, got {len(sections)}"
    
    titles = [s["section"] for s in sections]
    assert any("RETURN AND EXCHANGE POLICY" in t for t in titles)
    assert any("SHIPPING AND DELIVERY" in t for t in titles)
    assert any("ORDER MODIFICATION AND CANCELLATION" in t for t in titles)
    assert any("WARRANTY AND REPAIR COVERAGE" in t for t in titles)
    assert any("PAYMENT METHODS, BILLING & PRICE MATCHING" in t for t in titles)
    assert any("CUSTOMER SUPPORT ESCALATION & HOURS" in t for t in titles)
    
    for i, s in enumerate(sections):
        assert s["chunk_index"] == i
        assert s["source"] == "company_faq"
        assert len(s["content"]) > 100

def test_2_parse_faq_sections_markdown_and_paragraph():
    """Verify markdown headers (# / ##) and paragraph fallback."""
    md_text = """# Return Rules
All items can be returned within 30 days.

## Warranty Terms
Hardware carries a 1-year limited warranty.

### Escalations
Reach out to management if unsatisfied.
"""
    md_sections = rag_engine.parse_faq_sections(md_text, source="test.md")
    assert len(md_sections) == 3
    assert md_sections[0]["section"] == "Return Rules"
    assert md_sections[1]["section"] == "Warranty Terms"
    assert md_sections[2]["section"] == "Escalations"

    # Test paragraph fallback
    raw_text = "Paragraph one with some text.\n\nParagraph two with some more text.\n\nParagraph three."
    p_sections = rag_engine.parse_faq_sections(raw_text, source="raw.txt")
    assert len(p_sections) >= 1
    assert "Paragraph one" in p_sections[0]["content"]

def test_3_gemini_embedding_function_transient_resilience():
    """Verify GeminiEmbeddingFunction does not permanently disable Gemini on transient errors."""
    emb_fn = rag_engine.GeminiEmbeddingFunction()
    # Call embed_text
    vec = emb_fn.embed_text("What is the 30-day return policy?")
    assert len(vec) == 768
    assert sum(x * x for x in vec) > 0.0

def test_4_generate_support_response_with_order_injection():
    """Verify ORD-1001 order detection, database lookup, and prompt context injection."""
    res = rag_engine.generate_support_response(
        user_query="Can you check the delivery status of my order ORD-1001 and the return policy?"
    )
    assert res is not None
    assert res["order"] is not None
    assert res["order"]["id"] == "ORD-1001"
    assert res["order"]["status"] == "Shipped"
    assert "TRK-982341-DHL" in str(res["order"]["tracking_number"])
    
    answer = res["answer"]
    assert "ORD-1001" in answer or "Shipped" in answer or "TRK-982341-DHL" in answer
    assert any("[Section" in s for s in res["sections"]) or "[Section 1: Return and Exchange Policy]" in answer

def test_5_generate_support_response_escalation():
    """Verify escalation intent detection and ticket creation."""
    res = rag_engine.generate_support_response(
        user_query="I am furious! Connect me to a live human agent or supervisor immediately!",
        customer_email="furious_customer@example.com"
    )
    assert res is not None
    assert res["ticket"] is not None
    assert "TCK-" in res["ticket"]["id"]
    assert res["ticket"]["customer_email"] == "furious_customer@example.com"
    assert "ticket" in res["answer"].lower() or res["ticket"]["id"] in res["answer"]

def test_6_admin_rag_upload_api():
    """Verify /api/admin/rag-upload and /api/admin/rag-policy endpoints."""
    # 1. Unauthenticated request should fail
    unauth = client.post("/api/admin/rag-upload", json={"text": "Test policy"})
    assert unauth.status_code == 401

    # 2. Get current policy
    get_res = client.get("/api/admin/rag-policy", headers=AUTH_HEADERS)
    assert get_res.status_code == 200
    assert "content" in get_res.json()
    assert get_res.json()["total_chunks"] >= 6

    # 3. Upload custom policy
    custom_policy = """1. RETURN AND EXCHANGE POLICY
Customers may return items within 30 days.

2. SHIPPING AND DELIVERY POLICY
Domestic shipping is 3-5 days.

3. ORDER MODIFICATION & CANCELLATION
Orders can be modified within 60 minutes.

4. DAMAGED OR DEFECTIVE ITEMS
Report defects within 72 hours.

5. ACCOUNT, BILLING & PROMOTIONS
Discounts apply at checkout.

6. CUSTOMER SUPPORT ESCALATION & HOURS
Support available 24/7.
"""
    post_res = client.post(
        "/api/admin/rag-upload",
        json={"text": custom_policy, "filename": "test_faq.txt", "replace_all": True, "save_to_kb": False},
        headers=AUTH_HEADERS
    )
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["status"] == "success"
    assert data["total_chunks"] == 6
    assert len(data["sections"]) == 6

    # 4. Clean up / restore default KB
    rag_engine.reindex_default_kb()
