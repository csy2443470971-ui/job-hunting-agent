"""A company's mission in its own words, for "Why us?" answers (node 05 · Write).

Rule (from the person, 2026-10-18): a why-us answer opens with the company's mission, then why the person cares
about it as a person; experience comes last and stays light. The mission is read from every posting we hold for
that company (companies repeat it across postings even when the one being answered leaves it out).
"""
from __future__ import annotations
import html
import re

STRONG = re.compile(r"(?:'s|’s|\bour|\bthe company's)\s+mission\s+is\b|\bmission:\s|\bwe exist to\b|\bwe(?:'re| are) on a mission\b", re.I)
WEAK = re.compile(r"\bwe believe\b|\bour goal is\b|\bwe(?:'re| are) building\b", re.I)


def _sentences(text: str) -> list[str]:
    t = html.unescape(re.sub(r"<[^>]+>", " ", html.unescape(text or "")))
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", t) if 20 < len(s.strip()) < 400]


def mission(con, company: str, description: str = "") -> list[str]:
    """Up to three mission sentences: strong statements first, the current posting before other postings."""
    texts = [description] + [r[0] for r in con.execute("SELECT description FROM jobs WHERE company=? LIMIT 300", (company,)).fetchall()]
    strong, weak, seen = [], [], set()
    for t in texts:
        for s in _sentences(t):
            key = s.replace("’", "'").lower()
            if key in seen or re.search(r"mission[- ]critical|\bteam(?:'s|’s)?\b|\bsales\b|\bwe exist to make " + re.escape(company), s, re.I):
                continue   # team charters and sales copy are not the company's mission
            seen.add(key)
            (strong if STRONG.search(s) else weak if WEAK.search(s) else []).append(s)
    return (strong + weak)[:3]
