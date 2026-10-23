"""Write explainer.codecut from plan.json + cues.json (times are never typed by hand)."""
import base64, json
from pathlib import Path

ROOT = Path(__file__).parent
plan = json.loads((ROOT / "plan.json").read_text())
cues = json.loads((ROOT / "cues.json").read_text())
S = {s["scene"]: s for s in plan["scenes"]}
ICON = "data:image/webp;base64," + base64.b64encode((ROOT / "icon320.webp").read_bytes()).decode()


def cue_t(prefix):
    return next(c["start"] for c in cues if c["text"].startswith(prefix))


def f(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


CLIPS = ["tell", "find", "ready", "track"]
MARKERS = {"tell": "Tell it everything", "find": "It finds the roles", "ready": "Ready for your OK", "track": "It tracks replies"}

L = []
w = L.append
w("codecut 1")
w("title  Job Hunter Agent · how it works")
w("size   16:9")
w("fps    30")
w("by     claude")
w('theme  bg #F3EEE6  ink #1C1917  ink2 #57534E  accent #E5372A  accent2 #F27420  font "Roobert TWHINT"')
w("brief  A 45-second product demo for Job Hunter Agent, an open-source job-application agent: drop in everything or just talk, it finds and "
  "scores roles, the résumé and form come back done, nothing is sent until you approve. Fast, simple, a little American humour; "
  "real screen recordings with fictional demo data.")
w("lock   theme")
w("")
w("voice  vo   voice/narration.wav")
for sc in CLIPS:
    w(f"asset  {sc}  scenes/{sc}.mp4")
w('music  bed  find "light playful upbeat background, pizzicato or ukulele, positive tech explainer, instrumental"')
w("")
w("# ---- the cut (times from plan.json) -------------------------------------------")
w(f"0:00  hook  #hook  {f(S['hook']['dur'])}s")
w("      line1  \"Job hunting is a <em>full-time job</em>.\"")
w("      line2  \"With <em>zero pay</em>.\"")
w(f"      beat   {f(cue_t('With zero pay') - .1)}")
w("      edit   line1, line2")
w("      variant B  line2 \"And <em>way too many</em> dropdowns.\"")
w("      why    The pain first, in one breath, before any product shows up.")
w(f"{f(S['meet']['start'])}  meet  #meet  {f(S['meet']['dur'])}s")
w("      name   \"Job Hunter <em>Agent</em>\"")
w("      sub    \"It applies. <em>You approve.</em>\"")
w("      edit   name, sub")
w("      why    The product's face: the icon people will see in the Dock.")
for sc in CLIPS:
    w(f"{f(S[sc]['start'])}  clip  {sc}  {f(S[sc]['dur'])}s")
    w(f"      why    Real screen recording of the {sc} step (demo data, fictional applicant).")
w(f"{f(S['end']['start'])}  ending  #end  {f(S['end']['dur'])}s")
w("      name   \"Job Hunter <em>Agent</em>\"")
w("      sub    \"Open source · github.com/siennachen2002/job-hunting-agent\"")
w("      tag    \"It does the grind. <em>You do the talking.</em>\"")
w(f"      t_tag  {f(cue_t('It does the grind') - S['end']['start'])}")
w("      edit   name, sub, tag")
w("      why    Where to get it, and the promise in one line.")
w(f"0:00  voice  vo  {f(plan['total'])}s")
w("      why    Narration (Kokoro, af_heart). Swap the file to change the voice; captions are timed to it.")
w(f"0:00  music  bed  {f(plan['total'])}s  gain -17  fade 0.6  ending -1")
w("")
w("captions  size 36  x .05  y .935  w .9  color #1C1917  align center  fade 0")
for c in cues:
    w(f"  {f(c['start'])}-{f(c['end'])}  {c['text']}")
w("")
for sc, name in MARKERS.items():
    w(f"marker {f(S[sc]['start'])}  {name}")
w("")
w('ask #hook "Which second line for the hook?"')
w('ask "Is the music level right under the voice?"')
w("")
w((ROOT / "templates.cut").read_text().replace("@ICON@", ICON))
(ROOT / "explainer.codecut").write_text("\n".join(L) + "\n")
print("wrote explainer.codecut", len("\n".join(L)) // 1024, "KB")
