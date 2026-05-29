@echo off
cd /d "%~dp0"
title KINJENG MABUR
color 0A

echo ============================================
echo   KINJENG MABUR
echo   One-Click Launcher
echo ============================================
echo.

echo [1/2] Starting Backend...
start "KINJENG Backend" /D "%~dp0backend" /MIN cmd /c ".venv\Scripts\python run.py" >nul 2>&1

echo [2/2] Starting Frontend...
start "KINJENG Frontend" /D "%~dp0frontend" /MIN cmd /c "npm run dev" >nul 2>&1

echo.
echo Backend:  http://localhost:5001
echo Frontend: http://localhost:3000
echo.
timeout /t 5 /nobreak >nul
start "" "http://localhost:3000"
echo Window ini aman ditutup.
echo.
pause
