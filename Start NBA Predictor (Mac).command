#!/bin/bash
# Double-click to start the NBA Predictor in your browser.
cd "$(dirname "$0")" || exit 1

fail() { echo; echo "  $1"; echo; read -n 1 -s -r -p "  Press any key to close..."; exit 1; }

# ---- find Python 3.10+ (python.org installs to /Library/Frameworks) ----
PY=""
for c in python3 /Library/Frameworks/Python.framework/Versions/Current/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    PY="$c"; break
  fi
done
[ -z "$PY" ] && fail "Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/ then double-click this file again."

# ---- first run: create a private Python environment and install packages ----
if [ ! -x .venv/bin/python ]; then
  echo; echo "  First-time setup: installing what the app needs. This takes 1-3 minutes..."; echo
  "$PY" -m venv .venv || fail "Setup failed. Check your internet connection and try again."
fi
if ! cmp -s requirements.txt .venv/installed-requirements.txt; then
  .venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt \
    || fail "Setup failed. Check your internet connection, delete the .venv folder here, and try again."
  cp requirements.txt .venv/installed-requirements.txt
fi

# ---- start the app (opens your browser) ----
.venv/bin/python -m nba_predictor web
