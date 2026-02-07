#!/bin/bash

echo "=========================================="
echo "DomScout v2 - Setup Script"
echo "=========================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[!] Node.js is not installed. Please install Node.js first."
    echo "    Visit: https://nodejs.org/"
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "[*] Installing frontend dependencies..."
cd client
npm install

echo ""
echo "[*] Building frontend..."
npm run build

echo ""
echo "[*] Creating Python virtual environment..."
cd ..
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[+] Virtual environment created"
else
    echo "[+] Virtual environment already exists"
fi

echo ""
echo "[*] Installing backend dependencies..."
source venv/bin/activate
pip install -r server/requirements.txt

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "To start the application, run:"
echo "  ./start.sh"
echo ""
