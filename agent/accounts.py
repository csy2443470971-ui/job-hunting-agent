"""Accounts: one per person or per story. Each is a profile folder with its own database and browser profile.

  profile/             the main account (yours)
  profiles/<name>/     others: another story you tell, or a demo account

The app's account switcher writes data/account.json and restarts the dashboard on the chosen account; everything the
dashboard starts (Refresh, Prepare, Submit) runs on it too. Command-line and scheduled runs ignore the switcher and use
the main account unless JHA_PROFILE says otherwise, so a demo left open in the app never takes over your daily run.

A demo account (profile.yaml: demo: true) starts empty, can use the sample material in demo/, finds real postings and
fills real forms up to the Submit button, and never sends anything (see config.is_demo).
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from . import config

SWITCH = config.DATA_DIR / "account.json"
DEMO_DIR = config.ROOT / "demo"


def _name(path: Path) -> str:
    """The person's name from the account's standing answers, else its profile.yaml, else the folder."""
    import yaml
    sa, prof = path / "standing.yaml", path / "profile.yaml"
    a = (yaml.safe_load(sa.read_text(encoding="utf-8")) or {}) if sa.exists() else {}
    p = (yaml.safe_load(prof.read_text(encoding="utf-8")) or {}) if prof.exists() else {}
    n = " ".join(x for x in (a.get("preferred_name") or a.get("legal_first"), a.get("legal_last")) if x) or p.get("name") or ""
    return n or ("New demo account" if p.get("demo") else path.name)


def _is_demo(path: Path) -> bool:
    import yaml
    prof = path / "profile.yaml"
    return bool(prof.exists() and (yaml.safe_load(prof.read_text(encoding="utf-8")) or {}).get("demo"))


def listing() -> list[dict]:
    """Every account on this computer, the active one marked."""
    active = config.PROFILE_DIR.resolve()
    paths = ([config.ROOT / "profile"] if (config.ROOT / "profile").exists() else []) + \
            sorted(p for p in (config.ROOT / "profiles").glob("*") if p.is_dir() and (p / "master").exists())
    return [{"id": "" if p == config.ROOT / "profile" else str(p.relative_to(config.ROOT)), "name": _name(p),
             "demo": _is_demo(p), "active": p.resolve() == active} for p in paths]


def switch(account_id: str) -> dict:
    """Make the dashboard use this account from its next start ('' = the main account)."""
    ids = {a["id"] for a in listing()}
    if account_id not in ids:
        raise ValueError("no such account")
    if account_id:   # its database and browser profile follow from the name (config.ACCOUNT)
        SWITCH.write_text(json.dumps({"profile": account_id}), encoding="utf-8")
    else:
        SWITCH.unlink(missing_ok=True)
    return {"ok": True}


def create_demo() -> str:
    """A new, empty demo account: the profile templates, nothing about anyone yet. Returns its id."""
    from .setup import new_profile
    base = config.ROOT / "profiles"
    n = 1
    while (base / f"demo-{n}").exists():
        n += 1
    path = base / f"demo-{n}"
    new_profile(path, demo=True)
    return str(path.relative_to(config.ROOT))


def remove_demo(account_id: str) -> None:
    """Delete a demo account that isn't in use: its folder, database, browser profile, screenshots and résumés.
    Only demo accounts; your own account and other stories are never removed here."""
    a = next((x for x in listing() if x["id"] == account_id), None)
    if not a or not a["demo"] or a["active"] or not account_id.startswith("profiles/"):
        raise PermissionError("only a demo account you're not using can be removed")
    import sqlite3
    slug = Path(account_id).name
    db = config.DATA_DIR / f"{slug}.sqlite"
    if db.exists():
        con = sqlite3.connect(db)
        try:
            pdfs = [r[0] for r in con.execute("SELECT resume_pdf FROM applications WHERE resume_pdf IS NOT NULL")]
        except sqlite3.Error:
            pdfs = []
        con.close()
        for p in pdfs:
            for f in (Path(p), Path(p).with_suffix(".png")):
                f.unlink(missing_ok=True)
    for f in (db, db.with_name(db.name + "-wal"), db.with_name(db.name + "-shm"), config.DATA_DIR / f"last_refresh-{slug}.json"):
        f.unlink(missing_ok=True)
    for d in (config.ROOT / account_id, config.DATA_DIR / f"browser-{slug}", config.OUT_DIR / "screens" / slug):
        shutil.rmtree(d, ignore_errors=True)


def demo_answers() -> int:
    """Fill this demo account's standing answers with the sample person's (demo/standing.yaml). Returns how many."""
    if not config.is_demo():
        raise PermissionError("only in a demo account")
    src = DEMO_DIR / "standing.yaml"
    shutil.copy(src, config.PROFILE_DIR / "standing.yaml")
    import yaml
    return len(yaml.safe_load(src.read_text(encoding="utf-8")) or {})
