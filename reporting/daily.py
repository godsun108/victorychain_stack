import os
from datetime import datetime
from governance.prompt_version import compute_prompt_hash, get_git_commit

REPORTS_DIR = "reports"


def generate_daily_bundle():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d")
    ph = compute_prompt_hash()
    gc = get_git_commit()
    basename = f"daily_{ts}_{ph[:8]}_{(gc or '')[:7]}"
    path = os.path.join(REPORTS_DIR, basename + ".txt")
    with open(path, "w") as f:
        f.write(f"date={ts}\n")
        f.write(f"prompt_hash={ph}\n")
        f.write(f"git_commit={gc}\n")
    return os.path.abspath(path)
