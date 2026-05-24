#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Generate secure admin token mappings for .env files.

Usage:
  ./scripts/generate_admin_tokens.sh [options]

Options:
  --roles <csv>           Roles to generate (default: admin,board,compliance)
  --length <n>            Token length (default: 48)
  --include-legacy        Also emit ADMIN_LEGACY_API_TOKENS mapping
  --help                  Show this help

Examples:
  ./scripts/generate_admin_tokens.sh
  ./scripts/generate_admin_tokens.sh --roles admin,board --length 64
  ./scripts/generate_admin_tokens.sh --include-legacy
EOF
}

roles_csv="admin,board,compliance"
token_length=48
include_legacy="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --roles)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --roles" >&2
        exit 1
      fi
      roles_csv="$2"
      shift 2
      ;;
    --length)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --length" >&2
        exit 1
      fi
      token_length="$2"
      shift 2
      ;;
    --include-legacy)
      include_legacy="true"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! [[ "$token_length" =~ ^[0-9]+$ ]] || [[ "$token_length" -lt 24 ]]; then
  echo "--length must be an integer >= 24" >&2
  exit 1
fi

IFS=',' read -r -a roles <<< "$roles_csv"
if [[ ${#roles[@]} -eq 0 ]]; then
  echo "At least one role is required" >&2
  exit 1
fi

for role in "${roles[@]}"; do
  if [[ -z "$role" ]]; then
    echo "Roles list contains an empty role" >&2
    exit 1
  fi
  if ! [[ "$role" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Invalid role value: $role" >&2
    exit 1
  fi
done

generate_token() {
  local length="$1"
  local bytes
  bytes=$(( (length * 3 + 3) / 4 ))

  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 "$bytes" \
      | tr -d '\n' \
      | tr '+/' '-_' \
      | tr -d '=' \
      | cut -c1-"$length"
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    python3 - "$length" <<'PY'
import secrets
import sys

length = int(sys.argv[1])
token = ""
while len(token) < length:
    token += secrets.token_urlsafe(length)
print(token[:length], end="")
PY
    return
  fi

  echo "Neither openssl nor python3 is available to generate secure tokens" >&2
  exit 1
}

build_mapping() {
  local mapping=""
  local role token pair
  for role in "${roles[@]}"; do
    token="$(generate_token "$token_length")"
    pair="${token}:${role}"
    if [[ -n "$mapping" ]]; then
      mapping+=",${pair}"
    else
      mapping="${pair}"
    fi
  done
  printf "%s" "$mapping"
}

bootstrap_mapping="$(build_mapping)"

echo "# Generated $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "ADMIN_BOOTSTRAP_TOKENS=${bootstrap_mapping}"
if [[ "$include_legacy" == "true" ]]; then
  legacy_mapping="$(build_mapping)"
  echo "ADMIN_LEGACY_API_TOKENS=${legacy_mapping}"
fi
