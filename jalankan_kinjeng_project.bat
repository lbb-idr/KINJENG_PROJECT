@echo off

:: Spawn minimized instance, then exit this one
if "%MINIMIZED%"=="" (
    set MINIMIZED=1
    start /MIN cmd /c "%~f0" %*
    exit /b
)

cd /d "%~dp0"
title KINJENG_PROJECT Launcher
color 0B

echo ========================================
echo   KINJENG_PROJECT Launcher
echo ========================================
echo.

netstat -ano | findstr ":5001 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 ( set BACKEND_RUNNING=1 ) else ( set BACKEND_RUNNING=0 )

netstat -ano | findstr ":3000 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 ( set FRONTEND_RUNNING=1 ) else ( set FRONTEND_RUNNING=0 )

if %BACKEND_RUNNING% equ 1 (
    echo [1/2] Backend already running on port 5001
) else (
    echo [1/2] Starting backend...
    start "KINJENG_PROJECT-Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python run.py"
    timeout /t 4 /nobreak >nul
)

if %FRONTEND_RUNNING% equ 1 (
    echo [2/2] Frontend already running on port 3000
) else (
    echo [2/2] Starting frontend...
    start "KINJENG_PROJECT-Frontend" cmd /k "cd /d "%~dp0frontend" && npm.cmd run dev"
    timeout /t 5 /nobreak >nul
)

echo.
if %BACKEND_RUNNING% equ 1 if %FRONTEND_RUNNING% equ 1 (
    echo KINJENG_PROJECT already running -- opening browser...
) else (
    echo KINJENG_PROJECT is running!
)
start http://localhost:3000

echo.
echo Terminal ini bisa ditutup kapan saja.
echo Backend dan Frontend akan tetap berjalan.
echo.
pause
