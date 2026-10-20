"""Node 09 · Track: what happened after you applied.

Once a day the scheduled run reads the person's inbox (Gmail connector, read-only), saves the matching messages to a JSON
file and calls `python -m agent.run replies-ingest <file>`. Each message is matched to a submitted application and sorted:

  confirmation   "we received your application"
  next_step      assessment, take-home, portfolio review request
  interview      a request to schedule a call or interview
  rejected       not moving forward
  offer          an offer
  other          about an application, but none of the above (shown for the person to read)

The application's stage only moves forward (applied < confirmation < next_step < interview < offer); a rejection ends it.
The person can correct a stage in the dashboard. Nothing here ever replies to, labels or deletes an email.
"""
from __future__ import annotations
import json
import re
from urllib.parse import urlparse
from . import db

SCHEMA = """
CREATE TABLE IF NOT EXISTS replies (id INTEGER PRIMARY KEY, app_id INTEGER, at TEXT, msg_id TEXT UNIQUE, thread_id TEXT,
  sender TEXT, subject TEXT, snippet TEXT, kind TEXT, view_url TEXT, seen INTEGER DEFAULT 0);
"""
STAGES = ["applied", "confirmation", "next_step", "interview", "offer"]
LABELS = {"applied": "Applied", "confirmation": "Received", "next_step": "Next step", "interview": "Interview",
          "offer": "Offer", "rejected": "Rejected", "other": "Reply"}
ATS_SENDERS = ["greenhouse.io", "greenhouse-mail.io", "ashbyhq.com", "lever.co", "hire.lever.co", "myworkdayjobs.com",
               "workday.com", "smartrecruiters.com", "icims.com", "jobvite.com", "rippling.com", "gem.com"]

RULES = [   # first match wins; order matters (a rejection often says "thank you for applying" too)
    ("offer", r"\b(pleased|excited|happy) to (extend|offer)|offer letter|formal offer"),
    ("rejected", r"not (be )?(moving|move) forward|decided to (move|proceed) forward with other|(pursue|proceed with) other candidates|"
                 r"will not be (moving|proceeding)|position has been filled|no longer (being )?considered|unable to (move|offer)|"
                 r"not selected|regret to inform|unfortunately,? (we|after)|decided not to proceed"),
    ("interview", r"\binterview|schedule (a|some) time|(phone|recruiter|intro(ductory)?) (screen|call|chat)|your availability|"
                  r"calendly\.com|goodtime|book a time|would love to (chat|talk|speak|connect)|set up a (call|time)"),
    ("next_step", r"assessment|take[- ]home|design (exercise|challenge)|portfolio review|hackerrank|codesignal|"
                  r"next step|complete the following|questionnaire"),
    ("confirmation", r"(received|receipt of) your application|thank(s| you) for (applying|your (application|interest))|"
                     r"application (has been )?(received|submitted)|we.ve got your application"),
]
SKIP = r"security code|verification code|verify your email|one[- ]time (code|password)|job alert|recommended jobs|newsletter"


def init(con):
    con.executescript(SCHEMA)
    cols = {r[1] for r in con.execute("PRAGMA table_info(applications)")}
    for c in ("stage", "stage_at", "stage_note"):
        if c not in cols:
            con.execute(f"ALTER TABLE applications ADD COLUMN {c} TEXT")
    con.commit()


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def tracked(con) -> list[dict]:
    """Submitted applications, with the names and domains their replies may come from."""
    init(con)
    out = []
    for r in con.execute("SELECT a.id, a.sent_at, a.stage, j.company, j.title, j.url, j.apply_url FROM applications a "
                         "JOIN jobs j ON j.id=a.job_id WHERE a.status='sent'").fetchall():
        r = dict(r)
        hosts = {urlparse(u or "").hostname or "" for u in (r["url"], r["apply_url"])}
        r["domains"] = sorted(h.replace("www.", "") for h in hosts if h and not any(a in h for a in ATS_SENDERS))
        out.append(r)
    return out


def gmail_query(con, days: int = 3) -> str:
    """A read-only Gmail search for replies about submitted applications."""
    names = sorted({t["company"] for t in tracked(con)})
    who = " OR ".join([f"from:{d}" for d in ATS_SENDERS] + [f'"{n}"' for n in names])
    return f"newer_than:{days}d -in:sent -in:drafts ({who} OR subject:(application OR interview OR candidacy))"


def classify(text: str) -> str:
    t = text.lower()
    if re.search(SKIP, t):
        return "skip"
    for kind, pat in RULES:
        if re.search(pat, t):
            return kind
    return "other"


def match(msg: dict, apps: list[dict]) -> dict | None:
    """The application a message is about: company name in sender/subject/body, else the posting's domain."""
    hay = _norm(" ".join([msg.get("sender", ""), msg.get("subject", ""), msg.get("body", "")[:4000]]))
    best = None
    for a in apps:
        n = _norm(a["company"])
        score = (3 if n and f" {n} " in f" {hay} " else 0) + (2 if any(d.split(".")[0] in hay for d in a["domains"]) else 0)
        score += 1 if _norm(a["title"]) and _norm(a["title"])[:30] in hay else 0
        if score and (best is None or score > best[0] or (score == best[0] and (a["sent_at"] or "") > (best[1]["sent_at"] or ""))):
            best = (score, a)
    return best[1] if best and best[0] >= 2 else None


def ingest(con, messages: list[dict]) -> dict:
    """messages: [{msg_id, thread_id, date, sender, subject, body or snippet, view_url}] -> counts by kind."""
    init(con)
    apps = tracked(con)
    counts = {}
    for m in messages:
        if not m.get("msg_id") or con.execute("SELECT 1 FROM replies WHERE msg_id=?", (m["msg_id"],)).fetchone():
            continue
        text = " ".join([m.get("subject", ""), m.get("body") or m.get("snippet", "")])
        kind = classify(text)
        if kind == "skip":
            continue
        app = match(m, apps)
        if not app:
            continue
        con.execute("INSERT INTO replies(app_id, at, msg_id, thread_id, sender, subject, snippet, kind, view_url) VALUES (?,?,?,?,?,?,?,?,?)",
                    (app["id"], m.get("date") or db.now(), m["msg_id"], m.get("thread_id"), m.get("sender", "")[:200],
                     m.get("subject", "")[:300], (m.get("body") or m.get("snippet", ""))[:600], kind, m.get("view_url")))
        advance(con, app["id"], kind, m.get("subject", ""))
        counts[kind] = counts.get(kind, 0) + 1
    con.commit()
    return counts


def advance(con, app_id: int, kind: str, note: str = "", by_person: bool = False) -> None:
    """Move the stage forward (or set it outright when the person corrects it)."""
    init(con)
    cur = con.execute("SELECT stage FROM applications WHERE id=?", (app_id,)).fetchone()[0] or "applied"
    if kind == "other":
        return
    if not by_person:
        if cur in ("rejected", "offer"):
            return
        if kind != "rejected" and kind in STAGES and STAGES.index(kind) <= STAGES.index(cur if cur in STAGES else "applied"):
            return
    con.execute("UPDATE applications SET stage=?, stage_at=?, stage_note=? WHERE id=?", (kind, db.now(), note[:200], app_id))
    from .audit import log
    log(con, "track", "stage", f"{LABELS.get(kind, kind)}{' (set by you)' if by_person else ''}: {note[:120]}", app_id=app_id)
