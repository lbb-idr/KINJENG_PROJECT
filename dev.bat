@echo off
title KINJENG PROJECT - Dev Server
cd /d "%~dp0"

echo ============================================
echo   KINJENG PROJECT - Starting Dev Server
echo ============================================
echo.

echo [1/2] Starting Backend (Flask)...
start "KINJENG Backend" /min cmd /c "cd /d "%~dp0backend" && .venv\Scripts\python run.py"

echo [2/2] Starting Frontend (Vite)...
start "KINJENG Frontend" cmd /c "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both servers starting...
echo Backend:  http://localhost:5001
echo Frontend: http://localhost:5173
echo.
echo Close both windows to stop.
pause
