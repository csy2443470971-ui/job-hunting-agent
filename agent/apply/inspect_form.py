"""Read an application form's fields from the live page (Ashby / Greenhouse job-boards), without submitting anything."""
from __future__ import annotations
import json, sys
from playwright.sync_api import sync_playwright

JS = r"""
() => {
  const out = [];
  const seen = new Set();
  const labelFor = (el) => {
    if (el.id) { const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`); if (l) return l.innerText.trim(); }
    const wrap = el.closest('[class*="field"], fieldset, .application-question, [class*="Field"], [class*="question"]');
    if (wrap) { const l = wrap.querySelector('label, legend, [class*="label"], [class*="title"]'); if (l) return l.innerText.trim(); }
    return el.getAttribute('aria-label') || el.name || el.placeholder || '';
  };
  document.querySelectorAll('input, textarea, select, [role="combobox"]').forEach(el => {
    if (el.type === 'hidden' || el.type === 'submit') return;
    let label = labelFor(el).replace(/\s+/g, ' ').slice(0, 300);
    const key = label + '|' + (el.name || el.id);
    if (seen.has(key)) return; seen.add(key);
    const wrap = el.closest('fieldset') || el.parentElement;
    let options = [];
    if (el.tagName === 'SELECT') options = [...el.options].map(o => o.text.trim()).filter(Boolean);
    if (el.type === 'radio' || el.type === 'checkbox') { const l = el.closest('label') || (el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`)); options = [l ? l.innerText.trim() : el.value]; }
    out.push({ label, tag: el.tagName.toLowerCase(), type: el.type || el.getAttribute('role'), name: el.name || '', id: el.id || '',
               required: el.required || el.getAttribute('aria-required') === 'true' || /\*\s*$/.test(label), options });
  });
  return out;
}
"""

def inspect(url: str) -> list[dict]:
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1280, "height": 1600})
        pg.goto(url, wait_until="networkidle", timeout=60000); pg.wait_for_timeout(1500)
        fields = pg.evaluate(JS); b.close()
    # merge radio/checkbox groups by label
    merged, idx = [], {}
    for f in fields:
        if f["type"] in ("radio", "checkbox") and f["name"]:
            k = f["name"]
            if k in idx: merged[idx[k]]["options"] += f["options"]; continue
            idx[k] = len(merged)
        merged.append(f)
    return merged

if __name__ == "__main__":
    for f in inspect(sys.argv[1]):
        print(("*" if f["required"] else " "), f["type"], "|", f["label"][:120], "|", f["options"][:6] if f["options"] else "")
