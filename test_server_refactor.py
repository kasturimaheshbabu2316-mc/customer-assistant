import os
import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "admin-secret-key-2026")

def test_staticfiles_security_leak_fixed():
    """Verify /static directory is NOT mounted and cannot expose .env or omnidesk.db."""
    # /static must return 404 Not Found
    res_static_env = client.get("/static/.env")
    assert res_static_env.status_code == 404
    
    res_static_db = client.get("/static/omnidesk.db")
    assert res_static_db.status_code == 404
    
    # Static CSS and JS must remain accessible
    res_css = client.get("/css/style.css")
    assert res_css.status_code == 200

def test_two_window_desktop_html_routes():
    """Verify explicit routes for Window 1 (Customer Portal) and Window 2 (Admin Console)."""
    # Window 1: Customer Portal
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "Customer" in res_root.text
    
    res_app_html = client.get("/app.html")
    assert res_app_html.status_code == 200
    assert "Customer" in res_app_html.text

    # Window 2: Admin & Agent Console
    res_admin = client.get("/admin")
    assert res_admin.status_code == 200
    assert "Admin" in res_admin.text or "OmniDesk" in res_admin.text

    res_admin_html = client.get("/admin.html")
    assert res_admin_html.status_code == 200
    assert "Admin" in res_admin_html.text or "OmniDesk" in res_admin_html.text

    # Legacy routes must be removed (404)
    res_login = client.get("/login")
    assert res_login.status_code == 404

    res_admin_login_get = client.get("/admin/login")
    assert res_admin_login_get.status_code == 404

def test_api_admin_login():
    """Verify POST /api/admin/login validates credentials and issues bearer token."""
    # 1. Invalid password -> 401
    bad_res = client.post("/api/admin/login", json={"password": "wrong-password-999"})
    assert bad_res.status_code == 401

    # 2. Valid password -> 200 + bearer token
    good_res = client.post("/api/admin/login", json={"password": ADMIN_KEY})
    assert good_res.status_code == 200
    data = good_res.json()
    assert data["status"] == "success"
    assert "token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"

    # 3. Test using issued bearer token against a protected endpoint
    token = data["token"]
    protected_res = client.get("/api/admin/rag-policy", headers={"Authorization": f"Bearer {token}"})
    assert protected_res.status_code == 200

def test_api_chat_and_order_context():
    """Verify POST /api/chat with RAG policy, order context, auto-escalation, and 422 guard."""
    # 1. Empty payload -> 422
    empty_res = client.post("/api/chat", json={"query": ""})
    assert empty_res.status_code == 422

    # 2. Grounded policy query
    chat_res = client.post("/api/chat", json={"query": "What is the return window for items?"})
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["status"] == "success"
    assert len(chat_data["answer"]) > 5
    assert len(chat_data["sources"]) > 0

    # 3. Order lookup via query ORD-1001
    order_res = client.post("/api/chat", json={"query": "Where is my order ORD-1001?"})
    assert order_res.status_code == 200
    order_data = order_res.json()
    assert order_data["order"] is not None
    assert order_data["order"]["id"] == "ORD-1001"

    # 4. Auto-escalation triggered by angry customer
    esc_res = client.post(
        "/api/chat",
        json={
            "query": "I am furious, give me a human agent or supervisor right now!",
            "customer_email": "escalated_test@example.com"
        }
    )
    assert esc_res.status_code == 200
    esc_data = esc_res.json()
    assert esc_data["ticket"] is not None
    assert "TCK-" in esc_data["ticket"]["id"]

def test_api_orders():
    """Verify GET /api/orders and GET /api/orders/{order_id}."""
    # 1. Lookup specific order
    ord_res = client.get("/api/orders/ORD-1001")
    assert ord_res.status_code == 200
    ord_data = ord_res.json()
    assert ord_data["status"] == "success"
    assert ord_data["order"]["id"] == "ORD-1001"

    # 2. Non-existent order -> 404
    bad_ord = client.get("/api/orders/NONEXISTENT-999")
    assert bad_ord.status_code == 404

    # 3. List all orders
    all_res = client.get("/api/orders")
    assert all_res.status_code == 200
    assert all_res.json()["total"] >= 1

    # 4. Filter orders by email
    cust_email = ord_data["order"]["customer_email"]
    filt_res = client.get(f"/api/orders?email={cust_email}")
    assert filt_res.status_code == 200
    for o in filt_res.json()["orders"]:
        assert o["customer_email"].lower() == cust_email.lower()

def test_api_ticket_reply_and_live_sync():
    """Verify POST /api/tickets/{ticket_id}/reply and GET /api/tickets/{ticket_id}/State."""
    # 1. Create ticket
    t_res = client.post(
        "/api/tickets",
        json={
            "customer_name": "Test User",
            "customer_email": "test@example.com",
            "subject": "Two-Window Test",
            "query": "Can an agent help me with setup?"
        }
    )
    assert t_res.status_code == 200
    tck = t_res.json()["ticket"]
    tck_id = tck["id"]
    assert tck["status"] == "Open"

    # 2. Agent replies via POST /api/tickets/{ticket_id}/reply
    reply_res = client.post(
        f"/api/tickets/{tck_id}/reply",
        json={
            "sender": "Agent Smith",
            "message": "Hello! I am happy to help you set up your desk."
        }
    )
    assert reply_res.status_code == 200
    reply_data = reply_res.json()
    assert reply_data["status"] == "success"
    assert reply_data["ticket"]["status"] == "In Progress"
    assert reply_data["ticket"]["assigned_agent"] == "Agent Smith"

    # 3. Live State sync GET /api/tickets/{ticket_id}/State
    state_res = client.get(f"/api/tickets/{tck_id}/State")
    assert state_res.status_code == 200
    state_data = state_res.json()
    assert state_data["status"] == "success"
    assert state_data["ticket_id"] == tck_id
    assert state_data["ticket_status"] == "In Progress"
    assert len(state_data["messages"]) >= 2

    # 4. Also check lowercase /state
    state_res_lower = client.get(f"/api/tickets/{tck_id}/state")
    assert state_res_lower.status_code == 200
    assert state_res_lower.json()["ticket_id"] == tck_id

def test_api_analyze_image():
    """Verify POST /api/analyze-image damaged item claim inspection."""
    res = client.post(
        "/api/analyze-image",
        json={
            "claim_description": "Dropped tablet, glass is completely shattered.",
            "image_base64": ""
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "is_warranty_covered" in data
    assert data["is_warranty_covered"] is False

def test_api_rag_status_and_metrics():
    """Verify GET /api/rag/status, GET /api/metrics, and POST /api/csat."""
    # 1. RAG status
    rag_res = client.get("/api/rag/status")
    assert rag_res.status_code == 200
    rag_data = rag_res.json()
    assert rag_data["status"] == "ready"
    assert rag_data["total_chunks"] >= 6

    # 2. Executive Metrics
    met_res = client.get("/api/metrics")
    assert met_res.status_code == 200
    met_data = met_res.json()
    assert "deflection_rate" in met_data
    assert "csat_score" in met_data
    assert "total_tickets" in met_data
    assert "uptime_seconds" in met_data

    # 3. CSAT submission
    csat_res = client.post("/api/csat", json={"rating": 5, "comment": "Terrific service!"})
    assert csat_res.status_code == 200
    assert csat_res.json()["status"] == "success"

def test_admin_login_env_password_override():
    """Verify ADMIN_PASSWORD from .env/environ is strictly validated and rejects default key."""
    orig_env_pw = os.environ.get("ADMIN_PASSWORD")
    try:
        os.environ["ADMIN_PASSWORD"] = "custom-vault-pass-9988"
        # 1. Custom password succeeds
        good = client.post("/api/admin/login", json={"password": "custom-vault-pass-9988"})
        assert good.status_code == 200
        assert good.json()["status"] == "success"
        
        # 2. Hardcoded fallback string must be rejected when custom password is set
        bad = client.post("/api/admin/login", json={"password": "admin-secret-key-2026"})
        assert bad.status_code == 401
    finally:
        if orig_env_pw is not None:
            os.environ["ADMIN_PASSWORD"] = orig_env_pw
        else:
            os.environ.pop("ADMIN_PASSWORD", None)

def test_alias_fallback_with_empty_strings():
    """Verify primary fields with empty/whitespace strings properly fall back to aliases."""
    # 1. Chat: empty query falling back to message
    chat_res = client.post("/api/chat", json={"query": "   ", "message": "What is the return policy?"})
    assert chat_res.status_code == 200
    assert chat_res.json()["status"] == "success"

    # 2. Ticket creation: empty query falling back to message
    t_res = client.post("/api/tickets", json={
        "customer_name": "Alias Tester",
        "customer_email": "alias@test.com",
        "query": "",
        "message": "Desk motor making clicking noise."
    })
    assert t_res.status_code == 200
    tck_id = t_res.json()["ticket"]["id"]

    # 3. Ticket reply: empty text falling back to message
    rep_res = client.post(f"/api/tickets/{tck_id}/reply", json={
        "sender": "Agent Frank",
        "text": "",
        "message": "We have dispatched a replacement control box."
    })
    assert rep_res.status_code == 200
    assert rep_res.json()["ticket"]["assigned_agent"] == "Agent Frank"

    # 4. Image analysis: empty claim_description falling back to description
    img_res = client.post("/api/analyze-image", json={
        "claim_description": "",
        "description": "Scratched desktop surface during shipping."
    })
    assert img_res.status_code == 200
    assert "is_warranty_covered" in img_res.json()

def test_ticket_updates_via_post_and_put():
    """Verify PATCH, POST, and PUT can all update ticket status and assigned agent."""
    # Create ticket
    t_res = client.post("/api/tickets", json={
        "customer_name": "Update Tester",
        "customer_email": "update@test.com",
        "query": "Need help with assembly."
    })
    tck_id = t_res.json()["ticket"]["id"]

    # PATCH
    p_res = client.patch(f"/api/tickets/{tck_id}", json={"status": "In Progress", "assigned_agent": "Agent Sarah"})
    assert p_res.status_code == 200
    assert p_res.json()["ticket"]["status"] == "In Progress"
    assert p_res.json()["ticket"]["assigned_agent"] == "Agent Sarah"

    # POST alias
    post_res = client.post(f"/api/tickets/{tck_id}", json={"status": "Resolved"})
    assert post_res.status_code == 200
    assert post_res.json()["ticket"]["status"] == "Resolved"

    # PUT alias
    put_res = client.put(f"/api/tickets/{tck_id}", json={"status": "In Progress"})
    assert put_res.status_code == 200
    assert put_res.json()["ticket"]["status"] == "In Progress"

def test_orders_case_insensitivity_and_empty_filter():
    """Verify lowercase order IDs and empty query filters work properly."""
    # 1. Lowercase order ID
    ord_res = client.get("/api/orders/ord-1001")
    assert ord_res.status_code == 200
    assert ord_res.json()["order"]["id"] == "ORD-1001"

    # 2. Empty email filter returns full order list
    all_res = client.get("/api/orders?email=")
    assert all_res.status_code == 200
    assert all_res.json()["total"] >= 1

def test_html_routes_content_type_and_security():
    """Verify text/html content-type and blocking of direct file exposure."""
    # 1. Content-Type text/html
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "text/html" in res_root.headers.get("content-type", "")

    res_admin = client.get("/admin")
    assert res_admin.status_code == 200
    assert "text/html" in res_admin.headers.get("content-type", "")

    # 2. Sensitive database and env files are unreachable
    assert client.get("/.env").status_code == 404
    assert client.get("/omnidesk.db").status_code == 404
    assert client.get("/static/.env").status_code == 404

def test_html_routes_missing_file_returns_404(monkeypatch):
    """Verify missing HTML files return HTTP 404 Not Found (not 200)."""
    orig_exists = os.path.exists
    def mock_exists(path):
        if "app.html" in path or "admin.html" in path:
            return False
        return orig_exists(path)
    monkeypatch.setattr(os.path, "exists", mock_exists)

    res_app = client.get("/")
    assert res_app.status_code == 404
    assert "not found" in res_app.text.lower()

    res_admin = client.get("/admin")
    assert res_admin.status_code == 404
    assert "not found" in res_admin.text.lower()
