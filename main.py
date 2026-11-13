"""
Main entry point for OmniDesk AI Backend.
Supports Railway, Render, Docker, and direct Uvicorn deployments.
"""
import os
import threading
import time
import webbrowser
import uvicorn

from server import app

# Export app instance for ASGI servers (uvicorn main:app)
__all__ = ["app"]


def open_browser_windows():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000/app.html")
    webbrowser.open("http://127.0.0.1:8000/admin.html")


if __name__ == "__main__":
    threading.Thread(target=open_browser_windows, daemon=True).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
