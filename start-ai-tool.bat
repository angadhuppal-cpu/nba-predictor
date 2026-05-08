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
if not exist ".env" (
    echo [ERROR] backend\.env not found.
    echo         Copy .env.example to .env and add your GEMINI_API_KEY.
    pause
    exit /b 1
)

REM ---- 2. Verify GEMINI_API_KEY has a real value ----------------------
findstr /B /R /C:"GEMINI_API_KEY=AIza" .env >nul 2>nul
if errorlevel 1 (
    echo [WARNING] backend\.env does not contain a Gemini-shaped
    echo           GEMINI_API_KEY (starting with 'AIza').
    echo.
    echo  Open backend\.env in Notepad, replace the placeholder
    echo  with your real key from https://aistudio.google.com/apikey,
    echo  save, and re-run this script.
    echo.
    echo  If you intended to use Claude instead, set
    echo  LLM_PROVIDER=claude and ANTHROPIC_API_KEY=...
    echo.
    set /p continue="Continue anyway? [y/N] "
    if /I not "%continue%"=="y" exit /b 1
)

REM ---- 3. Verify the React build is present ---------------------------
if not exist "..\frontend\build\index.html" (
    echo [ERROR] React build is missing.
    echo         Run setup-ai-tool.bat first to build the frontend.
    pause
    exit /b 1
)

REM ---- 4. Open the browser shortly after Flask starts -----------------
start "" cmd /c "timeout /t 3 >nul && start http://localhost:5000"

REM ---- 5. Start Flask (this blocks until you Ctrl+C) ------------------
echo Starting Flask on http://localhost:5000
echo Press Ctrl+C in this window to stop the server.
echo.
python app.py

REM Keep the window open if Flask exits abnormally so you can read errors
echo.
echo Flask exited.
pause
