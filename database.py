"""
OmniDesk AI — SQLite Persistence Layer
Replaces volatile in-memory databases with persistent, thread-safe SQLite storage.
Manages:
1. Tickets & Lifecycle States (Open, In Progress, Resolved)
2. Ticket Message Threads & Private Staff Notes
3. Customer CSAT Feedback & Ratings
4. Query Audit Logs
5. Outbound Webhook Alert Logs
"""

import os
import sqlite3
import time
import json
from typing import Optional, Any

DB_DIR = os.getenv("DATA_DIR", "data")
DB_PATH = os.path.join(DB_DIR, "omnidesk.db")

def _get_connection() -> sqlite3.Connection:
    """Creates a thread-safe connection with row_factory set to dict-like sqlite3.Row."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging for high concurrency
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the database schema and populates initial demo seed data if empty."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    # 1. Tickets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        customer_tier TEXT NOT NULL DEFAULT 'Standard Retail',
        intent TEXT NOT NULL DEFAULT 'General Inquiry',
        sentiment TEXT NOT NULL DEFAULT 'Standard',
        subject TEXT NOT NULL,
        query TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'Medium',
        status TEXT NOT NULL DEFAULT 'Open',
        created_at TEXT NOT NULL,
        created_ts REAL NOT NULL,
        assigned_agent TEXT NOT NULL DEFAULT 'Unassigned',
        transcript_snippet TEXT
    );
    """)

    # 2. Ticket Messages & Internal Notes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket_messages (
        id TEXT PRIMARY KEY,
        ticket_id TEXT NOT NULL,
        sender TEXT NOT NULL,
        text TEXT NOT NULL,
        is_internal_note INTEGER NOT NULL DEFAULT 0,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE CASCADE
    );
    """)

    # 3. Customer CSAT Feedback Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id TEXT PRIMARY KEY,
        query TEXT NOT NULL,
        rating INTEGER NOT NULL,
        is_positive INTEGER NOT NULL,
        comment TEXT,
        language TEXT DEFAULT 'English',
        timestamp TEXT NOT NULL
    );
    """)

    # 4. Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        query TEXT NOT NULL,
        status TEXT NOT NULL,
        distance REAL,
        matched TEXT,
        latency_ms INTEGER,
        timestamp TEXT NOT NULL
    );
    """)

    # 5. Outbound Webhook Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS webhook_logs (
        id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        title TEXT NOT NULL,
        severity TEXT NOT NULL DEFAULT 'medium',
        destination TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'delivered',
        timestamp TEXT NOT NULL
    );
    """)

    conn.commit()

    # Seed initial data if tickets table is empty
    cursor.execute("SELECT COUNT(*) as count FROM tickets;")
    count = cursor.fetchone()["count"]
    if count == 0:
        _seed_initial_data(conn)

    conn.close()

def _seed_initial_data(conn: sqlite3.Connection):
    """Seeds default enterprise tickets and feedback for immediate demonstration."""
    cursor = conn.cursor()
    now_ts = time.time()
    now_str = time.strftime("%b %d, %H:%M")

    # Ticket 1
    cursor.execute("""
    INSERT INTO tickets (id, customer_id, customer_name, customer_email, customer_tier, intent, sentiment, subject, query, priority, status, created_at, created_ts, assigned_agent, transcript_snippet)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "TCK-1042", "CUST-8492", "Elena Rostova", "elena.r@techcorp.io", "VIP Enterprise",
        "Billing & Payment", "VIP / Commercial", "Custom enterprise bulk discount inquiry",
        "We are looking to order 250 units for our corporate team. Are custom volume pricing tiers available?",
        "High", "Open", now_str, now_ts - 3600, "Unassigned",
        "Customer asked for bulk volume tier pricing outside standard retail catalog."
    ))
    cursor.execute("""
    INSERT INTO ticket_messages (id, ticket_id, sender, text, is_internal_note, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ("msg_1042_1", "TCK-1042", "Elena Rostova", "We are looking to order 250 units for our corporate team. Are custom volume pricing tiers available?", 0, now_str))

    # Ticket 2
    cursor.execute("""
    INSERT INTO tickets (id, customer_id, customer_name, customer_email, customer_tier, intent, sentiment, subject, query, priority, status, created_at, created_ts, assigned_agent, transcript_snippet)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "TCK-1039", "CUST-6310", "Marcus Vance", "m.vance@vertex.com", "Pro Business",
        "Billing & Payment", "High Urgency", "Missing commercial tax exemption invoice",
        "Where can I upload our state resale tax exemption certificate for order #88412?",
        "Urgent", "In Progress", now_str, now_ts - 1200, "Sarah Chen",
        "Deflected tax exemption form request."
    ))
    cursor.execute("""
    INSERT INTO ticket_messages (id, ticket_id, sender, text, is_internal_note, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ("msg_1039_1", "TCK-1039", "Marcus Vance", "Where can I upload our state resale tax exemption certificate for order #88412?", 0, now_str))
    cursor.execute("""
    INSERT INTO ticket_messages (id, ticket_id, sender, text, is_internal_note, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ("msg_1039_2", "TCK-1039", "Sarah Chen", "Reviewing order #88412 against the Washington state sales tax exemption registry.", 1, now_str))

    # Ticket 3
    cursor.execute("""
    INSERT INTO tickets (id, customer_id, customer_name, customer_email, customer_tier, intent, sentiment, subject, query, priority, status, created_at, created_ts, assigned_agent, transcript_snippet)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "TCK-1031", "CUST-4195", "David Kim", "dkim@ventures.com", "Standard Retail",
        "Shipping & Logistics", "Standard", "Freight shipping to Antarctica research station",
        "Do you offer specialized freight shipping to McMurdo Station?",
        "Low", "Resolved", "Sep 16, 14:15", now_ts - 86400, "Alex Morgan",
        "Inquiry on non-standard remote geography delivery."
    ))
    cursor.execute("""
    INSERT INTO ticket_messages (id, ticket_id, sender, text, is_internal_note, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ("msg_1031_1", "TCK-1031", "David Kim", "Do you offer specialized freight shipping to McMurdo Station?", 0, "Sep 16, 14:15"))
    cursor.execute("""
    INSERT INTO ticket_messages (id, ticket_id, sender, text, is_internal_note, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ("msg_1031_2", "TCK-1031", "Alex Morgan", "Provided freight courier quote via DHL Global Forwarding charter.", 0, "Sep 16, 15:30"))

    # Seed Feedback
    cursor.executemany("""
    INSERT INTO feedback (id, query, rating, is_positive, comment, language, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ("fb_1", "Can I return open-box items?", 5, 1, "Clear return policy breakdown!", "English", "10:15:00"),
        ("fb_2", "Do you ship to Toronto Canada?", 5, 1, "DDP customs duties detail was super helpful.", "English", "11:20:00"),
        ("fb_3", "¿Cuál es la garantía del producto?", 5, 1, "Excelente respuesta en español.", "Spanish", "12:05:00")
    ])

    # Seed Audit Logs
    cursor.executemany("""
    INSERT INTO audit_logs (id, query, status, distance, matched, latency_ms, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ("audit_1", "Can I return open-box headphones?", "Resolved (100% Grounded)", 0.31, "Section 1: Return and Exchange Policy", 240, "10:15:00"),
        ("audit_2", "Do you ship to Toronto, Canada?", "Resolved (DDP Duties Cited)", 0.28, "Section 2: Shipping and Delivery Options", 195, "11:20:00"),
        ("audit_3", "How long is the manufacturer warranty?", "Resolved (1-Year Limited Cited)", 0.22, "Section 4: Warranty & Repair Coverage", 180, "12:05:00")
    ])

    # Seed Webhook Logs
    cursor.executemany("""
    INSERT INTO webhook_logs (id, event_type, title, severity, destination, payload_json, status, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ("wh_101", "sla_warning", "⏱️ SLA Warning (< 30m) — Ticket #TCK-1021", "high", "Slack #support-urgent", json.dumps({"ticket_id": "TCK-1021", "customer": "Elena Rostova", "tier": "VIP Enterprise", "remaining_minutes": 25}), "delivered", "10:15:00"),
        ("wh_102", "csat_alert", "⚠️ Low CSAT Rating Received (2/5)", "medium", "PagerDuty / Support Leads", json.dumps({"rating": 2, "query": "How to ship heavy electronics?", "language": "English"}), "delivered", "11:20:00")
    ])

    conn.commit()

# ==============================================================================
# TICKETS CRUD OPERATIONS
# ==============================================================================
def get_all_tickets(status: Optional[str] = None, priority: Optional[str] = None, search: Optional[str] = None) -> list[dict]:
    """Fetches all tickets with embedded message threads."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []
    
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)
    if priority and priority != "All":
        query += " AND priority = ?"
        params.append(priority)
    if search:
        query += " AND (customer_name LIKE ? OR subject LIKE ? OR id LIKE ? OR customer_email LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
        
    query += " ORDER BY created_ts DESC;"
    cursor.execute(query, params)
    ticket_rows = cursor.fetchall()

    tickets = []
    for row in ticket_rows:
        t_dict = dict(row)
        cursor.execute("SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY rowid ASC;", (t_dict["id"],))
        messages = [
            {
                "id": m["id"],
                "sender": m["sender"],
                "text": m["text"],
                "is_internal_note": bool(m["is_internal_note"]),
                "timestamp": m["timestamp"]
            }
            for m in cursor.fetchall()
        ]
        t_dict["messages"] = messages
        tickets.append(t_dict)

    conn.close()
    return tickets

def get_ticket_by_id(ticket_id: str) -> Optional[dict]:
    """Fetches a single ticket with its message history."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?;", (ticket_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    t_dict = dict(row)
    cursor.execute("SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY rowid ASC;", (ticket_id,))
    t_dict["messages"] = [
        {
            "id": m["id"],
            "sender": m["sender"],
            "text": m["text"],
            "is_internal_note": bool(m["is_internal_note"]),
            "timestamp": m["timestamp"]
        }
        for m in cursor.fetchall()
    ]
    conn.close()
    return t_dict

def create_ticket(ticket_data: dict) -> dict:
    """Inserts a new ticket and initial message into SQLite."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO tickets (id, customer_id, customer_name, customer_email, customer_tier, intent, sentiment, subject, query, priority, status, created_at, created_ts, assigned_agent, transcript_snippet)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_data["id"],
        ticket_data["customer_id"],
        ticket_data["customer_name"],
        ticket_data["customer_email"],
        ticket_data.get("customer_tier", "Standard Retail"),
        ticket_data.get("intent", "General Inquiry"),
        ticket_data.get("sentiment", "Standard"),
        ticket_data.get("subject", "Customer Inquiry"),
        ticket_data["query"],
        ticket_data.get("priority", "Medium"),
        ticket_data.get("status", "Open"),
        ticket_data["created_at"],
        ticket_data["created_ts"],
        ticket_data.get("assigned_agent", "Unassigned"),
        ticket_data.get("transcript_snippet", "")
    ))

    # Initial message
    if ticket_data.get("messages"):
        for m in ticket_data["messages"]:
            cursor.execute("""
            INSERT INTO ticket_messages (id, ticket_id, sender, text, is_internal_note, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                m["id"],
                ticket_data["id"],
                m["sender"],
                m["text"],
                1 if m.get("is_internal_note") else 0,
                m["timestamp"]
            ))

    conn.commit()
    conn.close()
    return get_ticket_by_id(ticket_data["id"])

def update_ticket(ticket_id: str, updates: dict) -> Optional[dict]:
    """Updates fields on an existing ticket."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    fields = []
    params = []
    allowed_keys = ["status", "priority", "assigned_agent", "subject", "intent", "sentiment", "transcript_snippet"]
    for k, v in updates.items():
        if k in allowed_keys and v is not None:
            fields.append(f"{k} = ?")
            params.append(v)
            
    if not fields:
        conn.close()
        return get_ticket_by_id(ticket_id)
        
    params.append(ticket_id)
    cursor.execute(f"UPDATE tickets SET {', '.join(fields)} WHERE id = ?;", params)
    conn.commit()
    conn.close()
    return get_ticket_by_id(ticket_id)

def delete_ticket(ticket_id: str) -> bool:
    """Deletes a ticket and its associated messages."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets WHERE id = ?;", (ticket_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def add_ticket_message(ticket_id: str, sender: str, text: str, is_internal_note: bool = False, timestamp: Optional[str] = None) -> Optional[dict]:
    """Appends a new message or staff note to a ticket thread."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tickets WHERE id = ?;", (ticket_id,))
    if not cursor.fetchone():
        conn.close()
        return None
        
    msg_id = f"msg_{int(time.time() * 1000)}"
    ts = timestamp or time.strftime("%b %d, %H:%M")
    
    cursor.execute("""
    INSERT INTO ticket_messages (id, ticket_id, sender, text, is_internal_note, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (msg_id, ticket_id, sender, text, 1 if is_internal_note else 0, ts))
    
    conn.commit()
    conn.close()
    return {
        "id": msg_id,
        "sender": sender,
        "text": text,
        "is_internal_note": is_internal_note,
        "timestamp": ts
    }

# ==============================================================================
# FEEDBACK & CSAT OPERATIONS
# ==============================================================================
def add_feedback(query: str, rating: int, is_positive: bool, comment: str = "", language: str = "English") -> dict:
    """Inserts a CSAT feedback record into SQLite."""
    conn = _get_connection()
    cursor = conn.cursor()
    fb_id = f"fb_{int(time.time() * 1000)}"
    ts = time.strftime("%H:%M:%S")
    
    cursor.execute("""
    INSERT INTO feedback (id, query, rating, is_positive, comment, language, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (fb_id, query, rating, 1 if is_positive else 0, comment, language, ts))
    
    conn.commit()
    conn.close()
    return {
        "id": fb_id,
        "query": query,
        "rating": rating,
        "is_positive": is_positive,
        "comment": comment,
        "language": language,
        "timestamp": ts
    }

def get_all_feedback() -> list[dict]:
    """Fetches all customer feedback records."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback ORDER BY rowid DESC;")
    rows = cursor.fetchall()
    results = [
        {
            "id": r["id"],
            "query": r["query"],
            "rating": r["rating"],
            "is_positive": bool(r["is_positive"]),
            "comment": r["comment"],
            "language": r["language"],
            "timestamp": r["timestamp"]
        }
        for r in rows
    ]
    conn.close()
    return results

def get_analytics_metrics() -> dict:
    """Calculates live analytics across persistent tickets and feedback."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved FROM tickets;")
    t_stats = cursor.fetchone()
    total_tickets = t_stats["total"] or 0
    resolved_tickets = t_stats["resolved"] or 0
    resolution_rate = round((resolved_tickets / total_tickets * 100), 1) if total_tickets > 0 else 100.0

    cursor.execute("SELECT COUNT(*) as total_fb, AVG(rating) as avg_rating, SUM(CASE WHEN is_positive = 1 THEN 1 ELSE 0 END) as pos_count FROM feedback;")
    fb_stats = cursor.fetchone()
    total_feedback = fb_stats["total_fb"] or 0
    avg_rating = round(fb_stats["avg_rating"] or 5.0, 2)
    pos_count = fb_stats["pos_count"] or 0
    csat_percentage = round((pos_count / total_feedback * 100), 1) if total_feedback > 0 else 100.0

    conn.close()
    return {
        "total_tickets": total_tickets,
        "resolved_tickets": resolved_tickets,
        "resolution_rate_percent": resolution_rate,
        "total_feedback": total_feedback,
        "average_rating": avg_rating,
        "csat_score_percent": csat_percentage
    }

# ==============================================================================
# AUDIT & WEBHOOK OPERATIONS
# ==============================================================================
def add_audit_log(query: str, status: str, distance: Optional[float] = None, matched: Optional[str] = None, latency_ms: int = 0) -> dict:
    """Records an audit log entry in SQLite."""
    conn = _get_connection()
    cursor = conn.cursor()
    audit_id = f"audit_{int(time.time() * 1000)}"
    ts = time.strftime("%H:%M:%S")
    cursor.execute("""
    INSERT INTO audit_logs (id, query, status, distance, matched, latency_ms, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (audit_id, query, status, distance, matched, latency_ms, ts))
    conn.commit()
    conn.close()
    return {"id": audit_id, "query": query, "status": status, "distance": distance, "matched": matched, "latency_ms": latency_ms, "timestamp": ts}

def get_audit_logs(limit: int = 50) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY rowid DESC LIMIT ?;", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def add_webhook_log(event_type: str, title: str, severity: str, destination: str, payload: dict, status: str = "delivered") -> dict:
    conn = _get_connection()
    cursor = conn.cursor()
    wh_id = f"wh_{int(time.time() * 1000)}"
    ts = time.strftime("%H:%M:%S")
    cursor.execute("""
    INSERT INTO webhook_logs (id, event_type, title, severity, destination, payload_json, status, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (wh_id, event_type, title, severity, destination, json.dumps(payload), status, ts))
    conn.commit()
    conn.close()
    return {"id": wh_id, "event_type": event_type, "title": title, "severity": severity, "destination": destination, "payload": payload, "status": status, "timestamp": ts}

def get_webhook_logs(limit: int = 50) -> list[dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM webhook_logs ORDER BY rowid DESC LIMIT ?;", (limit,))
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        try:
            d["payload"] = json.loads(d["payload_json"])
        except Exception:
            d["payload"] = {}
        rows.append(d)
    conn.close()
    return rows

# Initialize SQLite database immediately upon import
init_db()
