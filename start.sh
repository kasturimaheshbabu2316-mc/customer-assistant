#!/bin/bash
# Start FastAPI backend on Railway's PORT
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
