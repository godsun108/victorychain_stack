#!/usr/bin/env python3
import argparse
import os
import sys
import time
from statistics import median
from urllib.parse import urljoin

import requests


def ping(url: str, timeout: float) -> float:
    t0 = time.perf_counter()
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    _ = r.text
    return time.perf_counter() - t0


def p95(values):
    if not values:
        return 0.0
    vs = sorted(values)
    n = len(vs)
    k = max(0, min(n - 1, int((0.95 * n + 0.5) - 1)))  # nearest-rank style
    return vs[k]


def maybe_emit(url: str | None, jwt: str | None, timeout: float):
    if not url:
        return
    try:
        headers = {}
        if jwt:
            headers["Authorization"] = f"Bearer {jwt}"
        # Try POST first; fallback to GET
        try:
            r = requests.post(url, headers=headers, timeout=timeout)
            r.raise_for_status()
        except Exception:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
        print(f"[SMOKE] emit ok -> {url}")
    except Exception as e:
        print(f"[SMOKE] emit failed (ignored): {e}")


def check_prom(prom: str, timeout: float) -> bool:
    try:
        u = prom.rstrip("/") + "/api/v1/rules"
        r = requests.get(u, timeout=timeout)
        r.raise_for_status()
        print("[OK] Prometheus reachable")
        return True
    except Exception as e:
        print(f"[FAIL] Prometheus not reachable: {e}")
        return False


def main():
    ap = argparse.ArgumentParser(description="VTB Postdeploy Smoke")
    ap.add_argument("--prom", required=True, help="Prometheus base URL")
    ap.add_argument(
        "--agent",
        default=os.environ.get("AGENT_URL", "http://localhost:8080"),
        help="Agent base URL",
    )
    ap.add_argument(
        "--p95-s",
        type=float,
        default=float(os.environ.get("P95_LATENCY_S", 1.2)),
        help="Max allowed p95 latency (seconds)",
    )
    ap.add_argument(
        "--samples",
        type=int,
        default=int(os.environ.get("SMOKE_SAMPLES", 20)),
        help="Number of HTTP samples",
    )
    ap.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("SMOKE_TIMEOUT", 5)),
        help="HTTP timeout seconds",
    )
    args = ap.parse_args()

    emit_url = os.environ.get("SMOKE_EMIT_URL")
    emit_jwt = os.environ.get("SMOKE_JWT")

    ok = True

    # 0) Optional emit to create fresh traffic/metrics
    maybe_emit(emit_url, emit_jwt, args.timeout)

    # 1) Agent health ping loop
    health_url = urljoin(args.agent.rstrip("/") + "/", "health")
    samples = []
    for i in range(args.samples):
        try:
            dt = ping(health_url, args.timeout)
            samples.append(dt)
            time.sleep(0.05)
        except Exception as e:
            print(f"[FAIL] agent /health ping {i+1}/{args.samples}: {e}")
            ok = False
            break

    if samples:
        p95_v = p95(samples)
        med_v = median(samples)
        print(
            f"[SMOKE] agent /health latencies: n={len(samples)} p95={p95_v:.3f}s median={med_v:.3f}s"
        )
        if p95_v <= args.p95_s:
            print(f"[OK] p95 <= {args.p95_s:.3f}s")
        else:
            print(f"[FAIL] p95 {p95_v:.3f}s > {args.p95_s:.3f}s")
            ok = False

    # 2) Prom reachable
    if not check_prom(args.prom, args.timeout):
        ok = False

    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
