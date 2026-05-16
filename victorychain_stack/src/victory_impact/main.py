from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .compliance import NON_INVESTMENT_DISCLAIMER
from .config import settings
from .db import Base, SessionLocal, engine
from .policies import runtime_policies
from .routers import admin, beneficiaries, donors, governance, payments, transparency, webhooks
from .services.donations import ensure_default_categories
from .services.observability import build_prometheus_metrics

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Nonprofit donation-token platform. Impact tokens are receipts and governance signals only; "
        "they do not represent investment interests."
    ),
)

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(donors.router)
app.include_router(beneficiaries.router)
app.include_router(governance.router)
app.include_router(admin.router)
app.include_router(transparency.router)
app.include_router(payments.router)
app.include_router(webhooks.router)


@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_default_categories(db)
    finally:
        db.close()


@app.get("/")
def healthcheck() -> dict:
    return {
        "service": settings.app_name,
        "status": "ok",
        "disclaimer": NON_INVESTMENT_DISCLAIMER,
        "entities": {
            "steward": "Victory Foundation for Restoration",
            "operating_arm": "Sacred Earth Restoration Alliance",
        },
        "legal": {
            "charitable_solicitation": "placeholder_by_jurisdiction",
            "ofac_screening": "placeholder",
            "tax_receipts": "enabled" if runtime_policies.tax_receipts_enabled else "disabled_pending_legal_review",
        },
    }


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    db = SessionLocal()
    try:
        return build_prometheus_metrics(db)
    finally:
        db.close()
