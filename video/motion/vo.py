"""Voice lines for the motion film (Kokoro, local). One wav per line, then Whisper word times -> vo/lines.json."""
import json, sys
from pathlib import Path
import numpy as np, soundfile as sf

ROOT = Path(__file__).parent
LINES = [
    ("hook", "Job hunting is a full-time job. With zero pay."),
    ("dump", "Dump everything on it. Or just ramble."),
    ("find", "It finds the jobs."),
    ("nope", "Nope."),
    ("fill", "Every. Single. Dropdown."),
    ("ok", "Nothing goes out until you say so."),
    ("reply", "Then it tells you who wrote back."),
    ("end", "It does the grind. You do the talking."),
]

if sys.argv[1:] == ["speak"]:          # run with the Kokoro venv
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    for i, text in LINES:
        audio = np.concatenate([np.asarray(a) for _, _, a in pipe(text, voice="af_heart", speed=1.12)])
        sf.write(ROOT / "vo" / f"{i}.wav", audio, 24000)
        print(f"{i:6s} {len(audio) / 24000:5.2f}s  {text}")
else:                                  # word times with Whisper
    import mlx_whisper
    out = []
    for i, text in LINES:
        a, sr = sf.read(ROOT / "vo" / f"{i}.wav")
        r = mlx_whisper.transcribe(str(ROOT / "vo" / f"{i}.wav"), path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True)
        words = [{"w": w["word"].strip(), "t0": round(w["start"], 3), "t1": round(w["end"], 3)} for s in r["segments"] for w in s.get("words", [])]
        out.append({"id": i, "text": text, "dur": round(len(a) / sr, 3), "heard": r["text"].strip(), "words": words})
        print(f"{i:6s} {out[-1]['dur']:5.2f}s  heard: {out[-1]['heard']}")
    (ROOT / "vo" / "lines.json").write_text(json.dumps(out, indent=1))
