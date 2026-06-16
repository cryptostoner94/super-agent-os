#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
mkdir -p data/artifacts
if [ ! -f .env ]; then cp .env.example .env; fi
echo "Install complete. Edit .env, then run: bash scripts/run.sh"
