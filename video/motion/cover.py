"""Render cover.html at 2x -> out/cover.png (1920x1080 design, 3840x2160 pixels) and out/cover-1600.jpg for the web."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
from render import fonts

ROOT = Path(__file__).parent
fonts()
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
    pg.goto((ROOT / "cover.html").as_uri(), wait_until="networkidle"); pg.evaluate("document.fonts.ready")
    pg.screenshot(path=str(ROOT / "out" / "cover.png")); b.close()
Image.open(ROOT / "out" / "cover.png").convert("RGB").resize((1600, 900), Image.LANCZOS).save(ROOT / "out" / "cover-1600.jpg", quality=88)
print("cover -> out/cover.png, out/cover-1600.jpg")
