#!/usr/bin/env python
"""FastAPI Agent API with JWT RBAC + Prometheus metrics.

Endpoints:
  GET /health                - basic health
  POST /chat                 - anonymous simple echo (demo)
  GET /metrics               - Prometheus metrics
  POST /api/secure/task      - role=steward or higher
  POST /api/admin/reload     - role=flamekeeper only

JWT:
  Authorization: Bearer <token>
  Claims required: {"role": "member|steward|flamekeeper"}
Env:
  JWT_SECRET (required)

Generate token (example python snippet):
  from jose import jwt; print(jwt.encode({"role":"steward"}, secret, algorithm="HS256"))
"""
import os
import time
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from jose import jwt, JWTError
from starlette.responses import Response, PlainTextResponse

JWT_SECRET = os.getenv("JWT_SECRET")
ALGO = "HS256"

if not JWT_SECRET:
    print("WARNING: JWT_SECRET not set; secure endpoints will 401.")

app = FastAPI(title="VictoryChain Agent API", version="0.1.0")

# Metrics
REQ_COUNTER = Counter(
    "agent_requests_total", "Agent API requests", ["path", "method", "role", "code"]
)
LATENCY = Histogram(
    "agent_request_latency_seconds", "Request latency", ["path", "method"]
)  # coarse

security = HTTPBearer(auto_error=False)


class ChatRequest(BaseModel):
    message: str


class TaskRequest(BaseModel):
    task: str
    payload: Optional[dict] = None


ROLES_ORDER = ["member", "steward", "flamekeeper"]


def _role_level(r: str) -> int:
    try:
        return ROLES_ORDER.index(r)
    except ValueError:
        return -1


class AuthResult(BaseModel):
    role: str


async def auth_required(
    creds: HTTPAuthorizationCredentials = Depends(security), min_role: str = "member"
) -> AuthResult:
    if not creds or not creds.scheme.lower() == "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_token"
        )
    token = creds.credentials
    if not JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="secret_not_configured"
        )
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[ALGO])
        role = data.get("role")
        if _role_level(role) < _role_level(min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="insufficient_role"
            )
        return AuthResult(role=role)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid_token:{e}"
        )


@app.middleware("http")
async def _metrics_mw(request, call_next):
    start = time.time()
    role = "anon"
    # Try to decode for metrics only (ignore failures)
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer ") and JWT_SECRET:
        tok = auth.split(" ", 1)[1]
        try:
            data = jwt.decode(tok, JWT_SECRET, algorithms=[ALGO])
            role = data.get("role") or role
        except Exception:
            pass
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        code = getattr(response, "status_code", 500)
        REQ_COUNTER.labels(
            path=request.url.path, method=request.method, role=role, code=code
        ).inc()
        LATENCY.labels(path=request.url.path, method=request.method).observe(
            time.time() - start
        )


@app.get("/health")
async def health():
    return {"ok": True, "ts": time.time()}


@app.post("/chat")
async def chat(body: ChatRequest):
    # Echo demo (placeholder for model inference)
    return {"reply": f"echo: {body.message}"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/secure/task")
async def secure_task(
    body: TaskRequest,
    auth: AuthResult = Depends(lambda c=Depends(security): auth_required(c, "steward")),
):
    return {
        "accepted": True,
        "role": auth.role,
        "task": body.task,
        "payload": body.payload or {},
    }


@app.post("/api/admin/reload")
async def admin_reload(
    auth: AuthResult = Depends(
        lambda c=Depends(security): auth_required(c, "flamekeeper")
    )
):
    # Placeholder for reloading vector store / tools etc.
    return {"reloaded": True, "role": auth.role}
