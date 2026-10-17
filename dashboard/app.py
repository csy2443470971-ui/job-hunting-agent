"""Local review dashboard.  python -m dashboard.app  ->  http://127.0.0.1:8765"""
from __future__ import annotations
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent import db

HERE = Path(__file__).parent
app = FastAPI(title="Job hunting agent")


def rows(q, *args):
    with db.tx() as con:
        return [dict(r) for r in con.execute(q, args).fetchall()]


@app.get("/")
def index():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/api/stats")
def stats():
    with db.tx() as con:
        jobs = {r["status"]: r["c"] for r in con.execute("SELECT status, COUNT(*) c FROM jobs GROUP BY status")}
        apps = {r["status"]: r["c"] for r in con.execute("SELECT status, COUNT(*) c FROM applications GROUP BY status")}
        last = con.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    return {"jobs": jobs, "applications": apps, "last_run": dict(last) if last else None}


@app.get("/api/jobs")
def jobs(status: str | None = None, min_score: float = 0, limit: int = 300):
    q = "SELECT id, source, company, title, location, remote, url, sector, status, score, score_reason, discovered_at, posted_at FROM jobs WHERE score IS NOT NULL AND score>=?"
    args: list = [min_score]
    if status:
        q += " AND status=?"; args.append(status)
    q += " ORDER BY score DESC, discovered_at DESC LIMIT ?"; args.append(limit)
    return rows(q, *args)


@app.get("/api/jobs/{job_id}")
def job(job_id: int):
    r = rows("SELECT * FROM jobs WHERE id=?", job_id)
    if not r:
        raise HTTPException(404)
    j = r[0]
    j["score_json"] = json.loads(j["score_json"]) if j.get("score_json") else None
    return j


@app.get("/api/applications")
def applications(status: str | None = None):
    q = """SELECT a.*, j.company AS job_company, j.title AS job_title, j.url AS job_url, j.score AS job_score,
                  c.name AS company_name
           FROM applications a LEFT JOIN jobs j ON j.id=a.job_id LEFT JOIN companies c ON c.id=a.company_id"""
    args: list = []
    if status:
        q += " WHERE a.status=?"; args.append(status)
    q += " ORDER BY a.id DESC"
    out = rows(q, *args)
    for a in out:
        for k in ("resume_json", "answers_json"):
            if a.get(k):
                try:
                    a[k] = json.loads(a[k])
                except Exception:
                    pass
    return out


class Decision(BaseModel):
    note: str = ""


@app.post("/api/applications/{app_id}/approve")
def approve(app_id: int, d: Decision | None = None):
    from agent.audit import log
    with db.tx() as con:
        db.update_application(con, app_id, status="approved", approved_at=db.now())
        log(con, "review", "approved", d.note if d else "", app_id=app_id)
    return {"ok": True}


@app.post("/api/applications/{app_id}/reject")
def reject(app_id: int, d: Decision | None = None):
    from agent.audit import log
    with db.tx() as con:
        db.update_application(con, app_id, status="withdrawn", error=(d.note if d else None))
        log(con, "review", "rejected", d.note if d else "", app_id=app_id)
    return {"ok": True}


@app.get("/api/applications/{app_id}/checklist")
def app_checklist(app_id: int):
    from agent.audit import checklist
    a = rows("SELECT * FROM applications WHERE id=?", app_id)
    if not a:
        raise HTTPException(404)
    j = rows("SELECT * FROM jobs WHERE id=?", a[0]["job_id"]) if a[0].get("job_id") else []
    return checklist(a[0], j[0] if j else None)


@app.get("/api/events")
def events(limit: int = 200):
    from agent.audit import recent
    with db.tx() as con:
        return recent(con, limit)


class EmailEdit(BaseModel):
    email_to: str | None = None
    email_subject: str | None = None
    email_body: str | None = None
    cover_text: str | None = None


@app.post("/api/applications/{app_id}/edit")
def edit(app_id: int, e: EmailEdit):
    fields = {k: v for k, v in e.model_dump().items() if v is not None}
    if not fields:
        return {"ok": False}
    with db.tx() as con:
        db.update_application(con, app_id, **fields)
    return {"ok": True}


@app.get("/screen/{app_id}")
def screen(app_id: int):
    r = rows("SELECT sent_log FROM applications WHERE id=?", app_id)
    import re as _r
    m = _r.search(r"screenshot: (.+?\.png)", (r[0]["sent_log"] or "") if r else "")
    if not m or not Path(m.group(1)).exists():
        raise HTTPException(404)
    return FileResponse(m.group(1), media_type="image/png")


@app.get("/resume/{app_id}")
def resume(app_id: int):
    r = rows("SELECT resume_pdf FROM applications WHERE id=?", app_id)
    if not r or not r[0]["resume_pdf"] or not Path(r[0]["resume_pdf"]).exists():
        raise HTTPException(404)
    return FileResponse(r[0]["resume_pdf"], media_type="application/pdf")


# ---- playbook (profile/master) -------------------------------------------
from agent.config import MASTER_DIR
import re as _re


def _safe(name: str) -> Path:
    if not _re.fullmatch(r"[A-Za-z0-9._-]+\.(md|txt)", name):
        raise HTTPException(400, "bad name")
    return MASTER_DIR / name


@app.get("/api/playbook")
def playbook_list():
    out = []
    for f in sorted(MASTER_DIR.glob("*")):
        if f.suffix in (".md", ".txt"):
            txt = f.read_text(encoding="utf-8")
            out.append({"name": f.name, "words": len(txt.split()), "fill": txt.count("[fill"), "confirm": txt.count("[confirm"),
                        "mtime": f.stat().st_mtime})
    return out


@app.get("/api/playbook/{name}")
def playbook_get(name: str):
    f = _safe(name)
    if not f.exists():
        raise HTTPException(404)
    return {"name": name, "text": f.read_text(encoding="utf-8")}


class Text(BaseModel):
    text: str


@app.put("/api/playbook/{name}")
def playbook_put(name: str, t: Text):
    f = _safe(name)
    f.write_text(t.text, encoding="utf-8")
    return {"ok": True, "words": len(t.text.split())}


app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard.app:app", host="127.0.0.1", port=8765, reload=False)
