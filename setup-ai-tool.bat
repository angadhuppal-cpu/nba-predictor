@echo off
REM =====================================================================
REM  NBA Line AI - one-shot setup for Windows
REM
REM  Installs Python + Node deps and builds the React frontend.
REM  Run this ONCE after pulling the AI branch. After it finishes,
REM  use start-ai-tool.bat to launch the app.
REM =====================================================================

setlocal enableextensions
cd /d "%~dp0"

echo.
echo =============================================================
echo  NBA Line AI - Setup
echo =============================================================
echo.

REM ---- 1. Verify Python is on PATH ------------------------------------
where python >nul 2>nul
if errorlevel 1 goto :no_python

REM ---- 2. Verify Node is on PATH --------------------------------------
where node >nul 2>nul
if errorlevel 1 goto :no_node

REM ---- 3. Install backend Python dependencies -------------------------
echo [1/3] Installing Python dependencies...
echo.
cd backend
python -m pip install --upgrade pip
if errorlevel 1 goto :pip_failed
python -m pip install -r requirements.txt
if errorlevel 1 goto :pip_failed
cd ..

REM ---- 4. Install frontend Node dependencies --------------------------
echo.
echo [2/3] Installing frontend Node dependencies (this can take ~1 minute)...
echo.
cd frontend
call npm install --no-audit --no-fund
if errorlevel 1 goto :npm_install_failed

REM ---- 5. Build the React production bundle ---------------------------
echo.
echo [3/3] Building React production bundle...
echo.
call npm run build
if errorlevel 1 goto :npm_build_failed
cd ..

echo.
echo =============================================================
echo  Setup complete.
echo  Next: double-click start-ai-tool.bat (after editing
echo        backend\.env to add your GEMINI_API_KEY).
echo =============================================================
pause
exit /b 0

:no_python
echo [ERROR] Python is not on PATH. Install Python 3.10+ from
echo         https://www.python.org/downloads/ and re-run this script.
pause
exit /b 1

:no_node
echo [ERROR] Node.js is not on PATH. Install Node 18+ from
echo         https://nodejs.org/ and re-run this script.
pause
exit /b 1

:pip_failed
echo.
echo [ERROR] pip install failed. Common causes:
echo   - Behind a proxy: set HTTP_PROXY / HTTPS_PROXY env vars
echo   - Blocked by corp firewall on pypi.org
echo   - Out of disk space
pause
exit /b 1

:npm_install_failed
echo.
echo [ERROR] npm install failed. Common causes:
echo   - Network blocked from registry.npmjs.org
echo   - Old Node version (need 18+); check with: node --version
pause
exit /b 1

:npm_build_failed
echo.
echo [ERROR] npm run build failed. Scroll up for the actual error.
pause
exit /b 1
