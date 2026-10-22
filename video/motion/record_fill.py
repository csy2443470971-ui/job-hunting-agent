"""Film the real filler: agent/apply/fill.py fills ats.html (a demo Greenhouse-style form) for the demo applicant.

Nothing about the filling is staged: the agent's own fill() runs on the page with the demo profile's standing
answers and the demo application's answers. Only the browser is wrapped: 2x pixels, a screencast of every
frame, and the page's field log (which field was active, when) read just before the browser closes.

    python3 record_fill.py   ->  rec_fill/ (raw 2x frames, field log, the filler's own screenshot), then img/fill/ + img/fill.json
                                 + img/shot.jpg at film size
"""
from __future__ import annotations
import base64, json, os, shutil, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
os.environ["JHA_PROFILE"] = "profile.example"           # the fictional applicant
os.environ["JHA_DB"] = "data/demo.sqlite"
os.chdir(REPO); sys.path.insert(0, str(REPO))

from playwright.sync_api import Browser
OUT = ROOT / "rec_fill"
shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir()
frames, state = [], {}
_new_page, _close = Browser.new_page, Browser.close


def new_page(self, **kw):
    kw["device_scale_factor"] = 2
    pg = _new_page(self, **kw)
    cdp = pg.context.new_cdp_session(pg)

    def on_frame(p):
        n = len(frames)
        (OUT / f"{n:05d}.jpg").write_bytes(base64.b64decode(p["data"]))
        frames.append({"f": f"{n:05d}.jpg", "t": p["metadata"]["timestamp"] * 1000,
                       "scroll": p["metadata"].get("scrollOffsetY", 0)})
        cdp.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})
    cdp.on("Page.screencastFrame", on_frame)
    cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 90, "maxWidth": 2560, "maxHeight": 3200})
    state.update(page=pg, cdp=cdp)
    return pg


def close(self, *a, **kw):
    pg = state.get("page")
    if pg:
        pg.wait_for_timeout(400)
        state["fields"] = pg.evaluate("window.__log")
        state["cdp"].send("Page.stopScreencast")
    return _close(self, *a, **kw)


Browser.new_page, Browser.close = new_page, close

from agent.apply.fill import fill
con = sqlite3.connect("data/demo.sqlite")
aj = json.loads(con.execute("SELECT answers_json FROM applications WHERE id=1").fetchone()[0])
answers = {a["question"]: a["answer"] for a in aj["answers"]}
resume = con.execute("SELECT resume_pdf FROM applications WHERE id=1").fetchone()[0]
res = fill((ROOT / "ats.html").as_uri(), answers, resume, str(OUT / "shot.png"), submit=False)
(OUT / "frames.json").write_text(json.dumps(frames))
(OUT / "fields.json").write_text(json.dumps(state.get("fields", [])))
(OUT / "result.json").write_text(json.dumps(res, indent=1))
span = (frames[-1]["t"] - frames[0]["t"]) / 1000 if frames else 0
print(f"{len(frames)} frames over {span:.1f}s; {len(state.get('fields', []))} field events")
print("\n".join(res["log"]))

# film-size copies: frames, their times from the first frame, the field log, and the filler's screenshot
from PIL import Image
dst = ROOT / "img" / "fill"; shutil.rmtree(dst, ignore_errors=True); dst.mkdir(parents=True)
t0 = frames[0]["t"]
out = []
for i, f in enumerate(frames):
    Image.open(OUT / f["f"]).convert("RGB").resize((1280, 1600), Image.LANCZOS).save(dst / f"{i:03d}.jpg", quality=90)
    out.append({"f": f"img/fill/{i:03d}.jpg", "t": round((f["t"] - t0) / 1000, 3)})
fields = [{"t": round((e["t"] - t0) / 1000, 3), "kind": e["kind"], "id": e["id"], "y": round(e["y"]), "h": round(e["h"])} for e in state.get("fields", [])]
Image.open(OUT / "shot.png").convert("RGB").resize((1280, 1600), Image.LANCZOS).save(ROOT / "img" / "shot.jpg", quality=90)
(ROOT / "img" / "fill.json").write_text(json.dumps({"frames": out, "fields": fields}))
