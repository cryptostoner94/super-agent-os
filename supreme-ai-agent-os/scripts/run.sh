#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
pkill -f "uvicorn backend.app.main:app" 2>/dev/null || true
pkill -f "streamlit run frontend/streamlit/app.py" 2>/dev/null || true
nohup ./venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
sleep 2
nohup ./venv/bin/streamlit run frontend/streamlit/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > frontend.log 2>&1 &
sleep 2
echo "Backend:  http://127.0.0.1:8000/health"
echo "Frontend: http://127.0.0.1:8501"
