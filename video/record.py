"""Record the explainer's screen scenes from the demo dashboard (fictional applicant, fictional companies).

Each scene: retina frames from the browser's screencast (rec/<scene>/NNNNN.jpg + frames.json) and an event log
(cursor moves, clicks, camera focus) in rec/<scene>/events.json. The cursor is drawn later by compose.py, so it
moves smoothly at 30 fps. Actions that would do real work (refresh, prepare, approve/submit) are answered by mocks.
The "tell" scene is real: three files are dropped and the agent reads them; the storybook is put back afterwards.
The microphone hears a scripted sentence (SAY) through a stand-in for the browser's speech recognition.

    JHA_PROFILE=profile.example JHA_DB=data/demo.sqlite python3 scripts/demo.py   # fresh demo data first
    python3 video/record.py [scene ...]
"""
from __future__ import annotations
import asyncio, base64, json, os, subprocess, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
URL = "http://127.0.0.1:8766/?edit=0"
VW, VH = 1440, 900


class Scene:
    def __init__(self, name, page, cdp):
        self.name, self.page, self.cdp = name, page, cdp
        self.dir = ROOT / "rec" / name
        self.dir.mkdir(parents=True, exist_ok=True)
        for f in self.dir.glob("*"):
            f.unlink()
        self.frames, self.events, self.cur = [], [], [VW * .62, VH * .55]
        self.t0 = None

    def now(self):
        return time.time() - self.t0

    async def start(self):
        async def on_frame(p):
            n = len(self.frames)
            (self.dir / f"{n:05d}.jpg").write_bytes(base64.b64decode(p["data"]))
            self.frames.append({"f": f"{n:05d}.jpg", "t": p["metadata"]["timestamp"] - self.t0})
            try:
                await self.cdp.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})
            except Exception:
                pass
        self._h = lambda p: asyncio.ensure_future(on_frame(p))
        self.cdp.on("Page.screencastFrame", self._h)
        self.t0 = time.time()
        await self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": VW * 2, "maxHeight": VH * 2, "everyNthFrame": 1})
        await self.page.evaluate("document.body.style.setProperty('--rec', Math.random())")   # force a first frame
        self.focus(None, 1.0, 0)
        await self.wait(.6)

    async def stop(self):
        await self.wait(.5)
        await self.cdp.send("Page.stopScreencast")
        await asyncio.sleep(.3)
        self.cdp.remove_listener("Page.screencastFrame", self._h)
        (self.dir / "frames.json").write_text(json.dumps(self.frames))
        (self.dir / "events.json").write_text(json.dumps({"events": self.events, "dur": self.now(), "size": [VW, VH]}, indent=1))
        print(f"{self.name}: {len(self.frames)} frames, {self.now():.1f}s")

    async def wait(self, s):
        await self.page.wait_for_timeout(int(s * 1000))

    def wide(self, dur=.9):
        self.focus(None, 1.0, dur)

    def whole(self, dur=.9):   # the window fills the frame
        self.focus([0, 0, VW, VH], 1.36, dur)

    def speed(self, t0, t1, x):
        self.events.append({"type": "speed", "t0": t0, "t1": t1, "x": x})

    def mark(self, line, at=0.0):
        """Pin this moment to narration line `line` (+ `at` seconds) when composing."""
        self.events.append({"type": "mark", "t": self.now(), "line": line, "at": at})

    def focus(self, rect, zoom, dur=.9):
        """Camera: centre `rect` (x, y, w, h in CSS px; None = whole page) at `zoom`, easing over `dur`."""
        self.events.append({"type": "focus", "t": self.now(), "dur": dur, "rect": rect, "zoom": zoom})

    async def box(self, sel):
        loc = self.page.locator(sel).first if isinstance(sel, str) else sel
        await loc.scroll_into_view_if_needed()
        b = await loc.bounding_box()
        return [b["x"], b["y"], b["width"], b["height"]]

    async def union(self, *sels):
        bs = [await self.box(x) for x in sels]
        x0, y0 = min(b[0] for b in bs), min(b[1] for b in bs)
        return [x0, y0, max(b[0] + b[2] for b in bs) - x0, max(b[1] + b[3] for b in bs) - y0]

    async def drag_file(self, labels, start, sel, pdfs, dur=1.4, mark=None):
        """Drag file cards from outside the window onto `sel`, then fire a real drop with the files."""
        labels, pdfs = ([labels], [pdfs]) if isinstance(labels, str) else (labels, pdfs)
        self.cur = list(start)
        b = await self.box(sel)
        x, y = b[0] + b[2] / 2, b[1] + b[3] / 2
        t0 = self.now()
        self.events.append({"type": "move", "t": t0, "dur": .01, "from": list(start), "to": list(start)})
        await self.wait(.3)
        t1 = self.now()
        self.events.append({"type": "move", "t": t1, "dur": dur, "from": list(start), "to": [x, y]})
        self.events.append({"type": "drag", "t0": t0, "t1": t1 + dur + .25, "label": labels[0], "count": len(labels)})
        await self.page.wait_for_timeout(int(dur * 650))
        await self.page.evaluate("document.querySelector('%s').classList.add('over')" % sel)
        await self.page.wait_for_timeout(int(dur * 350) + 200)
        self.cur = [x, y]
        self.events.append({"type": "click", "t": self.now(), "at": [x, y]})
        if mark:
            self.mark(*mark)
        files = [[n, base64.b64encode(Path(f).read_bytes()).decode()] for n, f in zip(labels, pdfs)]
        await self.page.evaluate("""([sel, files]) => {
            const dt = new DataTransfer();
            for (const [name, b64] of files) {
                const bin = atob(b64), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
                dt.items.add(new File([u], name, {type: 'application/pdf'}));
            }
            document.querySelector(sel).dispatchEvent(new DragEvent('drop', {bubbles: true, cancelable: true, dataTransfer: dt}));
        }""", [sel, files])

    async def move(self, x, y, dur=.6):
        self.events.append({"type": "move", "t": self.now(), "dur": dur, "from": list(self.cur), "to": [x, y]})
        self.cur = [x, y]
        await self.page.mouse.move(x, y)
        await self.wait(dur)

    async def click(self, sel, dur=.6, pause=.18, dx=.5, dy=.5, mark=None):
        b = await self.box(sel)
        x, y = b[0] + b[2] * dx, b[1] + b[3] * dy
        await self.move(x, y, dur)
        await self.wait(pause)
        self.events.append({"type": "click", "t": self.now(), "at": [x, y]})
        if mark:
            self.mark(*mark)
        await self.page.mouse.click(x, y)

    async def type(self, sel, text, delay=28):
        loc = self.page.locator(sel).first
        await loc.click()
        await loc.press_sequentially(text, delay=delay)


async def mock(page):
    state = {"refresh_at": None}

    async def refresh(route):
        if route.request.method == "POST":
            state["refresh_at"] = time.time()
            return await route.fulfill(json={"ok": True})
        running = state["refresh_at"] and time.time() - state["refresh_at"] < 2.6
        await route.fulfill(json={"running": bool(running), "failed": False, **({} if running else {"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "new": 24})})
    await page.route("**/api/refresh", refresh)
    await page.route("**/api/jobs/*/prepare", lambda r: r.fulfill(json={"ok": True}))
    await page.route("**/api/config", lambda r: r.fulfill(json={"jev": True}))     # no setup banner in the demo
    await page.route("**/api/applications/*/approve", lambda r: r.fulfill(json={"ok": True, "msg": "Submitting in a browser window. If a CAPTCHA appears, finish it there."}))


SAY = "Oh, and I taught a UX workshop at Pratt last spring. Thirty students. Nobody fell asleep."
FAKE_MIC = """
window.SpeechRecognition = window.webkitSpeechRecognition = class {
  start() { const w = SAY.split(' '); let i = 0;
    this._t = setInterval(() => { i++; this.onresult && this.onresult({results: [[{transcript: w.slice(0, i).join(' ')}]]});
      if (i >= w.length) { clearInterval(this._t); setTimeout(() => this.onend && this.onend(), 350); } }, 135); }
  stop() { clearInterval(this._t); this.onend && this.onend(); }
};""".replace("SAY", json.dumps(SAY))
FILES = ["Alex_Rivera_Resume_2021.pdf", "Reference_Letter_Fieldwork.pdf", "Thesis_Irrigation_Dashboards.pdf"]


async def nav(page, tab, sub=None):
    await page.evaluate(f"tab='{tab}'; {f'sub={json.dumps(sub)};' if sub else ''} sel={{review:null,todo:null,applied:null}}; render()")
    await page.wait_for_timeout(700)


# ------------------------------------------------------------------ scenes
async def tell(s: Scene):
    p = s.page
    await p.evaluate("tab='storybook'; pbFile='02-experience.md'; picked=[]; draft=''; render()"); await s.wait(.6)
    await p.evaluate("document.querySelector('main').scrollTop = 0")
    await s.start()
    s.wide(.01); await s.wait(.2)
    s.focus(await s.box(".tell"), 1.12, .8)            # wide enough to see the files come in from the desk
    await s.wait(.3)
    await s.drag_file(FILES, (VW + 120, VH * .36), "#drop", [ROOT / "ref" / f for f in FILES], 1.5, mark=("t2", .1))
    await s.wait(.3)
    s.focus(await s.box(".composer .bar"), 1.9, .7)    # the three files, by name
    await s.wait(2.2)
    s.focus(await s.box(".composer"), 1.7, .7)
    await s.click("#mic", .6, mark=("t3", .5))
    await s.wait(2.7)                                  # the sentence comes in as it is "said"
    await s.click(".composer .btn.primary", .6, mark=("t4", .05))
    for _ in range(20):        # the run reports "running" a moment after Send; then the page shows its progress
        st = await p.evaluate("fetch('/api/storybook/learn-status').then(r => r.json())")
        if st.get("state") == "running":
            break
        await s.wait(.25)
    await p.evaluate("render()")
    await p.locator(".panel").first.wait_for(timeout=15000)
    s.focus(await s.box(".panel"), 1.45, .6)
    t_ff = s.now()
    for _ in range(150):   # the real agent at work
        st = await p.evaluate("fetch('/api/storybook/learn-status').then(r => r.json())")
        if st.get("state") in ("done", "stopped", "error"):
            break
        await s.wait(1.0)
    await s.wait(2.7)          # the page re-renders with the changes
    s.speed(t_ff + .4, s.now() - .4, 50)
    s.focus(await s.union(".panel b", ".change >> nth=2"), 1.75, .7)
    await s.wait(3.2)
    await s.stop()
    print("  agent:", st.get("state"), len(st.get("changes", [])), "lines added", st.get("error", ""))
    await p.evaluate("fetch('/api/storybook/back', {method: 'POST'}).then(() => { picked = []; draft = ''; })"); await s.wait(.8)


async def find(s: Scene):
    p = s.page
    await nav(p, "jobs", "todo")
    await s.start()
    s.whole(.01); await s.wait(.3)
    s.focus(await s.box(".queue"), 1.5, .8)
    await s.wait(.6)
    b = await s.union(".qi >> nth=0", ".qi >> nth=2")
    s.focus([b[0] + b[2] - 110, b[1], 140, b[3]], 2.3, .8)    # the score rings
    for i in range(3):
        q = await s.box(f".qi >> nth={i}")
        await s.move(q[0] + q[2] - 34, q[1] + q[3] / 2, .45)
        await s.wait(.35)
    await s.click(".qi >> nth=0", .5, mark=("f2", 0))
    await s.wait(.4)
    s.focus(await s.box(".d-head"), 1.7, .8)
    await s.wait(1.6)
    s.whole(.8)
    await s.wait(.6)
    await s.stop()


async def ready(s: Scene):
    p = s.page
    await nav(p, "jobs", "review")
    await p.locator(".qi:has-text('Northwind Energy')").first.click(); await s.wait(.6)
    await s.start()
    s.whole(.01); await s.wait(.3)
    s.focus(await s.box(".doc >> nth=0"), 2.3, .8)        # the tailored résumé
    await s.move(*(lambda b: (b[0] + b[2] * .5, b[1] + b[3] * .4))(await s.box(".doc >> nth=0")), .6)
    await s.wait(.5)
    s.mark("r1", 2.2)
    s.focus(await s.box(".doc >> nth=1"), 2.3, .7)        # the filled form
    await s.click(".doc >> nth=1", .6, mark=("r1", 3.4))
    await s.wait(.4)
    s.focus(await s.box(".modal .win"), 1.35, .8)
    await s.wait(1.8)
    await p.keyboard.press("Escape"); await s.wait(.3)
    s.focus(await s.box(".d-foot"), 2.2, .7)
    await s.wait(.4)
    await s.click(".d-foot .btn.primary", .8, mark=("r2", 1.6))
    await s.wait(.9)
    s.whole(.9)
    await s.wait(1.2)
    await s.stop()


async def track(s: Scene):
    p = s.page
    await nav(p, "jobs", "applied")
    await p.evaluate("stageFilter='all'; render()"); await s.wait(.5)
    await p.locator(".qi:has-text('Copperleaf')").first.click(); await s.wait(.5)
    await s.start()
    s.whole(.01); await s.wait(.3)
    s.focus(await s.box(".queue"), 1.7, .7)
    await s.wait(.9)
    s.focus(await s.box(".reply"), 2.0, .7)
    await s.wait(1.4)
    await s.stop()


SCENES = {"tell": tell, "find": find, "ready": ready, "track": track}


async def main(names):
    env = {**os.environ, "JHA_PROFILE": "profile.example", "JHA_DB": "data/demo.sqlite", "JHA_PORT": "8766"}
    srv = subprocess.Popen([sys.executable, "-m", "dashboard.app"], cwd=str(REPO), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        await asyncio.sleep(3)
        async with async_playwright() as pw:
            b = await pw.chromium.launch(args=["--force-device-scale-factor=2"])
            ctx = await b.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=2)
            page = await ctx.new_page()
            await page.add_init_script(FAKE_MIC)
            await mock(page)
            cdp = await ctx.new_cdp_session(page)
            await page.goto(URL, wait_until="networkidle"); await page.wait_for_timeout(1200)
            for n in names:
                await SCENES[n](Scene(n, page, cdp))
            await b.close()
    finally:
        srv.terminate()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or list(SCENES)))
