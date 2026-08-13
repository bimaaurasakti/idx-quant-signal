"""
api/main.py
============
Entry point FastAPI. Jalankan dengan:
    uvicorn api.main:app --reload --port 8000

Dokumentasi interaktif otomatis tersedia di /docs (Swagger) dan /redoc.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.core.config import settings
from api.core.rate_limit import limiter
from api.routers import meta, screener, detail, portfolio, positions, backtest

app = FastAPI(
    title="IDX Quant Signal API",
    description="Satu-satunya klien Supabase untuk dashboard IDX Quant Signal. "
                 "Frontend (Next.js) TIDAK PERNAH mengakses Supabase secara langsung.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(meta.router)
app.include_router(screener.router)
app.include_router(detail.router)
app.include_router(portfolio.router)
app.include_router(positions.router)
app.include_router(backtest.router)


@app.get("/api/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
