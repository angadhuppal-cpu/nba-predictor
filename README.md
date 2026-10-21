# NBA Predictor

An AI analyst for NBA player props. Ask it in plain English, e.g. *"Is Jalen Brunson over 26.5 points tonight
vs Boston going to hit?"*, and it will:

1. **Pull the numbers.** It loads the player's game logs (this season and last) and the opponent's defensive
   profile from stats.nba.com.
2. **Run the math.** It projects minutes and per-minute production, adjusts for the matchup, venue and rest, and
   models the outcome as a probability distribution. That gives the exact P(over), P(under) and P(push) for any line.
3. **Price it.** It turns those probabilities into fair odds, strips the vig from the book's price, and reports
   the edge, the expected value and a quarter-Kelly stake.
4. **Add basketball context.** Claude searches for injury reports, lineups, minutes limits and role changes,
   adjusts the projection when the news calls for it, and explains the call.
5. **Find better lines.** It builds an alternate-line ladder, shows which alt lines clear 70%+, ranks the
   book's alt-line offers by EV, and compares several props to find the best one.

> No model can tell you a line *will* hit. This tool tells you **how likely** it is and **whether the price is
> worth it**. Even a 70% play loses 3 times in 10. Bet only what you can afford to lose.

## Install (one time, no terminal needed)

1. **Install Python 3.10 or newer** from [python.org/downloads](https://www.python.org/downloads/).
   On Windows, tick **"Add python.exe to PATH"** on the first installer screen.
2. **Download this app.** On GitHub, pick this branch in the branch menu, click the green **Code** button, then
   **Download ZIP**. Unzip it somewhere easy to find, like your Desktop.
3. **Double-click the launcher** in the unzipped folder:
   - Windows: `Start NBA Predictor (Windows).bat`. If a blue "Windows protected your PC" box appears, click
     **More info**, then **Run anyway**.
   - Mac: `Start NBA Predictor (Mac).command`. The first time, macOS may block it: right-click it, choose
     **Open**, then **Open** again.

   The first launch spends 1–3 minutes installing what it needs. Your browser then opens the app.
4. **Add your Claude API key** (only needed for the AI chat). Create one at
   [console.anthropic.com](https://console.anthropic.com) under **API Keys** (you need a little credit on the
   account). Then click **Settings** in the app and paste it in. It's saved only on your computer.

**After that, just double-click the launcher.** Keep its black window open while you use the app, and close it
when you're done.

Run it on your own computer. stats.nba.com often blocks cloud servers. Stats are cached in
`~/.cache/nba_predictor` for 6 hours.

The browser app has three tabs:
- **Ask the AI**: plain-English questions. Claude checks injury news, runs the model and gives a call.
- **Check a line**: type a player, stat, line and odds to get the hit probability, edge, EV and stake size. No API key needed.
- **Alt lines**: every alternate line with its hit probability and fair odds, plus the safest over/under. No API key needed.

## Command line (optional)

If you prefer the terminal, set things up yourself:

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...                     # Windows: set ANTHROPIC_API_KEY=sk-ant-...
python -m nba_predictor web                             # the browser app
```

### AI analyst (Claude)

```bash
python -m nba_predictor chat
```

```
you> Is Jokic over 11.5 rebounds tonight vs the Lakers? Book has -130 / +105
you> Give me better alt lines for that
you> Rank these: Tatum o27.5 pts -115, Brown o6.5 reb +100, White o2.5 threes -140, all vs MIA
you> What does a 3-leg parlay of those pay vs what it should pay?
```

One-shot: `python -m nba_predictor ask "Will SGA go over 31.5 points vs DEN?"`

Add `--no-web` to turn off web search (injury news). Settings: `NBA_PREDICTOR_MODEL` (default `claude-opus-5-5`)
and `NBA_PREDICTOR_EFFORT` (`low` / `medium` / `high` (default) / `xhigh` / `max`).

### Pure math (no API key needed)

```bash
# Evaluate one line with the book's odds, opponent and venue
python -m nba_predictor analyze "Jalen Brunson" PTS 26.5 --over -115 --under -105 --opp BOS --home

# Alternate-line ladder: P(over/under) and fair odds for every line
python -m nba_predictor alt "Nikola Jokic" REB --opp LAL --min-prob 0.75

# Teammate out, so you expect 38 minutes instead of 34
python -m nba_predictor analyze "Jaylen Brown" PRA 37.5 --minutes 38

python -m nba_predictor recent "Anthony Edwards" -n 10
python -m nba_predictor backtest "Anthony Edwards" FG3M     # how well-calibrated is the model for this player?
python -m nba_predictor odds -110 +120                       # implied / no-vig probabilities, vig
```

Supported stats: `PTS REB AST FG3M STL BLK TOV FTM FGM OREB DREB PRA PR PA RA STOCKS`. Aliases such as
`points`, `threes`, `3PM` and `pts+reb+ast` work too.

## How the model works (`nba_predictor/model.py`)

| Step | What it does |
|---|---|
| Per-minute production | Recency-weighted (15-game half-life) per-minute rates from this season, with last season's games at 60% weight |
| Minutes | Recency-weighted recent minutes (5-game half-life), or your override. Back-to-backs trim 4% |
| Matchup | Opponent's stat allowed per game vs league average, shrunk 50% toward neutral (combos weighted by component) |
| Venue | ±1.2% home/away |
| Distribution | Negative binomial (discrete and over-dispersed, so it handles half-point lines and pushes exactly). Variance comes from the player's own game-to-game spread, shrunk toward stat-typical priors, plus terms for minutes volatility and uncertainty in the mean |
| Betting math | No-vig market probability, edge, EV per unit, Kelly fraction (`odds.py`) |
| Verdict | With odds: STRONG at ≥6% edge, LEAN at ≥3%. Without odds: STRONG at ≥62% probability, LEAN at ≥56% |

Claude layers on what box scores can't see: injuries, lineup changes, minutes restrictions, blowout risk,
motivation. When news changes a player's role, it re-runs the model with adjusted minutes and says what it changed.

## Project layout

```
nba_predictor/
  data.py      # nba_api fetches + disk cache (players, game logs, team pace/defence)
  model.py     # projection, distribution, hit rates, alt-line ladder, backtest
  odds.py      # odds conversion, de-vig, EV, Kelly, parlays
  tools.py     # data + model joined into JSON-returning functions
  agent.py     # Claude analyst: system prompt, tool definitions, agent loop, web search
  web.py       # local browser app server (127.0.0.1 only)
  static/      # the browser page
  __main__.py  # CLI
tests/         # offline tests on synthetic game logs (pytest)
```

Run the tests with `python -m pytest`.

## Limitations

- Lines and odds aren't pulled automatically. Give them to the AI, or let it search for them.
- Parlay pricing assumes legs are independent. Same-game legs are usually correlated.
- Early in a season the sample is small, so the model leans on last season's data. Watch the "small sample" notes.
