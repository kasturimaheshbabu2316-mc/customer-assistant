# OmniDesk AI | Customer Support RAG Hub

> Zero-hallucination AI customer service grounded in verified store policies and enterprise knowledge bases. Powered by Google Gemini 3 Flash, dense embeddings (`text-embedding-004`), and ChromaDB vector search.

---

## 🌟 Key Features

- **🛡️ Zero-Hallucination Guardrails**: Strict distance threshold enforcement (`1.2`) and low temperature (`0.1`) ensure the AI never fabricates dates, return windows, or pricing.
- **⚡ Sub-Second Vector Retrieval**: Dense vector indexing with Google `text-embedding-004` and ChromaDB persistent storage.
- **🔍 Verified Policy Citations**: Every response references exact policy clauses from the knowledge base.
- **🚀 Commercial Landing Page (`index.html`)**: Modern glassmorphic SaaS showcase with interactive RAG visualizer, live demo simulator, ROI savings calculator, and transparent pricing.
- **💬 Support Hub App Portal (`app.html`)**: Full-featured Single Page Application (SPA) with Live Chat, Text-to-Speech audio read-aloud, Knowledge Base Studio, Deflection & SLA Analytics Dashboard, and RAG Pipeline Settings.
- **🔌 Flexible Architecture**: Includes both an asynchronous FastAPI REST API (`server.py`) and a Streamlit application (`app.py`).

---

## 📁 Repository Structure

```text
├── index.html                  # Commercial SaaS marketing landing page
├── app.html                    # Support Hub Single Page Application portal
├── css/
│   └── style.css               # Core design system & modern glassmorphic styles
├── js/
│   ├── landing.js              # ROI calculator, demo simulator & interactions
│   └── app.js                  # Support Hub SPA controller & fallback engine
├── server.py                   # FastAPI REST backend with CORS & diagnostics
├── rag_engine.py               # RAG pipeline with ChromaDB & Gemini 3 Flash
├── app.py                      # Streamlit prototype customer portal
├── knowledge_base/
│   └── company_faq.txt         # Enterprise store policy knowledge dataset
├── .env.example                # Configuration & API key template
└── .gitignore                  # Git ignore rules for security
```

---

## 🚀 Quick Start Guide

### 1. Installation

Clone the repository and install required dependencies:

```bash
pip install fastapi uvicorn chromadb google-genai python-dotenv streamlit requests
```

### 2. Configure API Key

Copy the `.env.example` template to `.env`:

```bash
cp .env.example .env
```

Add your Google Gemini API Key:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Launch Services

#### Option A: Open Web Pages Directly

- Open `index.html` in any browser to explore the commercial website.
- Open `app.html` in any browser to use the Support Hub portal.
*(Both pages feature intelligent fallback simulation even if the backend is offline)*.

#### Option B: Start FastAPI Backend

```bash
python server.py
```

- API Endpoint: `http://localhost:8000`
- Swagger API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

#### Option C: Start Streamlit Application

```bash
python -m streamlit run app.py
```

- Streamlit Interface: `http://localhost:8501`

---

## 📄 License

MIT License. Developed for enterprise customer support automation.
