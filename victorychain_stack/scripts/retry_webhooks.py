#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime

from src.victory_impact.config import settings
from src.victory_impact.db import Base, SessionLocal, engine
from src.victory_impact.services.donations import ensure_default_categories
from src.victory_impact.services.payment_adapters import EVMIndexerAdapter, VUSDAdapter
from src.victory_impact.services.webhook_retry import run_retry_batch, webhook_queue_metrics


def initialize_storage() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_default_categories(db)
    finally:
        db.close()


def run_once(include_dead_letter: bool, limit: int) -> dict:
    indexer = EVMIndexerAdapter(settings.evm_rpc_url, settings.evm_required_confirmations)
    vusd = VUSDAdapter(indexer, settings.vusd_contract_address)
    db = SessionLocal()
    try:
        result = run_retry_batch(
            db=db,
            vusd_adapter=vusd,
            include_dead_letter=include_dead_letter,
            limit=limit,
        )
        metrics = webhook_queue_metrics(db)
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "result": result,
            "metrics": metrics,
        }
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Retry webhook events from DB queue.")
    parser.add_argument("--loop", action="store_true", help="Run continuously.")
    parser.add_argument("--sleep-seconds", type=int, default=15, help="Loop sleep interval in seconds.")
    parser.add_argument("--include-dead-letter", action="store_true", help="Include dead-letter events in retry runs.")
    parser.add_argument("--limit", type=int, default=100, help="Max events to process each run.")
    args = parser.parse_args()
    initialize_storage()

    if args.loop:
        while True:
            payload = run_once(include_dead_letter=args.include_dead_letter, limit=args.limit)
            print(json.dumps(payload, default=str), flush=True)
            time.sleep(max(1, args.sleep_seconds))
    else:
        payload = run_once(include_dead_letter=args.include_dead_letter, limit=args.limit)
        print(json.dumps(payload, default=str), flush=True)


if __name__ == "__main__":
    main()
