"""Record the explainer's screen scenes from the demo dashboard (fictional applicant, fictional companies).

Each scene: retina frames from the browser's screencast (rec/<scene>/NNNNN.jpg + frames.json) and an event log
(cursor moves, clicks, camera focus) in rec/<scene>/events.json. The cursor is drawn later by compose.py, so it
moves smoothly at 30 fps. Actions that would do real work (refresh, prepare, approve/submit) are answered by mocks.

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

    def focus(self, rect, zoom, dur=.9):
        """Camera: centre `rect` (x, y, w, h in CSS px; None = whole page) at `zoom`, easing over `dur`."""
        self.events.append({"type": "focus", "t": self.now(), "dur": dur, "rect": rect, "zoom": zoom})

    async def box(self, sel):
        loc = self.page.locator(sel).first if isinstance(sel, str) else sel
        await loc.scroll_into_view_if_needed()
        b = await loc.bounding_box()
        return [b["x"], b["y"], b["width"], b["height"]]

    async def drag_file(self, label, start, sel, pdf, dur=1.4):
        """Drag a file card from outside the window onto `sel`, then fire a real drop with the file."""
        self.cur = list(start)
        b = await self.box(sel)
        x, y = b[0] + b[2] / 2, b[1] + b[3] / 2
        t0 = self.now()
        self.events.append({"type": "move", "t": t0, "dur": .01, "from": list(start), "to": list(start)})
        await self.wait(.3)
        t1 = self.now()
        self.events.append({"type": "move", "t": t1, "dur": dur, "from": list(start), "to": [x, y]})
        self.events.append({"type": "drag", "t0": t0, "t1": t1 + dur + .25, "label": label})
        await self.page.wait_for_timeout(int(dur * 650))
        await self.page.evaluate("document.querySelector('%s').classList.add('over')" % sel)
        await self.page.wait_for_timeout(int(dur * 350) + 200)
        self.cur = [x, y]
        self.events.append({"type": "click", "t": self.now(), "at": [x, y]})
        b64 = base64.b64encode(Path(pdf).read_bytes()).decode()
        await self.page.evaluate("""([sel, name, b64]) => {
            const bin = atob(b64), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
            const dt = new DataTransfer(); dt.items.add(new File([u], name, {type: 'application/pdf'}));
            document.querySelector(sel).dispatchEvent(new DragEvent('drop', {bubbles: true, cancelable: true, dataTransfer: dt}));
        }""", [sel, label, b64])

    async def move(self, x, y, dur=.6):
        self.events.append({"type": "move", "t": self.now(), "dur": dur, "from": list(self.cur), "to": [x, y]})
        self.cur = [x, y]
        await self.page.mouse.move(x, y)
        await self.wait(dur)

    async def click(self, sel, dur=.6, pause=.18, dx=.5, dy=.5):
        b = await self.box(sel)
        x, y = b[0] + b[2] * dx, b[1] + b[3] * dy
        await self.move(x, y, dur)
        await self.wait(pause)
        self.events.append({"type": "click", "t": self.now(), "at": [x, y]})
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
    await page.route("**/api/applications/*/approve", lambda r: r.fulfill(json={"ok": True, "msg": "Submitting in a browser window. If a CAPTCHA appears, finish it there."}))


async def nav(page, tab, sub=None):
    await page.evaluate(f"tab='{tab}'; {f'sub={json.dumps(sub)};' if sub else ''} sel={{review:null,todo:null,applied:null}}; render()")
    await page.wait_for_timeout(700)


# ------------------------------------------------------------------ scenes
async def standing(s: Scene):
    p = s.page
    await p.evaluate("tab='storybook'; pbFile='@standing'; render()"); await s.wait(.6)
    await p.evaluate("document.querySelector('main').scrollTop = 0")
    await s.start()
    s.wide(.01); await s.wait(.5)
    s.focus(await s.box(".toc"), 1.9, 1.1)
    await s.click(".toc button:has-text('Standing answers')", .8)
    await s.wait(.4)
    s.focus(await s.box(".md h1"), 1.7, 1.1)
    await s.wait(1.2)
    s.whole(.9)
    await p.evaluate("document.querySelector('main').scrollTo({top: 520, behavior: 'smooth'})"); await s.wait(1.0)
    s.focus(await s.box("select[data-k='relocate']"), 2.1, .9)
    await s.click("select[data-k='relocate']", .7)
    await p.select_option("select[data-k='relocate']", "Yes"); await s.wait(.5)
    s.whole(.8)
    await p.evaluate("document.querySelector('main').scrollTo({top: 1500, behavior: 'smooth'})"); await s.wait(1.0)
    s.focus(await s.box("select[data-k='gender']"), 2.1, .9)
    await s.click("select[data-k='gender']", .7)
    await p.select_option("select[data-k='gender']", "Prefer not to say"); await s.wait(.5)
    await s.click("select[data-k='race']", .5)
    await p.select_option("select[data-k='race']", "Prefer not to say"); await s.wait(.5)
    s.wide(1.1)
    await s.wait(1.4)
    await s.stop()


async def storybook(s: Scene):
    p = s.page
    await p.evaluate("tab='storybook'; pbFile='02-experience.md'; picked=null; draft=''; render()"); await s.wait(.6)
    await p.evaluate("document.querySelector('main').scrollTop = 0")
    await s.start()
    s.wide(.01); await s.wait(.6)
    s.focus(await s.box(".tell"), 1.12, 1.0)          # wide enough to see the file come in from the desk
    await s.wait(.4)
    await s.drag_file("Jordan_Lee_Resume.pdf", (VW + 120, VH * .36), "#drop", ROOT / "ref" / "Jordan_Lee_Resume.pdf", 1.7)
    await s.wait(.5)
    s.focus(await s.box("#drop"), 2.0, .8)
    await s.wait(1.0)
    s.focus(await s.box(".composer"), 1.9, .9)
    await s.click(".pill:has-text('Change how my résumé is written')", .7)
    await s.wait(.2)
    await p.locator("#ask").press_sequentially("lead every bullet with the result, like Jordan does.", delay=24)
    await s.wait(.3)
    await s.click(".composer .btn.primary", .7)
    for _ in range(20):        # the run reports "running" a moment after Send; then the page shows its progress
        st = await p.evaluate("fetch('/api/storybook/learn-status').then(r => r.json())")
        if st.get("state") == "running":
            break
        await s.wait(.25)
    await p.evaluate("render()"); await s.wait(1.0)
    s.wide(1.0)
    await s.wait(1.0)
    await p.locator(".panel").first.wait_for(timeout=15000)
    s.focus(await s.box(".panel"), 1.7, 1.0)
    t_ff = s.now()
    for _ in range(150):   # the real agent at work
        st = await p.evaluate("fetch('/api/storybook/learn-status').then(r => r.json())")
        if st.get("state") in ("done", "stopped", "error"):
            break
        await s.wait(2.0)
    await s.wait(2.8)          # the dashboard re-renders with the changes
    s.speed(t_ff + .8, s.now() - 1.6, 8)
    await p.evaluate("document.querySelector('main').scrollTo({top: 260, behavior: 'smooth'})"); await s.wait(.8)
    s.focus(await s.box(".change >> nth=0"), 2.2, 1.0)
    await s.wait(3.2)
    s.whole(.9)
    await p.evaluate("document.querySelector('main').scrollTo({top: 99999, behavior: 'smooth'})"); await s.wait(1.0)
    s.focus(await s.box(".toc .back"), 2.2, .9)
    await s.click(".toc .back button", .8)
    await s.wait(1.4)
    s.wide(1.0)
    await s.wait(1.2)
    await s.stop()


async def find(s: Scene):
    p = s.page
    await nav(p, "jobs", "todo")
    await s.start()
    s.wide(.01); await s.wait(.4)
    s.focus(await s.box(".side-foot"), 2.3, 1.0)
    await s.click("#refresh", .9)
    await s.wait(2.9)
    s.whole(.9); await s.wait(.6)
    s.focus(await s.box(".queue"), 1.75, 1.0)
    await s.wait(.6)
    for name in ("Tidewater", "Halden Studio", "Parcel & Co"):
        b = await s.box(f".qi:has-text('{name}')")
        s.focus([b[0] + b[2] - 90, b[1] - 20, 120, b[3] + 40], 2.4, .55)
        await s.move(b[0] + b[2] - 34, b[1] + b[3] / 2, .5)
        await s.wait(.5)
    s.whole(.8)
    await s.click(".qi:has-text('Tidewater')", .6)
    await s.wait(.6)
    s.focus(await s.box(".d-head"), 1.8, .9)
    await s.wait(1.2)
    s.wide(1.0)
    await s.wait(1.0)
    await s.stop()


async def prepare(s: Scene):
    p = s.page
    await nav(p, "jobs", "todo")
    await p.locator(".qi:has-text('Tidewater')").first.click(); await s.wait(.5)
    await s.start()
    s.focus(await s.box(".d-foot"), 2.0, .01); await s.wait(.3)
    await s.click(".d-foot .btn.primary", .7)
    await p.evaluate("const b=document.querySelector('.d-foot .btn.primary'); b.innerHTML='<span class=\"spin\"></span>Preparing…'; b.disabled=true")
    await s.wait(1.1)
    s.wide(.8)
    await nav(p, "jobs", "review")
    await p.locator(".qi:has-text('Northwind Energy')").first.click(); await s.wait(.5)
    s.focus(await s.box(".docs"), 2.1, .9)
    await s.click(".doc >> nth=0", .7)
    await s.wait(.4)
    s.focus(await s.box(".modal .win"), 1.45, .9)
    await s.wait(2.0)
    await p.keyboard.press("Escape"); await s.wait(.3)
    await s.stop()


async def fill(s: Scene):
    p = s.page
    _box = s.box

    async def colbox(sel):   # frame the whole form column at the field's height, not the field alone
        b = await _box(sel); w = await _box(".wrap")
        return [w[0] - 20, b[1], w[2] + 40, b[3]]
    await p.goto((ROOT / "form.html").as_uri()); await s.wait(.5)
    await s.start()
    s.wide(.01); await s.wait(.5)
    s.focus(await colbox("#first"), 1.95, 1.0)
    for sel, text in (("#first", "Alejandro"), ("#last", "Rivera"), ("#email", "alex@example.com"), ("#phone", "(555) 010-0000")):
        await s.click(sel, .32, .06); await p.locator(sel).press_sequentially(text, delay=24)
    await s.click("#loc .v", .35, .05); await s.wait(.25)
    await s.click("#loc .menu div >> nth=0", .3, .1)
    await s.click("#up .btn", .35, .08); await s.wait(.3)
    s.focus(await colbox("#li"), 1.95, .8)
    await s.click("#li", .3, .05); await p.locator("#li").press_sequentially("linkedin.com/in/alex-rivera", delay=14)
    await s.click("#pf", .3, .05); await p.locator("#pf").press_sequentially("alexrivera.example", delay=16)
    s.focus(await colbox("#auth"), 2.0, .8)
    await s.click("#auth button >> nth=0", .45, .08)
    await s.click("#spon button >> nth=1", .4, .08)
    await s.click("#heard .v", .4, .05); await s.wait(.25)
    await s.click("#heard .menu div >> nth=0", .3, .1)
    s.focus(await colbox("#why"), 2.0, .8)
    await s.click("#why", .4, .05)
    await p.locator("#why").press_sequentially("Northwind's mission is to help the grid run on clean power, and I love that it treats planning as a design problem. "
                                              "I'm happiest untangling messy workflows, which is most of what a planner's day is.", delay=9)
    s.focus(await colbox("#gender"), 2.05, .8)
    await s.click("#gender .v", .45, .05); await s.wait(.25)
    await s.click("#gender .menu div >> nth=3", .35, .1)
    await s.click("#consent", .4, .1)
    await s.wait(.4)
    s.focus(await colbox("#submit"), 1.9, .8)
    await s.move(*(lambda b: (b[0] + b[2] / 2, b[1] + b[3] / 2))(await s.box("#submit")), .7)
    await s.wait(.5)
    s.wide(1.1)
    await s.wait(1.2)
    await s.stop()
    await p.goto(URL); await s.wait(.8)


async def review(s: Scene):
    p = s.page
    await nav(p, "jobs", "review")
    await s.start()
    s.wide(.01); await s.wait(.5)
    s.focus(await s.box(".queue"), 1.8, 1.0)
    await s.wait(.8)
    await s.click(".qi:has-text('Lumen Labs')", .8)
    await s.wait(.6)
    s.whole(.7)
    s.focus(await s.box(".section.ask"), 1.85, 1.0)
    await s.click(".section.ask select", .8)
    await p.select_option(".section.ask select", "Within 2 weeks"); await s.wait(.5)
    await s.click(".section.ask input[type=text]", .6)
    await p.locator(".section.ask input[type=text]").press_sequentially("No password needed", delay=30)
    await s.wait(.3)
    await s.click(".section.ask .btn.primary", .7)
    await s.wait(1.3)
    s.focus(await s.box(".d-foot"), 2.3, .9)
    await s.wait(.6)
    await s.click(".d-foot .btn.primary", .9)
    await s.wait(.9)
    s.wide(1.2)
    await s.wait(1.8)
    await s.wait(1.5)
    await s.stop()


async def track(s: Scene):
    p = s.page
    await nav(p, "jobs", "applied")
    await p.evaluate("stageFilter='all'; render()"); await s.wait(.5)
    await s.start()
    s.wide(.01); await s.wait(.5)
    s.focus(await s.box(".queue"), 1.8, 1.0)
    await s.wait(1.0)
    await s.click(".qi:has-text('Copperleaf')", .7)
    await s.wait(.5)
    s.focus(await s.box(".reply"), 2.2, 1.0)
    await s.wait(2.0)
    s.whole(.9)
    await s.click(".chips .pill:has-text('Rejected')", .8)
    await s.wait(1.4)
    await s.stop()


SCENES = {"standing": standing, "storybook": storybook, "find": find, "prepare": prepare, "fill": fill, "review": review, "track": track}


async def main(names):
    env = {**os.environ, "JHA_PROFILE": "profile.example", "JHA_DB": "data/demo.sqlite", "JHA_PORT": "8766"}
    srv = subprocess.Popen([sys.executable, "-m", "dashboard.app"], cwd=str(REPO), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        await asyncio.sleep(3)
        async with async_playwright() as pw:
            b = await pw.chromium.launch(args=["--force-device-scale-factor=2"])
            ctx = await b.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=2)
            page = await ctx.new_page()
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
