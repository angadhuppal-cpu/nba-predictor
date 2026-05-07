#!/usr/bin/env python3
"""
NBA Line AI — interactive command-line front-end for the gambling advisor.

Usage:
    python nba_line_ai.py                       # interactive REPL
    python nba_line_ai.py "Will LeBron go..."   # one-shot question

Environment:
    ANTHROPIC_API_KEY must be set (export it or place in backend/.env).
"""

from __future__ import annotations

import os
import sys

try:
    from dotenv import load_dotenv  # optional
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

from ai_advisor import NBALineAdvisor


BANNER = """\
============================================================
🏀  NBA Line AI — gambling line advisor
    Type 'reset' to start a new conversation, 'quit' to exit.
    Try: "Will LeBron go OVER 24.5 points tonight vs BOS?"
============================================================
"""


def run_interactive():
    print(BANNER)
    advisor = NBALineAdvisor()
    history = []

    while True:
        try:
            question = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            break
        if question.lower() == "reset":
            history = []
            print("(conversation reset)")
            continue

        try:
            result = advisor.chat(question, history=history)
        except Exception as exc:
            print(f"error: {exc}")
            continue

        history = result["history"]
        if result["tool_calls"]:
            print(f"\n[ran {len(result['tool_calls'])} tool call(s): "
                  f"{', '.join(c['name'] for c in result['tool_calls'])}]")
        print(f"\nai> {result['reply']}")


def run_oneshot(question: str):
    advisor = NBALineAdvisor()
    result = advisor.chat(question)
    print(result["reply"])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_oneshot(" ".join(sys.argv[1:]))
    else:
        run_interactive()
