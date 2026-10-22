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


arch0 = S["arch"]["start"]
A = {"title": .35, "story": cue_t("Your storybook goes in.") - arch0, "agent": cue_t("The agent finds roles") - arch0,
     "agent_end": cue_t("You approve.") - arch0, "approve": cue_t("You approve.") - arch0, "loop": cue_t("It submits") - arch0}

STEPS = [("standing", "01", "Standing<br>answers"), ("storybook", "02", "Your<br>storybook"), ("find", "03", "It finds<br>the roles"),
         ("prepare", "04", "Résumé +<br>the form"), ("review", "05", "You<br>approve"), ("track", "06", "It tracks<br>replies")]

L = []
w = L.append
w("codecut 1")
w("title  Job Hunter Agent · how it works")
w("size   16:9")
w("fps    30")
w("by     claude")
w('theme  bg #F3EEE6  ink #1C1917  ink2 #57534E  accent #E5372A  accent2 #F27420  font "Roobert TWHINT"')
w("brief  A 2-minute product explainer for Job Hunter Agent, an open-source job-application agent: what the person does, what the agent does, "
  "and that nothing is sent without the person's approval. Plain words, a little American humour, real screen recordings with fictional demo data.")
w("lock   theme")
w("")
w("voice  vo   voice/narration.wav")
for sc in ("standing", "storybook", "find", "prepare", "fill", "review", "track"):
    w(f"asset  {sc}  scenes/{sc}.mp4")
w('music  bed  find "light playful upbeat background, pizzicato or ukulele, positive tech explainer, instrumental"')
w("")
w("# ---- the cut (times from plan.json) -------------------------------------------")
w(f"0:00  hook  #hook  {f(S['hook']['dur'])}s")
w("      line1  \"Applying for jobs is a <em>full-time job</em>.\"")
w("      line2  \"It doesn't pay. And it's <em>90% dropdowns</em>.\"")
w(f"      beat   {f(cue_t('Except') - .1)}")
w("      edit   line1, line2")
w("      variant B  line2 \"No salary. <em>Infinite</em> dropdowns.\"")
w("      why    The pain first, in one breath, before any product shows up.")
w(f"{f(S['meet']['start'])}  meet  #meet  {f(S['meet']['dur'])}s")
w("      name   \"Job Hunter <em>Agent</em>\"")
w("      sub    \"It does the boring part. You keep the part that matters.\"")
w("      edit   name, sub")
w("      why    The product's face: the icon people will see in the Dock.")
for sc in ("standing", "storybook", "find", "prepare", "fill", "review", "track"):
    w(f"{f(S[sc]['start'])}  clip  {sc}  {f(S[sc]['dur'])}s")
    w(f"      why    Real screen recording of the {sc} step (demo data, fictional applicant).")
w(f"{f(S['human']['start'])}  human  #human  {f(S['human']['dur'])}s")
w("      title  \"That one's <em>yours</em>.\"")
w("      note   \"The agent never solves CAPTCHAs or types your codes.\"")
w("      code   K7Q2MX9B")
w("      edit   title, note")
w("      why    The one place the agent hands the keyboard back, made visible.")
w(f"{f(S['arch']['start'])}  arch  #arch  {f(S['arch']['dur'])}s")
for k, v in A.items():
    w(f"      t_{k}  {f(v)}")
w("      edit   title")
w("      why    The architecture in three lanes, revealed on the narration's beat: you, the agent, the outside world.")
w(f"{f(S['end']['start'])}  ending  #end  {f(S['end']['dur'])}s")
w("      name   \"Job Hunter <em>Agent</em>\"")
w("      sub    \"Open source · github.com/csy2443470971-ui/job-hunting-agent\"")
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
for sc, _, _ in STEPS:
    w(f"marker {f(S[sc]['start'])}  {sc.title()}")
w(f"marker {f(S['arch']['start'])}  Architecture")
w("")
w('ask #hook "Which second line for the hook?"')
w('ask "Is the music level right under the voice?"')
w("")
w((ROOT / "templates.cut").read_text().replace("@ICON@", ICON))
(ROOT / "explainer.codecut").write_text("\n".join(L) + "\n")
print("wrote explainer.codecut", len("\n".join(L)) // 1024, "KB")
