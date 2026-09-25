#!/bin/bash
# Start FastAPI backend on Railway's PORT
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} &

# Start Streamlit frontend
export BACKEND_URL="http://127.0.0.1:${PORT:-8000}"
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false
