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
from .standing import standing_answer


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
        # files first: some ATSs (Ashby) parse an uploaded résumé and reset the form state, wiping earlier typing
        fields.sort(key=lambda f: 0 if f["type"] == "file" else 1)
        uploaded = False
        typed = []   # (selector, value, label) of plain text fills, re-checked before Submit
        for f in fields:
            if uploaded is True and f["type"] != "file":
                pg.wait_for_timeout(4000); uploaded = "done"
            sel = f'[id="{f["id"]}"]' if f["id"] else (f"[name=\"{f['name']}\"]" if f["name"] else
                  (f'[data-field-path="{f["path"]}"] {f["tag"]}' if f.get("path") else None))
            if not sel or "recaptcha" in (f["label"] + f["name"]).lower():
                continue
            lab = _norm(f["label"])
            if f["type"] == "file":
                key = lab + " " + _norm(f.get("id", "")) + " " + _norm(f.get("name", ""))
                if resume_pdf and re.search(r"\bresume\b|\bcv\b", key) and "cover" not in key:
                    pg.set_input_files(sel, resume_pdf); log.append(f"attached résumé → {f['label']}"); uploaded = uploaded or True
                continue
            if f["type"] == "checkbox" and pg.locator(sel).first.locator("xpath=..").locator("button[data-option]").count():
                # Ashby yes/no: two buttons next to a hidden checkbox
                ans = next((v for k, v in answers.items() if _norm(k) and _norm(k) in lab), None) or standing_answer(f["label"])
                if ans is not None:
                    choice = "yes" if str(ans).strip().lower() in ("yes", "on", "true", "y") else "no"
                    try:
                        pg.locator(sel).first.locator("xpath=..").locator(f'button[data-option="{choice}"]').click(timeout=5000)
                        log.append(f"chose {choice} → {f['label'][:50]}")
                    except Exception as e:
                        log.append(f"could not choose {f['label'][:40]}: {e.__class__.__name__}")
                elif f["required"]:
                    log.append(f"UNFILLED required: {f['label']}")
                continue
            if f["type"] in ("radio", "checkbox"):
                # one element per option: tick it when the group's answer names this option,
                # or when the option itself is a standing answer (a demographic choice or a "not a veteran" line)
                opt = (f.get("options") or [""])[0]
                grp = next((v for k, v in answers.items() if _norm(k) and _norm(k) in lab), None) or standing_answer(f["label"])
                own = standing_answer(opt)
                tick = (own == "Yes") if own in ("Yes", "No") else bool(grp and _norm(opt) and (_norm(opt) == _norm(grp) or _norm(opt) in _norm(grp)))
                if tick:
                    try:
                        pg.check(sel, force=True, timeout=5000); log.append(f"ticked {opt[:60] or f['label'][:60]}")
                    except Exception:
                        try:   # custom checkboxes: click the label or the wrapper instead of the hidden input
                            target = pg.locator(f'label[for="{f["id"]}"]').first if f["id"] else None
                            if target is None or not target.count():
                                target = pg.locator(sel).first.locator("xpath=..")
                            target.click(timeout=5000)
                            ok = pg.locator(sel).first.is_checked()
                            log.append(f"ticked {opt[:60] or f['label'][:60]}" if ok else f"could not tick {f['label'][:40]}")
                        except Exception as e:
                            log.append(f"could not tick {f['label'][:40]}: {e.__class__.__name__}")
                continue
            val = identity_answer(f["label"])          # legal name first; preferred name only in its own field
            if val is None:
                val = standing_answer(f["label"], f.get("options"))
            if val is None:
                val = next((v for k, v in answers.items() if _norm(k) and _norm(k) in lab), None)
            if val is None:
                if f["required"]: log.append(f"UNFILLED required: {f['label']}")
                continue
            if f["tag"] in ("input", "textarea") and f["type"] not in ("radio", "checkbox"):
                if f["type"] == "search" or not pg.locator(sel).first.is_visible():
                    continue   # hidden helpers (country pickers, comboboxes) are not answers
                try:
                    loc = pg.locator(sel).first
                    if loc.get_attribute("role") == "combobox" or loc.get_attribute("aria-autocomplete"):
                        # custom dropdowns (Greenhouse react-select): type, then pick the matching option
                        loc.click(timeout=5000); loc.fill(val, timeout=5000); pg.wait_for_timeout(500)
                        opt = pg.get_by_role("option", name=re.compile(rf"^\s*{re.escape(val)}", re.I)).first
                        if not opt.count() and "," in val:   # "Brooklyn, NY" vs "Brooklyn, New York, United States"
                            loc.fill(val.split(",")[0], timeout=5000); pg.wait_for_timeout(1200)
                            opt = pg.get_by_role("option", name=re.compile(re.escape(val.split(",")[0]), re.I)).first
                        (opt.click(timeout=3000) if opt.count() else pg.keyboard.press("Enter"))
                        log.append(f"chose {val[:30]} → {f['label'][:50]}")
                    else:
                        pg.fill(sel, val, timeout=5000); loc.press("Tab"); log.append(f"filled {f['label'][:60]}")
                        typed.append((sel, val, f["label"]))
                except Exception as e:
                    log.append(f"could not fill {f['label'][:40]}: {e.__class__.__name__}")
            elif f["tag"] == "select":
                pick = next((o for o in f.get("options") or [] if _norm(o) == _norm(val)), None) or next((o for o in f.get("options") or [] if _norm(val) and _norm(val) in _norm(o)), None)
                if pick:
                    try:
                        pg.select_option(sel, label=pick, timeout=5000); log.append(f"selected {pick[:40]} → {f['label'][:40]}")
                    except Exception as e:
                        log.append(f"could not select {f['label'][:40]}: {e.__class__.__name__}")
        pg.wait_for_timeout(1500)
        pg.screenshot(path=shot_path, full_page=True)
        result = {"ok": True, "log": log, "screenshot": shot_path, "submitted": False}
        if submit:
            def refill_cleared():
                for s_, v_, l_ in typed:
                    try:
                        if not pg.locator(s_).first.input_value(timeout=2000).strip():
                            pg.fill(s_, v_, timeout=5000); pg.locator(s_).first.press("Tab"); log.append(f"refilled {l_[:50]}")
                    except Exception:
                        pass
            refill_cleared()
            btn = pg.get_by_role("button", name=re.compile(r"submit", re.I)).first
            btn.click(); pg.wait_for_timeout(5000)
            body = pg.inner_text("body").lower()
            if re.search(r"missing entry for required field|needs corrections", body) and not any(w in body for w in ("thank", "successfully submitted")):
                refill_cleared()   # one retry after the form reset a field
                btn.click(); pg.wait_for_timeout(5000)
                body = pg.inner_text("body").lower()
            m = re.search(r"(missing entry for required field[^\n]*|needs corrections[^\n]*|this field is required[^\n]*)", body)
            if m and not any(w in body for w in ("thank", "received", "submitted")):
                result["needs_person"] = "form rejected: " + m.group(1)[:200]
            elif "recaptcha" in pg.content().lower() and not any(w in body for w in ("thank", "received", "submitted")):
                result["needs_person"] = "CAPTCHA or extra check shown; finish it in the browser window"
                if headed: pg.wait_for_timeout(180000); body = pg.inner_text("body").lower()
            result["submitted"] = any(w in body for w in ("thank", "received", "submitted", "application was"))
            pg.screenshot(path=shot_path.replace(".png", "-after.png"), full_page=True)
        b.close()
    return result
