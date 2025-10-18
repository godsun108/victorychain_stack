#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Usage: status.sh [-j|--json]
JSON=0
if [[ "${1:-}" == "-j" || "${1:-}" == "--json" ]]; then
  JSON=1
fi

# Compute prompt version (sha256 of prompts if present) and git commit short SHA
PROMPT_VERSION=""
if [[ -n "${PROMPT_FILE:-}" && -f "$PROMPT_FILE" ]]; then
  PROMPT_VERSION=$(shasum -a 256 "$PROMPT_FILE" | awk '{print $1}')
elif [[ -f prompts/PROMPT.txt ]]; then
  PROMPT_VERSION=$(shasum -a 256 prompts/PROMPT.txt | awk '{print $1}')
fi
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "nogit")

# Query status via Python helper
if (( JSON )); then
  ACTOR=${LOCK_ACTOR:-} PROMPT_VERSION="$PROMPT_VERSION" GIT_COMMIT="$GIT_COMMIT" python - <<'PY'
import os, json, sys
from governance import vault
s = vault.status()
# augment
s.update({
  'prompt_version': os.environ.get('PROMPT_VERSION') or None,
  'git_commit': os.environ.get('GIT_COMMIT') or None,
  'requires_approval': True,
  'victory_anchor_ready': True,
})
print(json.dumps(s, indent=2, sort_keys=True))
sys.exit(2 if s.get('locked') else 0)
PY
else
  ACTOR=${LOCK_ACTOR:-} PROMPT_VERSION="$PROMPT_VERSION" GIT_COMMIT="$GIT_COMMIT" python - <<'PY'
import os, sys
from governance import vault
s = vault.status()
print(f"Lockdown: {'ACTIVE' if s.get('locked') else 'INACTIVE'}")
print(f"Reason: {s.get('reason')}")
print(f"Trace ID: {s.get('trace_id')}")
print(f"Since: {s.get('since')}")
print(f"By: {s.get('by')}")
print("Approval Required To Unlock: YES")
print(f"Prompt Version: {os.environ.get('PROMPT_VERSION')}")
print(f"Git Commit: {os.environ.get('GIT_COMMIT')}")
print("Victory Anchor Ready: YES")
sys.exit(2 if s.get('locked') else 0)
PY
fi
