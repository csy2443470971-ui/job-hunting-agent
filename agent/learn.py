"""Node 08 · Learn (self-improvement, with you in charge).

Inputs: your notes on applications, the reasons you rejected drafts, and edits you made in the dashboard.
Output: proposed patches, each small and reviewable:
  - brief_example   add or sharpen one Weak → Strong row in docs/00-house-rules.md (the brief stays one page)
  - storybook_line  replace one line in the storybook with a better-worded one (same facts)
  - ban_phrase      add a phrase to the writing check (profile/learned_patterns.yaml; code is never edited)
Nothing is applied until you approve it on the dashboard's Learn page. Every applied patch keeps its before/after,
so it can be reverted.
"""
from __future__ import annotations
import json
import re
from pydantic import BaseModel, Field
from . import config, db

SCHEMA = """
CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, at TEXT, app_id INTEGER, job_id INTEGER, text TEXT, used INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS proposals (id INTEGER PRIMARY KEY, at TEXT, kind TEXT, target TEXT, before TEXT, after TEXT,
  reason TEXT, source TEXT, status TEXT DEFAULT 'pending', decided_at TEXT);
"""
PATTERNS = lambda: config.PROFILE_DIR / "learned_patterns.yaml"


def init(con):
    con.executescript(SCHEMA)


def add_feedback(con, text: str, app_id: int | None = None, job_id: int | None = None):
    init(con)
    con.execute("INSERT INTO feedback(at, app_id, job_id, text) VALUES (?,?,?,?)", (db.now(), app_id, job_id, text.strip()))
    con.commit()


class Patch(BaseModel):
    kind: str = Field(description="brief_example | storybook_line | ban_phrase")
    target: str = Field(description="file the patch applies to: docs/00-house-rules.md, profile/master/<file>.md, or learned_patterns")
    before: str = Field(description="exact existing text to replace; '' when adding a brief example row or a ban phrase")
    after: str = Field(description="new text: a full table row '| Weak | Strong | Why |', a replacement storybook line, or a phrase")
    reason: str = Field(description="one sentence linking the patch to the note it came from")
    source: str = Field(description="the note or edit that prompted it, quoted briefly")


class Patches(BaseModel):
    patches: list[Patch]


def propose(con) -> int:
    """Turn unused feedback into pending proposals. Returns how many were proposed."""
    init(con)
    notes = [dict(r) for r in con.execute("SELECT * FROM feedback WHERE used=0").fetchall()]
    rejected = [dict(r) for r in con.execute("SELECT id, error FROM applications WHERE status='withdrawn' AND error IS NOT NULL AND error!=''").fetchall()]
    if not notes and not rejected:
        return 0
    from .llm import _system
    from .providers import structured
    body = ("## Notes from the person\n" + "\n".join(f"- (app {n['app_id']}) {n['text']}" for n in notes) +
            "\n\n## Reasons given when rejecting drafts\n" + "\n".join(f"- (app {r['id']}) {r['error']}" for r in rejected) +
            "\n\n## Current brief\n" + (config.DOCS_DIR / "00-house-rules.md").read_text(encoding="utf-8"))
    task = ("Propose the smallest patches that would have prevented each problem. Prefer one example row in the brief over a new rule; "
            "keep the brief to one page. Use storybook_line only to reword an existing line with the same facts, quoting it exactly in 'before'. "
            "Use ban_phrase for a phrase that should never appear. Skip notes that need no change.")
    res = structured(_system(task), body, Patches, effort="high", max_tokens=6000)
    for p in res.patches:
        con.execute("INSERT INTO proposals(at, kind, target, before, after, reason, source) VALUES (?,?,?,?,?,?,?)",
                    (db.now(), p.kind, p.target, p.before, p.after, p.reason, p.source))
    con.execute("UPDATE feedback SET used=1 WHERE used=0")
    con.commit()
    return len(res.patches)


def apply(con, pid: int) -> str:
    """Apply one approved proposal. Returns a short description; raises if the target text is not found."""
    init(con)
    p = dict(con.execute("SELECT * FROM proposals WHERE id=?", (pid,)).fetchone())
    if p["kind"] == "brief_example":
        path = config.DOCS_DIR / "00-house-rules.md"; s = path.read_text(encoding="utf-8")
        anchor = "| I am excited to apply…"
        if p["before"] and p["before"] in s:
            s = s.replace(p["before"], p["after"], 1)
        else:
            s = s.replace(anchor, p["after"].strip() + "\n" + anchor, 1)
        path.write_text(s, encoding="utf-8")
    elif p["kind"] == "storybook_line":
        hits = [f for f in config.MASTER_DIR.glob("*.md") if p["before"] and p["before"] in f.read_text(encoding="utf-8")]
        if not hits:
            raise ValueError("the line to replace was not found in the storybook")
        f = hits[0]; f.write_text(f.read_text(encoding="utf-8").replace(p["before"], p["after"], 1), encoding="utf-8")
    elif p["kind"] == "ban_phrase":
        import yaml
        path = PATTERNS(); data = yaml.safe_load(path.read_text()) if path.exists() else {}
        data = data or {}; data.setdefault("ban_phrases", [])
        if p["after"].lower() not in data["ban_phrases"]:
            data["ban_phrases"].append(p["after"].lower())
        path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    con.execute("UPDATE proposals SET status='applied', decided_at=? WHERE id=?", (db.now(), pid)); con.commit()
    from .audit import log
    log(con, "learn", "patch-applied", f"{p['kind']}: {p['after'][:200]}")
    return f"{p['kind']} applied"


def revert(con, pid: int) -> str:
    p = dict(con.execute("SELECT * FROM proposals WHERE id=?", (pid,)).fetchone())
    if p["kind"] == "brief_example":
        path = config.DOCS_DIR / "00-house-rules.md"; s = path.read_text(encoding="utf-8")
        s = s.replace(p["after"], p["before"], 1) if p["before"] else s.replace(p["after"].strip() + "\n", "", 1)
        path.write_text(s, encoding="utf-8")
    elif p["kind"] == "storybook_line":
        for f in config.MASTER_DIR.glob("*.md"):
            t = f.read_text(encoding="utf-8")
            if p["after"] in t:
                f.write_text(t.replace(p["after"], p["before"], 1), encoding="utf-8"); break
    elif p["kind"] == "ban_phrase":
        import yaml
        path = PATTERNS(); data = yaml.safe_load(path.read_text()) or {}
        data["ban_phrases"] = [x for x in data.get("ban_phrases", []) if x != p["after"].lower()]
        path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    con.execute("UPDATE proposals SET status='reverted', decided_at=? WHERE id=?", (db.now(), pid)); con.commit()
    from .audit import log
    log(con, "learn", "patch-reverted", p["after"][:200])
    return "reverted"


def learned_bans() -> list[str]:
    import yaml
    path = PATTERNS()
    return (yaml.safe_load(path.read_text()) or {}).get("ban_phrases", []) if path.exists() else []
