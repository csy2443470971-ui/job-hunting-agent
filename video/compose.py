"""Recorded scenes -> 1920x1080 30 fps clips with a desktop-level camera.

The app is placed in a macOS-style window on a "desk" drawn at 2x (3840x2160); the camera eases over the desk
(wide = the whole window, close = a detail), so zooms and pull-backs move the window itself. The cursor (with
click ripples and a dragged file card) is drawn at 30 fps from the recorder's event log; fast-forwarded stretches
(a real agent run) get a speed badge; each scene is retimed to its narration, and "mark" events pin a moment
(a click) to a narration line so picture and words land together. The bottom BAND stays clear for captions.

    python3 video/compose.py [scene ...]      # reads plan.json and rec/<scene>/, writes scenes/<scene>.mp4
"""
from __future__ import annotations
import bisect, json, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
W, H, FPS = 1920, 1080, 30
DW, DH = W * 2, H * 2                                   # the desk, at 2x
BG = (243, 238, 230)
WXd, WYd, WWd, TBd, WHd = 544, 92, 2752, 68, 1720       # window on the desk
CYd = WYd + TBd
VW, VH = 1440, 900                                      # recorded page, CSS px
SX, SY = WWd / VW, WHd / VH
FONT = "/System/Library/Fonts/Helvetica.ttc"
ROOBERT_B = str(Path.home() / "Library/Fonts/Roobert TWHINT Bold 2.ttf")      # any bold font works
ROOBERT_SB = str(Path.home() / "Library/Fonts/Roobert TWHINT SemiBold.ttf")
BAND, FADE = 116, 36                                   # caption strip under the picture, and its soft edge
HC = H - BAND
TITLES = {"fill": ("url", "jobs.northwind.example/apply")}
STEPS = {"tell": ("01", "Tell it everything", True), "find": ("02", "It finds the roles", True),
         "ready": ("03", "Ready for your OK", True), "track": ("04", "It tracks replies", True)}


def ease(p):
    p = max(0.0, min(1.0, p))
    return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2


def out_cubic(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype(FONT, size)


# ------------------------------------------------------------------ static pieces
def desk_base(kind: str, label: str) -> Image.Image:
    im = Image.new("RGB", (DW, DH), BG)
    sh = Image.new("L", (DW, DH), 0)
    ImageDraw.Draw(sh).rounded_rectangle((WXd, WYd + 34, WXd + WWd, CYd + WHd + 34), 32, fill=72)
    im.paste((60, 40, 20), (0, 0), sh.filter(ImageFilter.GaussianBlur(54)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((WXd - 2, WYd - 2, WXd + WWd + 2, CYd + WHd + 2), 30, fill=(222, 216, 208))
    d.rounded_rectangle((WXd, WYd, WXd + WWd, CYd + WHd), 28, fill=(248, 246, 243))
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        x = WXd + 40 + i * 40
        d.ellipse((x - 12, WYd + TBd / 2 - 12, x + 12, WYd + TBd / 2 + 12), fill=c)
    if kind == "url":
        pw = 1040
        d.rounded_rectangle((DW / 2 - pw / 2, WYd + 12, DW / 2 + pw / 2, WYd + TBd - 12), 16, fill=(234, 230, 224))
        d.text((DW / 2, WYd + TBd / 2), label, font=font(FONT, 30), fill=(90, 84, 78), anchor="mm")
    else:
        d.text((DW / 2, WYd + TBd / 2), label, font=font(FONT, 30), fill=(110, 104, 98), anchor="mm")
    d.line((WXd, CYd - 1, WXd + WWd, CYd - 1), fill=(226, 221, 214), width=2)
    return im


def content_mask() -> Image.Image:
    m = Image.new("L", (WWd, WHd), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, -40, WWd, WHd), 28, fill=255)
    return m


def cursor_img(px_height=62):
    s = px_height / 22 * 3
    pts = [(0, 0), (0, 17), (4.2, 13.2), (7.2, 20), (9.8, 18.9), (6.9, 12.4), (12.6, 12.4)]
    pad = 8 * s / 3
    big = Image.new("RGBA", (int(16 * s + 2 * pad), int(23 * s + 2 * pad)), (0, 0, 0, 0))
    P = [((x + 1.2) * s + pad, (y + 1.2) * s + pad) for x, y in pts]
    shadow = Image.new("RGBA", big.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).polygon([(x + 1.5 * s, y + 2 * s) for x, y in P], fill=(0, 0, 0, 90))
    big = Image.alpha_composite(big, shadow.filter(ImageFilter.GaussianBlur(2 * s)))
    d = ImageDraw.Draw(big)
    d.polygon(P, fill=(255, 255, 255, 255))
    inner = [((x + 1.2) * s + pad, (y + 1.2) * s + pad) for x, y in [(1.6, 3.8), (1.6, 14.2), (4.6, 11.4), (7.6, 18.1), (8.3, 17.8), (5.4, 11.0), (9.9, 11.0)]]
    d.polygon(inner, fill=(18, 18, 18, 255))
    out = big.resize((big.width // 3, big.height // 3), Image.LANCZOS)
    return out, (int((1.2 * s + pad) / 3), int((1.2 * s + pad) / 3))


def file_card(label: str, count: int = 1) -> Image.Image:
    """A dragged file; with count > 1, a small stack with the count on a badge."""
    w, h = max(470, int(138 + font(ROOBERT_SB, 28).getlength(label) + 40)), 112
    im = Image.new("RGBA", (w + 60, h + 60 + (28 if count > 1 else 0)), (0, 0, 0, 0))
    if count > 1:
        for k in range(min(count, 3) - 1, 0, -1):   # cards behind, fanned
            back = Image.new("RGBA", im.size, (0, 0, 0, 0))
            ImageDraw.Draw(back).rounded_rectangle((30 + 14 * k, 30 + 12 * k, 30 + w + 14 * k, 30 + h + 12 * k), 20,
                                                   fill=(250, 248, 245, 255), outline=(222, 216, 208, 255), width=2)
            im = Image.alpha_composite(im, back.rotate(3 * k, resample=Image.BICUBIC, center=(30 + w / 2, 30 + h / 2)))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((30, 40, 30 + w, 40 + h), 20, fill=(40, 25, 10, 90))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 30, 30 + w, 30 + h), 20, fill=(255, 255, 255, 250), outline=(222, 216, 208, 255), width=2)
    d.rounded_rectangle((56, 50, 56 + 60, 50 + 72), 10, fill=(229, 55, 42, 255))
    d.text((86, 86), "PDF", font=font(ROOBERT_B, 22), fill=(255, 255, 255), anchor="mm")
    d.text((138, 86), label, font=font(ROOBERT_SB, 28), fill=(28, 25, 23), anchor="lm")
    if count > 1:
        d.ellipse((w + 4, 8, w + 52, 56), fill=(229, 55, 42, 255))
        d.text((w + 28, 33), str(count), font=font(ROOBERT_B, 26), fill=(255, 255, 255), anchor="mm")
    return im.rotate(-4, resample=Image.BICUBIC, expand=True)


# ------------------------------------------------------------------ motion
def to_desk(x, y):
    return WXd + x * SX, CYd + y * SY


class Camera:
    def __init__(self, events):
        ev = sorted([e for e in events if e["type"] == "focus"], key=lambda e: e["t"])
        self.states = []
        for e in ev:
            start = self.at(e["t"], raw=True) if self.states else (DW / 2, DH / 2, .96)
            self.states.append((e, start, self._target(e)))

    @staticmethod
    def _target(e):
        if not e["rect"]:
            return (DW / 2, (WYd + CYd + WHd) / 2, 1.0)
        x, y, w, h = e["rect"]
        cx, cy = to_desk(x + w / 2, y + h / 2)
        return (cx, cy, e["zoom"])

    def at(self, t, raw=False):
        times = [s[0]["t"] for s in self.states]
        i = bisect.bisect_right(times, t) - 1
        if i < 0:
            return (DW / 2, DH / 2, 1.0)
        e, a, b = self.states[i]
        p = ease((t - e["t"]) / max(e["dur"], 1e-6))
        cx, cy, z = (a[k] + (b[k] - a[k]) * p for k in range(3))
        if raw:
            return cx, cy, z
        hold = t - (e["t"] + e["dur"])
        if hold > 0:                                   # slow drift on holds keeps the frame alive
            z *= 1 + .022 * ease(min(1, hold / 5))
        z = max(z, 1.0)                                # never wider than the desk
        hw, hh = DW / 2 / z, DH * HC / H / 2 / z
        return min(max(cx, hw), DW - hw), min(max(cy, hh), DH - hh), z


def cursor_at(events, t, start):
    pos = list(start)
    for e in events:
        if e["type"] == "move" and e["t"] <= t:
            p = ease((t - e["t"]) / max(e["dur"], 1e-6))
            pos = [e["from"][k] + (e["to"][k] - e["from"][k]) * p for k in (0, 1)]
    return pos


def time_map(events, R, target, anchors=()):
    """Output time -> source time, with fast-forward segments. Between anchors (source time, output time) the normal
    parts are scaled to fit, so a marked click lands on its narration line."""
    segs = sorted([e for e in events if e["type"] == "speed"], key=lambda e: e["t0"])
    cuts, t = [], 0.0
    for e in segs:
        if e["t0"] > t:
            cuts.append((t, e["t0"], 1.0))
        cuts.append((e["t0"], e["t1"], e["x"]))
        t = e["t1"]
    cuts.append((t, R, 1.0))
    pts = [(0.0, 0.0)] + sorted(anchors) + [(R, target)]
    table, rates = [], []
    for (sa, ta), (sb, tb) in zip(pts, pts[1:]):
        sub = [(max(a, sa), min(b, sb), r) for a, b, r in cuts if min(b, sb) > max(a, sa)]
        normal = sum(b - a for a, b, r in sub if r == 1.0)
        fast = sum((b - a) / r for a, b, r in sub if r != 1.0)
        f = normal / max(.1, (tb - ta) - fast)       # playback rate of the normal parts in this stretch
        rates.append(round(f, 2))
        acc = ta
        for a, b, r in sub:
            rate = r if r != 1.0 else f
            table.append((acc, a, rate, r != 1.0))
            acc += (b - a) / rate
    starts = [x[0] for x in table]

    def src(tau):
        k = max(0, bisect.bisect_right(starts, tau) - 1)
        o, a, rate, ff = table[k]
        return a + (tau - o) * rate, ff, (rate if ff else 0)
    return src, rates


def draw_step(fr, scene, tau):
    if scene not in STEPS:
        return
    num, label, anim = STEPS[scene]
    p = out_cubic(tau / .6) if anim else 1.0
    if p <= 0:
        return
    fn, fl = font(ROOBERT_B, 26), font(ROOBERT_SB, 24)
    w = 40 + fn.getlength(num) + 14 + fl.getlength(label) + 26
    lay = Image.new("RGBA", (int(w) + 60, 110), (0, 0, 0, 0))
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((30, 36, 30 + w, 36 + 52), 26, fill=(40, 25, 10, int(60 * p)))
    lay = Image.alpha_composite(lay, sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((30, 30, 30 + w, 30 + 52), 26, fill=(255, 255, 255, int(245 * p)))
    d.text((52, 56), num, font=fn, fill=(229, 55, 42, int(255 * p)), anchor="lm")
    d.text((52 + fn.getlength(num) + 14, 57), label, font=fl, fill=(28, 25, 23, int(255 * p)), anchor="lm")
    fr.paste(lay, (8, int(4 - (1 - p) * 20)), lay)


def draw_ff(fr, rate, a):
    if a <= 0:
        return
    lay = Image.new("RGBA", (190, 70), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((0, 0, 189, 69), 34, fill=(28, 25, 23, int(225 * a)))
    for dx in (34, 58):
        d.polygon([(dx, 22), (dx, 48), (dx + 22, 35)], fill=(255, 255, 255, int(255 * a)))
    d.text((96, 36), f"{int(rate)}×", font=font(ROOBERT_B, 30), fill=(255, 255, 255, int(255 * a)), anchor="lm")
    fr.paste(lay, (W - 190 - 36, 34), lay)


# ------------------------------------------------------------------ render
def render(scene: str, target: float, start: float = 0.0, lines=()):
    rd = ROOT / "rec" / scene
    frames = json.loads((rd / "frames.json").read_text())
    meta = json.loads((rd / "events.json").read_text())
    events, R = meta["events"], meta["dur"]
    times = [f["t"] for f in frames]
    cam = Camera(events)
    clicks = [e for e in events if e["type"] == "click"]
    drags = [e for e in events if e["type"] == "drag"]
    cards = {e["label"]: file_card(e["label"], e.get("count", 1)) for e in drags}
    kind, label = TITLES.get(scene, ("app", "Job Hunter Agent"))
    base, mask = desk_base(kind, label), content_mask()
    cur, hot = cursor_img(62)
    first_move = next((e for e in events if e["type"] == "move"), None)
    start_pos = first_move["from"] if first_move else [VW * .62, VH * .55]
    line_at = {ln["id"]: ln["start"] - start for ln in lines}
    anchors = [(e["t"], line_at[e["line"]] + e.get("at", 0)) for e in events if e["type"] == "mark" and e["line"] in line_at]
    src_of, rate = time_map(events, R, target, anchors)
    band = Image.new("RGB", (W, H), BG)
    fade = Image.linear_gradient("L").resize((W, FADE))   # picture at the top of the strip -> desk colour at the bottom
    out = ROOT / "scenes" / f"{scene}.mp4"
    out.parent.mkdir(exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    n = int(round(target * FPS))
    cache_i, cache_im = -1, None
    ff_alpha = 0.0
    for i in range(n):
        tau = i / FPS
        s, fast, frate = src_of(tau)
        fi = max(0, bisect.bisect_right(times, s) - 1)
        if fi != cache_i:
            cache_i = fi
            cache_im = Image.open(rd / frames[fi]["f"]).convert("RGB").resize((WWd, WHd), Image.BICUBIC, reducing_gap=2.0)
        desk = base.copy()
        desk.paste(cache_im, (WXd, CYd), mask)
        px, py = to_desk(*cursor_at(events, s, start_pos))
        k = 1.0
        for c in clicks:
            dt = s - c["t"]
            if 0 <= dt < .38:
                k = 1 - .16 * math.sin(math.pi * min(dt / .22, 1))
                rp = out_cubic(dt / .38); rad = 20 + 50 * rp
                ring = Image.new("RGBA", (int(rad * 2 + 12),) * 2, (0, 0, 0, 0))
                ImageDraw.Draw(ring).ellipse((6, 6, 6 + rad * 2, 6 + rad * 2), outline=(242, 116, 32, int(170 * (1 - rp))), width=6)
                desk.paste(ring, (int(px - rad - 6), int(py - rad - 6)), ring)
        for e in drags:
            if e["t0"] <= s <= e["t1"]:
                a = min(1, (s - e["t0"]) / .25, (e["t1"] - s) / .2)
                card = cards[e["label"]]
                if a < 1:
                    card = card.copy(); card.putalpha(card.getchannel("A").point(lambda v: int(v * max(0, a))))
                desk.paste(card, (int(px + 18), int(py + 10)), card)
        c2 = cur if k == 1 else cur.resize((max(1, int(cur.width * k)), max(1, int(cur.height * k))), Image.LANCZOS)
        desk.paste(c2, (int(px - hot[0] * k), int(py - hot[1] * k)), c2)
        cx, cy, z = cam.at(s)
        cw, ch = DW / z, DH * HC / H / z
        view = desk.resize((W, HC), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2), reducing_gap=2.0)
        fr = band.copy(); fr.paste(view, (0, 0))
        fr.paste(BG, (0, HC - FADE, W, HC), fade)
        draw_step(fr, scene, tau)
        ff_alpha = min(1, ff_alpha + .2) if fast else max(0, ff_alpha - .2)
        if ff_alpha > 0:
            draw_ff(fr, frate or 8, ff_alpha)
        ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait()
    print(f"{scene}: {target:.2f}s from {R:.1f}s recorded (normal parts x{rate}) -> {out.name}")


if __name__ == "__main__":
    plan = json.loads((ROOT / "plan.json").read_text())
    want = sys.argv[1:] or [s["scene"] for s in plan["scenes"] if (ROOT / "rec" / s["scene"]).exists()]
    for s in plan["scenes"]:
        if s["scene"] in want:
            render(s["scene"], s["dur"], s["start"], [ln for ln in plan["lines"] if ln["scene"] == s["scene"]])
