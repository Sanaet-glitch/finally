#!/bin/bash

echo "Starting QR Attendance System with resilient server..."
echo ""
echo "This terminal will monitor your server's health. Do not close it!"
echo "Press Ctrl+C to stop the server."
echo ""

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "Virtual environment activated."
else
    echo "No virtual environment found at .venv, using system Python."
fi

# Install requirements if needed
pip install -r requirements.txt

# Run the resilient server script
python run_server.py

# Deactivate virtual environment if it was activated
if [ -f ".venv/bin/activate" ]; then
    deactivate
fi 