# Problem Statement: OmniDesk AI — Policy-Grounded Dual-Portal Customer Support System

**Project Name:** OmniDesk AI (`mc-customer-assistant`)

**Architecture:** FastAPI Backend + ChromaDB Vector Engine + Google Gemini 2.5 Flash + Dual-Window Desktop Web UI

**Target Interfaces:** Window 1 — Customer Support Portal (`app.html`) | Window 2 — Admin & Agent Command Center (`admin.html`)

## 1. Executive Summary

Modern e-commerce and SaaS support teams face an operational bottleneck: high volumes of repetitive Tier-1 inquiries (order tracking, return eligibility, refund timelines, and warranty claims) overwhelm human agents, while ungrounded generative AI chatbots introduce severe financial and legal liability by hallucinating company policies.

**OmniDesk AI** solves this by combining a **strictly policy-grounded Retrieval-Augmented Generation (RAG) engine** with a **synchronized Dual-Window Desktop Web Architecture**:

1. **Window 1 — Customer Support Portal (`app.html`):** A clean, desktop-first web interface where customers can ask policy questions grounded in official company documentation, inspect real-time order statuses, submit multimodal damage/warranty claims, and track support tickets.

2. **Window 2 — Admin & Agent Command Center (`admin.html`):** A dedicated operational console for support engineers and administrators to monitor live SLA queues, take over escalated tickets, hot-reload official RAG policy documents without server downtime, and audit system metrics.

## 2. Core Problem Analysis

### 2.1 Industry & Business Problems

1. **AI Hallucination & Policy Liability:** Generic LLM wrappers invent return windows, promise unauthorized refunds, or fabricate shipping guarantees when answering customer queries without deterministic retrieval constraints.

2. **Tier-1 Support Overload:** Up to 70% of incoming support volume consists of repetitive status checks (`ORD-1001` through `ORD-1005`) and standard policy lookups that delay human response times on complex, high-priority escalations.

3. **Disconnected Customer & Agent Workflows:** Customers and support agents often operate in siloed tools. When an AI assistant cannot resolve an issue or detects negative customer sentiment, context is lost during handoff to a human agent.

4. **Manual Visual Claim Triage:** Processing damaged-product returns requires manual photo inspection by support staff before a replacement or refund ticket can be categorized.

### 2.2 Technical Regressions Identified in Current Repository (`mc-customer-assistant`)

A comprehensive audit of the current codebase revealed four critical regressions that shifted the project away from its original specification:

| Subsystem | Original Working Design | Regression Introduced in Current Repo | Operational Impact | 
| ----- | ----- | ----- | ----- | 
| **Internal RAG Policy Engine (`rag_engine.py`)** | `parse_faq_sections()` split `knowledge_base/company_faq.txt` by numbered policy headers (`1. RETURN AND EXCHANGE POLICY` to `6. CUSTOMER SUPPORT ESCALATION & HOURS`), preserving full semantic rules per vector document. | Replaced with naive character slicing (`chunk_text(full_text, chunk_size=400, overlap=80)`), cutting sentences mid-clause and labeling chunks generically as `Policy Clause 1..N`. Added an overly aggressive `_gemini_api_working` circuit breaker that falls back to keyword-seeded random noise vectors on any transient error. | Policy retrieval loses section context, returns fragmented sentences, or fails completely when falling back to synthetic vectors. | 
| **Dual-Window Desktop UI (`app.html` & `admin.html`)** | Clean, full-viewport desktop two-window workflow: `app.html` for Customers and `admin.html` (with built-in `#admin-auth-gate` modal) for Admins, styled with a unified dark glassmorphism desktop layout. | Injected Stitch mobile-first prototypes (`ai_support_assistant_claymorphism/`, `tickets_sla_claymorphism/`, etc.) with `<meta content="mobile_tab" name="shell-type">`, `max-w-md` narrow mobile frames, bottom app docks, and forced page redirects (`window.location.href = 'admin-login.html'`). | UI renders like a cramped mobile app with broken multi-page redirects instead of a synchronized two-window desktop web application. | 
| **Unwanted UI Widgets & Theme Bloat (`js/` & `css/`)** | Clean enterprise support UI with zero visual distractions. | Added `js/kid-assistant.js` (injecting `#sparky-mascot-root` floating cartoon robot, speech bubbles, and Web Audio chimes), `js/clay-theme.js` (synthesized pop sound effects on every click and pastel clay overrides), and conflicting `css/cyberpunk.css` scanlines. | Unprofessional consumer/toy appearance, audio clutter on every click, and severe CSS specificity conflicts across windows. | 
| **Server Routing & Deployment (`server.py`, `start.sh`)** | Single FastAPI ASGI server (`uvicorn main:app`) serving REST APIs and the two desktop windows (`/` -> `app.html`, `/admin` -> `admin.html`). | `start.sh` launches both FastAPI and a legacy Streamlit server (`app.py`) simultaneously; `server.py` mounts `StaticFiles(directory=".")` at `/static` (exposing `.env` and `omnidesk.db`) and routes `/login` to mobile prototype folders. | Deployment port conflicts, exposed database/environment files, and broken navigation between the Customer and Admin windows. | 

## 3. Target System Architecture & Scope

### 3.1 Dual-Window Web UI Specification

The frontend must operate strictly as a responsive, desktop-first **Two-Window Web Application** sharing a single FastAPI + SQLite + ChromaDB backend:

* **Window 1: Customer Portal (`/` or `/app.html`)**

  * **AI Policy & Order Assistant:** Grounded conversational interface with inline order lookup cards, quick-action prompts, and transparent source citations (`Section 1: Return Policy`, etc.).

  * **Order Lookup & Tracking Drawer/View:** Instant status lookup by Order ID (`ORD-1001`–`ORD-1005`) or customer email, displaying fulfillment progress, tracking numbers, and items.

  * **My Support Tickets:** Live view of customer-submitted and AI-escalated tickets with status badges (`Open`, `In Progress`, `Resolved`) and priority levels.

  * **Visual Claim Inspection:** Drag-and-drop image upload (`POST /api/analyze-image`) using Gemini Vision to assess product damage and optionally auto-create a support ticket.

* **Window 2: Admin & Agent Command Center (`/admin` or `/admin.html`)**

  * **Inline Session Auth Gate:** Clean modal authentication (`POST /api/admin/login`) inside `admin.html` without redirecting to mobile prototype pages.

  * **Live Ticket & SLA Queue:** Real-time table of all customer tickets with filtering by status/priority, one-click status transitions (`Open` -> `In Progress` -> `Resolved`), and **Human Agent Takeover** reply composer (`POST /api/tickets/{id}/reply`).

  * **Internal RAG Policy Studio:** Live document editor and uploader (`POST /api/admin/rag-upload`) allowing admins to view, edit, or upload `.txt`/`.md` policy files and immediately re-index ChromaDB by numbered policy section.

  * **Executive KPI & Telemetry Bar:** Real-time metrics (`GET /api/metrics`) tracking Total Tickets, Open/Escalated Queue, AI Resolution Rate, CSAT Score, and Vector DB Chunk Count.

### 3.2 Internal RAG Policy Engine Specification (`rag_engine.py`)

1. **Section-Aware Document Parsing:** Parse `knowledge_base/company_faq.txt` using regex header boundaries (`^\d+\.\s+[A-Z]`) so each numbered company policy section is stored with its exact `section` title and complete semantic rules.

2. **Deterministic Grounding & Thresholding:** Query ChromaDB for the top-$k$ relevant policy sections (`n_results=3`), enforce a cosine/L2 relevance threshold, and instruct Gemini 2.5 Flash via a strict system prompt to answer **exclusively** using retrieved policy clauses and verified SQLite order records.

3. **Automatic Escalation Trigger:** When customer sentiment is frustrated (`angry`, `lawsuit`, `unacceptable`, `human`, `agent`) or when a request requires manual override, automatically create an escalated ticket in SQLite (`database.py`) and surface it immediately in Window 2 (`admin.html`).

## 4. Functional & Non-Functional Requirements

### Functional Requirements

* **FR-01 (Dual-Window Synchronization):** Actions taken in Window 1 (Customer creating a ticket or triggering an AI escalation) must appear in Window 2 (Admin Queue) via API polling/refresh, and Admin replies/status changes in Window 2 must reflect in Window 1.

* **FR-02 (Section-Based Policy RAG):** `ingest_faq()` must index `company_faq.txt` into distinct, titled policy sections and support live hot-reloading via `/api/admin/rag-upload`.

* **FR-03 (Order Context Injection):** Mentioning an Order ID (`ORD-XXXX`) in chat must automatically query SQLite (`get_order()`) and inject structured order metadata into the RAG prompt.

* **FR-04 (Multimodal Damage Triage):** Uploading a product photo must return structured JSON (`damage_detected`, `severity`, `confidence_score`, `recommended_action`) and optionally log a priority ticket.

### Non-Functional & Security Requirements

* **NFR-01 (Static File Isolation):** Never mount the project root `.` via `StaticFiles`. Serve only `/css`, `/js`, and explicit HTML entrypoints (`index.html`, `app.html`, `admin.html`) so `.env` and `omnidesk.db` are never web-accessible.

* **NFR-02 (Zero Toy/Mobile Clutter):** Remove all floating mascots (`kid-assistant.js`), click sound synthesizers (`clay-theme.js`), and mobile-tab prototype directories (`*_claymorphism/`).

* **NFR-03 (Resilient API Fallback):** If `GEMINI_API_KEY` is missing or rate-limited, provide deterministic, section-matched policy responses rather than random noise embeddings.

## 5. Success Metrics & Acceptance Criteria

| Metric / Criterion | Target Threshold | Verification Method | 
| ----- | ----- | ----- | 
| **Policy Grounding Accuracy** | 100% citation of official `company_faq.txt` sections; 0 fabricated return/refund rules | Automated `pytest` suite (`tests/test_api.py`) + manual policy query tests | 
| **Dual-Window Desktop Layout** | Full desktop viewport utilization on both `/app.html` and `/admin.html`; 0 mobile tab docks or mascot overlays | Visual DOM inspection across 1280px–1920px desktop viewports | 
| **End-to-End Ticket Sync Latency** | < 1 second from Customer escalation in Window 1 to visibility in Window 2 Admin Queue | Live dual-window browser verification (`POST /api/chat` -> `GET /api/tickets`) | 
| **Security & Static Isolation** | `GET /static/.env` and `GET /static/omnidesk.db` return `404 Not Found` | Security endpoint test in `tests/test_api.py` | 
