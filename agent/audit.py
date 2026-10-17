"""Node 7 · Review and audit.

Two things the dashboard shows for every application:
- checklist(): the checkpoints that must pass before anything is submitted or sent.
- events: an append-only log of what each node did, and every approval, rejection, submission and send.
"""
from __future__ import annotations
import json
from . import db

SCHEMA = """CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY, at TEXT, node TEXT, action TEXT, job_id INTEGER, app_id INTEGER, detail TEXT)"""


def log(con, node: str, action: str, detail: str = "", job_id: int | None = None, app_id: int | None = None) -> None:
    con.execute(SCHEMA)
    con.execute("INSERT INTO events(at, node, action, job_id, app_id, detail) VALUES (?,?,?,?,?,?)",
                (db.now(), node, action, job_id, app_id, detail[:2000]))
    con.commit()


def recent(con, limit: int = 200, app_id: int | None = None) -> list[dict]:
    con.execute(SCHEMA)
    q = "SELECT * FROM events" + (" WHERE app_id=?" if app_id else "") + " ORDER BY id DESC LIMIT ?"
    return [dict(r) for r in con.execute(q, ((app_id, limit) if app_id else (limit,))).fetchall()]


def checklist(app: dict, job: dict | None = None) -> list[dict]:
    """Each item: {label, ok (True/False/None = not applicable), detail}."""
    from .voicecheck import lint, lint_resume
    from .links import has_raw_url
    from . import config
    items = []
    rj = json.loads(app["resume_json"]) if isinstance(app.get("resume_json"), str) and app["resume_json"] else (app.get("resume_json") or {})
    aj = json.loads(app["answers_json"]) if isinstance(app.get("answers_json"), str) and app["answers_json"] else (app.get("answers_json") or {})
    diy_max = config.preferences().get("automation", {}).get("diy_max", 0.15)
    if rj:
        lines = [b["text"] for e in rj.get("experience", []) for b in e.get("bullets", [])] + [p.get("blurb", "") for p in rj.get("projects", [])]
        hard = [i.what for l in lines for i in lint(l, "resume") if i.level == "hard"] + [i.what for i in lint_resume(rj)]
        items.append({"label": "Résumé fits one page", "ok": bool(app.get("resume_pdf")), "detail": ""})
        items.append({"label": "Writing passes the brief's checks", "ok": not hard, "detail": "; ".join(hard[:4])})
    items.append({"label": f"Invented content ≤ {diy_max:.0%}", "ok": (app.get("diy_ratio") or 0) <= diy_max, "detail": f"{(app.get('diy_ratio') or 0):.0%}"})
    if app.get("kind") == "ats_web":
        nh = aj.get("needs_human") or []
        items.append({"label": "All form questions answered", "ok": not nh, "detail": "; ".join(nh[:3])})
        items.append({"label": "Form filled and screenshotted", "ok": "screenshot:" in (app.get("sent_log") or ""), "detail": ""})
    if app.get("kind") in ("email", "proposal", "social_mention"):
        body = app.get("email_body") or ""
        items.append({"label": "Recipient set", "ok": bool(app.get("email_to")), "detail": app.get("email_to") or ""})
        items.append({"label": "No placeholders or raw links", "ok": "[YOUR ANSWER" not in body and not has_raw_url(body), "detail": ""})
    if job is not None:
        items.append({"label": "Posting still open", "ok": job.get("status") != "closed", "detail": ""})
    items.append({"label": "Approved by you", "ok": app.get("status") in ("approved", "sent"), "detail": app.get("approved_at") or ""})
    return items
