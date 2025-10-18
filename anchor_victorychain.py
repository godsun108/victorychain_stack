#!/usr/bin/env python3
import os, sys, json, time, hmac, hashlib
import urllib.request, urllib.error
from urllib.parse import urljoin

EXPORTS_DIR = os.getenv("EXPORTS_DIR", "runtime/exports")
GATEWAY_URL = os.getenv("VICTORYCHAIN_GATEWAY_URL", "").rstrip("/")
API_KEY = os.getenv("VICTORYCHAIN_API_KEY", "")
TIMEOUT_S = int(os.getenv("VICTORYCHAIN_TIMEOUT_S", "15"))
QUEUE_FILE = os.path.join(EXPORTS_DIR, "anchor_queue.jsonl")
SUMMARY = os.path.join(EXPORTS_DIR, "session_summary.json")

# Optional: verify/compute signature using APPROVAL_SECRET if not present
APPROVAL_SECRET = os.getenv("APPROVAL_SECRET", "")


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_summary(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def hmac_sig(secret: str, payload: dict) -> str:
    msg = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def attach_sig(payload: dict) -> dict:
    if APPROVAL_SECRET:
        clean = {k: v for k, v in payload.items() if k != "signature"}
        if not payload.get("signature"):
            payload["signature"] = hmac_sig(APPROVAL_SECRET, clean)
    return payload


def post_json(url: str, payload: dict, api_key: str) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        body = resp.read()
        code = resp.getcode()
        try:
            parsed = json.loads(body.decode("utf-8"))
        except Exception:
            parsed = {"raw": body.decode("utf-8", "ignore")}
        return {"status": code, "body": parsed}


def enqueue(payload: dict):
    ensure_dir(EXPORTS_DIR)
    with open(QUEUE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": int(time.time()), "payload": payload}) + "\n")


def flush_queue():
    if not os.path.exists(QUEUE_FILE):
        return
    lines = []
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines:
        return
    tmp = []
    for line in lines:
        try:
            item = json.loads(line)
            payload = item.get("payload")
            if not payload:
                continue
            res = post_json(
                urljoin(GATEWAY_URL + "/", "anchor/session"), payload, API_KEY
            )
            if 200 <= res["status"] < 300:
                continue  # delivered
            else:
                tmp.append(line)  # keep for next time
        except Exception:
            tmp.append(line)
    if tmp:
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(tmp) + ("\n" if tmp else ""))
    else:
        try:
            os.remove(QUEUE_FILE)
        except Exception:
            pass


def post_anchor(payload: dict) -> dict:
    """Library function: sign and post a session summary payload.
    Falls back to queue on failure. Returns a result dict.
    """
    if not GATEWAY_URL or not API_KEY:
        return {"ok": False, "error": "missing_gateway_env"}
    ensure_dir(EXPORTS_DIR)
    payload = attach_sig(payload)
    try:
        res = post_json(urljoin(GATEWAY_URL + "/", "anchor/session"), payload, API_KEY)
        if 200 <= res["status"] < 300:
            return {"ok": True, "response": res["body"]}
        enqueue(payload)
        return {
            "ok": False,
            "deferred": True,
            "status": res["status"],
            "body": res["body"],
        }
    except Exception as e:
        enqueue(payload)
        return {"ok": False, "error": str(e), "deferred": True}


def main():
    if not GATEWAY_URL or not API_KEY:
        print("ERROR: Set VICTORYCHAIN_GATEWAY_URL and VICTORYCHAIN_API_KEY in env.")
        sys.exit(2)
    ensure_dir(EXPORTS_DIR)
    # try to anchor the current summary if exists
    if os.path.exists(SUMMARY):
        payload = load_summary(SUMMARY)
        payload = attach_sig(payload)
        try:
            res = post_json(
                urljoin(GATEWAY_URL + "/", "anchor/session"), payload, API_KEY
            )
            if 200 <= res["status"] < 300:
                print("ANCHOR_OK", res["body"])
            else:
                print("ANCHOR_DEFER", res["status"], res["body"])
                enqueue(payload)
        except Exception as e:
            print("ANCHOR_ERROR", e)
            enqueue(payload)
    # always attempt to flush any queued payloads
    flush_queue()


if __name__ == "__main__":
    main()
