"""Render film.html frame by frame (window.seek(t) -> screenshot -> ffmpeg), and dump its sound cues.

    python3 render.py --stills 0 1.2 2.6 ...   # contact sheet -> out/sheet.png
    python3 render.py                          # out/film_silent.mp4 + out/cues.json (SFX hits, VO starts, duration)
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
OUT = ROOT / "out"
FPS, W, H = 30, 1920, 1080


FONTS = {"Roobert-Bold.ttf": "Roobert TWHINT Bold 2.ttf", "Roobert-SemiBold.ttf": "Roobert TWHINT SemiBold.ttf", "Roobert-Regular.ttf": "Roobert TWHINT Regular 2.ttf"}


def fonts():
    """The brand font is licensed, so it is not in the repo: copy it from this Mac's font folder (fonts/ is git-ignored)."""
    import shutil
    (ROOT / "fonts").mkdir(exist_ok=True)
    for dst, src in FONTS.items():
        if not (ROOT / "fonts" / dst).exists():
            shutil.copy(Path.home() / "Library" / "Fonts" / src, ROOT / "fonts" / dst)


def page_of(p):
    fonts()
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    pg.add_init_script("window.VO_LINES = " + (ROOT / "vo" / "lines.json").read_text())
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: m.type in ("error", "warning") and errors.append(m.text))
    pg.goto((ROOT / "film.html").as_uri(), wait_until="networkidle")
    pg.evaluate("window.ready")
    return b, pg, errors


def stills(times):
    from PIL import Image
    import io
    with sync_playwright() as p:
        b, pg, errors = page_of(p)
        ims = []
        for t in times:
            pg.evaluate(f"seek({t})")
            ims.append(Image.open(io.BytesIO(pg.screenshot(type="jpeg", quality=90))).resize((480, 270)))
        b.close()
    cols = 4
    sheet = Image.new("RGB", (480 * cols, 270 * ((len(ims) + cols - 1) // cols)), "white")
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
    OUT.mkdir(exist_ok=True); sheet.save(OUT / "sheet.png")
    print("sheet ->", OUT / "sheet.png", *(["errors:", *errors[:8]] if errors else []))


def full():
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b, pg, errors = page_of(p)
        dur = pg.evaluate("window.DUR")
        cues = {"dur": dur, "sfx": pg.evaluate("window.SFX"), "vo": pg.evaluate("window.VO_AT")}
        (OUT / "cues.json").write_text(json.dumps(cues, indent=1))
        n = int(round(dur * FPS))
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                               "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(FPS), str(OUT / "film_silent.mp4")],
                              stdin=subprocess.PIPE)
        for i in range(n):
            pg.evaluate(f"seek({i / FPS})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=95))
        ff.stdin.close(); ff.wait(); b.close()
    print(f"{n} frames, {dur:.2f}s -> {OUT / 'film_silent.mp4'}", *(["errors:", *errors[:8]] if errors else []))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--stills"]:
        stills([float(x) for x in sys.argv[2:]])
    else:
        full()
