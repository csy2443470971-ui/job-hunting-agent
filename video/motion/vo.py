"""Voice lines for the motion film (Kokoro, local). One wav per line, then Whisper word times -> vo/lines.json."""
import json, re, sys
from pathlib import Path
import numpy as np, soundfile as sf

ROOT = Path(__file__).parent
LINES = [
    ("hook", "Job hunting is a full-time job. With zero pay."),
    ("pile", "And about a thousand dropdowns."),
    ("meet", "Meet Job Hunter Agent."),
    ("tell", "Step one: tell it your whole life story."),
    ("dump", "Old résumés, reference letters, that paper nobody read. Or just talk. It's a great listener."),
    ("book", "It turns all of it into your storybook. True stuff only. No surprise PhD."),
    ("find", "Step two: every morning, it finds jobs that actually fit you, using the Jev model."),
    ("nope", "Entry level, ten years required? Nope."),
    ("resume", "Step three: for each job, it writes a résumé from your storybook and the job description."),
    ("fill", "Then it fills out the whole application. Every. Single. Dropdown."),
    ("shot", "And takes a screenshot, so you can check every answer."),
    ("ok", "Nothing gets sent until you hit Approve."),
    ("reply", "Then it watches your inbox and tells you who wrote back."),
    ("end", "Job Hunter Agent. It does the grind. You do the talking."),
]

if sys.argv[1:2] == ["chatterbox"]:     # run with ~/.cache/chatterbox-venv: expressive male voice (timbre from voices/ref_male.wav)
    import torch, torchaudio as ta
    from chatterbox.tts import ChatterboxTTS
    m = ChatterboxTTS.from_pretrained(device="mps" if torch.backends.mps.is_available() else "cpu")
    attempt = int(sys.argv[2]); only = sys.argv[3:]
    for i, text in LINES:
        if only and i not in only:
            continue
        torch.manual_seed(attempt * 1000 + sum(map(ord, i)))   # each re-roll gets a new seed
        wav = m.generate(text, audio_prompt_path=str(ROOT / "voices" / "ref_male.wav"), exaggeration=1.05, cfg_weight=.3)   # "D": the comic setting
        ta.save(str(ROOT / "vo" / "raw" / f"{i}.wav"), wav, m.sr)
        print(f"{i:6s} {wav.shape[1] / m.sr:5.2f}s  {text}")
elif sys.argv[1:2] == ["tempo"]:         # vo/raw/<id>.wav -> vo/<id>.wav: silence trimmed, each line at its own pace
    import subprocess
    TEMPO = {"hook": 1.25, "pile": 1.2}  # the opening runs fast; everything else a touch tighter than read
    trim = "silenceremove=start_periods=1:start_threshold=-45dB"
    for i, _ in LINES:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(ROOT / "vo" / "raw" / f"{i}.wav"),
                        "-af", f"{trim},areverse,{trim},areverse,atempo={TEMPO.get(i, 1.08)}", str(ROOT / "vo" / f"{i}.wav")], check=True)
elif sys.argv[1:] == ["speak"]:          # run with the Kokoro venv
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    for i, text in LINES:
        audio = np.concatenate([np.asarray(a) for _, _, a in pipe(text, voice="af_heart", speed=1.12)])
        sf.write(ROOT / "vo" / f"{i}.wav", audio, 24000)
        print(f"{i:6s} {len(audio) / 24000:5.2f}s  {text}")
else:                                  # word times with Whisper
    import mlx_whisper
    out, bad = [], []
    for i, text in LINES:
        a, sr = sf.read(ROOT / "vo" / f"{i}.wav")
        r = mlx_whisper.transcribe(str(ROOT / "vo" / f"{i}.wav"), path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True)
        words = [{"w": w["word"].strip(), "t0": round(w["start"], 3), "t1": round(w["end"], 3)} for s in r["segments"] for w in s.get("words", [])]
        out.append({"id": i, "text": text, "dur": round(len(a) / sr, 3), "heard": r["text"].strip(), "words": words})
        NUM = {"one": "1", "two": "2", "three": "3", "ten": "10"}
        norm = lambda x: re.sub(r"[^a-z0-9]", "", re.sub(r"\b(one|two|three|ten)\b", lambda mm: NUM[mm.group(1)], x.lower().replace("é", "e")))
        ok = norm(text) == norm(r["text"])
        if not ok:
            bad.append(i)
        print(f"{i:6s} {out[-1]['dur']:5.2f}s  {'ok ' if ok else 'BAD'} heard: {out[-1]['heard']}")
    (ROOT / "vo" / "lines.json").write_text(json.dumps(out, indent=1))
    (ROOT / "vo" / "bad.txt").write_text(" ".join(bad))
