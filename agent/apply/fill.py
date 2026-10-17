"""Fill an ATS application form in a real browser and stop before Submit.

fill(url, answers, resume_pdf, shot_path, submit=False, headed=False)
- answers: {label substring (lowercase ok): value}
- Never solves CAPTCHAs. If submit=True and a challenge appears, it waits for the person (headed mode) and reports it.
"""
from __future__ import annotations
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from .inspect_form import JS as FIELDS_JS
from .identity import identity_answer


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def fill(url: str, answers: dict[str, str], resume_pdf: str | None, shot_path: str, submit: bool = False,
         headed: bool = False) -> dict:
    log = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=not headed)
        pg = b.new_page(viewport={"width": 1280, "height": 1600})
        pg.goto(url, wait_until="networkidle", timeout=60000); pg.wait_for_timeout(1500)
        if "not found" in pg.inner_text("body")[:300].lower():
            b.close(); return {"ok": False, "error": "posting closed", "log": log}
        fields = pg.evaluate(FIELDS_JS)
        for f in fields:
            sel = f'[id="{f["id"]}"]' if f["id"] else (f"[name=\"{f['name']}\"]" if f["name"] else None)
            if not sel or "recaptcha" in (f["label"] + f["name"]).lower():
                continue
            lab = _norm(f["label"])
            if f["type"] == "file":
                if lab and resume_pdf and ("resume" in lab or "cv" in lab):
                    pg.set_input_files(sel, resume_pdf); log.append(f"attached résumé → {f['label']}")
                continue
            val = identity_answer(f["label"])          # legal name first; preferred name only in its own field
            if val is None:
                val = next((v for k, v in answers.items() if _norm(k) and _norm(k) in lab), None)
            if val is None:
                if f["required"]: log.append(f"UNFILLED required: {f['label']}")
                continue
            if f["tag"] in ("input", "textarea") and f["type"] not in ("radio", "checkbox"):
                pg.fill(sel, val); log.append(f"filled {f['label'][:60]}")
        pg.wait_for_timeout(1500)
        pg.screenshot(path=shot_path, full_page=True)
        result = {"ok": True, "log": log, "screenshot": shot_path, "submitted": False}
        if submit:
            btn = pg.get_by_role("button", name=re.compile(r"submit", re.I)).first
            btn.click(); pg.wait_for_timeout(5000)
            body = pg.inner_text("body").lower()
            if "recaptcha" in pg.content().lower() and not any(w in body for w in ("thank", "received", "submitted")):
                result["needs_person"] = "CAPTCHA or extra check shown; finish it in the browser window"
                if headed: pg.wait_for_timeout(180000); body = pg.inner_text("body").lower()
            result["submitted"] = any(w in body for w in ("thank", "received", "submitted", "application was"))
            pg.screenshot(path=shot_path.replace(".png", "-after.png"), full_page=True)
        b.close()
    return result
