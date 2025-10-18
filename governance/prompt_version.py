import hashlib
import os
import subprocess
from datetime import datetime
from typing import Optional, Tuple

PROMPT_PATH_DEFAULT = os.path.join(
    "prompts", "master_prompt_trillion_bot_coding_council.md"
)
LEDGER_PATH = "trade_ledger.jsonl"


def compute_prompt_hash(path: Optional[str] = None) -> str:
    path = path or PROMPT_PATH_DEFAULT
    try:
        with open(path, "rb") as f:
            data = f.read()
        return hashlib.sha256(data).hexdigest()
    except Exception:
        return "unknown"


def get_git_commit() -> str:
    try:
        commit = (
            subprocess.check_output(
                ["git", "--no-pager", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        return commit
    except Exception:
        return "unknown"


def append_ledger_event(
    event_type: str,
    component: str,
    prompt_hash: str,
    commit: str,
    extra: Optional[dict] = None,
) -> None:
    record = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        "component": component,
        "prompt_hash": prompt_hash,
        "git_commit": commit,
        "victory_anchor_ref": os.getenv("VICTORY_ANCHOR_REF") or None,
    }
    if extra:
        record.update(extra)
    try:
        with open(LEDGER_PATH, "a") as f:
            import json

            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def activate_prompt(
    component: str, prompt_path: Optional[str] = None
) -> Tuple[str, str]:
    """Compute prompt hash and git commit, append PROMPT_ACTIVATED ledger event, and return (hash, commit)."""
    ph = compute_prompt_hash(prompt_path)
    gc = get_git_commit()
    try:
        append_ledger_event("PROMPT_ACTIVATED", component, ph, gc)
    except Exception:
        pass
    return ph, gc


def current_version(prompt_path: Optional[str] = None) -> Tuple[str, str]:
    """Return (prompt_hash, git_commit) without writing to ledger."""
    return compute_prompt_hash(prompt_path), get_git_commit()
