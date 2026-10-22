"""Timeline from the narration: sentence start times, scene windows, caption cues -> plan.json."""
import json
from pathlib import Path

root = Path(__file__).parent
lines = json.loads((root / "voice" / "timing.json").read_text())
SCENE_OF = {"s5e": "human"}           # the CAPTCHA line gets its own graphic
GAP_IN, GAP_SCENE, LEAD, TAIL = .32, .75, .45, 1.6
PAUSE_AFTER = {"s4a": 1.6, "s2c": .3, "s5d": .3}   # let a few shots breathe

t, out, scenes, prev = 0.0, [], [], None
for ln in lines:
    sc = SCENE_OF.get(ln["id"], ln["scene"])
    if sc != prev:
        if prev is not None:
            t += GAP_SCENE
        scenes.append({"scene": sc, "start": round(max(0, t - LEAD), 3)})
        t = max(t, LEAD) if prev is None else t
        prev = sc
    elif out:
        t += GAP_IN
    out.append({**ln, "scene": sc, "start": round(t, 3), "end": round(t + ln["dur"], 3)})
    t += ln["dur"] + PAUSE_AFTER.get(ln["id"], 0)
total = round(t + TAIL, 3)
for i, s in enumerate(scenes):
    s["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else total
    s["dur"] = round(s["end"] - s["start"], 3)
plan = {"total": total, "lines": out, "scenes": scenes}
(root / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
for s in scenes:
    print(f"{s['scene']:10s} {s['start']:6.2f} → {s['end']:6.2f}  ({s['dur']:.1f}s)")
print("total", total)
