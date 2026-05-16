#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/reseed_demo_data.py

echo "Bootstrapped local self-service environment."
echo "Run: source .venv/bin/activate && uvicorn src.victory_impact.main:app --reload"
