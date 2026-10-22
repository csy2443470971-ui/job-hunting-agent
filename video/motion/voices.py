"""Voice candidates for the film, same lines each: Kokoro (two male voices) and Chatterbox (expressive), all local.

    ~/.cache/jha-tts/bin/python voices.py kokoro       # A, B, and the male reference clip for Chatterbox
    ~/.cache/chatterbox-venv/bin/python voices.py chatterbox   # C, D
"""
import sys
from pathlib import Path
import numpy as np, soundfile as sf

ROOT = Path(__file__).parent / "voices"
SAMPLE = ("Step one: tell it your whole life story. Old résumés, reference letters, that paper nobody read. "
          "Entry level, ten years required? Nope. Then it fills out the whole application. Every. Single. Dropdown.")
REF = "Hi, I'm here to help with your job search. I read everything you give me, and I only say what's true about you."

if sys.argv[1] == "kokoro":
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    say = lambda text, v, sp: np.concatenate([np.asarray(a) for _, _, a in pipe(text, voice=v, speed=sp)])
    sf.write(ROOT / "A_kokoro_michael.wav", say(SAMPLE, "am_michael", 1.1), 24000)
    sf.write(ROOT / "B_kokoro_puck.wav", say(SAMPLE, "am_puck", 1.1), 24000)
    sf.write(ROOT / "ref_male.wav", say(REF, "am_michael", 1.0), 24000)
else:
    import torch, torchaudio as ta
    from chatterbox.tts import ChatterboxTTS
    m = ChatterboxTTS.from_pretrained(device="mps" if torch.backends.mps.is_available() else "cpu")
    for name, ex, cfg in (("C_chatterbox_expressive", .7, .4), ("D_chatterbox_comic", 1.05, .3)):
        parts = [m.generate(s.strip(), audio_prompt_path=str(ROOT / "ref_male.wav"), exaggeration=ex, cfg_weight=cfg)
                 for s in ("Step one: tell it your whole life story.", "Old résumés, reference letters, that paper nobody read.",
                           "Entry level, ten years required? Nope.", "Then it fills out the whole application. Every. Single. Dropdown.")]
        gap = torch.zeros(1, int(.25 * m.sr))
        ta.save(str(ROOT / f"{name}.wav"), torch.cat([x for p in parts for x in (p, gap)], dim=1), m.sr)
        print(name, "done")
