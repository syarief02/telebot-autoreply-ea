@echo off
title EA Budak Ubat - Start Brave for TeleBot
echo ================================================================
echo   EA BUDAK UBAT - TELEGRAM AUTO-REPLY BOT
echo   Starting Brave Browser with Remote Debugging
echo ================================================================
echo.

REM Check if Brave is already running on port 9222
netstat -ano | findstr ":9222" >nul 2>&1
if %errorlevel%==0 (
    echo [INFO] Brave is already running on port 9222.
    echo [INFO] You can start the bot now with START_BOT.bat
    echo.
    pause
    exit /b
)

echo [INFO] Launching Brave with remote debugging on port 9222...
echo.

start "" "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" ^
    --remote-debugging-port=9222 ^
    --user-data-dir="%USERPROFILE%\BraveDebugProfile"

echo [INFO] Brave launched successfully!
echo.
echo ================================================================
echo   NEXT STEPS:
echo   1. Open https://web.telegram.org in the Brave window
echo   2. Log in to your Telegram account (if not already)
echo   3. Run START_BOT.bat to start the auto-reply bot
echo ================================================================
echo.
pause
