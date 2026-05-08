@echo off
REM =====================================================================
REM  NBA Line AI - FULL stats refresh (every active player, every game)
REM
REM  Heavier than update-stats.bat: re-fetches every active 2025-26
REM  player's full-season game log (not just top-100). Use this when you
REM  want everything current through today.
REM
REM  Expect 30-60+ minutes total because NBA Stats rate-limits us.
REM =====================================================================

setlocal enableextensions
cd /d "%~dp0\backend"

echo.
echo =============================================================
echo  NBA Line AI - FULL stats refresh
echo  Started: %date% %time%
echo =============================================================
echo.

REM ---- Verify Python is on PATH ---------------------------------------
where python >nul 2>nul
if errorlevel 1 goto :no_python

REM ---- 1. Team stats (current season) ---------------------------------
echo [1/6] Refreshing team stats (def/off ratings, pace, four factors)...
python fetch_team_stats.py
if errorlevel 1 echo   (team-stats step failed; continuing)

REM ---- 2. Player season stats (every active player) -------------------
echo.
echo [2/6] Refreshing 2025-26 player season stats...
python fetch_2025_26_season.py
if errorlevel 1 echo   (season-stats fetch failed; continuing)
python populate_season_stats.py
if errorlevel 1 echo   (derive season stats failed; continuing)

REM ---- 3. Game logs for EVERY active player ---------------------------
echo.
echo [3/6] Refreshing game logs for ALL active players (this takes a while)...
python update_all_players_games.py --season 2025-26 --min-games 1
if errorlevel 1 echo   (player-games step had errors; continuing)

REM ---- 4. Usage rates -------------------------------------------------
echo.
echo [4/6] Refreshing usage rates...
python populate_usage_rates.py
if errorlevel 1 echo   (usage-rates step failed; continuing)

REM ---- 5. StatMuse cache ----------------------------------------------
echo.
echo [5/6] Refreshing StatMuse cached data...
python populate_statmuse_data.py
if errorlevel 1 echo   (StatMuse step failed; continuing)

REM ---- 6. Status summary ----------------------------------------------
echo.
echo [6/6] Database status:
python manage_data.py status

echo.
echo =============================================================
echo  Full refresh complete: %date% %time%
echo =============================================================
echo.
echo  Note: the game_schedule table is NOT refreshed by this script.
echo  Tonight-games / slate views need a separate schedule fetcher
echo  (not yet implemented on this branch). Everything else - game
echo  logs, season stats, team stats, usage rates - is current.
echo.
pause
exit /b 0

:no_python
echo [ERROR] Python is not on PATH. Install Python 3.10+ from
echo         https://www.python.org/downloads/ and re-run this script.
pause
exit /b 1
