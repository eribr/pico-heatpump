@echo off
REM Cloudflare Proxy Setup - Windows Batch Wrapper
REM Makes it easy to run Python setup on Windows

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Cloudflare Free Proxy Setup
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Download from: https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check if requests module is installed
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Installing required Python package: requests
    pip install requests
    if errorlevel 1 (
        echo ERROR: Failed to install requests package
        pause
        exit /b 1
    )
)

REM Check if config.json exists
if not exist "config.json" (
    echo ERROR: config.json not found in current directory
    echo.
    echo Please create config.json with your Cloudflare credentials:
    echo   1. Copy config.json.example to config.json
    echo   2. Edit config.json with your API token and Zone ID
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)

REM Run the Python setup script
echo Running setup...
echo.
python setup-cloudflare.py
if errorlevel 1 (
    echo.
    echo ERROR: Setup failed
    pause
    exit /b 1
)

echo.
echo Setup complete!
pause
