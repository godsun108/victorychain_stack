#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import sys
from pathlib import Path
from urllib.parse import urlparse


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def normalize_bool(raw: str | None) -> bool:
    return (raw or "").strip().lower() in {"1", "true", "yes", "on"}


def parse_url_list(raw: str | None) -> list[str]:
    normalized = (raw or "").replace(";", "\n").replace(",", "\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def is_internal_hostname(hostname: str) -> bool:
    host = hostname.strip().lower()
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    if host.endswith(".local") or host.endswith(".internal"):
        return True
    if "." not in host and host.replace("-", "").isalnum():
        return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False


def is_internal_url(url: str) -> bool:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.hostname:
        return False
    return is_internal_hostname(parsed.hostname)


def check_file(env_path: Path) -> list[str]:
    values = parse_env_file(env_path)
    errors: list[str] = []

    required_true = {"ZERO_EXTERNAL_MODE", "SOVEREIGN_MODE", "INHOUSE_ONLY_MODE"}
    required_false = {"ENABLE_EXTERNAL_STRIPE_WEBHOOKS", "ENABLE_EXTERNAL_WALLETCONNECT", "PUBLIC_WEB_MODE"}
    for key in sorted(required_true):
        if not normalize_bool(values.get(key)):
            errors.append(f"{key} must be true")
    for key in sorted(required_false):
        if normalize_bool(values.get(key)):
            errors.append(f"{key} must be false")

    sanctions_provider = (values.get("SANCTIONS_SCREENING_PROVIDER") or "").strip().lower()
    if sanctions_provider and sanctions_provider != "local_rules":
        errors.append("SANCTIONS_SCREENING_PROVIDER must be local_rules")

    url_keys = (
        "EVM_RPC_URL",
        "INHOUSE_PAYMENT_GATEWAY_BASE_URL",
        "INHOUSE_CHECKOUT_APP_BASE_URL",
        "DELIVERY_INSTACART_BASE_URL",
        "DELIVERY_DOORDASH_BASE_URL",
        "DELIVERY_UBER_EATS_BASE_URL",
        "DELIVERY_GRUBHUB_BASE_URL",
        "DELIVERY_SHIPT_BASE_URL",
    )
    for key in url_keys:
        value = (values.get(key) or "").strip()
        if not value:
            continue
        if not is_internal_url(value):
            errors.append(f"{key} must be internal/private: {value}")

    for fallback_url in parse_url_list(values.get("EVM_RPC_FALLBACK_URLS")):
        if not is_internal_url(fallback_url):
            errors.append(f"EVM_RPC_FALLBACK_URLS must only contain internal/private URLs: {fallback_url}")

    origins = parse_url_list(values.get("CORS_ORIGINS"))
    for origin in origins:
        parsed = urlparse(origin)
        host = (parsed.hostname or "").strip().lower()
        if not host:
            errors.append(f"CORS_ORIGINS entry must include host: {origin}")
            continue
        if not is_internal_hostname(host):
            errors.append(f"CORS_ORIGINS must only use internal/private hosts: {origin}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate sovereign/off-grid env baseline.")
    parser.add_argument(
        "--env-file",
        action="append",
        dest="env_files",
        required=True,
        help="Path to env file (can be provided multiple times).",
    )
    args = parser.parse_args()

    failed = 0
    for raw_path in args.env_files:
        env_path = Path(raw_path)
        if not env_path.exists():
            print(f"{env_path}: missing file", file=sys.stderr)
            failed += 1
            continue

        errors = check_file(env_path)
        if errors:
            failed += 1
            print(f"{env_path}:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
        else:
            print(f"{env_path}: ok")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
