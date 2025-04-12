@echo off
echo Starting QR Attendance System with resilient server...
echo.
echo This window will monitor your server's health. Do not close it!
echo Press Ctrl+C to stop the server.
echo.

REM Activate virtual environment if it exists
IF EXIST .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) ELSE (
    echo No virtual environment found at .venv, using system Python.
)

REM Install requirements if needed
pip install -r requirements.txt

REM Run the resilient server script
python run_server.py

REM Deactivate virtual environment if it was activated
IF EXIST .venv\Scripts\deactivate.bat (
    call .venv\Scripts\deactivate.bat
)

pause 