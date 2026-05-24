#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ALLOWED_ROLES = {"admin", "board", "compliance"}
BANNED_TOKEN_LITERALS = {
    "admin-token",
    "board-token",
    "compliance-token",
    "replace-with-strong-bootstrap-secret",
}


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


def parse_token_mapping(raw: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    normalized = raw.replace(";", "\n").replace(",", "\n")
    for line in normalized.splitlines():
        token_part, sep, role_part = line.partition(":")
        if not sep:
            continue
        token = token_part.strip()
        role = role_part.strip().lower()
        if token and role in ALLOWED_ROLES:
            mapping[token] = role
    return mapping


def normalize_bool(raw: str | None) -> bool:
    return (raw or "").strip().lower() in {"1", "true", "yes", "on"}


def check_env_file(
    env_path: Path,
    expect_bootstrap_disabled: bool,
    expect_legacy_disabled: bool,
    require_empty_bootstrap_tokens: bool,
    require_empty_legacy_tokens: bool,
) -> list[str]:
    errors: list[str] = []
    values = parse_env_file(env_path)

    bootstrap_enabled = normalize_bool(values.get("ADMIN_BOOTSTRAP_ENABLED"))
    legacy_enabled = normalize_bool(values.get("ADMIN_ALLOW_LEGACY_API_TOKENS"))
    bootstrap_tokens_raw = values.get("ADMIN_BOOTSTRAP_TOKENS", "")
    legacy_tokens_raw = values.get("ADMIN_LEGACY_API_TOKENS", "")

    if expect_bootstrap_disabled and bootstrap_enabled:
        errors.append("ADMIN_BOOTSTRAP_ENABLED must be false")
    if expect_legacy_disabled and legacy_enabled:
        errors.append("ADMIN_ALLOW_LEGACY_API_TOKENS must be false")
    if require_empty_bootstrap_tokens and bootstrap_tokens_raw:
        errors.append("ADMIN_BOOTSTRAP_TOKENS must be empty")
    if require_empty_legacy_tokens and legacy_tokens_raw:
        errors.append("ADMIN_LEGACY_API_TOKENS must be empty")

    combined = "\n".join([bootstrap_tokens_raw, legacy_tokens_raw]).lower()
    for literal in sorted(BANNED_TOKEN_LITERALS):
        if literal in combined:
            errors.append(f"forbidden static token literal found: {literal}")

    bootstrap_mapping = parse_token_mapping(bootstrap_tokens_raw)
    legacy_mapping = parse_token_mapping(legacy_tokens_raw)

    if bootstrap_tokens_raw and not bootstrap_mapping:
        errors.append("ADMIN_BOOTSTRAP_TOKENS must use token:role mapping")
    if legacy_tokens_raw and not legacy_mapping:
        errors.append("ADMIN_LEGACY_API_TOKENS must use token:role mapping")
    if bootstrap_enabled and not bootstrap_mapping:
        errors.append("ADMIN_BOOTSTRAP_TOKENS must include at least one mapping when bootstrap is enabled")
    if legacy_enabled and not legacy_mapping:
        errors.append("ADMIN_LEGACY_API_TOKENS must include at least one mapping when legacy auth is enabled")

    token_pattern = re.compile(r"^[A-Za-z0-9_-]{16,}$")
    for token in bootstrap_mapping:
        if not token_pattern.fullmatch(token):
            errors.append("ADMIN_BOOTSTRAP_TOKENS includes malformed token value")
            break
    for token in legacy_mapping:
        if not token_pattern.fullmatch(token):
            errors.append("ADMIN_LEGACY_API_TOKENS includes malformed token value")
            break

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate admin auth token hygiene in env files.")
    parser.add_argument(
        "--env-file",
        action="append",
        dest="env_files",
        required=True,
        help="Path to env file (can be provided multiple times).",
    )
    parser.add_argument("--expect-bootstrap-disabled", action="store_true")
    parser.add_argument("--expect-legacy-disabled", action="store_true")
    parser.add_argument("--require-empty-bootstrap-tokens", action="store_true")
    parser.add_argument("--require-empty-legacy-tokens", action="store_true")
    args = parser.parse_args()

    overall_errors = 0
    for raw_path in args.env_files:
        env_path = Path(raw_path)
        if not env_path.exists():
            print(f"{env_path}: missing file", file=sys.stderr)
            overall_errors += 1
            continue

        errors = check_env_file(
            env_path=env_path,
            expect_bootstrap_disabled=args.expect_bootstrap_disabled,
            expect_legacy_disabled=args.expect_legacy_disabled,
            require_empty_bootstrap_tokens=args.require_empty_bootstrap_tokens,
            require_empty_legacy_tokens=args.require_empty_legacy_tokens,
        )
        if errors:
            overall_errors += 1
            print(f"{env_path}:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
        else:
            print(f"{env_path}: ok")

    return 1 if overall_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
