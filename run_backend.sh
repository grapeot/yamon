#!/bin/bash
# Start FastAPI backend server
# Usage: ./run_backend.sh [port]
#
# Note: This script uses the yamon package. Make sure to install it first:
#   pip install -e .

PORT=${1:-8000}

cd "$(dirname "$0")"
python -m uvicorn yamon.main:app --reload --port $PORT

