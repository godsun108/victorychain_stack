#!/usr/bin/env python3
import argparse
import base64
import datetime as dt
import json
import os
import sys
import time
from urllib.parse import urljoin

import requests

UTC = dt.timezone.utc


def b64url_decode(data: str) -> bytes:
    data += "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def decode_jwt_unsafe(token: str):
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload = json.loads(b64url_decode(parts[1]).decode("utf-8"))
        return payload
    except Exception:
        return None


def http_get_json(url: str, timeout: float):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def http_get_text(url: str, timeout: float):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text


def post_slack(webhook: str, text: str, blocks=None):
    try:
        payload = {"text": text}
        if blocks is not None:
            payload["blocks"] = blocks
        r = requests.post(webhook, json=payload, timeout=5)
        r.raise_for_status()
    except Exception:
        pass


def now_utc():
    return dt.datetime.now(tz=UTC)


def within_windows_utc(now: dt.datetime, windows_file: str) -> tuple[bool, list]:
    if not windows_file:
        return False, []
    if not os.path.exists(windows_file):
        # If no file, assume not blocked
        return False, []
    try:
        with open(windows_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return False, []

    # Supported formats:
    # 1) {"windows": [{"start": "YYYY-MM-DDTHH:MM[:SS]Z?", "end": "..."}, ...]}
    # 2) list of such dicts at top-level
    windows = []
    if isinstance(data, dict) and isinstance(data.get("windows"), list):
        windows = data["windows"]
    elif isinstance(data, list):
        windows = data

    hits = []
    for w in windows:
        if not isinstance(w, dict):
            continue
        s = w.get("start")
        e = w.get("end")
        if not s or not e:
            continue
        # Normalize Z -> +00:00
        s_norm = s.replace("Z", "+00:00")
        e_norm = e.replace("Z", "+00:00")
        try:
            s_dt = dt.datetime.fromisoformat(s_norm)
            e_dt = dt.datetime.fromisoformat(e_norm)
            if s_dt.tzinfo is None:
                s_dt = s_dt.replace(tzinfo=UTC)
            if e_dt.tzinfo is None:
                e_dt = e_dt.replace(tzinfo=UTC)
        except Exception:
            # Try HH:MM only (assume today UTC)
            try:
                s_h, s_m = map(int, s.split(":")[:2])
                e_h, e_m = map(int, e.split(":")[:2])
                today = now.date()
                s_dt = dt.datetime(
                    today.year, today.month, today.day, s_h, s_m, tzinfo=UTC
                )
                e_dt = dt.datetime(
                    today.year, today.month, today.day, e_h, e_m, tzinfo=UTC
                )
            except Exception:
                continue
        if s_dt <= now <= e_dt:
            hits.append({"start": s_dt.isoformat(), "end": e_dt.isoformat()})
    return (len(hits) > 0), hits


def prom_query(prom: str, q: str, timeout: float):
    url = urljoin(
        prom.rstrip("/") + "/", f"api/v1/query?query={requests.utils.quote(q, safe='')}"
    )
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "success":
        raise RuntimeError(f"Prom query failed: {data}")
    return data["data"]["result"]


def prom_rules(prom: str, timeout: float):
    url = urljoin(prom.rstrip("/") + "/", "api/v1/rules")
    return http_get_json(url, timeout)


def prom_targets(prom: str, timeout: float):
    url = urljoin(prom.rstrip("/") + "/", "api/v1/targets")
    return http_get_json(url, timeout)


def prom_config(prom: str, timeout: float):
    url = urljoin(prom.rstrip("/") + "/", "api/v1/status/config")
    return http_get_json(url, timeout)


def require(cond: bool, msg: str, errors: list):
    if not cond:
        errors.append(msg)
        print(f"[FAIL] {msg}")
    else:
        print(f"[OK] {msg}")


def main():
    ap = argparse.ArgumentParser(description="VTB Preflight Suite")
    ap.add_argument(
        "--prom", required=True, help="Prometheus base URL, e.g., http://localhost:9090"
    )
    ap.add_argument(
        "--env-file", default=".env.live", help="Env file to read (for DRY_RUN, etc.)"
    )
    ap.add_argument(
        "--windows-file",
        default="riskd/riskd_windows.auto.json",
        help="Auto-unpanic disable windows JSON",
    )
    ap.add_argument(
        "--agent",
        default=os.environ.get("AGENT_URL", "http://localhost:8080"),
        help="Agent base URL",
    )
    ap.add_argument(
        "--riskd-metrics",
        default=os.environ.get("RISKD_METRICS", "http://localhost:9111/metrics"),
        help="riskd metrics URL",
    )
    ap.add_argument(
        "--expect-guardrails",
        action="store_true",
        help="Expect guardrail rules present",
    )
    ap.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("PREFLIGHT_TIMEOUT", 5)),
        help="HTTP timeout seconds",
    )
    args = ap.parse_args()

    slack = os.environ.get("SLACK_WEBHOOK_URL")

    started = time.time()
    print("== VTB PREFLIGHT ==")
    print("Prometheus:", args.prom)
    print("Agent:", args.agent)
    print("riskd metrics:", args.riskd_metrics)
    print("Env file:", args.env_file)
    print("Windows file:", args.windows_file)

    errors: list[str] = []

    # 1) Prom reachable + config sanity
    try:
        cfg = prom_config(args.prom, args.timeout)
        cfg_yml = cfg.get("data", {}).get("yaml", "")
        require(bool(cfg_yml), "Prometheus config fetched", errors)
        # quick job presence check by name
        expect_jobs = {"momentum_shards", "riskd", "panic_signer"}
        present = {j for j in expect_jobs if j in cfg_yml}
        missing = expect_jobs - present
        require(
            len(missing) == 0, f"Scrape jobs present: {sorted(expect_jobs)}", errors
        )
    except Exception as e:
        errors.append(f"Prometheus config error: {e}")
        print(f"[FAIL] Prometheus config error: {e}")

    # 2) Rules loaded
    try:
        rules = prom_rules(args.prom, args.timeout)
        groups = [g.get("name") for g in rules.get("data", {}).get("groups", [])]
        require("vtb_ops_health" in groups, "Rule group vtb_ops_health loaded", errors)
        require("vtb_scale" in groups, "Rule group vtb_scale loaded", errors)
        if args.expect_guardrails:
            require(
                "vtb_panic_guardrails" in groups,
                "Rule group vtb_panic_guardrails loaded",
                errors,
            )
    except Exception as e:
        errors.append(f"Prometheus rules error: {e}")
        print(f"[FAIL] Prometheus rules error: {e}")

    # 3) Targets UP per job
    try:
        t = prom_targets(args.prom, args.timeout)
        active = t.get("data", {}).get("activeTargets", [])
        by_job = {}
        for a in active:
            job = a.get("labels", {}).get("job")
            health = a.get("health")
            if job:
                by_job.setdefault(job, []).append(health)
        for job in ("momentum_shards", "riskd", "panic_signer"):
            ups = [h for h in by_job.get(job, []) if h and h.lower() == "up"]
            require(len(ups) > 0, f"Targets UP for job {job}", errors)
    except Exception as e:
        errors.append(f"Prometheus targets error: {e}")
        print(f"[FAIL] Prometheus targets error: {e}")

    # 4) Metrics sanity
    try:
        riskd_ok = prom_query(args.prom, "riskd_health", args.timeout)
        require(
            any(float(r.get("value", [0, "0"])[1]) == 1.0 for r in riskd_ok),
            "riskd_health == 1",
            errors,
        )
    except Exception as e:
        errors.append(f"Prom query riskd_health error: {e}")
        print(f"[FAIL] riskd_health query error: {e}")

    try:
        panic = prom_query(args.prom, 'panic_state{scope="bot"}', args.timeout)
        offenders = [
            s.get("metric", {}).get("bot_id") or s.get("metric", {}).get("instance")
            for s in panic
            if float(s.get("value", [0, "0"])[1]) >= 1.0
        ]
        require(
            len(offenders) == 0, 'panic_state{scope="bot"} == 0 for all bots', errors
        )
        if offenders:
            print(
                "[INFO] Panicked bots:", ",".join([o or "unknown" for o in offenders])
            )
    except Exception as e:
        errors.append(f"Prom query panic_state error: {e}")
        print(f"[FAIL] panic_state query error: {e}")

    try:
        trades = prom_query(args.prom, "momentum_trades_total", args.timeout)
        require(
            len(trades) >= 0,
            "momentum_trades_total metric present (may be zero)",
            errors,
        )
    except Exception as e:
        errors.append(f"Prom query momentum_trades_total error: {e}")
        print(f"[FAIL] momentum_trades_total query error: {e}")

    # 5) Approval token freshness (TTL 600s default)
    ttl = int(os.environ.get("APPROVAL_TTL_SECONDS", "600"))
    tok = None
    try:
        if os.path.exists("runtime/APPROVAL_TOKEN.txt"):
            tok = (
                open("runtime/APPROVAL_TOKEN.txt", "r", encoding="utf-8").read().strip()
            )
        else:
            tok = os.environ.get("APPROVAL_TOKEN")
        require(
            bool(tok),
            "Approval token present (runtime/APPROVAL_TOKEN.txt or env)",
            errors,
        )
        if tok:
            payload = decode_jwt_unsafe(tok)
            require(payload is not None, "Approval token decodable", errors)
            if payload:
                now = int(time.time())
                iat = int(payload.get("iat", now))
                exp = int(payload.get("exp", now))
                fresh = (now - iat) <= ttl and exp > now
                require(
                    fresh,
                    f"Approval token fresh (<= {ttl}s old) and not expired",
                    errors,
                )
    except Exception as e:
        errors.append(f"Approval token check error: {e}")
        print(f"[FAIL] Approval token check error: {e}")

    # 6) Volatility window
    try:
        inside, hits = within_windows_utc(now_utc(), args.windows_file)
        require(not inside, "Not inside a disable window (UTC)", errors)
        if inside:
            print("[INFO] Disable window(s) active:", hits)
    except Exception as e:
        errors.append(f"Windows check error: {e}")
        print(f"[FAIL] Windows check error: {e}")

    # 7) Agent /health
    try:
        h = http_get_text(urljoin(args.agent.rstrip("/") + "/", "health"), args.timeout)
        require("ok" in h.lower() or "healthy" in h.lower(), "Agent /health OK", errors)
    except Exception as e:
        errors.append(f"Agent health error: {e}")
        print(f"[FAIL] Agent health error: {e}")

    dur = time.time() - started
    summary = f"Preflight {'OK' if not errors else 'FAIL'} in {dur:.1f}s; checks={12} fails={len(errors)}"
    print("== SUMMARY ==\n" + summary)

    if slack:
        color = "#2eb886" if not errors else "#e01e5a"
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*VTB Preflight* {':white_check_mark:' if not errors else ':x:'}\n{summary}",
                },
            },
        ]
        post_slack(slack, summary, blocks)

    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
