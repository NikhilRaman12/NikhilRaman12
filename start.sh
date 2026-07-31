#!/usr/bin/env bash
set -euo pipefail
uvicorn medicobuddy.api:app --host 0.0.0.0 --port 8000 &
API_PID=$!
trap 'kill $API_PID' EXIT INT TERM
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 7860 --server.headless true
