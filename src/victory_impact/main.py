import ipaddress
import logging
import re
import threading
from collections import defaultdict, deque
from datetime import UTC, datetime
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from .compliance import NON_INVESTMENT_DISCLAIMER
from .config import settings
from .db import Base, SessionLocal, engine
from .policies import runtime_policies
from .routers import admin, beneficiaries, delivery, donors, governance, payments, public, subscriptions, transparency, webhooks
from .services.donations import ensure_default_categories
from .services.observability import build_prometheus_metrics
from .services.sanctions import screening_provider_name

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
app.include_router(delivery.router)
app.include_router(public.router)
app.include_router(subscriptions.router)

logger = logging.getLogger(__name__)

_rate_limiter_lock = threading.Lock()
_rate_limiter_events: dict[str, deque[datetime]] = defaultdict(deque)
Network = ipaddress.IPv4Network | ipaddress.IPv6Network


def _parse_admin_token_role_mapping(raw_value: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    normalized = (raw_value or "").replace(";", "\n").replace(",", "\n")
    for line in normalized.splitlines():
        token_part, sep, role_part = line.partition(":")
        if not sep:
            continue
        token = token_part.strip()
        role = role_part.strip().lower()
        if not token or role not in {"admin", "board", "compliance"}:
            continue
        mapping[token] = role
    return mapping


def _parse_trusted_proxy_networks() -> list[Network]:
    networks: list[Network] = []
    for raw_cidr in settings.trusted_proxy_cidrs.split(","):
        cidr = raw_cidr.strip()
        if not cidr:
            continue
        try:
            networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError as exc:
            raise RuntimeError(f"invalid trusted proxy CIDR '{cidr}'") from exc
    return networks


def _is_ip_in_networks(ip_value: str, networks: list[Network]) -> bool:
    try:
        ip = ipaddress.ip_address(ip_value)
    except ValueError:
        return False
    return any(ip in network for network in networks)


def _forwarded_client_ip_if_trusted_proxy(request: Request) -> str | None:
    if not settings.trust_proxy_headers:
        return None
    if not request.client or not request.client.host:
        return None

    networks = _parse_trusted_proxy_networks()
    if not _is_ip_in_networks(request.client.host, networks):
        return None

    forwarded = request.headers.get("x-forwarded-for")
    if not forwarded:
        return None

    candidate = forwarded.split(",")[0].strip()
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return None
    return candidate


def _client_ip(request: Request) -> str:
    forwarded = _forwarded_client_ip_if_trusted_proxy(request)
    if forwarded:
        return forwarded
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _is_private_or_loopback_ip(ip_value: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_value)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback


def _is_internal_hostname(hostname: str) -> bool:
    host = hostname.strip().lower()
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    if host.endswith(".local") or host.endswith(".internal"):
        return True
    # Docker/Kubernetes-style service hostnames (single-label) are treated as internal.
    if "." not in host and re.fullmatch(r"[a-z0-9-]{1,63}", host):
        return True

    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False


def _is_internal_url(url: str) -> bool:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.hostname:
        return False
    return _is_internal_hostname(parsed.hostname)


def _parse_url_list(raw_value: str) -> list[str]:
    normalized = (raw_value or "").replace(";", "\n").replace(",", "\n")
    return [value.strip() for value in normalized.splitlines() if value.strip()]


def validate_sovereign_runtime_settings() -> None:
    if not settings.sovereign_mode or not settings.enforce_internal_endpoints_in_sovereign_mode:
        return

    violations: list[str] = []
    if not _is_internal_url(settings.evm_rpc_url):
        violations.append(f"evm_rpc_url must be internal/private in sovereign mode: {settings.evm_rpc_url}")
    if not _is_internal_url(settings.inhouse_payment_gateway_base_url):
        violations.append(
            "inhouse_payment_gateway_base_url must be internal/private in sovereign mode: "
            f"{settings.inhouse_payment_gateway_base_url}"
        )

    if violations:
        raise RuntimeError("sovereign mode misconfiguration: " + "; ".join(violations))


def validate_zero_external_mode_settings() -> None:
    if not settings.zero_external_mode:
        return

    violations: list[str] = []
    if not settings.sovereign_mode:
        violations.append("sovereign_mode must be true when zero_external_mode=true")
    if settings.enable_external_stripe_webhooks:
        violations.append("enable_external_stripe_webhooks must be false when zero_external_mode=true")
    if settings.enable_external_walletconnect:
        violations.append("enable_external_walletconnect must be false when zero_external_mode=true")
    if settings.public_web_mode:
        violations.append("public_web_mode must be false when zero_external_mode=true")

    url_settings = {
        "evm_rpc_url": settings.evm_rpc_url,
        "inhouse_payment_gateway_base_url": settings.inhouse_payment_gateway_base_url,
        "inhouse_checkout_app_base_url": settings.inhouse_checkout_app_base_url,
        "delivery_instacart_base_url": settings.delivery_instacart_base_url,
        "delivery_doordash_base_url": settings.delivery_doordash_base_url,
        "delivery_uber_eats_base_url": settings.delivery_uber_eats_base_url,
        "delivery_grubhub_base_url": settings.delivery_grubhub_base_url,
        "delivery_shipt_base_url": settings.delivery_shipt_base_url,
    }
    for key, url in url_settings.items():
        value = (url or "").strip()
        if not value:
            continue
        if not _is_internal_url(value):
            violations.append(f"{key} must be internal/private when zero_external_mode=true")

    for fallback_url in _parse_url_list(settings.evm_rpc_fallback_urls):
        if not _is_internal_url(fallback_url):
            violations.append("evm_rpc_fallback_urls must only contain internal/private URLs when zero_external_mode=true")

    if settings.sanctions_screening_provider.strip().lower() not in {"local_rules"}:
        violations.append("sanctions_screening_provider must be local_rules when zero_external_mode=true")

    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    for origin in origins:
        parsed = urlparse(origin)
        host = (parsed.hostname or "").strip().lower()
        if not host:
            violations.append("cors_origins entries must include host when zero_external_mode=true")
            continue
        if not _is_internal_hostname(host):
            violations.append("cors_origins must only use internal/private hosts when zero_external_mode=true")

    if violations:
        raise RuntimeError("zero-external mode misconfiguration: " + "; ".join(sorted(set(violations))))


def validate_inhouse_only_settings() -> None:
    if not settings.inhouse_only_mode:
        return

    violations: list[str] = []
    if not settings.sovereign_mode:
        violations.append("sovereign_mode must be true when inhouse_only_mode=true")
    if settings.enable_external_stripe_webhooks:
        violations.append("enable_external_stripe_webhooks must be false when inhouse_only_mode=true")
    if settings.enable_external_walletconnect:
        violations.append("enable_external_walletconnect must be false when inhouse_only_mode=true")
    if settings.admin_allow_legacy_api_tokens:
        violations.append("admin_allow_legacy_api_tokens must be false when inhouse_only_mode=true")
    if settings.public_web_mode:
        violations.append("public_web_mode must be false when inhouse_only_mode=true")
    if not _is_internal_url(settings.evm_rpc_url):
        violations.append("evm_rpc_url must be internal/private when inhouse_only_mode=true")
    if settings.trust_proxy_headers:
        try:
            parsed_networks = _parse_trusted_proxy_networks()
            if not parsed_networks:
                violations.append("trusted_proxy_cidrs must include at least one CIDR when trust_proxy_headers=true")
        except RuntimeError as exc:
            violations.append(str(exc))

    if violations:
        raise RuntimeError("inhouse-only misconfiguration: " + "; ".join(sorted(set(violations))))


def validate_public_runtime_settings() -> None:
    if settings.app_env.lower() != "prod" or not settings.public_web_mode:
        return

    violations: list[str] = []
    if settings.admin_allow_legacy_api_tokens:
        violations.append("admin_allow_legacy_api_tokens must be false in prod public_web_mode")
    if settings.admin_bootstrap_enabled:
        violations.append("admin_bootstrap_enabled must be false in prod public_web_mode")
    if settings.trust_proxy_headers:
        try:
            parsed_networks = _parse_trusted_proxy_networks()
            if not parsed_networks:
                violations.append("trusted_proxy_cidrs must include at least one CIDR when trust_proxy_headers=true")
        except RuntimeError as exc:
            violations.append(str(exc))

    if not settings.inhouse_only_mode and not settings.enable_external_walletconnect:
        violations.append("enable_external_walletconnect must be true in prod public_web_mode")

    parsed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    if not parsed_origins:
        violations.append("cors_origins must include at least one public origin in prod public_web_mode")
    for origin in parsed_origins:
        parsed = urlparse(origin)
        host = (parsed.hostname or "").lower()
        if host in {"localhost", "127.0.0.1"}:
            violations.append("cors_origins cannot include localhost/127.0.0.1 in prod public_web_mode")
        if parsed.scheme not in {"https"}:
            violations.append("cors_origins must use https in prod public_web_mode")

    if violations:
        raise RuntimeError("public mode misconfiguration: " + "; ".join(sorted(set(violations))))


def validate_admin_auth_settings() -> None:
    violations: list[str] = []

    if settings.admin_bootstrap_enabled:
        bootstrap_mapping = _parse_admin_token_role_mapping(settings.admin_bootstrap_tokens)
        if not bootstrap_mapping:
            violations.append(
                "admin_bootstrap_tokens must include at least one valid token:role mapping "
                "when admin_bootstrap_enabled=true"
            )

    if settings.admin_allow_legacy_api_tokens:
        legacy_mapping = _parse_admin_token_role_mapping(settings.admin_legacy_api_tokens)
        if not legacy_mapping:
            violations.append(
                "admin_legacy_api_tokens must include at least one valid token:role mapping "
                "when admin_allow_legacy_api_tokens=true"
            )

    if violations:
        raise RuntimeError("admin auth misconfiguration: " + "; ".join(sorted(set(violations))))


def log_admin_auth_mode() -> None:
    bootstrap_mapping = _parse_admin_token_role_mapping(settings.admin_bootstrap_tokens)
    legacy_mapping = _parse_admin_token_role_mapping(settings.admin_legacy_api_tokens)
    logger.warning(
        "admin_auth_mode bootstrap_enabled=%s bootstrap_token_count=%d legacy_enabled=%s "
        "legacy_token_count=%d bearer_enabled=true",
        settings.admin_bootstrap_enabled,
        len(bootstrap_mapping),
        settings.admin_allow_legacy_api_tokens,
        len(legacy_mapping),
    )


def validate_runtime_startup_settings() -> None:
    validate_zero_external_mode_settings()
    validate_inhouse_only_settings()
    validate_sovereign_runtime_settings()
    validate_public_runtime_settings()
    validate_admin_auth_settings()


@app.on_event("startup")
def startup_event() -> None:
    validate_runtime_startup_settings()
    log_admin_auth_mode()
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
            "ofac_screening": {
                "provider": screening_provider_name(),
                "enforced": runtime_policies.enforce_ofac_screening,
            },
            "tax_receipts": "enabled" if runtime_policies.tax_receipts_enabled else "disabled_pending_legal_review",
        },
        "sovereignty": {
            "zero_external_mode": settings.zero_external_mode,
            "sovereign_mode": settings.sovereign_mode,
            "inhouse_only_mode": settings.inhouse_only_mode,
            "external_stripe_webhooks": settings.enable_external_stripe_webhooks,
            "external_walletconnect": settings.enable_external_walletconnect,
        },
    }


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    db = SessionLocal()
    try:
        return build_prometheus_metrics(db)
    finally:
        db.close()


@app.middleware("http")
async def inhouse_only_network_guard(request: Request, call_next):
    if settings.inhouse_only_mode:
        ip = _client_ip(request)
        if not _is_private_or_loopback_ip(ip):
            return JSONResponse(
                status_code=403,
                content={"detail": "inhouse_only_mode enabled: external client IP denied"},
            )
    return await call_next(request)


@app.middleware("http")
async def public_rate_limit(request: Request, call_next):
    path = request.url.path
    if not path.startswith("/public/"):
        return await call_next(request)

    window_seconds = max(settings.public_rate_limit_window_seconds, 1)
    max_requests = max(settings.public_rate_limit_max_requests, 1)
    now = datetime.now(UTC)
    ip = _client_ip(request)
    key = f"{ip}:{path}"

    with _rate_limiter_lock:
        bucket = _rate_limiter_events[key]
        cutoff = now.timestamp() - window_seconds
        while bucket and bucket[0].timestamp() < cutoff:
            bucket.popleft()
        if len(bucket) >= max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        f"public rate limit exceeded: {max_requests} requests per "
                        f"{window_seconds} seconds for this endpoint"
                    )
                },
            )
        bucket.append(now)

    return await call_next(request)
