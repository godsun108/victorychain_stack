"""
victory_bot/audit.py
Audit logging for Victory Trading Bot
"""

import json
import os
import threading
import hashlib
from datetime import datetime, timezone
from .config import AUDIT_DIR
from pathlib import Path
from typing import Dict, Any, Optional

LEDGER_PATH = AUDIT_DIR.parent / "ledger" / "live_ledger.jsonl"
AUDIT_LOG_PATH = AUDIT_DIR / "audit_log.jsonl"
audit_lock = threading.Lock()
_hash_cache_last: Optional[str] = None


def now_utc():
    return datetime.now(timezone.utc)


def _read_last_hash() -> Optional[str]:
    global _hash_cache_last
    try:
        with open(LEDGER_PATH, "rb") as f:
            last = None
            for line in f:
                last = line
            if not last:
                return None
            rec = json.loads(last.decode("utf-8", "ignore"))
            _hash_cache_last = rec.get("hash")
            return _hash_cache_last
    except Exception:
        return None


def _write_ledger(event: str, data: Dict[str, Any]):
    prev = _read_last_hash()
    record = {
        "ts": now_utc().isoformat().replace("+00:00", "Z"),
        "event": event,
        **data,
        "prev_hash": prev,
    }
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    h = hashlib.sha256(payload + (prev or "").encode()).hexdigest()
    record["hash"] = h
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def audit(event: str, data: Dict[str, Any]):
    try:
        with audit_lock:
            os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
            rec = {
                "ts": now_utc().isoformat().replace("+00:00", "Z"),
                "event": event,
                **data,
            }
            with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


class AuditLogger:
    def __init__(self, name: str):
        self.file = AUDIT_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.jsonl"
        Path(AUDIT_DIR).mkdir(parents=True, exist_ok=True)

    def log(self, event: dict):
        event["timestamp"] = datetime.utcnow().isoformat()
        with open(self.file, "a") as f:
            f.write(json.dumps(event) + "\n")
