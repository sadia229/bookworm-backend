"""Vercel serverless entrypoint.

Vercel's Python runtime looks for an ASGI/WSGI `app` in files under `api/`.
This re-exports the FastAPI app so the whole API is served as one function.
"""

from app.main import app

__all__ = ["app"]
