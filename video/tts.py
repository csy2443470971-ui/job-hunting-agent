"""Narration with Kokoro (local, open-source). One wav per sentence; writes video/voice/timing.json."""
import json, sys, numpy as np, soundfile as sf
from pathlib import Path
from kokoro import KPipeline
VOICE = sys.argv[1] if len(sys.argv) > 1 else "af_heart"
SPEED = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
root = Path(__file__).parent
lines = json.loads((root / "script.json").read_text())
pipe = KPipeline(lang_code="a")
out = []
for ln in lines:
    say = ln.get("say", ln["text"]).replace("CAPTCHA", "captcha").replace("PhD", "P H D")
    audio = np.concatenate([np.asarray(a) for _, _, a in pipe(say, voice=VOICE, speed=SPEED)])
    p = root / "voice" / f"{ln['id']}.wav"; sf.write(p, audio, 24000)
    out.append({**ln, "file": str(p.relative_to(root)), "dur": round(len(audio) / 24000, 3)})
    print(f"{ln['id']:6s} {out[-1]['dur']:5.2f}s  {ln['text'][:60]}")
(root / "voice" / "timing.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print("total", round(sum(x["dur"] for x in out), 1), "s")
