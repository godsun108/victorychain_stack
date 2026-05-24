#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Rotate admin token mappings directly in an env file with backup + validation.

Usage:
  ./scripts/rotate_admin_tokens.sh [options]

Options:
  --env-file <path>       Env file to update (default: .env)
  --roles <csv>           Roles to generate (default: admin,board,compliance)
  --length <n>            Token length (default: 48)
  --include-legacy        Generate legacy token mappings and enable legacy auth
  --enable-bootstrap      Set ADMIN_BOOTSTRAP_ENABLED=true (default: false)
  --help                  Show this help

Examples:
  ./scripts/rotate_admin_tokens.sh --env-file .env
  ./scripts/rotate_admin_tokens.sh --env-file .env --enable-bootstrap
  ./scripts/rotate_admin_tokens.sh --env-file .env --include-legacy
EOF
}

env_file=".env"
roles_csv="admin,board,compliance"
token_length=48
include_legacy="false"
enable_bootstrap="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --env-file" >&2
        exit 1
      fi
      env_file="$2"
      shift 2
      ;;
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
    --enable-bootstrap)
      enable_bootstrap="true"
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

if [[ ! -f "$env_file" ]]; then
  echo "Env file not found: $env_file" >&2
  exit 1
fi

script_dir="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

tmp_output="$(mktemp)"
tmp_env="$(mktemp)"
backup_file="${env_file}.bak.$(date -u +%Y%m%dT%H%M%SZ)"

cleanup() {
  rm -f "$tmp_output" "$tmp_env"
}
trap cleanup EXIT

gen_args=(--roles "$roles_csv" --length "$token_length")
if [[ "$include_legacy" == "true" ]]; then
  gen_args+=(--include-legacy)
fi

"$repo_root/scripts/generate_admin_tokens.sh" "${gen_args[@]}" >"$tmp_output"

bootstrap_mapping="$(sed -n 's/^ADMIN_BOOTSTRAP_TOKENS=//p' "$tmp_output")"
legacy_mapping="$(sed -n 's/^ADMIN_LEGACY_API_TOKENS=//p' "$tmp_output")"

if [[ -z "$bootstrap_mapping" ]]; then
  echo "Failed to generate ADMIN_BOOTSTRAP_TOKENS mapping" >&2
  exit 1
fi

set_env_var() {
  local key="$1"
  local value="$2"
  local file="$3"
  awk -v key="$key" -v value="$value" '
    BEGIN { updated = 0 }
    $0 ~ ("^" key "=") {
      if (!updated) {
        print key "=" value
        updated = 1
      }
      next
    }
    { print }
    END {
      if (!updated) {
        print key "=" value
      }
    }
  ' "$file" >"$tmp_env"
  mv "$tmp_env" "$file"
}

cp "$env_file" "$backup_file"

set_env_var "ADMIN_BOOTSTRAP_ENABLED" "$enable_bootstrap" "$env_file"
set_env_var "ADMIN_BOOTSTRAP_ALLOWED_ROLES" "$roles_csv" "$env_file"
set_env_var "ADMIN_BOOTSTRAP_TOKENS" "$bootstrap_mapping" "$env_file"

if [[ "$include_legacy" == "true" ]]; then
  if [[ -z "$legacy_mapping" ]]; then
    echo "Failed to generate ADMIN_LEGACY_API_TOKENS mapping" >&2
    exit 1
  fi
  set_env_var "ADMIN_ALLOW_LEGACY_API_TOKENS" "true" "$env_file"
  set_env_var "ADMIN_LEGACY_API_TOKENS" "$legacy_mapping" "$env_file"
else
  set_env_var "ADMIN_ALLOW_LEGACY_API_TOKENS" "false" "$env_file"
  set_env_var "ADMIN_LEGACY_API_TOKENS" "" "$env_file"
fi

"$repo_root/scripts/check_admin_env_hygiene.py" --env-file "$env_file" >/dev/null

echo "Rotated admin token mappings in $env_file"
echo "Backup created at $backup_file"
echo "Validation passed"
if [[ "$enable_bootstrap" == "true" ]]; then
  echo "ADMIN_BOOTSTRAP_ENABLED=true"
else
  echo "ADMIN_BOOTSTRAP_ENABLED=false"
fi
if [[ "$include_legacy" == "true" ]]; then
  echo "ADMIN_ALLOW_LEGACY_API_TOKENS=true"
else
  echo "ADMIN_ALLOW_LEGACY_API_TOKENS=false"
fi
