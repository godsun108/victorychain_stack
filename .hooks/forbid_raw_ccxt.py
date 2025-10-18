#!/usr/bin/env python3
import sys
import re
import os

FORBIDDEN = re.compile(r"^import\s+ccxt\s*$|^from\s+ccxt\s+import\s+", re.M)

allowlist = set(
    [
        "libs/exchange_adapters/binance_us.py",
    ]
)

scan_roots = (
    "libs" + os.sep,
    "governance" + os.sep,
    "tests" + os.sep,
    "helper_scripts" + os.sep,
)

exit_code = 0
for path in sys.argv[1:]:
    # Normalize to repo-relative POSIX-ish path
    p = path.replace("\\", "/")
    if any(p.startswith(root) for root in scan_roots):
        if any(p.endswith(a) for a in allowlist):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if FORBIDDEN.search(content):
                print(f"FORBIDDEN_CCXT_IMPORT {p}")
                exit_code = 1
        except Exception as e:
            print(f"SCAN_ERROR {p} {e}")
            exit_code = 1
    else:
        # Skip files outside core governance/guards paths
        continue

sys.exit(exit_code)
