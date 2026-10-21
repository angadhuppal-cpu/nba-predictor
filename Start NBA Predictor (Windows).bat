@echo off
setlocal
cd /d "%~dp0"
title NBA Predictor

rem ---- find Python 3.10+ ----
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY goto nopython
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 || goto nopython

rem ---- first run: create a private Python environment and install packages ----
if not exist ".venv\Scripts\python.exe" (
  echo.
  echo  First-time setup: installing what the app needs. This takes 1-3 minutes...
  echo.
  %PY% -m venv .venv || goto fail
)
fc /b requirements.txt ".venv\installed-requirements.txt" >nul 2>&1
if errorlevel 1 (
  ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt || goto fail
  copy /y requirements.txt ".venv\installed-requirements.txt" >nul
)

rem ---- start the app (opens your browser) ----
".venv\Scripts\python.exe" -m nba_predictor web
goto end

:nopython
echo.
echo  Python 3.10 or newer was not found.
echo  1. Install it from https://www.python.org/downloads/
echo  2. On the first installer screen, tick "Add python.exe to PATH".
echo  3. Double-click this file again.
echo.
pause
exit /b 1

:fail
echo.
echo  Setup failed. Check your internet connection and try again.
echo  If it keeps failing, delete the ".venv" folder here and double-click again.
echo.
pause
exit /b 1

:end
pause
