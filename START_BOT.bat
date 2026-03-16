@echo off
title EA Budak Ubat - TeleBot Auto-Reply
echo ================================================================
echo   EA BUDAK UBAT - TELEGRAM AUTO-REPLY BOT
echo   Installing dependencies and starting bot...
echo ================================================================
echo.

REM Check Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo [ERROR] Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Install dependencies
echo [INFO] Installing Python dependencies...
pip install -r requirements.txt --quiet
echo [INFO] Dependencies installed.
echo.

REM Install Playwright browsers (if not already installed)
echo [INFO] Checking Playwright browser installation...
python -m playwright install chromium --quiet 2>nul
echo [INFO] Playwright ready.
echo.

REM Check .env file
if not exist .env (
    echo [ERROR] .env file not found!
    echo [ERROR] Copy .env.example to .env and add your Anthropic API key.
    pause
    exit /b 1
)

REM Start bot
echo [INFO] Starting auto-reply bot...
echo.
python auto_reply.py

echo.
echo [INFO] Bot stopped.
pause
