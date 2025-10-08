@echo off
title ImageCrop Server

echo Starting ImageCrop Server...
echo.

REM Environment validation
echo Checking environment...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo Found Python
python --version

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is not installed or not in PATH
    echo Please ensure pip is properly installed with Python
    pause
    exit /b 1
)

echo Found pip

REM Install dependencies
echo.
echo Installing/checking dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo Dependencies check completed.
echo.

REM Start the server (now main.py handles port detection and browser opening)
echo Starting FastAPI server...
echo Press Ctrl+C to stop the server
echo.
python main.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start server
    pause
    exit /b 1
)

REM If server stops normally, wait for user input before closing
echo.
echo Server stopped.
pause
