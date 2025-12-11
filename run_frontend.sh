#!/bin/bash
# Start Vite frontend development server
# Usage: ./run_frontend.sh [port]

PORT=${1:-5173}

cd "$(dirname "$0")/frontend"
npm run dev -- --port $PORT

