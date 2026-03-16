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
    echo [INFO] Brave is already running with remote debugging on port 9222.
    echo [INFO] You can start the bot now with START_BOT.bat
    echo.
    pause
    exit /b
)

REM Check if Brave is running WITHOUT remote debugging
tasklist /FI "IMAGENAME eq brave.exe" 2>NUL | find /I "brave.exe" >NUL
if %errorlevel%==0 (
    echo [WARNING] Brave is currently running WITHOUT remote debugging.
    echo [WARNING] Please close ALL Brave windows first, then run this again.
    echo.
    echo           This is needed so Brave can restart with the debugging port.
    echo           Your bookmarks, logins, and Telegram session will be preserved.
    echo.
    pause
    exit /b
)

echo [INFO] Launching Brave with your existing profile + remote debugging...
echo.

REM Use the default Brave profile so bookmarks, logins, and sessions are kept
start "" "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" ^
    --remote-debugging-port=9222 ^
    --user-data-dir="%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"

echo [INFO] Brave launched with your existing profile!
echo.
echo ================================================================
echo   NEXT STEPS:
echo   1. Your bookmarks and logins should all be there
echo   2. Open https://web.telegram.org (should already be logged in)
echo   3. Run START_BOT.bat to start the auto-reply bot
echo ================================================================
echo.
pause
