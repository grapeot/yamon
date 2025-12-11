#!/bin/bash
# Build frontend for production
# Usage: ./build_frontend.sh

set -e

cd "$(dirname "$0")"

echo "Building frontend..."
cd frontend
npm install
npm run build

echo "Copying static files to backend..."
cd ..
rm -rf backend/static
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

echo "Build complete! Static files are in backend/static/"
echo "You can now start the backend server with: ./run_backend.sh"

