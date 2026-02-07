#!/bin/bash

echo "======================================"
echo "DomScout v2 - Development Mode"
echo "======================================"
echo ""
echo "[*] Activating Python virtual environment..."
source venv/bin/activate

echo "[*] Starting backend server..."

# Start backend in background
cd server
python app.py &
BACKEND_PID=$!

echo "[*] Backend running on http://localhost:5000 (PID: $BACKEND_PID)"
echo ""
echo "[*] Starting frontend development server..."
cd ../client
npm run serve

# When frontend stops, kill backend
echo ""
echo "[*] Stopping backend server..."
kill $BACKEND_PID
