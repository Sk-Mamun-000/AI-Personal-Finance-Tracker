"""
AI Personal Finance & Expense Tracker — FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import init_db
from app.config import get_settings
from app.routers import (
    auth_router, expense_router, income_router,
    budget_router, dashboard_router, reports_router,
)

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # creates tables if they don't exist (use Alembic in real prod)
    yield


app = FastAPI(
    title=settings.app_name,
    description="An AI-powered personal finance & expense tracking API with "
                 "ML-based prediction, anomaly detection, and financial scoring.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — tighten allow_origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(expense_router.router)
app.include_router(income_router.router)
app.include_router(budget_router.router)
app.include_router(dashboard_router.router)
app.include_router(reports_router.router)


@app.get("/", tags=["Health"])
@limiter.limit("30/minute")
def root(request: Request):
    return {
        "message": f"{settings.app_name} API is running.",
        "docs": "/docs",
        "status": "healthy",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
