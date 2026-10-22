"""The film's sound, synthesised on the beat grid (120 BPM, A minor: Am F C G), plus the hits from film.html
(out/cues.json) and the voice lines (vo/*.wav). Music ducks under the voice; the mix is levelled at export.

    python3 audio.py   ->  out/mix.wav
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, soundfile as sf
from scipy.signal import butter, lfilter, resample_poly

ROOT = Path(__file__).parent
SR, BPM = 48000, 120
BEAT = 60 / BPM
cues = json.loads((ROOT / "out" / "cues.json").read_text())
DUR = cues["dur"] + .6
N = int(DUR * SR)
rng = np.random.default_rng(7)


def t_(d): return np.arange(int(d * SR)) / SR
def env(d, a=.003, k=8.0): t = t_(d); return np.minimum(1, t / a) * np.exp(-k * t)
def noise(d): return rng.uniform(-1, 1, int(d * SR))
def bp(x, lo, hi, o=2): b, a = butter(o, [lo / (SR / 2), hi / (SR / 2)], "band"); return lfilter(b, a, x)
def lp(x, f, o=2): b, a = butter(o, f / (SR / 2), "low"); return lfilter(b, a, x)
def hp(x, f, o=2): b, a = butter(o, f / (SR / 2), "high"); return lfilter(b, a, x)
def sweep(f0, f1, d, curve=3.0):
    t = t_(d); f = f1 + (f0 - f1) * np.exp(-curve * t / d) if f1 < f0 else f0 + (f1 - f0) * (t / d) ** 1.5
    return np.sin(2 * np.pi * np.cumsum(f) / SR)
def note(m): return 440 * 2 ** ((m - 69) / 12)
def over(a, b): a = a.copy(); a[: len(b)] += b[: len(a)]; return a      # b layered onto the start of a
def saw(f, d): t = t_(d); return 2 * ((t * f) % 1) - 1


def place(buf, x, at, g=1.0, pan=0.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(x) <= 0: return
    j = max(0, -i); x = x[j:]; i = max(0, i); x = x[: len(buf) - i]
    buf[i:i + len(x), 0] += x * g * np.sqrt((1 - pan) / 2) * 1.414
    buf[i:i + len(x), 1] += x * g * np.sqrt((1 + pan) / 2) * 1.414


# ---- instruments --------------------------------------------------------------------------------------------
def kick():
    x = sweep(150, 46, .4, 9) * env(.4, .002, 7)
    click = hp(noise(.006), 2000) * .4
    x[: len(click)] += click
    return x
def clap():
    d = .3; x = np.zeros(int(d * SR))
    for k in range(3):                                      # three quick bursts, the last one rings
        o = int(k * .011 * SR); seg = bp(noise(d - k * .011), 900, 2600) * env(d - k * .011, .001, 22 if k < 2 else 11)
        x[o:o + len(seg)] += seg[: len(x) - o]
    return x * .9 + .3 * np.sin(2 * np.pi * 190 * t_(d)) * env(d, .001, 30)
def hat(open_=False): d = .25 if open_ else .05; return hp(noise(d), 7000) * env(d, .001, 9 if open_ else 60)
def bass(f, d): return lp(saw(f, d) * .6 + np.sin(2 * np.pi * f * t_(d)) * .6, 420) * env(d, .004, 4.5)
def stab(fs, d=.32):
    x = sum(lp(saw(f, d) + .5 * saw(f * 1.004, d), 2600) for f in fs) / len(fs)
    return x * env(d, .002, 9)
def pad(fs, d):
    t = t_(d); x = sum(np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * 2 * f * t) for f in fs) / len(fs)
    return lp(x, 1800) * np.minimum(1, t / .3) * np.minimum(1, (d - t) / .6)


def reverb(x, d=1.1, mix=.18):
    ir = noise(d) * np.exp(-5 * t_(d)); ir = lp(ir, 5000); ir /= np.abs(ir).sum() / 6
    from scipy.signal import fftconvolve
    return x + mix * fftconvolve(x, ir)[: len(x)]


CHORDS = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]   # Am F C G (root, triad)
music = np.zeros((N, 2)); drums = np.zeros((N, 2))
GROOVE = (4.0, 23.5)
GAPS = [(3.78, 4.0), (19.78, 20.0), (23.5, 24.0)]          # silence before the booms, and the beat of stillness
in_gap = lambda t: any(a <= t < b for a, b in GAPS)

steps = int(24.0 / (BEAT / 4))
for s in range(steps):
    t = s * BEAT / 4; b4, beat = s % 4, s // 4
    if in_gap(t): continue
    bar = int(t // 2); root, triad = CHORDS[bar % 4]
    full = GROOVE[0] <= t < GROOVE[1]
    if full and b4 == 0: place(drums, kick(), t, .95)
    if (full or t >= 2.0) and b4 == 0 and beat % 2 == 1: place(drums, clap(), t, .55, .05)
    if b4 == 2: place(drums, hat(open_=full and beat % 2 == 1), t, .22 if full else .16, .25)
    elif full or t >= 2.0: place(drums, hat(), t, .09, -.2)
    if full and b4 in (0, 2): place(music, bass(note(root - 12), BEAT / 2 - .01), t, .5)
    if b4 == 2: place(music, stab([note(m + 12) for m in triad]), t, .17 if full else .12, -.15)
music[: int(4.0 * SR)] += 0                                 # intro pad under the first 4 s
place(music, pad([note(m) for m in CHORDS[0][1]], 2.0), 0.0, .12); place(music, pad([note(m) for m in CHORDS[1][1]], 1.8), 2.0, .12)

# ending: one hit chord that rings out
place(drums, kick(), 24.0, 1.0)
place(music, reverb(pad([note(m) for m in (57, 60, 64, 71)], 3.4), 1.6, .3), 24.0, .22)
place(music, stab([note(m + 12) for m in (57, 60, 64, 71)], .9), 24.0, .25)

# sidechain pump: everything but the drums breathes with the kick
pump = np.ones(N)
for s in range(int(GROOVE[0] / BEAT), int(GROOVE[1] / BEAT)):
    i = int(s * BEAT * SR); k = np.minimum(1, t_(.22) / .22) ** .6
    pump[i:i + len(k)] = np.minimum(pump[i:i + len(k)], .45 + .55 * k)
music *= pump[:, None]
for ch in (0, 1): music[:, ch] = reverb(music[:, ch], .9, .12)

# ---- hits from the film -----------------------------------------------------------------------------------
def sfx(kind):
    if kind == "tick":
        x = np.sin(2 * np.pi * 2600 * t_(.035)) * env(.035, .001, 90) * .6
        c = hp(noise(.02), 4000) * env(.02, .0005, 200) * .2; x[: len(c)] += c
        return x
    if kind == "pop": return sweep(500, 1300, .08) * env(.08, .002, 40)
    if kind == "thump": return over(sweep(140, 46, .26, 8) * env(.26, .002, 12), lp(noise(.05), 900) * env(.05, .001, 60) * .5)
    if kind == "whoosh":
        d = .55; t = t_(d)
        return (bp(noise(d), 500, 5000) * .8 + hp(noise(d), 3000) * .3) * np.sin(np.pi * t / d) ** 1.5 * 1.2
    if kind == "swipe":
        d = .3; t = t_(d); return hp(noise(d), 1800) * np.sin(np.pi * t / d) ** 2 * .9
    if kind == "riser":
        d = 1.1; t = t_(d); return (hp(noise(d), 1500) * .5 + sweep(220, 1400, d) * .25) * (t / d) ** 2.2
    if kind in ("boom", "boomlite", "hit"):
        big = kind != "boomlite"; d = 1.6 if big else .7
        x = sweep(70, 30, d, 4) * env(d, .002, 2.6 if big else 5) * 1.1
        x[: int(.4 * SR)] += lp(noise(.4), 1200) * env(.4, .001, 12) * .7
        x[: int(1.2 * SR) if big else int(.5 * SR)] += hp(noise(1.2 if big else .5), 5000) * env(1.2 if big else .5, .001, 3.5 if big else 7) * (.35 if big else .2)
        return x
    if kind == "stamp":
        return np.concatenate([sweep(180, 60, .2, 7) * env(.2, .001, 16) + bp(noise(.2), 600, 3000) * env(.2, .001, 45) * .6])
    raise KeyError(kind)


fx = np.zeros((N, 2))
PAN = {"whoosh": None, "swipe": None}
for c in cues["sfx"]:
    x = sfx(c["type"])
    if c["type"] in PAN:                                    # the plane and the flick travel left → right
        half = len(x) // 2
        place(fx, x[:half], c["t"], .55 * c["gain"], -.7); place(fx, x[half:], c["t"] + half / SR, .55 * c["gain"], .7)
    else:
        place(fx, x, c["t"], {"tick": .35, "pop": .45, "thump": .7, "riser": .5, "boom": .9, "boomlite": .7, "hit": .8, "stamp": .8}[c["type"]] * c["gain"])

# ---- voice, and the duck --------------------------------------------------------------------------------
vo = np.zeros((N, 2)); voenv = np.zeros(N)
for i, at in cues["vo"].items():
    a, sr = sf.read(ROOT / "vo" / f"{i}.wav", dtype="float64")
    a = resample_poly(a, SR, sr) if sr != SR else a
    a = a / (np.abs(a).max() + 1e-9) * .9
    place(vo, a, at, 1.0)
    j = int(at * SR); voenv[j:j + len(a)] = 1
k = int(.08 * SR); voenv = np.convolve(voenv, np.ones(k) / k, mode="same")
duck = 1 - .6 * voenv                                      # about −8 dB under the voice
bed = (music + drums * .9) * duck[:, None]

mix = bed * .55 + fx * .8 + vo * 1.0
mix /= max(1.0, np.abs(mix).max() / .95)
sf.write(ROOT / "out" / "mix.wav", mix.astype(np.float32), SR)
print(f"mix: {DUR:.2f}s, {len(cues['sfx'])} hits, {len(cues['vo'])} voice lines -> out/mix.wav")
