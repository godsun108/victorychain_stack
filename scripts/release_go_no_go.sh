#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:-inhouse}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
SKIP_FRONTEND="${SKIP_FRONTEND:-0}"

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

normalize_bool() {
  echo "${1:-}" | tr '[:upper:]' '[:lower:]'
}

expect_eq() {
  local key="$1"
  local expected="$2"
  local actual="${!key:-}"
  if [[ "$actual" != "$expected" ]]; then
    fail "$key must be '$expected' (got '${actual:-<unset>}')"
  fi
  echo "[OK] $key=$actual"
}

expect_bool() {
  local key="$1"
  local expected="$2"
  local actual
  actual="$(normalize_bool "${!key:-}")"
  if [[ "$actual" != "$expected" ]]; then
    fail "$key must be '$expected' (got '${actual:-<unset>}')"
  fi
  echo "[OK] $key=$actual"
}

expect_https_origins() {
  local origins="${CORS_ORIGINS:-}"
  [[ -n "$origins" ]] || fail "CORS_ORIGINS must be set"
  IFS=',' read -r -a parts <<< "$origins"
  for origin in "${parts[@]}"; do
    local trimmed
    trimmed="$(echo "$origin" | xargs)"
    [[ "$trimmed" == https://* ]] || fail "CORS_ORIGINS entry must use https: $trimmed"
    [[ "$trimmed" != *localhost* ]] || fail "CORS_ORIGINS cannot include localhost: $trimmed"
    [[ "$trimmed" != *127.0.0.1* ]] || fail "CORS_ORIGINS cannot include 127.0.0.1: $trimmed"
  done
  echo "[OK] CORS_ORIGINS uses HTTPS public origins"
}

[[ -f "$ENV_FILE" ]] || fail "Env file not found: $ENV_FILE"

while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
  line="${raw_line%$'\r'}"
  [[ -z "$line" ]] && continue
  [[ "${line:0:1}" == "#" ]] && continue
  key="${line%%=*}"
  value="${line#*=}"
  [[ -n "$key" ]] || continue
  export "$key=$value"
done < "$ENV_FILE"

echo "[INFO] Profile: $PROFILE"
echo "[INFO] Env file: $ENV_FILE"

expect_eq APP_ENV "prod"
expect_bool ADMIN_ALLOW_LEGACY_API_TOKENS "false"
expect_bool ADMIN_BOOTSTRAP_ENABLED "false"

case "$PROFILE" in
  inhouse)
    expect_bool ZERO_EXTERNAL_MODE "true"
    expect_bool PUBLIC_WEB_MODE "false"
    expect_bool INHOUSE_ONLY_MODE "true"
    expect_bool SOVEREIGN_MODE "true"
    expect_bool ENABLE_EXTERNAL_STRIPE_WEBHOOKS "false"
    expect_bool ENABLE_EXTERNAL_WALLETCONNECT "false"
    ./.venv_victoryimpact/bin/python scripts/check_sovereign_env_baseline.py --env-file "$ENV_FILE"
    ;;
  public)
    expect_bool ZERO_EXTERNAL_MODE "false"
    expect_bool PUBLIC_WEB_MODE "true"
    expect_bool INHOUSE_ONLY_MODE "false"
    expect_bool ENABLE_EXTERNAL_WALLETCONNECT "true"
    expect_https_origins
    ;;
  *)
    fail "Unknown profile '$PROFILE' (expected: inhouse|public)"
    ;;
esac

echo "[INFO] Running backend runtime validation and tests..."
cd "$ROOT_DIR"
./.venv_victoryimpact/bin/python - <<'PY'
from src.victory_impact.main import (
    validate_inhouse_only_settings,
    validate_public_runtime_settings,
    validate_sovereign_runtime_settings,
    validate_zero_external_mode_settings,
)

validate_zero_external_mode_settings()
validate_inhouse_only_settings()
validate_sovereign_runtime_settings()
validate_public_runtime_settings()
print("[OK] backend runtime validation passed")
PY

APP_ENV=dev \
PUBLIC_WEB_MODE=false \
INHOUSE_ONLY_MODE=false \
ADMIN_BOOTSTRAP_ENABLED=true \
ADMIN_ALLOW_LEGACY_API_TOKENS=true \
ENABLE_EXTERNAL_WALLETCONNECT=false \
CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173" \
./.venv_victoryimpact/bin/pytest -q tests/test_self_service.py -k \
  "admin_auth_session_endpoints_issue_and_revoke or admin_session_limit_auto_revokes_oldest or admin_bootstrap_can_be_disabled or admin_ops_action_and_audit_endpoints or admin_ops_support_bundle_archive_and_list or public_runtime_validation_requires_walletconnect_and_https_origins or public_runtime_validation_allows_no_walletconnect_in_inhouse_only_mode or internal_url_accepts_single_label_service_hostnames"

if [[ "$SKIP_FRONTEND" != "1" ]]; then
  echo "[INFO] Running frontend release build + iOS sync..."
  cd "$ROOT_DIR/frontend"
  npm run ios:sync
  echo "[OK] frontend build + iOS sync passed"
else
  echo "[INFO] SKIP_FRONTEND=1, skipping frontend build and iOS sync"
fi

echo "[PASS] Release go/no-go checks completed for profile '$PROFILE'."
