#!/bin/bash
set -e

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

