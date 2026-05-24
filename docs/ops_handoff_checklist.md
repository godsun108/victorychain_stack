# Ops Handoff Checklist (Admin Auth + Runtime)

Use this checklist for shift handoff, planned rotations, and post-incident stabilization.

## 1. Pre-Change Snapshot

1. Confirm API status:
`make api-status PORT=9000`
2. Confirm current admin auth mode line:
`grep 'admin_auth_mode' .victory_impact_api.log | tail -n 5`
3. Confirm current env posture:
`grep '^ADMIN_BOOTSTRAP_ENABLED=' .env`
`grep '^ADMIN_ALLOW_LEGACY_API_TOKENS=' .env`

## 2. Token Rotation

1. Rotate admin tokens with backup:
`make admin-token-rotate ENV_FILE=.env`
2. Record backup filename shown in command output (`.env.bak.<timestamp>`).
3. Validate env hygiene:
`make admin-env-check ENV_FILE=.env EXPECT_BOOTSTRAP_DISABLED=true EXPECT_LEGACY_DISABLED=true`

## 3. Runtime Apply

1. Restart managed API process:
`make api-restart PORT=9000`
2. Re-check service status:
`make api-status PORT=9000`
3. Verify startup admin auth mode audit:
`grep 'admin_auth_mode' .victory_impact_api.log | tail -n 5`
Expected steady state:
- `bootstrap_enabled=False`
- `legacy_enabled=False`
- `bearer_enabled=true`

## 4. Functional Verification

1. Health endpoint:
`curl -sS http://127.0.0.1:9000/`
2. Run regression tests:
`pytest -q`
3. Confirm no unexpected admin auth warnings in logs:
`grep -iE 'admin auth|bootstrap|legacy' .victory_impact_api.log | tail -n 50`

## 5. Incident Recovery (If Needed)

1. Follow emergency bootstrap procedure in:
`docs/admin_auth_rotation.md`
2. After bearer recovery, disable bootstrap immediately:
`make admin-token-rotate ENV_FILE=.env`
`make api-restart PORT=9000`
3. Re-run Section 3 and Section 4.

## 6. Drill (Non-Production, Recommended Each Release)

Run the full recovery drill on isolated port and temp env:

`make admin-auth-recovery-drill ENV_FILE=.env PORT=9010`

Success means:

1. bootstrap session mint succeeds during temporary bootstrap enablement
2. bearer session access + revoke succeeds
3. bootstrap mint fails (401) after bootstrap disablement
4. drill log contains `admin_auth_mode bootstrap_enabled=False`

## 7. Rollback (If Rotation Fails)

1. Restore latest backup:
`cp .env.bak.<timestamp> .env`
2. Validate and restart:
`make admin-env-check ENV_FILE=.env`
`make api-restart PORT=9000`
3. Escalate with backup timestamp and failure log excerpt.
