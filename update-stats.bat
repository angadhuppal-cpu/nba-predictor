@echo off
REM =====================================================================
REM  NBA Line AI - update all stats
REM
REM  Refreshes the local SQLite database with the latest NBA data:
REM   1. Team stats (offensive/defensive ratings, pace, etc.)
REM   2. Active player rosters and season stats
REM   3. Recent player game logs
REM   4. Usage rates
REM   5. StatMuse cached data
REM
REM  Run this any time you want fresh numbers feeding the AI advisor.
REM  Takes ~5-10 minutes the first time, less on subsequent runs.
REM =====================================================================

setlocal enableextensions
cd /d "%~dp0\backend"

echo.
echo =============================================================
echo  NBA Line AI - Refreshing all stats
echo =============================================================
echo.

REM ---- Verify Python is on PATH ---------------------------------------
where python >nul 2>nul
if errorlevel 1 goto :no_python

REM ---- 1. Team stats --------------------------------------------------
echo [1/5] Refreshing team stats (defensive/offensive ratings, pace)...
python fetch_team_stats.py
if errorlevel 1 echo   (team stats step failed; continuing)

REM ---- 2. Active rosters + season stats -------------------------------
echo.
echo [2/5] Refreshing active 2025-26 rosters and season stats...
python fetch_all_active_players_2025_26.py
if errorlevel 1 echo   (roster step failed; continuing)
python populate_season_stats.py
if errorlevel 1 echo   (season-stats step failed; continuing)

REM ---- 3. Game logs ---------------------------------------------------
echo.
echo [3/5] Refreshing recent player game logs...
python fetch_top_players_games.py
if errorlevel 1 echo   (game-logs step failed; continuing)

REM ---- 4. Usage rates -------------------------------------------------
echo.
echo [4/5] Refreshing usage rates...
python populate_usage_rates.py
if errorlevel 1 echo   (usage-rates step failed; continuing)

REM ---- 5. StatMuse cached data ----------------------------------------
echo.
echo [5/5] Refreshing StatMuse cached data...
python populate_statmuse_data.py
if errorlevel 1 echo   (StatMuse step failed; continuing)

REM ---- Summary --------------------------------------------------------
echo.
echo =============================================================
echo  Done. Showing database status:
echo =============================================================
python manage_data.py status

echo.
echo Stats refresh complete.
pause
exit /b 0

:no_python
echo [ERROR] Python is not on PATH. Install Python 3.10+ from
echo         https://www.python.org/downloads/ and re-run this script.
pause
exit /b 1
