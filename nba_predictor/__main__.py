"""Command-line entry point.

    python -m nba_predictor chat                                   # talk to the AI analyst
    python -m nba_predictor ask "Will Tatum go over 27.5 points vs NYK?"
    python -m nba_predictor analyze "Jayson Tatum" PTS 27.5 --over -115 --under -105 --opp NYK --home
    python -m nba_predictor alt "Jayson Tatum" PTS --opp NYK
    python -m nba_predictor recent "Jayson Tatum"
    python -m nba_predictor backtest "Jayson Tatum" PTS
    python -m nba_predictor odds -110 -110
"""

from __future__ import annotations

import argparse
import json
import sys

from . import tools


def _pct(p: float) -> str:
    return f"{100 * p:.1f}%"


def _odds(o: int) -> str:
    return f"{o:+d}"


def print_analysis(r: dict) -> None:
    ctx, proj, pr, v = r["context"], r["projection"], r["probabilities"], r["verdict"]
    print(f"\n{ctx['player']} ({ctx['team']}) {proj['stat']} {r['line']}" + (f" vs {ctx['opponent']}" if ctx["opponent"] else ""))
    print("-" * 60)
    print(f"Projection: {proj['projected_mean']} (median {proj['projected_median']:.0f}, sd {proj['std_dev']}) "
          f"in {proj['projected_minutes']} min")
    print(f"  80% range: {proj['range_10_90'][0]:.0f} to {proj['range_10_90'][1]:.0f}")
    for note in proj["notes"]:
        print(f"  - {note}")
    print(f"P(over) {_pct(pr['over'])}   P(under) {_pct(pr['under'])}" + (f"   P(push) {_pct(pr['push'])}" if pr["push"] else ""))
    print(f"Fair odds: over {_odds(r['fair_odds']['over'])} / under {_odds(r['fair_odds']['under'])}")
    for side in ("over", "under"):
        ev = r["bet_evaluation"][side]
        if ev:
            print(f"  {side.upper()} @ {_odds(int(ev['odds']))}: edge {ev['edge_vs_market']:+.1%}, "
                  f"EV {ev['ev_per_1_unit']:+.3f}/unit, quarter-Kelly {ev['kelly_quarter_pct']}% of bankroll")
    hr = r["hit_rates"]
    windows = [k for k in hr if k != "recent_values" and hr[k]]
    print("Hit rates (over): " + ", ".join(f"{k} {hr[k]['over']}/{hr[k]['games']}" for k in windows))
    print(f"Last 10: {hr['recent_values']}")
    print(f"\n>>> {v['pick']} ({_pct(v['hit_probability'])}) - {v['strength']}  [{v['basis']}]\n")


def print_alt(r: dict) -> None:
    ctx, proj = r["context"], r["projection"]
    print(f"\n{ctx['player']} {proj['stat']}: projection {proj['projected_mean']} in {proj['projected_minutes']} min")
    print(f"{'line':>6} {'P(over)':>8} {'fair':>6} {'P(under)':>9} {'fair':>6}")
    for row in r["ladder"]:
        print(f"{row['line']:>6} {_pct(row['p_over']):>8} {_odds(row['fair_over_odds']):>6} "
              f"{_pct(row['p_under']):>9} {_odds(row['fair_under_odds']):>6}")
    for k, val in r.items():
        if k.startswith(("highest_", "lowest_")) and val:
            print(f"{k.replace('_', ' ')}: {val['line']}")
    print()


def chat(use_web_search: bool) -> None:
    from .agent import Analyst

    analyst = Analyst(use_web_search=use_web_search)
    print("NBA prop analyst. Ask things like 'Will Jokic get over 11.5 rebounds tonight vs the Lakers?'")
    print("Type 'quit' to exit. Not financial advice; bet responsibly.\n")
    while True:
        try:
            q = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if q.lower() in {"quit", "exit", "q"}:
            return
        if q:
            print(f"\n{analyst.ask(q)}\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="nba_predictor", description="NBA player prop predictor")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("chat", help="Interactive AI analyst (needs ANTHROPIC_API_KEY)")
    c.add_argument("--no-web", action="store_true", help="Disable web search for injuries/news")
    a = sub.add_parser("ask", help="One-shot question to the AI analyst")
    a.add_argument("question")
    a.add_argument("--no-web", action="store_true")

    def game_args(p):
        p.add_argument("--opp", help="Opponent (abbr or name)")
        venue = p.add_mutually_exclusive_group()
        venue.add_argument("--home", dest="home", action="store_true", default=None)
        venue.add_argument("--away", dest="home", action="store_false")
        p.add_argument("--minutes", type=float, help="Override projected minutes")
        p.add_argument("--b2b", action="store_true", help="Second night of a back-to-back")
        p.add_argument("--json", action="store_true", help="Raw JSON output")

    an = sub.add_parser("analyze", help="Evaluate one prop line (no AI needed)")
    an.add_argument("player")
    an.add_argument("stat")
    an.add_argument("line", type=float)
    an.add_argument("--over", type=float, help="American odds for the over")
    an.add_argument("--under", type=float, help="American odds for the under")
    game_args(an)

    al = sub.add_parser("alt", help="Alternate-line probability ladder")
    al.add_argument("player")
    al.add_argument("stat")
    al.add_argument("--min-prob", type=float, default=0.70)
    game_args(al)

    rc = sub.add_parser("recent", help="Recent game log")
    rc.add_argument("player")
    rc.add_argument("-n", type=int, default=10)

    bt = sub.add_parser("backtest", help="Walk-forward model check on a player")
    bt.add_argument("player")
    bt.add_argument("stat")
    bt.add_argument("-n", type=int, default=30)

    od = sub.add_parser("odds", help="Odds math: implied/no-vig probabilities")
    od.add_argument("odds", type=float, nargs="+")

    args = ap.parse_args(argv)

    if args.cmd == "chat":
        chat(not args.no_web)
    elif args.cmd == "ask":
        from .agent import Analyst

        print(Analyst(use_web_search=not args.no_web).ask(args.question))
    elif args.cmd == "analyze":
        r = tools.analyze_prop(args.player, args.stat, args.line, args.over, args.under, args.opp, args.home, args.minutes, args.b2b)
        print(json.dumps(r, indent=2, default=str)) if args.json else print_analysis(r)
    elif args.cmd == "alt":
        r = tools.alt_lines(args.player, args.stat, None, args.min_prob, args.opp, args.home, args.minutes, args.b2b)
        print(json.dumps(r, indent=2, default=str)) if args.json else print_alt(r)
    elif args.cmd == "recent":
        print(json.dumps(tools.player_recent_games(args.player, args.n), indent=2, default=str))
    elif args.cmd == "backtest":
        print(json.dumps(tools.backtest(args.player, args.stat, args.n), indent=2))
    elif args.cmd == "odds":
        print(json.dumps(tools.odds_math(odds=args.odds), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
