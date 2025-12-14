#!/bin/bash
# Build frontend for production
# Usage: ./build_frontend.sh

set -e

cd "$(dirname "$0")"

echo "Building frontend..."
cd frontend
npm install
npm run build

echo "Copying static files to yamon/static..."
cd ..
rm -rf yamon/static
mkdir -p yamon/static
cp -r frontend/dist/* yamon/static/

echo "Build complete! Static files are in yamon/static/"
echo "You can now start the server with: ./run_backend.sh or yamon"

