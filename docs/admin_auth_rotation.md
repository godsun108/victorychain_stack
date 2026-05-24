# Admin Auth Rotation Runbook

This runbook covers secure rotation and emergency handling for admin authentication secrets.

Defaults in this repository are:

- `ADMIN_BOOTSTRAP_ENABLED=false`
- `ADMIN_ALLOW_LEGACY_API_TOKENS=false`
- bearer sessions are the primary admin auth path

## 1. Scheduled Rotation (Recommended)

Rotate tokens in-place with backup and validation:

```bash
make admin-token-rotate ENV_FILE=.env
```

What this does:

- Creates a timestamped backup (for example: `.env.bak.20260524T180140Z`)
- Rotates `ADMIN_BOOTSTRAP_TOKENS`
- Keeps bootstrap disabled unless explicitly enabled
- Keeps legacy disabled unless explicitly enabled
- Validates env hygiene before completion

Then verify:

```bash
make admin-env-check ENV_FILE=.env EXPECT_BOOTSTRAP_DISABLED=true EXPECT_LEGACY_DISABLED=true
```

## 2. Emergency Bootstrap Enable (Temporary)

Use only for controlled incident response when you need to mint a new bearer token and current bearer auth is unavailable.

Enable bootstrap temporarily (and rotate fresh token mappings):

```bash
make admin-token-rotate ENV_FILE=.env ENABLE_BOOTSTRAP=true ROLES=admin
```

Restart API process if needed so runtime picks up updated env:

```bash
make api-restart PORT=9000
```

Mint a bearer token:

```bash
curl -sS -X POST "http://localhost:9000/admin/auth/session" \
  -H "x-api-token: <bootstrap-token-from-.env>" \
  -H "Content-Type: application/json"
```

After bearer recovery, immediately disable bootstrap again:

```bash
make admin-token-rotate ENV_FILE=.env
make api-restart PORT=9000
```

## 3. Rollback

List backups:

```bash
ls -1t .env.bak.* | head
```

Restore a backup:

```bash
cp .env.bak.<timestamp> .env
make admin-env-check ENV_FILE=.env
make api-restart PORT=9000
```

## 4. Incident-Closure Checklist

1. Confirm bootstrap disabled:
`grep '^ADMIN_BOOTSTRAP_ENABLED=' .env`
2. Confirm legacy disabled:
`grep '^ADMIN_ALLOW_LEGACY_API_TOKENS=' .env`
3. Verify startup auth-mode audit line:
`grep 'admin_auth_mode' .victory_impact_api.log | tail -n 5`
4. Re-run regression tests:
`pytest -q`

## 5. CI/Policy Guardrails

CI enforces token hygiene in `.env.example` and `.env.inhouse.example` via:

```bash
python scripts/check_admin_env_hygiene.py \
  --env-file .env.example \
  --env-file .env.inhouse.example \
  --expect-bootstrap-disabled \
  --expect-legacy-disabled \
  --require-empty-bootstrap-tokens \
  --require-empty-legacy-tokens
```
