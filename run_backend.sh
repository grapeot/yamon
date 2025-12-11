#!/bin/bash
# Start FastAPI backend server
# Usage: ./run_backend.sh [port]

PORT=${1:-8000}

cd "$(dirname "$0")"
python -m uvicorn backend.main:app --reload --port $PORT

