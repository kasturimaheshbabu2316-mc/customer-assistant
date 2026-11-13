"""
OmniDesk AI — System Restoration Verification API Test Suite
Comprehensive verification tests covering:
1. Health & RAG index status (confirming all 6 numbered sections of company_faq.txt are indexed)
2. Policy grounding in Section 1 (return window and restocking fee)
3. Order context injection from SQLite (ORD-1002 status 'Shipped', tracking '1Z999AA10123456784')
4. Autonomous escalation trigger creates high-priority ticket visible in GET /api/tickets
5. Static security (.env -> 404) and clean desktop UI (no kid-assistant.js or clay-theme.js)
"""

import os
import sys
from pathlib import Path

# Ensure workspace root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from fastapi.testclient import TestClient

import database
from server import app

client = TestClient(app)


# ==============================================================================
# 1. HEALTH AND RAG STATUS: ALL 6 NUMBERED SECTIONS INDEXED
# ==============================================================================

def test_1_health_and_rag_status_indexed_sections():
    """
    1. Test GET /api/health and GET /api/rag/status confirm all 6 numbered sections
    of company_faq.txt are indexed.
    """
    # 1a. Test GET /api/health
    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Expected 200 from /api/health but got {res_health.status_code}: {res_health.text}"
    health_data = res_health.json()
    assert health_data.get("status") == "healthy", f"Health status not healthy: {health_data}"
    assert health_data.get("vector_count") >= 6, f"Expected at least 6 vector chunks in /api/health, got {health_data.get('vector_count')}"
    assert health_data.get("database") == "connected", f"Database not connected: {health_data}"
    assert health_data.get("chroma_connected") is True, f"Chroma not connected: {health_data}"

    # Also verify base /health alias behaves identically
    res_base_health = client.get("/health")
    assert res_base_health.status_code == 200
    assert res_base_health.json().get("vector_count") >= 6

    # 1b. Test GET /api/rag/status
    res_rag = client.get("/api/rag/status")
    assert res_rag.status_code == 200, f"Expected 200 from /api/rag/status but got {res_rag.status_code}: {res_rag.text}"
    rag_data = res_rag.json()
    assert rag_data.get("status") == "ready", f"RAG status not ready: {rag_data}"
    assert rag_data.get("total_chunks") >= 6, f"Expected total_chunks >= 6, got {rag_data.get('total_chunks')}"

    chunks = rag_data.get("chunks", [])
    assert len(chunks) >= 6, f"Expected at least 6 chunks in chunks list, got {len(chunks)}"

    # 1c. Confirm all 6 numbered sections of company_faq.txt are indexed
    expected_sections = [
        ("1. RETURN AND EXCHANGE POLICY", "30-Day Return Window"),
        ("2. SHIPPING AND DELIVERY", "Shipping"),
        ("3. ORDER MODIFICATION AND CANCELLATION", "Cancellation Window"),
        ("4. WARRANTY AND REPAIR COVERAGE", "Warranty"),
        ("5. PAYMENT METHODS, BILLING & PRICE MATCHING", "Payment Methods"),
        ("6. CUSTOMER SUPPORT ESCALATION & HOURS", "Customer Support Escalation"),
    ]

    titles = [chunk.get("title", "") for chunk in chunks]
    sections = [chunk.get("section", "") for chunk in chunks]
    chunk_ids = [chunk.get("id", "") for chunk in chunks]

    # Verify each expected section is indexed with proper title and content
    for expected_title_prefix, key_phrase in expected_sections:
        matching_chunks = [
            c for c in chunks
            if expected_title_prefix in c.get("title", "") or expected_title_prefix in c.get("section", "")
        ]
        assert len(matching_chunks) >= 1, (
            f"Expected section '{expected_title_prefix}' not found among indexed chunks. Titles: {titles}"
        )
        chunk_content = matching_chunks[0].get("content", "")
        assert chunk_content, f"Content for section '{expected_title_prefix}' is empty!"
        assert key_phrase.lower() in chunk_content.lower(), (
            f"Expected key phrase '{key_phrase}' not found in content of section '{expected_title_prefix}'"
        )

    # Verify chunk IDs exist for all 6 sections (sec_1 through sec_6)
    for i in range(1, 7):
        expected_cid = f"sec_{i}"
        assert any(expected_cid == cid for cid in chunk_ids), (
            f"Expected chunk ID '{expected_cid}' not found in chunk IDs: {chunk_ids}"
        )


# ==============================================================================
# 2. POLICY GROUNDING IN SECTION 1 (RETURN WINDOW & RESTOCKING FEE)
# ==============================================================================

def test_2_policy_question_grounded_in_section_1():
    """
    2. Test POST /api/chat with a policy question ("What is your return window and restocking fee?")
    returns a response grounded in Section 1.
    """
    query = "What is your return window and restocking fee?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"

    data = res.json()
    assert data.get("status") == "success", f"Chat status not success: {data}"
    assert data.get("deflected") is False, "Policy query should not be deflected"

    answer = data.get("answer", "")
    sources = data.get("sources", [])
    sections = data.get("sections", [])

    # Grounded in Section 1:
    # 1. Answer text must cite Section 1
    assert "Section 1" in answer, (
        f"Answer text missing explicit citation to 'Section 1'. Answer: {answer}"
    )

    # 2. Citations / sections metadata list must cite Section 1
    assert any("Section 1" in s for s in sections), (
        f"Sections metadata missing 'Section 1'. Sections: {sections}"
    )

    # 3. Must specify 30-day return window
    answer_lower = answer.lower()
    assert "30" in answer_lower or "30-day" in answer_lower, (
        f"Answer missing 30-day return window. Answer: {answer}"
    )

    # 4. Must specify 15% restocking fee
    assert "15%" in answer, (
        f"Answer missing explicit '15%' restocking fee details. Answer: {answer}"
    )

    # 5. Sources list must include Section 1 text
    assert len(sources) > 0, "Sources should not be empty"
    assert any("RETURN AND EXCHANGE POLICY" in s for s in sources), (
        "Sources do not include Return and Exchange Policy"
    )

    # 6. Intent correctly tagged as Return & Refund
    assert data.get("intent") == "Return & Refund", (
        f"Expected intent 'Return & Refund', got '{data.get('intent')}'"
    )
    assert data.get("order") is None, "Policy inquiry should not contain order context"


def test_2b_policy_question_with_message_key():
    """Verify POST /api/chat also accepts 'message' payload key for policy queries."""
    res = client.post("/api/chat", json={"message": "What is your return window and restocking fee?"})
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "success"
    assert "Section 1" in data.get("answer", "")
    assert "15%" in data.get("answer", "")


# ==============================================================================
# 3. ORDER CONTEXT INJECTION FROM SQLITE (ORD-1002 SHIPPED & TRACKING)
# ==============================================================================

def test_3_order_query_injects_sqlite_status():
    """
    3. Test POST /api/chat with an order query ("Where is ORD-1002?") injects
    the real SQLite order status (Shipped, tracking 1Z999AA10123456784).
    """
    # 3a. Verify the SQLite database record directly
    db_order = database.get_order("ORD-1002")
    assert db_order is not None, "ORD-1002 must exist in SQLite database"
    assert db_order["status"] == "Shipped", f"Expected status 'Shipped', got '{db_order['status']}'"
    assert db_order["tracking_number"] == "1Z999AA10123456784", (
        f"Expected tracking '1Z999AA10123456784', got '{db_order['tracking_number']}'"
    )
    assert "Elena Rostova" in db_order.get("customer_name", ""), "Customer name mismatch"
    assert "ErgoDesk Cable Management Tray" in db_order.get("items", ""), "Items mismatch"

    # 3b. Query chat endpoint with ORD-1002
    res = client.post("/api/chat", json={"query": "Where is ORD-1002?"})
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"

    data = res.json()
    assert data.get("status") == "success"

    # Order context must be injected in payload
    order_data = data.get("order")
    assert order_data is not None, "Expected order context in chat response"
    assert order_data["id"] == "ORD-1002"
    assert order_data["status"] == "Shipped", f"Expected 'Shipped', got '{order_data.get('status')}'"
    assert order_data["tracking_number"] == "1Z999AA10123456784", (
        f"Expected tracking '1Z999AA10123456784', got '{order_data.get('tracking_number')}'"
    )

    # Injected details must be reflected in the generated answer text
    answer = data.get("answer", "")
    assert "Shipped" in answer, f"Expected 'Shipped' in answer text: {answer}"
    assert "1Z999AA10123456784" in answer, f"Expected tracking '1Z999AA10123456784' in answer text: {answer}"

    # 3c. Case-insensitivity check: query with lowercase "ord-1002"
    res_lower = client.post("/api/chat", json={"query": "Can you check the delivery status for ord-1002 please?"})
    assert res_lower.status_code == 200
    data_lower = res_lower.json()
    assert data_lower.get("order") is not None
    assert data_lower["order"]["id"] == "ORD-1002"
    assert data_lower["order"]["status"] == "Shipped"
    assert data_lower["order"]["tracking_number"] == "1Z999AA10123456784"

    # 3d. Also verify direct GET /api/orders/ORD-1002 endpoint
    ord_endpoint_res = client.get("/api/orders/ORD-1002")
    assert ord_endpoint_res.status_code == 200
    assert ord_endpoint_res.json()["order"]["status"] == "Shipped"
    assert ord_endpoint_res.json()["order"]["tracking_number"] == "1Z999AA10123456784"


# ==============================================================================
# 4. AUTONOMOUS ESCALATION TRIGGER CREATES HIGH-PRIORITY TICKET
# ==============================================================================

def test_4_escalation_trigger_creates_high_priority_ticket():
    """
    4. Test POST /api/chat with an escalation trigger ("I am furious, connect me to a human agent now")
    automatically creates a high-priority ticket visible in GET /api/tickets.
    """
    escalation_query = "I am furious, connect me to a human agent now"
    test_email = "furious_customer@example.com"

    res = client.post("/api/chat", json={"query": escalation_query, "customer_email": test_email})
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"

    data = res.json()
    assert data.get("status") == "success"

    # 4a. Ticket creation verification
    ticket = data.get("ticket")
    assert ticket is not None, f"Expected ticket to be created for escalation trigger. Response: {data}"
    ticket_id = ticket.get("id")
    assert ticket_id and ticket_id.startswith("TCK-"), f"Invalid ticket id: {ticket_id}"

    # High priority check: "Urgent" or "High"
    priority = ticket.get("priority", "")
    assert priority in ("Urgent", "High"), f"Expected high priority ('Urgent' or 'High'), got '{priority}'"
    assert ticket.get("status") == "Open"
    assert test_email in (ticket.get("customer_email") or "")
    assert ticket.get("sentiment") == "High Urgency", f"Expected 'High Urgency' sentiment, got '{ticket.get('sentiment')}'"

    # 4b. Confirm ticket is visible in GET /api/tickets
    tickets_res = client.get("/api/tickets")
    assert tickets_res.status_code == 200
    all_tickets = tickets_res.json().get("tickets", [])

    matching = [t for t in all_tickets if t.get("id") == ticket_id]
    assert len(matching) == 1, f"Ticket {ticket_id} not found in GET /api/tickets: {all_tickets}"

    matched_ticket = matching[0]
    assert matched_ticket["priority"] in ("Urgent", "High")
    assert matched_ticket["status"] == "Open"
    assert test_email in (matched_ticket.get("customer_email") or "")

    # 4c. Confirm ticket is visible with priority filtering: GET /api/tickets?priority=Urgent
    filtered_res = client.get(f"/api/tickets?priority={priority}")
    assert filtered_res.status_code == 200
    filtered_tickets = filtered_res.json().get("tickets", [])
    assert any(t.get("id") == ticket_id for t in filtered_tickets), (
        f"Ticket {ticket_id} not returned when filtering by priority={priority}"
    )

    # 4d. Confirm ticket exists directly in SQLite
    db_ticket = database.get_ticket_by_id(ticket_id)
    assert db_ticket is not None, f"Ticket {ticket_id} not found in SQLite database"
    assert db_ticket["priority"] in ("Urgent", "High")
    assert db_ticket["status"] == "Open"

    # 4e. Confirm chat response answer mentions ticket creation or live escalation
    answer = data.get("answer", "")
    assert "ticket" in answer.lower() or ticket_id in answer or "support" in answer.lower(), (
        f"Expected escalation/ticket notice in answer text. Answer: {answer}"
    )


def test_4b_escalation_trigger_without_customer_email():
    """Verify escalation trigger creates ticket even when customer email is omitted."""
    escalation_query = "I am furious, connect me to a human agent now"
    res = client.post("/api/chat", json={"query": escalation_query})
    assert res.status_code == 200
    data = res.json()
    ticket = data.get("ticket")
    assert ticket is not None
    assert ticket["id"].startswith("TCK-")
    assert ticket["priority"] in ("Urgent", "High")
    assert ticket["status"] == "Open"


# ==============================================================================
# 5. STATIC ISOLATION AND CLEAN DESKTOP UI ENTRYPOINTS
# ==============================================================================

def test_5_static_isolation_and_clean_desktop_ui():
    """
    5. Test that GET /static/.env returns 404 Not Found and both / (app.html)
    and /admin (admin.html) return 200 OK without any references to
    kid-assistant.js or clay-theme.js.
    """
    # 5a. Static isolation / security tests: leak vectors must return 404 Not Found
    res_static_env = client.get("/static/.env")
    assert res_static_env.status_code == 404, f"Expected 404 for /static/.env, got {res_static_env.status_code}"

    res_static_db = client.get("/static/omnidesk.db")
    assert res_static_db.status_code == 404, f"Expected 404 for /static/omnidesk.db, got {res_static_db.status_code}"

    res_static_git = client.get("/static/.git/config")
    assert res_static_git.status_code == 404, f"Expected 404 for /static/.git/config, got {res_static_git.status_code}"

    res_root_env = client.get("/.env")
    assert res_root_env.status_code == 404, f"Expected 404 for /.env, got {res_root_env.status_code}"

    # 5b. Desktop window entrypoints
    routes_to_test = [
        ("/", "app.html entrypoint (root)"),
        ("/app.html", "app.html direct route"),
        ("/admin", "admin.html entrypoint (/admin)"),
        ("/admin.html", "admin.html direct route"),
    ]

    forbidden_strings = ["kid-assistant.js", "clay-theme.js"]

    for route, desc in routes_to_test:
        res = client.get(route)
        assert res.status_code == 200, f"Expected 200 for {desc} at '{route}', got {res.status_code}"
        assert "text/html" in res.headers.get("content-type", ""), f"Expected text/html content-type for {route}"
        content = res.text

        for forbidden in forbidden_strings:
            assert forbidden not in content, (
                f"Forbidden script reference '{forbidden}' found in {desc} ('{route}')!"
            )

    # 5c. Direct filesystem verification of app.html and admin.html
    for html_file in ["app.html", "admin.html"]:
        html_path = ROOT_DIR / html_file
        assert html_path.exists(), f"File {html_file} does not exist at {html_path}"
        with open(html_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        for forbidden in forbidden_strings:
            assert forbidden not in file_content, (
                f"Forbidden script reference '{forbidden}' found in {html_file} on disk!"
            )


# ==============================================================================
# 6. EDGE CASES: VALIDATION AND MISSING DATA
# ==============================================================================

def test_edge_case_empty_and_whitespace_chat_query():
    """Verify empty and whitespace chat payloads raise 422 Unprocessable Entity."""
    res_empty = client.post("/api/chat", json={"query": ""})
    assert res_empty.status_code == 422

    res_whitespace = client.post("/api/chat", json={"query": "   \n\t  "})
    assert res_whitespace.status_code == 422

    res_no_query = client.post("/api/chat", json={})
    assert res_no_query.status_code == 422


def test_edge_case_query_without_order_has_no_order_context():
    """Verify chat query without order pattern returns order=None."""
    res = client.post("/api/chat", json={"query": "How do I update my account password?"})
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "success"
    assert data.get("order") is None


def test_edge_case_nonexistent_order_query():
    """Verify querying an unknown order (ORD-9999) does not crash and returns graceful output."""
    res = client.post("/api/chat", json={"query": "Can you track ORD-9999?"})
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "success"
