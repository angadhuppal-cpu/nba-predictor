@echo off
REM =====================================================================
REM  NBA Line AI - launch
REM
REM  Validates the env file, then starts Flask. Opens the browser at
REM  http://localhost:5000 once the server is up.
REM =====================================================================

setlocal enableextensions
cd /d "%~dp0\backend"

echo.
echo =============================================================
echo  NBA Line AI - Launch
echo =============================================================
echo.

REM ---- 1. Verify .env exists ------------------------------------------
if not exist ".env" goto :no_env

REM ---- 2. Verify GEMINI_API_KEY has a Gemini-shaped value -------------
findstr /B /C:"GEMINI_API_KEY=AIza" .env >nul 2>nul
if errorlevel 1 goto :bad_key

REM ---- 3. Verify the React build is present ---------------------------
if not exist "..\frontend\build\index.html" goto :no_build

REM ---- 4. Open the browser shortly after Flask starts -----------------
start "" cmd /c "timeout /t 3 >nul & start http://localhost:5000"

REM ---- 5. Start Flask (this blocks until you Ctrl+C) ------------------
echo Starting Flask on http://localhost:5000
echo Press Ctrl+C in this window to stop the server.
echo.
python app.py
echo.
echo Flask exited.
pause
exit /b 0

:no_env
echo [ERROR] backend\.env not found.
echo         Copy .env.example to .env and add your GEMINI_API_KEY.
pause
exit /b 1

:bad_key
echo [WARNING] backend\.env does not contain a Gemini-shaped
echo           GEMINI_API_KEY (starting with 'AIza').
echo.
echo  Open backend\.env in Notepad, replace the placeholder
echo  with your real key from https://aistudio.google.com/apikey,
echo  save, and re-run this script.
echo.
echo  If you intend to use Claude instead, set
echo  LLM_PROVIDER=claude and ANTHROPIC_API_KEY=...
pause
exit /b 1

:no_build
echo [ERROR] React build is missing.
echo         Run setup-ai-tool.bat first to build the frontend.
pause
exit /b 1
