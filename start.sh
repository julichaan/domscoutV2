#!/bin/bash

echo "======================================"
echo "DomScout v2 - Starting Server"
echo "======================================"
echo ""

# Check if build exists
if [ ! -d "server/static" ]; then
    echo "[!] Frontend not built. Running setup.sh first..."
    ./setup.sh
fi

echo "[*] Activating Python virtual environment..."
source venv/bin/activate

echo "[*] Starting Flask server..."
echo "[*] Access the application at: http://localhost:5000"
echo ""
echo "[!] Press Ctrl+C to stop the server"
echo ""

cd server
python app.py
