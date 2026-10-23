"""Jev (TypeSafe System One) as the cheap first-pass relevance scorer.

Jev answers typed questions with calibrated probabilities: ~70-500 ms per request, billed on input tokens only.
We ask one `noul` (true/false) question per posting, 40 postings per request, against a compact profile.
Claude then only looks at postings Jev rates as likely fits, for reasons, gaps and the lens.

Same request shape as CodeCut's codecut/transcribe.py::jev_noul (verified working there).
Env: TYPESAFE_API_KEY (required), TYPESAFE_API_URL, JEV_MODEL.
"""
from __future__ import annotations
import json
import os
import re
import httpx
from . import config

URL = os.getenv("TYPESAFE_API_URL", "https://api.typesafe.ai/v1/systemone")
MODEL = os.getenv("JEV_MODEL", "jev-latest")
BATCH = 40


def available() -> bool:
    return bool(os.getenv("TYPESAFE_API_KEY"))


def _lens_lines() -> str:
    """Titles, fit and guards of every lens in 06-roles.md, plus the experience headings: the profile Jev reads."""
    roles = (config.MASTER_DIR / "06-roles.md")
    exp = (config.MASTER_DIR / "02-experience.md")
    proj = (config.MASTER_DIR / "03-projects.md")
    keep = []
    if roles.exists():
        for line in roles.read_text(encoding="utf-8").splitlines():
            if line.startswith("## ") or re.match(r"- \*\*(Titles|Fit|Seniority guard|Drop)\*\*", line):
                keep.append(line)
    for f in (exp, proj):
        if f.exists():
            keep += [l for l in f.read_text(encoding="utf-8").splitlines() if l.startswith("## ")]
    return "\n".join(keep)


def profile_state() -> str:
    prefs = config.preferences()
    prof = config.profile()
    return (f"Candidate: {config._name()}. {prof.get('summary_for_ranker', '')}"
            "\n\nRole lenses and experience:\n" + _lens_lines() +
            "\n\nPreferences (yaml as json): " + json.dumps(prefs.get("targets", {}), ensure_ascii=False) +
            " Eligibility: " + json.dumps(prefs.get("eligibility", {}), ensure_ascii=False))


def _posting(i: int, job: dict) -> str:
    desc = re.sub(r"\s+", " ", job.get("description") or "")[:700]
    return f"«{i}: {job.get('company')} | {job.get('title')} | {job.get('location') or ''}{' | remote' if job.get('remote') else ''} | {desc}»"


QUESTION = ("Posting {i} is {company}, \"{title}\". Is this a role the candidate should apply to: a credible fit for one of "
            "the candidate's role lenses, at a seniority the candidate can get, in a sector they want?")
CRITERIA = {"true": "apply: the candidate is a credible applicant and the role matches one of their lenses",
            "false": "skip: wrong discipline, far too senior or junior, a sector they avoid, or a hard requirement they clearly lack"}


def score_batch(jobs: list[dict], client: httpx.Client | None = None) -> list[float | None]:
    """Returns P(apply) per job, same order. Raises on HTTP errors; returns [None]*n without a key."""
    key = os.getenv("TYPESAFE_API_KEY")
    if not key or not jobs:
        return [None] * len(jobs)
    c = client or httpx.Client(timeout=60)
    base = profile_state()
    out: list[float | None] = []
    for start in range(0, len(jobs), BATCH):
        chunk = jobs[start:start + BATCH]
        state = base + "\n\nPostings, marked «n: company | title | location | description»:\n" + "\n".join(
            _posting(start + k + 1, j) for k, j in enumerate(chunk))
        qs = {f"j{start + k + 1}": {"type": "noul",
                                     "instructions": QUESTION.format(i=start + k + 1, company=j.get("company"), title=j.get("title")),
                                     "criteria": CRITERIA}
              for k, j in enumerate(chunk)}
        r = c.post(URL, json={"state": state, "model": MODEL, "questions": qs},
                   headers={"Authorization": f"Bearer {key}", "User-Agent": "job-hunting-agent"})
        r.raise_for_status()
        ans = r.json().get("answers", {})
        for k in range(len(chunk)):
            a = ans.get(f"j{start + k + 1}") or {}
            v = a.get("noul", a.get("probability"))
            out.append(float(v) if v is not None else None)
    return out
