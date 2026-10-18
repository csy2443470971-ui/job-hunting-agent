"""Seed a demo database with a fictional applicant (Alex Rivera, profile.example/) and fictional companies.

    JHA_PROFILE=profile.example JHA_DB=data/demo.sqlite python scripts/demo.py
    JHA_PROFILE=profile.example JHA_DB=data/demo.sqlite JHA_PORT=8766 python -m dashboard.app

Used for README and website screenshots, so no real person or posting ever appears in them.
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
assert os.getenv("JHA_DB", "").endswith("demo.sqlite"), "set JHA_DB=data/demo.sqlite so the real database is never touched"
from agent import db, config
from agent.assemble import assemble
from agent.resume.render import render_one_page
from agent.audit import log

Path(os.environ["JHA_DB"]).unlink(missing_ok=True)
FORM = """<html><head><style>
body{font:15px -apple-system,Helvetica,sans-serif;margin:0;background:#fff;color:#222} .w{max-width:640px;margin:36px auto;padding:0 24px}
.q{font-weight:600;margin-bottom:7px} .row{margin-bottom:18px} .box{border:1px solid #ccc;border-radius:6px;padding:9px 11px;min-height:20px}
label.o{display:flex;align-items:center;gap:9px;margin:5px 0;font-weight:400} input{accent-color:#4F46E5;width:17px;height:17px;margin:0}
.sub{margin-top:26px;background:#4F46E5;color:#fff;text-align:center;padding:12px;border-radius:24px;font-weight:600}</style></head>
<body><div class="w"><div style="font-weight:700;font-size:22px;margin-bottom:4px">{co}</div><div style="color:#666;margin-bottom:26px">{title}</div>{rows}<div class="sub">Submit Application</div></div></body></html>"""
ROW = '<div class="row"><div class="q">{q}</div><div class="box">{a}</div></div>'
CHOICE = '<div class="row"><div class="q">{q}</div>{opts}</div>'
OPT = '<label class="o"><input type="{t}" {c}>{o}</label>'


def choice(q, opts, picked, kind="radio"):
    return CHOICE.format(q=q, opts="".join(OPT.format(t=kind, c="checked" if o in picked else "", o=o) for o in opts))

JOBS = [
  dict(company="Northwind Energy", title="Product Designer, Grid Tools", location="New York, NY", salary="$150K - $180K", kw=0.94, sector="climate", tab="review",
       desc="Northwind builds software that helps utilities plan for a grid with more solar, storage and EVs. You will design the tools planners use every day: load forecasts, interconnection queues and scenario comparison.\n\nWhat you'll do\n• Own the planning workspace end to end, from research to shipped UI\n• Work with engineers and data scientists on how uncertainty is shown\n• Run usability sessions with utility planners\n\nWhat we look for\n• 3+ years designing complex B2B products\n• Comfort with data-dense interfaces\n• Curiosity about the energy transition",
       fields=[("First name", "Alejandro"), ("Last name", "Rivera"), ("Email", "alex@example.com"), ("Portfolio", "alexrivera.example"), ("Why Northwind?", "Grid planning is where design decides how fast clean energy connects. At Fieldwork I designed scenario tools for municipal energy teams.")], needs=[]),
  dict(company="Lumen Labs", title="AI Product Designer", location="San Francisco, CA · Hybrid", salary="$165K - $200K", kw=0.86, sector="ai", tab="review",
       desc="Lumen Labs makes research assistants for scientists. Design how people direct, check and correct an AI agent across long tasks.",
       fields=[("First name", "Alejandro"), ("Last name", "Rivera"), ("Email", "alex@example.com"), ("LinkedIn", "linkedin.com/in/alex-rivera-example")],
       needs=["When is the earliest you could start?", "Portfolio password (if your case studies are protected)"]),
  dict(company="Studio Kite", title="Design Engineer", location="Remote", salary=None, kw=0.82, sector="design_agency", tab="review", email=True,
       desc="Small studio, launch sites for climate and science companies. Email hello@studiokite.example with two pieces of work.", needs=[]),
  dict(company="Fernhill", title="Motion Designer", location="Brooklyn, NY", salary="$110K - $130K", kw=0.68, sector="creative", tab="review",
       desc="Motion for product launches and brand systems.", fields=[("Name", "Alejandro Rivera"), ("Reel URL", "alexrivera.example/reel")], needs=["Are you available for a paid test project?"]),
  dict(company="Tidewater", title="Senior Product Designer", location="Boston, MA", salary="$170K - $195K", kw=0.91, sector="climate", tab="todo", desc="Ocean data platform for coastal resilience planning.", why="Climate data product with a planning workflow, close to your Fieldwork scenario tools."),
  dict(company="Open Circuit", title="Product Designer, Platform", location="Remote (US)", salary=None, kw=0.88, sector="ai", tab="todo", desc="Developer platform for evaluating AI models.", why="AI tooling for technical users; your design-system work at Fieldwork fits."),
  dict(company="Halden Studio", title="Creative Technologist", location="New York, NY", salary="$120K - $140K", kw=0.83, sector="design_agency", tab="todo", desc="Interactive installations and web experiences for museums.", why="Agency role mixing prototyping and front-end; strong match for your Three.js projects."),
  dict(company="Brightline Grid", title="UX Researcher", location="Chicago, IL", salary=None, kw=0.74, sector="climate", tab="todo", desc="Research with utility operators.", why="Research-heavy; fewer of your projects lead with research."),
  dict(company="Parcel & Co", title="Brand Designer", location="Remote", salary=None, kw=0.57, sector="creative", tab="todo", desc="Brand refresh for a logistics startup.", why="Brand-led; a stretch from your product focus."),
  dict(company="Copperleaf", title="Product Designer", location="Denver, CO", salary="$140K - $160K", kw=0.93, sector="climate", tab="applied", desc="Water utility software."),
  dict(company="Signal & Noise", title="Design Engineer", location="Remote", salary=None, kw=0.85, sector="ai", tab="applied", desc="AI audio tools."),
]

with db.tx() as con:
    shots = config.OUT_DIR / "screens"; shots.mkdir(parents=True, exist_ok=True)
    for i, J in enumerate(JOBS):
        desc = J["desc"] + (f"\n\nCompensation: {J['salary']}" if J.get("salary") else "")
        jid, _ = db.upsert_job(con, {"source": "email" if J.get("email") else "ashby", "external_id": f"demo-{i}", "company": J["company"], "title": J["title"],
                                     "location": J["location"], "url": f"https://jobs.example/{i}", "apply_url": None if J.get("email") else f"https://jobs.example/{i}/apply",
                                     "description": desc, "sector": J["sector"], "raw": json.dumps({"compensation": {"scrapeableCompensationSalarySummary": J.get("salary")}})})
        con.execute("UPDATE jobs SET kw_score=?, score_reason=?, status=? WHERE id=?", (J["kw"], J.get("why", ""), {"review": "applied_draft", "todo": "queued", "applied": "applied"}[J["tab"]], jid))
        if J["tab"] == "todo":
            continue
        lens = "design_engineer" if "Engineer" in J["title"] or "Technologist" in J["title"] else ("motion" if "Motion" in J["title"] else "product_design")
        pdf, rendered, _ = render_one_page(assemble(lens, J["sector"], posting_text=J["title"] + " " + desc), f"Alex_Rivera_{J['company'].replace(' ', '_')}_demo", role_family=lens, posting_title=J["title"])
        common = dict(job_id=jid, needs_approval=1, resume_pdf=str(pdf), resume_json=json.dumps(rendered), diy_ratio=0.0)
        status = "pending_approval" if J["tab"] == "review" else "sent"
        if J.get("email"):
            aid = db.create_application(con, kind="email", status=status, email_to="hello@studiokite.example", email_subject="Design engineer for Studio Kite's launch work",
                                        email_body="Hi Mara,\n\nYour Halden launch page is the reason I'm writing. I build launch sites in code at Fieldwork, from design to deploy, and two of them are below.\n\nWould you have 20 minutes next week?\n\nAlex", answers_json="{}", **common)
        else:
            fields = J.get("fields") or [("Name", "Alejandro Rivera"), ("Email", "alex@example.com")]
            shot = shots / f"demo-{i}.png"
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                b = p.chromium.launch(); pg = b.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=2)
                rows = "".join(ROW.format(q=q, a=a) for q, a in fields if not q.startswith("Are you willing"))
                rows += choice("Are you willing to relocate?", ["Yes", "No"], {"Yes"})
                rows += choice("Will you now or in the future require visa sponsorship?", ["Yes", "No"], {"No"})
                rows += choice("Which kinds of work are you open to?", ["Full-time", "Contract", "Internship"], {"Full-time", "Contract"}, "checkbox")
                rows += "".join(ROW.format(q=q, a="") for q in J.get("needs", []))
                rows += choice("", ["I agree to the processing of my data for this application"], {"I agree to the processing of my data for this application"}, "checkbox")
                pg.set_content(FORM.replace("{co}", J["company"]).replace("{title}", J["title"]).replace("{rows}", rows))
                pg.set_viewport_size({"width": 816, "height": max(1056, pg.evaluate("document.body.scrollHeight"))})
                pg.screenshot(path=str(shot), full_page=True); b.close()
            aj = {"answers": [{"question": q, "answer": a, "provenance": "master"} for q, a in fields], "needs_human": J.get("needs", []), "diy_ratio": 0.0}
            aid = db.create_application(con, kind="ats_web", status=status, answers_json=json.dumps(aj), sent_log=f"screenshot: {shot}", **common)
        if status == "sent":
            con.execute("UPDATE applications SET sent_at=?, approved_at=? WHERE id=?", (db.now(), db.now(), aid))
        log(con, "compose", "resume", f"lens {lens}", job_id=jid, app_id=aid)
    log(con, "discover", "scraped", "142 public postings from Greenhouse, Ashby and Lever boards")
    log(con, "rank", "jev", "38 postings rated; 11 above 50%")
    log(con, "apply", "submit-sent", "Copperleaf · Product Designer")
    con.commit()
print("demo data ready:", os.environ["JHA_DB"])
