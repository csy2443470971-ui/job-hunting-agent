"""Caption cues (house rules: one sentence per cue, single line, split only when too long, at the most natural seam)
and the narration track. Word times come from Whisper on the generated voice. Writes cues.json, captions.srt, voice/narration.wav."""
import json, re
from pathlib import Path
import numpy as np, soundfile as sf
import mlx_whisper

ROOT = Path(__file__).parent
plan = json.loads((ROOT / "plan.json").read_text())
MAXC = 90


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = []
    for s in parts:
        if len(s) <= MAXC:
            out.append(s); continue
        # too long for one line: split at the comma nearest the middle that leaves no scrap
        cands = [m.end() for m in re.finditer(r",\s", s)]
        best = min(cands, key=lambda i: abs(i - len(s) / 2)) if cands else len(s) // 2
        out += [s[:best].strip(), s[best:].strip()]
    return out


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower().replace("é", "e"))


cues, sr = [], 24000
total = int(plan["total"] * sr) + sr
mix = np.zeros(total, dtype=np.float32)
for ln in plan["lines"]:
    audio, _ = sf.read(ROOT / ln["file"], dtype="float32")
    i0 = int(ln["start"] * sr); mix[i0:i0 + len(audio)] += audio
    words = [w for seg in mlx_whisper.transcribe(str(ROOT / ln["file"]), path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
                                                  word_timestamps=True)["segments"] for w in seg.get("words", [])]
    sents = sentences(ln["text"])
    # walk our words against Whisper's: each sentence ends at its last word's end time
    ours = [len(s.split()) for s in sents]
    n_w = len(words); n_o = sum(ours)
    t_cursor, k = 0.0, 0
    for si, s in enumerate(sents):
        k_end = round((sum(ours[:si + 1])) * n_w / n_o) - 1
        k_end = max(k, min(n_w - 1, k_end))
        last = norm(s.split()[-1])
        for j in range(max(k, k_end - 2), min(n_w, k_end + 3)):   # snap to the matching word near the estimate
            if norm(words[j]["word"]) == last:
                k_end = j; break
        start = ln["start"] + (words[k]["start"] if si else 0.0)
        end = ln["start"] + (words[k_end]["end"] if si < len(sents) - 1 else ln["dur"])
        cues.append({"start": round(start, 2), "end": round(end + (.0 if si < len(sents) - 1 else .15), 2), "text": s})
        k = k_end + 1
# no two cues on screen together; small gaps closed so captions don't flicker
for a, b in zip(cues, cues[1:]):
    if b["start"] - a["end"] < .25:
        a["end"] = b["start"]
sf.write(ROOT / "voice" / "narration.wav", mix[:int(plan["total"] * sr)], sr)
(ROOT / "cues.json").write_text(json.dumps(cues, indent=1, ensure_ascii=False))


def ts(t):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
(ROOT / "captions.srt").write_text("\n".join(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n" for i, c in enumerate(cues, 1)))
for c in cues:
    print(f"{c['start']:7.2f} → {c['end']:7.2f}  {c['text']}")
