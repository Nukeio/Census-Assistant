#!/usr/bin/env bash
# Census Assistant Linux/macOS Startup Script

echo "==================================================="
echo "Starting Census Assistant Application Server"
echo "Lakhipur Circle - By Shahin Sha A. - S. A. Ahmed"
echo "==================================================="

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
python -m backend.main
