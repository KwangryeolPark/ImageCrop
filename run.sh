#!/bin/bash

echo "Starting ImageCrop Server..."

# Environment validation
echo "Checking environment..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "Error: Python is not installed or not in PATH"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Found Python: $PYTHON_CMD"

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed or not in PATH"
    exit 1
fi

echo "Found pip"

# Check Python version
python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
required_version="3.8"

# Simple version comparison
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher required, found $python_version"
    exit 1
fi

echo "Python version check passed: $python_version"

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found in current directory"
    exit 1
fi

echo "Found main.py"

# Install dependencies
echo "Installing/checking dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi
echo "Dependencies check completed."
echo

# Start the server (now main.py handles port detection and browser opening)
echo "Starting FastAPI server..."
$PYTHON_CMD main.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to start server"
    exit 1
fi